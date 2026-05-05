import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
import time
import threading

try:
    from moveit.planning import MoveItPy
    HAVE_MOVEIT_PY = True
except ImportError:
    HAVE_MOVEIT_PY = False

class FixedSequenceNode(Node):
    def __init__(self):
        super().__init__('fixed_sequence_node')

        # Publish to autonomous controller topics
        self.arm_pub = self.create_publisher(JointTrajectory, '/auto_controller/joint_trajectory', 10)
        self.gripper_pub = self.create_publisher(JointTrajectory, '/auto_controller/gripper_trajectory', 10)
        
        global HAVE_MOVEIT_PY
        if not HAVE_MOVEIT_PY:
            self.get_logger().error("moveit.planning not found!")
            return
            
        self.get_logger().info('Initializing MoveItPy...')
        try:
            self.robot = MoveItPy(node_name="fixed_sequence_planner")
            self.arm_group = self.robot.get_planning_component("arm")
            self.get_logger().info('Fixed sequence planner ready. Starting demo loop shortly...')
            
            # Start loop in a separate thread so node can spin
            self.demo_thread = threading.Thread(target=self.demo_loop)
            self.demo_thread.start()
        except Exception as e:
            self.get_logger().error(f"Failed to init MoveItPy: {e}")
            HAVE_MOVEIT_PY = False

    def publish_trajectory(self, trajectory):
        if trajectory is None:
            return False
        try:
            self.arm_pub.publish(trajectory)
            duration = trajectory.points[-1].time_from_start.sec + trajectory.points[-1].time_from_start.nanosec / 1e9
            time.sleep(max(2.0, duration))
            return True
        except Exception as e:
            self.get_logger().error(f"Failed to publish trajectory: {e}")
            return False

    def send_gripper_cmd(self, angle, delay=0.6):
        gripper_msg = JointTrajectory()
        gripper_msg.header.frame_id = "world"
        gripper_msg.header.stamp = self.get_clock().now().to_msg()
        gripper_msg.joint_names = ['link_6']
        pt = JointTrajectoryPoint()
        pt.positions = [angle]
        pt.time_from_start.sec = 0
        pt.time_from_start.nanosec = 500_000_000
        gripper_msg.points.append(pt)
        self.gripper_pub.publish(gripper_msg)
        time.sleep(delay)

    def plan_and_execute_pose(self, x, y, z):
        pose = PoseStamped()
        pose.header.frame_id = "world"
        pose.pose.position.x = x
        pose.pose.position.y = y
        pose.pose.position.z = z
        # Point straight down
        pose.pose.orientation.x = 0.0
        pose.pose.orientation.y = 1.0 # 180 degrees pitch
        pose.pose.orientation.z = 0.0
        pose.pose.orientation.w = 0.0
        
        self.arm_group.set_goal_state(pose_stamped_msg=pose, pose_link="link_5_1")
        plan_result = self.arm_group.plan()
        if plan_result and hasattr(plan_result, 'trajectory'):
            return self.publish_trajectory(plan_result.trajectory)
        else:
            self.get_logger().warn(f"Failed to plan to pose: x={x:.2f}, y={y:.2f}, z={z:.2f}")
            return False

    def demo_loop(self):
        # Give MoveIt state some time to stabilize
        time.sleep(2.0)
        cycle_count = 1
        
        while rclpy.ok():
            self.get_logger().info(f'--- STARTING FIXED DEMO CYCLE {cycle_count} ---')
            
            # FIXED POSITIONS FOR A CANNED DEMO
            home_config = "initial"
            pick_x, pick_y = 0.25, 0.0     # Somewhere straight ahead
            place_x, place_y = 0.15, 0.20  # Somewhere to the side
            grasp_z = 0.04
            hover_z = 0.15
            
            # 1. Start Home
            self.get_logger().info('Moving to Home')
            self.arm_group.set_goal_state(configuration_name=home_config)
            plan = self.arm_group.plan()
            if plan: self.publish_trajectory(plan.trajectory)
            
            # 2. Open Gripper
            self.get_logger().info('Opening Gripper')
            self.send_gripper_cmd(0.0)

            # 3. Pre-grasp (Hover over pick location)
            self.get_logger().info('Pre-grasp hover')
            self.plan_and_execute_pose(pick_x, pick_y, hover_z)
            
            # 4. Grasp descend
            self.get_logger().info('Descend to grasp')
            self.plan_and_execute_pose(pick_x, pick_y, grasp_z)

            # 5. Close Gripper
            self.get_logger().info('Closing Gripper')
            self.send_gripper_cmd(-1.04)

            # 6. Lift
            self.get_logger().info('Lifting object')
            self.plan_and_execute_pose(pick_x, pick_y, hover_z)

            # 7. Move to drop area
            self.get_logger().info('Moving to Drop Bin')
            self.plan_and_execute_pose(place_x, place_y, hover_z)

            # 8. Descend slightly (optional)
            self.plan_and_execute_pose(place_x, place_y, grasp_z + 0.05)

            # 9. Release
            self.get_logger().info('Releasing object')
            self.send_gripper_cmd(0.0)

            # 10. Lift
            self.plan_and_execute_pose(place_x, place_y, hover_z)
            
            self.get_logger().info(f'--- CYCLE {cycle_count} COMPLETE ---')
            cycle_count += 1
            time.sleep(1.0)

def main(args=None):
    rclpy.init(args=args)
    node = FixedSequenceNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
