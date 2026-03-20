import os
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
from moveit_configs_utils import MoveItConfigsBuilder

def generate_launch_description():
    # Build MoveIt configuration but set it to use the Gazebo URDF instead of fake controllers.
    moveit_config = (
        MoveItConfigsBuilder("robotic_arm", package_name="robot_arm_moveit2")
        .robot_description(mappings={"use_fake_hardware": "false", "use_gazebo": "true"})
        .to_moveit_configs()
    )

    # Incorporate the existing Gazebo launch file
    gazebo_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory('robot_arm_gazebo'), 'launch', 'gazebo.launch.py')
        )
    )

    # Start MoveGroup with Simulation Time
    move_group_node = Node(
        package="moveit_ros_move_group",
        executable="move_group",
        output="screen",
        parameters=[
            moveit_config.to_dict(),
            {"use_sim_time": True},
            {"publish_robot_description_semantic": True}
        ],
    )

    # Start RViz with Simulation Time
    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="log",
        arguments=["-d", os.path.join(get_package_share_directory("robot_arm_moveit2"), "config", "moveit.rviz")],
        parameters=[
            moveit_config.robot_description,
            moveit_config.robot_description_semantic,
            moveit_config.robot_description_kinematics,
            moveit_config.joint_limits,
            {"use_sim_time": True}
        ],
    )

    return LaunchDescription([
        gazebo_launch,
        # Give Gazebo and Controller Spawners a slight head start before bringing up MoveIt
        TimerAction(period=8.0, actions=[move_group_node]),
        TimerAction(period=8.0, actions=[rviz_node])
    ])
