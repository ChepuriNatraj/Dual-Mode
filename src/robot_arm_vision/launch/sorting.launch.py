from launch import LaunchDescription
from launch_ros.actions import Node
from moveit_configs_utils import MoveItConfigsBuilder

def generate_launch_description():
    moveit_config = MoveItConfigsBuilder("robotic_arm", package_name="robot_arm_moveit2").to_moveit_configs()

    sorting_planner_node = Node(
        package="robot_arm_vision",
        executable="sorting_planner_node",
        name="sorting_planner",
        parameters=[
            moveit_config.to_dict(),
            {"use_sim_time": True},
        ],
        output="screen",
    )

    vision_camera_node = Node(
        package="robot_arm_vision",
        executable="vision_node",
        name="vision_node",
        output="screen",
    )

    return LaunchDescription([
        sorting_planner_node,
        vision_camera_node
    ])