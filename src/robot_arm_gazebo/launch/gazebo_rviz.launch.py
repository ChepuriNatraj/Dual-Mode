import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
import xacro

def generate_launch_description():
    pkg_robot_arm_gazebo = get_package_share_directory('robot_arm_gazebo')

    # Include Gazebo launch which spins up Gazebo, Robot State Pub, and spawns the bot
    gazebo_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_robot_arm_gazebo, 'launch', 'gazebo.launch.py')
        )
    )

    # Launch RViz without Joint State Publisher GUI (driven by physics/control later)
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        parameters=[{'use_sim_time': True}]
    )

    return LaunchDescription([
        gazebo_launch,
        rviz_node
    ])
