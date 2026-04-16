#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint

class HardwareTester(Node):
    def __init__(self):
        super().__init__('hardware_tester')
        
        self.arm_pub = self.create_publisher(JointTrajectory, '/arm_controller/joint_trajectory', 10)
        self.grip_pub = self.create_publisher(JointTrajectory, '/gripper_controller/joint_trajectory', 10)
        self.sub = self.create_subscription(JointState, '/gui_joint_positions', self.joint_cb, 10)
        
        self.arm_joints = ['link_1', 'link_2', 'link_3', 'link_4', 'link_5']
        self.grip_joints = ['link_6']

    def joint_cb(self, msg: JointState):
        arm_traj = JointTrajectory()
        arm_traj.joint_names = self.arm_joints
        arm_pt = JointTrajectoryPoint()
        
        grip_traj = JointTrajectory()
        grip_traj.joint_names = self.grip_joints
        grip_pt = JointTrajectoryPoint()
        
        for j in self.arm_joints:
            if j in msg.name:
                idx = msg.name.index(j)
                arm_pt.positions.append(msg.position[idx])
            else:
                arm_pt.positions.append(0.0)
                
        for j in self.grip_joints:
            if j in msg.name:
                idx = msg.name.index(j)
                grip_pt.positions.append(msg.position[idx])
            else:
                grip_pt.positions.append(0.0)
                
        arm_pt.time_from_start.sec = 0
        arm_pt.time_from_start.nanosec = 200000000  # 0.2s smoothing
        arm_traj.points = [arm_pt]
        self.arm_pub.publish(arm_traj)
        
        grip_pt.time_from_start.sec = 0
        grip_pt.time_from_start.nanosec = 200000000
        grip_traj.points = [grip_pt]
        self.grip_pub.publish(grip_traj)

def main():
    rclpy.init()
    node = HardwareTester()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
