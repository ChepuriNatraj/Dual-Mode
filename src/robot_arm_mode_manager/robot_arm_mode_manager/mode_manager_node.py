import rclpy
from rclpy.node import Node
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from std_msgs.msg import String

class ModeManagerNode(Node):
    def __init__(self):
        super().__init__('mode_manager_node')
        
        self.declare_parameter('timeout_sec', 3.0)
        self.timeout_sec = self.get_parameter('timeout_sec').value
        
        # Current active mode: AUTONOMOUS, LOCAL, or REMOTE
        self.current_mode = "AUTONOMOUS"
        self.last_remote_time = self.get_clock().now()
        
        self.get_logger().info(f"Mode Manager started in {self.current_mode} mode")

        # Publishers
        self.arm_pub = self.create_publisher(JointTrajectory, '/arm_controller/joint_trajectory', 10)
        self.gripper_pub = self.create_publisher(JointTrajectory, '/gripper_controller/joint_trajectory', 10)
        self.mode_pub = self.create_publisher(String, '/current_system_mode', 10)
        
        # Subscribers for the three different input streams
        self.auto_arm_sub = self.create_subscription(
            JointTrajectory, '/auto_controller/joint_trajectory', self.auto_arm_cb, 10)
        self.auto_gripper_sub = self.create_subscription(
            JointTrajectory, '/auto_controller/gripper_trajectory', self.auto_gripper_cb, 10)
            
        self.local_arm_sub = self.create_subscription(
            JointTrajectory, '/local_controller/joint_trajectory', self.local_arm_cb, 10)
        self.local_gripper_sub = self.create_subscription(
            JointTrajectory, '/local_controller/gripper_trajectory', self.local_gripper_cb, 10)
            
        self.remote_arm_sub = self.create_subscription(
            JointTrajectory, '/remote_controller/joint_trajectory', self.remote_arm_cb, 10)
        self.remote_gripper_sub = self.create_subscription(
            JointTrajectory, '/remote_controller/gripper_trajectory', self.remote_gripper_cb, 10)
            
        # Subscriber to switch modes natively
        self.mode_sub = self.create_subscription(
            String, '/system_mode', self.mode_cb, 10)
            
        # Watchdog timer to check remote timeout and publish current mode
        self.timer = self.create_timer(0.5, self.timer_cb)

    def mode_cb(self, msg: String):
        new_mode = msg.data.upper()
        if new_mode in ["AUTONOMOUS", "LOCAL", "REMOTE"]:
            if new_mode != self.current_mode:
                self.get_logger().info(f"Mode switched from {self.current_mode} to {new_mode}")
                self.current_mode = new_mode
                if new_mode == "REMOTE":
                    self.last_remote_time = self.get_clock().now()
        else:
            self.get_logger().warn(f"Unknown mode requested: {new_mode}")

    def auto_arm_cb(self, msg: JointTrajectory):
        if self.current_mode == "AUTONOMOUS":
            self.arm_pub.publish(msg)

    def auto_gripper_cb(self, msg: JointTrajectory):
        if self.current_mode == "AUTONOMOUS":
            self.gripper_pub.publish(msg)

    def local_arm_cb(self, msg: JointTrajectory):
        if self.current_mode == "LOCAL":
            self.arm_pub.publish(msg)

    def local_gripper_cb(self, msg: JointTrajectory):
        if self.current_mode == "LOCAL":
            self.gripper_pub.publish(msg)

    def remote_arm_cb(self, msg: JointTrajectory):
        if self.current_mode == "REMOTE":
            self.last_remote_time = self.get_clock().now()
            self.arm_pub.publish(msg)

    def remote_gripper_cb(self, msg: JointTrajectory):
        if self.current_mode == "REMOTE":
            self.last_remote_time = self.get_clock().now()
            self.gripper_pub.publish(msg)

    def timer_cb(self):
        # Publish current mode
        mode_msg = String()
        mode_msg.data = self.current_mode
        self.mode_pub.publish(mode_msg)
        
        # Watchdog check
        if self.current_mode == "REMOTE":
            dt = (self.get_clock().now() - self.last_remote_time).nanoseconds / 1e9
            if dt > self.timeout_sec:
                self.get_logger().error(f"Remote connection lost for {dt:.1f}s! Aborting to AUTONOMOUS safe mode.")
                self.current_mode = "AUTONOMOUS"
                self.send_safe_home_pose()
                self.send_safe_open_gripper()
                
    def send_safe_home_pose(self):
        msg = JointTrajectory()
        msg.joint_names = ['link_1', 'link_2', 'link_3', 'link_4', 'link_5']
        pt = JointTrajectoryPoint()
        pt.positions = [0.0, 0.0, 0.0, 0.0, 0.0]
        pt.time_from_start.sec = 2
        pt.time_from_start.nanosec = 0
        msg.points.append(pt)
        self.arm_pub.publish(msg)

    def send_safe_open_gripper(self):
        msg = JointTrajectory()
        msg.joint_names = ['link_6']
        pt = JointTrajectoryPoint()
        pt.positions = [0.0] # Open gripper
        pt.time_from_start.sec = 1
        pt.time_from_start.nanosec = 0
        msg.points.append(pt)
        self.gripper_pub.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    node = ModeManagerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
