import rclpy
from rclpy.node import Node
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint

import paho.mqtt.client as mqtt
import json

class MqttBridgeNode(Node):
    def __init__(self):
        super().__init__('mqtt_bridge_node')

        # Parameters (overridable via ros2 launch / ros-args)
        self.declare_parameter('broker', 'broker.emqx.io')
        self.declare_parameter('port', 1883)
        self.declare_parameter('topic', 'natraj/robot_arm/teleop/target_state')
        self.declare_parameter('telemetry_topic', 'natraj/robot_arm/teleop/state')
        self.declare_parameter('mqtt_timeout_sec', 3.0)
        self.declare_parameter('client_id', '')

        # Unified safety bounds (must match local gesture + hardware calibration)
        self.arm_ranges = [(-3.14, 3.14), (-1.0, 1.0), (-1.0, 1.0), (-1.57, 1.57), (-1.57, 1.57)]
        self.gripper_range = (-1.0472, 0.0)

        # ROS 2 Publishers to local /arm_controller & /gripper_controller
        self.arm_pub = self.create_publisher(JointTrajectory, '/arm_controller/joint_trajectory', 10)
        self.gripper_pub = self.create_publisher(JointTrajectory, '/gripper_controller/joint_trajectory', 10)

        # Read params
        self.broker = str(self.get_parameter('broker').value)
        self.port = int(self.get_parameter('port').value)
        self.topic = str(self.get_parameter('topic').value)
        self.telemetry_topic = str(self.get_parameter('telemetry_topic').value)
        self.mqtt_timeout = float(self.get_parameter('mqtt_timeout_sec').value)
        client_id = str(self.get_parameter('client_id').value) or None

        # MQTT client
        self.client = mqtt.Client(client_id=client_id)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

        self.rx_count = 0
        self.last_rx_ts = None
        self.last_arm = [0.0] * 5
        self.last_grip = 0.0

        self.get_logger().info(f"Connecting to MQTT broker at {self.broker}:{self.port}...")
        try:
            self.client.connect(self.broker, self.port, 60)
            self.client.loop_start()
        except Exception as e:
            self.get_logger().error(f"MQTT connect failed: {e}")

        # Watchdog timer to detect MQTT dropout/safety
        self.create_timer(0.5, self._watchdog_tick)

    def on_connect(self, client, userdata, flags, rc):
        self.get_logger().info(f"Connected to HiveMQ with result code {rc}")
        self.client.subscribe(self.topic)
        self.get_logger().info(f"Subscribed to topic: {self.topic}")

    def on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode('utf-8'))

            if 'arm_angles' not in payload or 'gripper_angle' not in payload:
                self.get_logger().warn(f"Invalid payload keys on {msg.topic}: {payload}")
                return

            arr_angles = payload['arm_angles']
            grip_angle = payload['gripper_angle']

            if not isinstance(arr_angles, list) or len(arr_angles) != 5:
                self.get_logger().warn(f"Invalid arm_angles length/type: {arr_angles}")
                return

            arr_angles = [self.clamp(float(v), *self.arm_ranges[i]) for i, v in enumerate(arr_angles)]
            grip_angle = self.clamp(float(grip_angle), *self.gripper_range)

            # Send to local ROS2 system
            self.publish_arm(arr_angles)
            self.publish_gripper(grip_angle)

            # Save last seen for telemetry and watchdog
            self.last_arm = arr_angles
            self.last_grip = grip_angle
            self.last_rx_ts = self.get_clock().now()

            self.rx_count += 1
            if self.rx_count % 20 == 0:
                self.get_logger().info(f"MQTT messages received: {self.rx_count}")
            
        except Exception as e:
            self.get_logger().error(f"Error parsing MQTT message: {e}")

    def publish_arm(self, angles):
        msg = JointTrajectory()
        msg.joint_names = ['link_1', 'link_2', 'link_3', 'link_4', 'link_5']
        point = JointTrajectoryPoint()
        point.positions = angles
        point.time_from_start.sec = 0
        point.time_from_start.nanosec = 200_000_000 # 200ms target execution time
        msg.points.append(point)
        self.arm_pub.publish(msg)

    def publish_gripper(self, angle):
        msg = JointTrajectory()
        msg.joint_names = ['link_6']
        point = JointTrajectoryPoint()
        point.positions = [angle]
        point.time_from_start.sec = 0
        point.time_from_start.nanosec = 200_000_000
        msg.points.append(point)
        self.gripper_pub.publish(msg)
        # Optionally publish telemetry back to MQTT clients
        try:
            payload = json.dumps({
                'arm_angles': [float(x) for x in self.last_arm],
                'gripper_angle': float(self.last_grip),
                'rx_count': self.rx_count,
                'ts': int(self.get_clock().now().nanoseconds / 1_000_000)
            })
            # Use low QoS, non-blocking
            if getattr(self, 'telemetry_topic', None):
                self.client.publish(self.telemetry_topic, payload, qos=0)
        except Exception:
            pass

    def _watchdog_tick(self):
        # If we've not received any MQTT messages within mqtt_timeout, issue a warning.
        if self.last_rx_ts is None:
            return
        age = (self.get_clock().now() - self.last_rx_ts).nanoseconds / 1_000_000_000.0
        if age > self.mqtt_timeout:
            self.get_logger().warn(f"No MQTT messages for {age:.1f}s (timeout={self.mqtt_timeout}s).")

    @staticmethod
    def clamp(value, low, high):
        return max(low, min(high, value))

def main(args=None):
    rclpy.init(args=args)
    node = MqttBridgeNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.client.loop_stop()
        node.client.disconnect()
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
