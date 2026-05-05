import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
import time

try:
    from moveit.planning import MoveItPy
    HAVE_MOVEIT_PY = True
except ImportError:
    HAVE_MOVEIT_PY = False

class SortingPlannerNode(Node):
    def __init__(self):
        super().__init__('sorting_planner_node')

        self.declare_parameter('pre_grasp_hover', 0.12)
        self.declare_parameter('grasp_offset', 0.01)
        self.declare_parameter('lift_offset', 0.12)
        self.declare_parameter('min_reach_x', 0.15)
        self.declare_parameter('max_reach_x', 0.42)
        self.declare_parameter('min_reach_y', -0.25)
        self.declare_parameter('max_reach_y', 0.25)

        self.pre_grasp_hover = float(self.get_parameter('pre_grasp_hover').value)
        self.grasp_offset = float(self.get_parameter('grasp_offset').value)
        self.lift_offset = float(self.get_parameter('lift_offset').value)
        self.min_reach_x = float(self.get_parameter('min_reach_x').value)
        self.max_reach_x = float(self.get_parameter('max_reach_x').value)
        self.min_reach_y = float(self.get_parameter('min_reach_y').value)
        self.max_reach_y = float(self.get_parameter('max_reach_y').value)
        
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
            
            # Note: We won't use MoveItPy for the gripper, we will just publish direct trajectories.
            self.controller_manager = self.robot._control_node
            self.get_logger().info('Sorting planner ready. Waiting for targets...')
        except Exception as e:
            self.get_logger().error(f"Failed to init MoveItPy: {e}")
            HAVE_MOVEIT_PY = False
        
    def target_callback(self, msg):
        if self.is_busy or not HAVE_MOVEIT_PY:
            return
            
        self.is_busy = True
        self.get_logger().info(
            f'Received target: x={msg.pose.position.x:.3f}, '
            f'y={msg.pose.position.y:.3f}, z={msg.pose.position.z:.3f}. Planning sequence...'
        )
        
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
        
        def as_joint_trajectory(trajectory):
            """MoveItPy usually returns moveit_msgs/RobotTrajectory; controllers need JointTrajectory."""
            if trajectory is None:
                return None
            if isinstance(trajectory, JointTrajectory):
                return trajectory
            if hasattr(trajectory, 'joint_trajectory'):
                return trajectory.joint_trajectory
            if hasattr(trajectory, 'trajectory') and hasattr(trajectory.trajectory, 'joint_trajectory'):
                return trajectory.trajectory.joint_trajectory
            return None

        def publish_trajectory(trajectory, label):
            joint_trajectory = as_joint_trajectory(trajectory)
            if joint_trajectory is None:
                self.get_logger().error(
                    f"{label}: plan did not contain a publishable JointTrajectory "
                    f"(type={type(trajectory).__name__})"
                )
                return False
            if not joint_trajectory.points:
                self.get_logger().error(f"{label}: planned JointTrajectory has no points")
                return False
            try:
                joint_trajectory.header.stamp = self.get_clock().now().to_msg()
                self.arm_pub.publish(joint_trajectory)
                last_point = joint_trajectory.points[-1]
                duration = last_point.time_from_start.sec + last_point.time_from_start.nanosec / 1e9
                self.get_logger().info(
                    f"{label}: published {len(joint_trajectory.points)} points "
                    f"for joints {list(joint_trajectory.joint_names)}"
                )
                time.sleep(max(2.0, duration))
                return True
            except Exception as e:
                self.get_logger().error(f"{label}: failed to publish trajectory: {e}")
                return False

        def send_gripper_cmd(angle, _delay=0.6):
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
            time.sleep(_delay)

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
        
        self.arm_group.set_start_state_to_current_state()
        self.arm_group.set_goal_state(pose_stamped_msg=pre_grasp_pose, pose_link="link_5_1")
        plan_result = self.arm_group.plan()
        if plan_result and hasattr(plan_result, 'trajectory'):
            if not publish_trajectory(plan_result.trajectory, "pre-grasp"):
                raise Exception("Failed to publish pre-grasp trajectory")
        else:
            raise Exception("Failed to plan to pre-grasp")

        # 2. Open Gripper
        self.get_logger().info('2. Opening Gripper')
        send_gripper_cmd(0.0) # Open position

        # 3. Grasp
        self.get_logger().info('3. Moving to Grasp')
        grasp_pose = PoseStamped()
        grasp_pose.header.frame_id = "world"
        grasp_pose.pose.position.x = position.x
        grasp_pose.pose.position.y = position.y
        grasp_pose.pose.position.z = position.z + self.grasp_offset
        grasp_pose.pose.orientation = pre_grasp_pose.pose.orientation
        self.arm_group.set_start_state_to_current_state()
        self.arm_group.set_goal_state(pose_stamped_msg=grasp_pose, pose_link="link_5_1")
        plan_result = self.arm_group.plan()
        if plan_result and hasattr(plan_result, 'trajectory'):
            if not publish_trajectory(plan_result.trajectory, "grasp"):
                raise Exception("Failed to publish grasp trajectory")
        else:
            raise Exception("Failed to plan to grasp")

        # 4. Close Gripper
        self.get_logger().info('4. Closing Gripper')
        send_gripper_cmd(-1.0472) # Close position

        # 5. Lift up
        self.get_logger().info('5. Lifting Object')
        lift_pose = PoseStamped()
        lift_pose.header.frame_id = "world"
        lift_pose.pose.position.x = position.x
        lift_pose.pose.position.y = position.y
        lift_pose.pose.position.z = position.z + self.lift_offset
        lift_pose.pose.orientation = pre_grasp_pose.pose.orientation
        self.arm_group.set_start_state_to_current_state()
        self.arm_group.set_goal_state(pose_stamped_msg=lift_pose, pose_link="link_5_1")
        plan_result = self.arm_group.plan()
        if plan_result and hasattr(plan_result, 'trajectory'):
            if not publish_trajectory(plan_result.trajectory, "lift"):
                raise Exception("Failed to publish lift trajectory")
        else:
            raise Exception("Failed to plan lift")

        # 6. Drop Area
        self.get_logger().info('6. Moving to Drop Bin')
        drop_pose = PoseStamped()
        drop_pose.header.frame_id = "world"
        drop_pose.pose.position.x = 0.24
        drop_pose.pose.position.y = -0.14
        drop_pose.pose.position.z = 0.16
        drop_pose.pose.orientation.y = 1.0
        
        self.arm_group.set_start_state_to_current_state()
        self.arm_group.set_goal_state(pose_stamped_msg=drop_pose, pose_link="link_5_1")
        plan_result = self.arm_group.plan()
        if plan_result and hasattr(plan_result, 'trajectory'):
            if not publish_trajectory(plan_result.trajectory, "drop"):
                raise Exception("Failed to publish drop trajectory")
        else:
            raise Exception("Failed to plan drop")

        # 7. Open
        self.get_logger().info('7. Releasing Object')
        send_gripper_cmd(0.0)
        
        # 8. Home
        self.get_logger().info('8. Returning Home')
        self.arm_group.set_start_state_to_current_state()
        self.arm_group.set_goal_state(configuration_name="initial")
        plan_result = self.arm_group.plan()
        if plan_result and hasattr(plan_result, 'trajectory'):
            if not publish_trajectory(plan_result.trajectory, "home"):
                raise Exception("Failed to publish home trajectory")
        else:
            raise Exception("Failed to plan home")
            
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
