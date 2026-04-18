#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
import time

class StressTester(Node):
    def __init__(self):
        super().__init__('stress_tester')
        
        self.arm_pub = self.create_publisher(JointTrajectory, '/arm_controller/joint_trajectory', 10)
        
        self.total_cycles = 50
        self.current_cycle = 1
        
        self.get_logger().info(f"Starting {self.total_cycles}-cycle hardware stress test...")
        
        # Give hardware interface a second to warm up
        time.sleep(2.0)
        
        self.timer = self.create_timer(4.0, self.run_cycle) # 4 seconds per cycle

    def run_cycle(self):
        if self.current_cycle > self.total_cycles:
            self.get_logger().info("Stress test completed successfully!")
            self.destroy_timer(self.timer)
            rclpy.shutdown()
            return
            
        self.get_logger().info(f"Executing cycle {self.current_cycle}/{self.total_cycles}")
        
        # We simulate a "pick and place" sweeping motion spanning the servo limits
        msg = JointTrajectory()
        msg.joint_names = ['link_1', 'link_2', 'link_3', 'link_4', 'link_5']
        
        # Target A: Extend outward and twist
        pt_ext = JointTrajectoryPoint()
        pt_ext.positions = [1.0, 0.5, 0.5, 0.5, 1.0] # Radians
        pt_ext.time_from_start.sec = 1
        pt_ext.time_from_start.nanosec = 500_000_000
        
        # Target B: Return to Base / Home orientation
        pt_home = JointTrajectoryPoint()
        pt_home.positions = [0.0, 0.0, 0.0, 0.0, 0.0]
        pt_home.time_from_start.sec = 3
        pt_home.time_from_start.nanosec = 500_000_000

        msg.points = [pt_ext, pt_home]
        
        # Publish trajectory to override standard positions
        self.arm_pub.publish(msg)
        self.current_cycle += 1

def main():
    rclpy.init()
    node = StressTester()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass

if __name__ == '__main__':
    main()
