"""
Hardware Blind Sorting Launch (Fixed Auto Demo)
================================================

This launch bypasses the vision camera and vision node entirely
and continuously loops through predefined hardcoded Cartesian/Joint points.

Usage:
    ros2 launch robot_arm_vision hardware_blind_sorting.launch.py serial_port:=/dev/ttyUSB0
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, TimerAction
from launch.substitutions import LaunchConfiguration
from launch.conditions import IfCondition
from launch_ros.actions import Node
from moveit_configs_utils import MoveItConfigsBuilder
from ament_index_python.packages import get_package_share_directory
import os
import yaml

def generate_launch_description():
    
    serial_port_arg = DeclareLaunchArgument('serial_port', default_value='/dev/ttyUSB0')
    baud_rate_arg = DeclareLaunchArgument('baud_rate', default_value='115200')
    use_rviz_arg = DeclareLaunchArgument('use_rviz', default_value='false')
    
    moveit_config = MoveItConfigsBuilder("robotic_arm", package_name="robot_arm_moveit2").to_moveit_configs()

    ompl_planning_yaml_file = os.path.join(get_package_share_directory('robot_arm_moveit2'), 'config', 'ompl_planning.yaml')
    with open(ompl_planning_yaml_file, 'r') as file:
        ompl_planning_yaml = yaml.safe_load(file)
        
    if 'ompl' not in moveit_config.planning_pipelines:
        moveit_config.planning_pipelines['ompl'] = ompl_planning_yaml

    moveit_dict = moveit_config.to_dict()
    if 'ompl' in ompl_planning_yaml:
        moveit_dict['ompl'] = ompl_planning_yaml['ompl']

    # 1. Hardware Base
    ros2_controllers_path = os.path.join(get_package_share_directory('robot_arm_moveit2'), 'config', 'ros2_controllers.yaml')
    
    robot_state_publisher = Node(
        package='robot_state_publisher', executable='robot_state_publisher',
        output='screen',
        parameters=[moveit_config.robot_description, {'use_sim_time': False},
            {'robot_description_xacro_extra_args': {'serial_port': LaunchConfiguration('serial_port'),'baud_rate': LaunchConfiguration('baud_rate')}}]
    )
    
    control_node = Node(
        package='controller_manager', executable='ros2_control_node',
        parameters=[moveit_config.robot_description, ros2_controllers_path, {'use_sim_time': False}],
        output='screen', remappings=[('/controller_manager/robot_description', '/robot_description')]
    )
    
    joint_state_broadcaster = TimerAction(period=1.0, actions=[Node(package='controller_manager', executable='spawner', arguments=['joint_state_broadcaster', '--controller-manager', '/controller_manager'], output='screen')])
    arm_controller = TimerAction(period=2.0, actions=[Node(package='controller_manager', executable='spawner', arguments=['arm_controller', '--controller-manager', '/controller_manager'], output='screen')])
    gripper_controller = TimerAction(period=3.0, actions=[Node(package='controller_manager', executable='spawner', arguments=['gripper_controller', '--controller-manager', '/controller_manager'], output='screen')])
    
    # 2. Mode Manager (Set to AUTONOMOUS)
    mode_manager = TimerAction(period=4.0, actions=[Node(package='robot_arm_mode_manager', executable='mode_manager_node', output='screen', parameters=[{'timeout_sec': 3.0}])])
    
    # 3. Fixed Sequence Planner Node (Replaces Vision + Sorting Planner)
    fixed_planner = TimerAction(
        period=7.0,
        actions=[
            Node(
                package='robot_arm_vision',
                executable='fixed_sequence_node',
                name='fixed_sequence_node',
                output='screen',
                parameters=[
                    moveit_dict,
                    {'use_sim_time': False},
                    {'planning_pipelines': ['ompl']},
                    {'default_planning_pipeline': 'ompl'}
                ]
            )
        ]
    )

    # Optional RViz2
    pkg_moveit_config = get_package_share_directory('robot_arm_moveit2')
    rviz_config_file = os.path.join(pkg_moveit_config, 'config', 'moveit.rviz')
    
    rviz_node = TimerAction(period=8.0, actions=[
        Node(package='rviz2', executable='rviz2', name='rviz2', output='screen',
             arguments=['-d', rviz_config_file], parameters=[moveit_dict, {'use_sim_time': False}],
             condition=IfCondition(LaunchConfiguration('use_rviz')))
    ])

    return LaunchDescription([
        serial_port_arg, baud_rate_arg, use_rviz_arg,
        robot_state_publisher, control_node, joint_state_broadcaster,
        arm_controller, gripper_controller, mode_manager, fixed_planner, rviz_node
    ])
