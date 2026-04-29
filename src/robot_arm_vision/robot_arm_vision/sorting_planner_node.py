import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
import time

# NOTE: Since moveit_py might not be fully configured in the environment 
# until the launch file includes MoveIt configs, we import conditionally or 
# catch setup errors. This is the skeleton for MoveIt2 MoveGroup Python integration.
try:
    from moveit.planning import MoveItPy
    HAVE_MOVEIT_PY = True
except ImportError:
    HAVE_MOVEIT_PY = False

class SortingPlannerNode(Node):
    def __init__(self):
        super().__init__('sorting_planner_node')

        # Tunable approach values for small tabletop cubes.
        self.pre_grasp_hover = 0.12
        self.grasp_offset = 0.01
        self.lift_offset = 0.12
        self.min_reach_x = 0.15
        self.max_reach_x = 0.42
        self.min_reach_y = -0.20
        self.max_reach_y = 0.20
        
        # Subscribe to vision target
        self.pose_sub = self.create_subscription(
            PoseStamped,
            '/target_pose',
            self.target_callback,
            1)
        
        # Publish to autonomous controller (mode_manager will arbitrate)
        self.arm_pub = self.create_publisher(JointTrajectory, '/auto_controller/joint_trajectory', 10)
        self.gripper_pub = self.create_publisher(JointTrajectory, '/auto_controller/gripper_trajectory', 10)
            
        self.is_busy = False
        
        global HAVE_MOVEIT_PY
        if not HAVE_MOVEIT_PY:
            self.get_logger().error("moveit.planning not found! Please ensure 'moveit_py' is installed to use arm planning.")
            return
            
        self.get_logger().info('Initializing MoveItPy...')
        try:
            # MoveItPy requires a node name
            self.robot = MoveItPy(node_name="sorting_planner")
            self.arm_group = self.robot.get_planning_component("arm")
            self.gripper_group = self.robot.get_planning_component("gripper")
            
            # Get the controller manager to execute trajectories
            self.controller_manager = self.robot._control_node
            self.get_logger().info('Sorting planner ready. Waiting for targets...')
        except Exception as e:
            self.get_logger().error(f"Failed to init MoveItPy: {e}")
            HAVE_MOVEIT_PY = False
        
    def target_callback(self, msg):
        if self.is_busy or not HAVE_MOVEIT_PY:
            return
            
        self.is_busy = True
        self.get_logger().info('Received target. Planning sequence...')
        
        try:
            self.execute_pick_and_place(msg.pose.position)
        except Exception as e:
            self.get_logger().error(f'Failure in pipeline: {e}')
            
        self.is_busy = False

    def execute_pick_and_place(self, position):
        if not (self.min_reach_x <= position.x <= self.max_reach_x and self.min_reach_y <= position.y <= self.max_reach_y):
            self.get_logger().warn(
                f"Target out of reachable window: x={position.x:.3f}, y={position.y:.3f}. "
                f"Expected x in [{self.min_reach_x:.2f},{self.max_reach_x:.2f}], "
                f"y in [{self.min_reach_y:.2f},{self.max_reach_y:.2f}]"
            )
            return

        self.get_logger().info('--- STARTED AI SORTING LOOP ---')
        
        # Helper function to execute and publish a trajectory
        def publish_trajectory(group, trajectory):
            """Extract trajectory from plan and publish directly to mode_manager."""
            if trajectory is None:
                return False
            try:
                # Publish to auto_controller topic so mode_manager can arbitrate
                self.arm_pub.publish(trajectory)
                # Wait for execution (approximate - use MoveIt's actual execution timing)
                time.sleep(max(2.0, trajectory.points[-1].time_from_start.sec + 
                              trajectory.points[-1].time_from_start.nanosec / 1e9))
                return True
            except Exception as e:
                self.get_logger().error(f"Failed to publish trajectory: {e}")
                return False
        
        # 1. Pre-Grasp
        self.get_logger().info('1. Planning Pre-Grasp')
        pre_grasp_pose = PoseStamped()
        pre_grasp_pose.header.frame_id = "world"
        pre_grasp_pose.pose.position.x = position.x
        pre_grasp_pose.pose.position.y = position.y
        pre_grasp_pose.pose.position.z = position.z + self.pre_grasp_hover
        pre_grasp_pose.pose.orientation.x = 0.0
        pre_grasp_pose.pose.orientation.y = 1.0 # Pitch down
        pre_grasp_pose.pose.orientation.z = 0.0
        pre_grasp_pose.pose.orientation.w = 0.0
        
        self.arm_group.set_goal_state(pose_stamped_msg=pre_grasp_pose, pose_link="link_6")
        plan_result = self.arm_group.plan()
        if plan_result and hasattr(plan_result, 'trajectory'):
            publish_trajectory(self.arm_group, plan_result.trajectory)
        else:
            raise Exception("Failed to plan to pre-grasp")

        # 2. Open Gripper
        self.get_logger().info('2. Opening Gripper')
        self.gripper_group.set_goal_state(configuration_name="open")
        plan_result = self.gripper_group.plan()
        if plan_result and hasattr(plan_result, 'trajectory'):
            # Publish gripper trajectory
            gripper_msg = JointTrajectory()
            gripper_msg.header.frame_id = "world"
            gripper_msg.header.stamp = self.get_clock().now().to_msg()
            gripper_msg.joint_names = ['link_6']
            pt = JointTrajectoryPoint()
            pt.positions = [0.0]  # Open position
            pt.time_from_start.sec = 0
            pt.time_from_start.nanosec = 500_000_000  # 0.5s
            gripper_msg.points.append(pt)
            self.arm_pub.publish(gripper_msg)
            time.sleep(0.6)

        # 3. Grasp
        self.get_logger().info('3. Moving to Grasp')
        grasp_pose = PoseStamped()
        grasp_pose.header.frame_id = "world"
        grasp_pose.pose.position.x = position.x
        grasp_pose.pose.position.y = position.y
        grasp_pose.pose.position.z = position.z + self.grasp_offset
        grasp_pose.pose.orientation = pre_grasp_pose.pose.orientation
        self.arm_group.set_goal_state(pose_stamped_msg=grasp_pose, pose_link="link_6")
        plan_result = self.arm_group.plan()
        if plan_result and hasattr(plan_result, 'trajectory'):
            publish_trajectory(self.arm_group, plan_result.trajectory)
        else:
            raise Exception("Failed to plan to grasp")

        # 4. Close Gripper
        self.get_logger().info('4. Closing Gripper')
        self.gripper_group.set_goal_state(configuration_name="close")
        plan_result = self.gripper_group.plan()
        if plan_result and hasattr(plan_result, 'trajectory'):
            gripper_msg = JointTrajectory()
            gripper_msg.header.frame_id = "world"
            gripper_msg.header.stamp = self.get_clock().now().to_msg()
            gripper_msg.joint_names = ['link_6']
            pt = JointTrajectoryPoint()
            pt.positions = [-1.0472]  # Close position (~60 degrees)
            pt.time_from_start.sec = 0
            pt.time_from_start.nanosec = 500_000_000
            gripper_msg.points.append(pt)
            self.arm_pub.publish(gripper_msg)
            time.sleep(0.6)

        # 5. Lift up
        self.get_logger().info('5. Lifting Object')
        lift_pose = PoseStamped()
        lift_pose.header.frame_id = "world"
        lift_pose.pose.position.x = position.x
        lift_pose.pose.position.y = position.y
        lift_pose.pose.position.z = position.z + self.lift_offset
        lift_pose.pose.orientation = pre_grasp_pose.pose.orientation
        self.arm_group.set_goal_state(pose_stamped_msg=lift_pose, pose_link="link_6")
        plan_result = self.arm_group.plan()
        if plan_result and hasattr(plan_result, 'trajectory'):
            publish_trajectory(self.arm_group, plan_result.trajectory)

        # 6. Drop Area
        self.get_logger().info('6. Moving to Drop Bin')
        drop_pose = PoseStamped()
        drop_pose.header.frame_id = "world"
        drop_pose.pose.position.x = 0.24
        drop_pose.pose.position.y = -0.14
        drop_pose.pose.position.z = 0.16
        drop_pose.pose.orientation.y = 1.0
        
        self.arm_group.set_goal_state(pose_stamped_msg=drop_pose, pose_link="link_6")
        plan_result = self.arm_group.plan()
        if plan_result and hasattr(plan_result, 'trajectory'):
            publish_trajectory(self.arm_group, plan_result.trajectory)

        # 7. Open
        self.get_logger().info('7. Releasing Object')
        self.gripper_group.set_goal_state(configuration_name="open")
        plan_result = self.gripper_group.plan()
        if plan_result and hasattr(plan_result, 'trajectory'):
            gripper_msg = JointTrajectory()
            gripper_msg.header.frame_id = "world"
            gripper_msg.header.stamp = self.get_clock().now().to_msg()
            gripper_msg.joint_names = ['link_6']
            pt = JointTrajectoryPoint()
            pt.positions = [0.0]  # Open position
            pt.time_from_start.sec = 0
            pt.time_from_start.nanosec = 500_000_000
            gripper_msg.points.append(pt)
            self.arm_pub.publish(gripper_msg)
            time.sleep(0.6)
        
        # 8. Home
        self.get_logger().info('8. Returning Home')
        self.arm_group.set_goal_state(configuration_name="home")
        plan_result = self.arm_group.plan()
        if plan_result and hasattr(plan_result, 'trajectory'):
            publish_trajectory(self.arm_group, plan_result.trajectory)
            
        self.get_logger().info('--- CYCLE COMPLETE ---')

def main(args=None):
    rclpy.init(args=args)
    node = SortingPlannerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
