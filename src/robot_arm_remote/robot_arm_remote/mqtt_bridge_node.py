import rclpy
from rclpy.node import Node
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint

import paho.mqtt.client as mqtt
import json

class MqttBridgeNode(Node):
    def __init__(self):
        super().__init__('mqtt_bridge_node')

        # Unified safety bounds (must match local gesture + hardware calibration)
        self.arm_ranges = [(-1.57, 1.57), (-1.0, 1.0), (-1.0, 1.0), (-1.57, 1.57), (-1.57, 1.57)]
        self.gripper_range = (-1.0472, 0.0)
        
        # ROS 2 Publishers to local /arm_controller & /gripper_controller
        self.arm_pub = self.create_publisher(JointTrajectory, '/arm_controller/joint_trajectory', 10)
        self.gripper_pub = self.create_publisher(JointTrajectory, '/gripper_controller/joint_trajectory', 10)

        # Connect to public HiveMQ WebSocket broker
        self.broker = "broker.hivemq.com"
        self.port = 1883
        self.topic = "natraj/robot_arm/teleop/target_state"
        
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

        self.rx_count = 0
        
        self.get_logger().info(f"Connecting to MQTT broker at {self.broker}:{self.port}...")
        self.client.connect(self.broker, self.port, 60)
        self.client.loop_start()

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
