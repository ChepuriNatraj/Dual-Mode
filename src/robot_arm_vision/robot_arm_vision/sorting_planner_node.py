import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped
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
        
        # Subscribe to vision target
        self.pose_sub = self.create_subscription(
            PoseStamped,
            '/target_pose',
            self.target_callback,
            1)
            
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
        self.get_logger().info('--- STARTED AI SORTING LOOP ---')
        
        # 1. Pre-Grasp
        self.get_logger().info('1. Planning Pre-Grasp')
        pre_grasp_pose = PoseStamped()
        pre_grasp_pose.header.frame_id = "world"
        pre_grasp_pose.pose.position.x = position.x
        pre_grasp_pose.pose.position.y = position.y
        pre_grasp_pose.pose.position.z = position.z + 0.15  # 15cm hover
        pre_grasp_pose.pose.orientation.x = 0.0
        pre_grasp_pose.pose.orientation.y = 1.0 # Pitch down
        pre_grasp_pose.pose.orientation.z = 0.0
        pre_grasp_pose.pose.orientation.w = 0.0
        
        self.arm_group.set_goal_state(pose_stamped_msg=pre_grasp_pose, pose_link="link_6") # Adjust link to your tip link
        plan_result = self.arm_group.plan()
        if plan_result:
            self.robot.execute(plan_result.trajectory, controllers=[])
        else:
            raise Exception("Failed to plan to pre-grasp")

        # 2. Open Gripper
        self.get_logger().info('2. Opening Gripper')
        self.gripper_group.set_goal_state(configuration_name="open")
        plan_result = self.gripper_group.plan()
        if plan_result:
            self.robot.execute(plan_result.trajectory, controllers=[])

        # 3. Grasp
        self.get_logger().info('3. Moving to Grasp')
        grasp_pose = pre_grasp_pose
        grasp_pose.pose.position.z = position.z + 0.02
        self.arm_group.set_goal_state(pose_stamped_msg=grasp_pose, pose_link="link_6")
        plan_result = self.arm_group.plan()
        if plan_result:
            self.robot.execute(plan_result.trajectory, controllers=[])

        # 4. Close Gripper
        self.get_logger().info('4. Closing Gripper')
        self.gripper_group.set_goal_state(configuration_name="close")
        plan_result = self.gripper_group.plan()
        if plan_result:
            self.robot.execute(plan_result.trajectory, controllers=[])

        # 5. Lift up
        self.get_logger().info('5. Lifting Object')
        self.arm_group.set_goal_state(pose_stamped_msg=pre_grasp_pose, pose_link="link_6")
        plan_result = self.arm_group.plan()
        if plan_result:
            self.robot.execute(plan_result.trajectory, controllers=[])

        # 6. Drop Area
        self.get_logger().info('6. Moving to Drop Bin')
        drop_pose = PoseStamped()
        drop_pose.header.frame_id = "world"
        drop_pose.pose.position.x = 0.3
        drop_pose.pose.position.y = -0.3 # Negative Y Drop Bin
        drop_pose.pose.position.z = 0.2
        drop_pose.pose.orientation.y = 1.0
        
        self.arm_group.set_goal_state(pose_stamped_msg=drop_pose, pose_link="link_6")
        plan_result = self.arm_group.plan()
        if plan_result:
            self.robot.execute(plan_result.trajectory, controllers=[])

        # 7. Open
        self.get_logger().info('7. Releasing Object')
        self.gripper_group.set_goal_state(configuration_name="open")
        plan_result = self.gripper_group.plan()
        if plan_result:
            self.robot.execute(plan_result.trajectory, controllers=[])
        
        # 8. Home
        self.get_logger().info('8. Returning Home')
        self.arm_group.set_goal_state(configuration_name="home")
        plan_result = self.arm_group.plan()
        if plan_result:
            self.robot.execute(plan_result.trajectory, controllers=[])
            
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
