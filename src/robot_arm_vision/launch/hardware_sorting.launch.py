"""
Complete Hardware Autonomous Sorting Launch
===========================================

Launches the full autonomous sorting pipeline on real hardware:
1. Hardware initialization (ros2_control, controller manager, controllers)
2. Robot state publisher and joint state broadcaster
3. Mode manager (set to AUTONOMOUS for autonomous control)
4. Vision processing node (YOLO object detection + calibration)
5. Sorting planner node (MoveIt trajectory planning + execution)
6. Optional RViz2

Usage:
    ros2 launch robot_arm_vision hardware_sorting.launch.py \
        serial_port:=/dev/ttyUSB0 \
        camera_index:=0
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, TimerAction
from launch.substitutions import Command, FindExecutable, LaunchConfiguration, PathJoinSubstitution
from launch.conditions import IfCondition
from launch_ros.actions import Node
from moveit_configs_utils import MoveItConfigsBuilder
from ament_index_python.packages import get_package_share_directory
import os
import yaml

def generate_launch_description():
    
    # =====================================================
    # Launch Arguments
    # =====================================================
    serial_port_arg = DeclareLaunchArgument(
        'serial_port',
        default_value='/dev/ttyUSB0',
        description='Serial port for hardware controller'
    )
    
    baud_rate_arg = DeclareLaunchArgument(
        'baud_rate',
        default_value='115200',
        description='Serial port baud rate'
    )

    camera_index_arg = DeclareLaunchArgument(
        'camera_index',
        default_value='0',
        description='Camera index for simple_camera_publisher'
    )

    detector_mode_arg = DeclareLaunchArgument(
        'detector_mode',
        default_value='red',
        description='Detector mode: red or yolo'
    )

    use_rviz_arg = DeclareLaunchArgument(
        'use_rviz',
        default_value='false',
        description='Whether to start RViz'
    )

    stable_frames_arg = DeclareLaunchArgument(
        'stable_frames_required',
        default_value='10',
        description='Number of stable detection frames required before publishing target_pose'
    )
    
    # =====================================================
    # Config Builder Setup
    # =====================================================
    moveit_config = MoveItConfigsBuilder("robotic_arm", package_name="robot_arm_moveit2").to_moveit_configs()

    pkg_moveit_config = get_package_share_directory('robot_arm_moveit2')
    xacro_file = PathJoinSubstitution([pkg_moveit_config, 'config', 'robotic_arm.urdf.xacro'])
    initial_positions_file = PathJoinSubstitution([pkg_moveit_config, 'config', 'initial_positions.yaml'])

    robot_description_config = Command([
        FindExecutable(name='xacro'),
        ' ',
        xacro_file,
        ' ',
        'use_fake_hardware:=true',
        ' ',
        'initial_positions_file:=',
        initial_positions_file,
        ' ',
        'serial_port:=',
        LaunchConfiguration('serial_port'),
        ' ',
        'baud_rate:=',
        LaunchConfiguration('baud_rate'),
    ])
    robot_description = {'robot_description': robot_description_config}

    ompl_planning_yaml_file = os.path.join(
        pkg_moveit_config,
        'config',
        'ompl_planning.yaml'
    )
    with open(ompl_planning_yaml_file, 'r') as file:
        ompl_planning_yaml = yaml.safe_load(file)
        
    if 'ompl' not in moveit_config.planning_pipelines:
        moveit_config.planning_pipelines['ompl'] = ompl_planning_yaml

    moveit_dict = moveit_config.to_dict()
    if 'ompl' in ompl_planning_yaml:
        moveit_dict['ompl'] = ompl_planning_yaml['ompl']
    moveit_dict['robot_description'] = robot_description_config

    # =====================================================
    # 1. Hardware Bringup
    # =====================================================
    ros2_controllers_path = os.path.join(pkg_moveit_config, 'config', 'ros2_controllers.yaml')
    
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[
            robot_description,
            {'use_sim_time': False},
        ]
    )
    
    control_node = Node(
        package='controller_manager',
        executable='ros2_control_node',
        parameters=[
            robot_description,
            ros2_controllers_path,
            {'use_sim_time': False},
        ],
        output='screen',
        remappings=[('/controller_manager/robot_description', '/robot_description')]
    )
    
    joint_state_broadcaster = TimerAction(
        period=1.0,
        actions=[Node(package='controller_manager', executable='spawner', arguments=['joint_state_broadcaster', '--controller-manager', '/controller_manager'], output='screen')]
    )
    
    arm_controller = TimerAction(
        period=2.0,
        actions=[Node(package='controller_manager', executable='spawner', arguments=['arm_controller', '--controller-manager', '/controller_manager'], output='screen')]
    )
    
    gripper_controller = TimerAction(
        period=3.0,
        actions=[Node(package='controller_manager', executable='spawner', arguments=['gripper_controller', '--controller-manager', '/controller_manager'], output='screen')]
    )
    
    # =====================================================
    # 2. Camera Publisher
    # =====================================================
    camera_publisher = TimerAction(
        period=4.0,
        actions=[
            Node(
                package='robot_arm_vision',
                executable='simple_camera_publisher',
                name='camera_publisher',
                output='screen',
                parameters=[
                    {'camera_index': LaunchConfiguration('camera_index')},
                    {'frame_width': 640},
                    {'frame_height': 480},
                    {'camera_frame': 'camera_link'},
                    {'fx': 500.0},
                    {'fy': 500.0},
                    {'cx': 320.0},
                    {'cy': 240.0}
                ]
            )
        ]
    )
    
    # =====================================================
    # 3. Mode Manager (Set to AUTONOMOUS)
    # =====================================================
    mode_manager = TimerAction(
        period=4.0,
        actions=[
            Node(
                package='robot_arm_mode_manager',
                executable='mode_manager_node',
                name='mode_manager',
                output='screen',
                parameters=[{'timeout_sec': 3.0}]
            )
        ]
    )
    
    # =====================================================
    # 4. Vision Processing Node
    # =====================================================
    vision_node = TimerAction(
        period=5.0,
        actions=[
            Node(
                package='robot_arm_vision',
                executable='vision_node',
                name='vision_node',
                output='screen',
                parameters=[
                    {'detector_mode': LaunchConfiguration('detector_mode')},
                    {'camera_height': 0.8},
                    {'workspace_z': 0.02},
                    {'min_world_x': 0.15},
                    {'max_world_x': 0.45},
                    {'min_world_y': -0.25},
                    {'max_world_y': 0.25},
                    {'stable_frames_required': LaunchConfiguration('stable_frames_required')},
                    {'stability_tolerance': 0.02}
                ]
            )
        ]
    )
    
    # =====================================================
    # 5. Sorting Planner Node
    # =====================================================
    sorting_planner = TimerAction(
        period=8.0,
        actions=[
            Node(
                package='robot_arm_vision',
                executable='sorting_planner_node',
                name='sorting_planner',
                output='screen',
                parameters=[
                    moveit_dict,
                    {'use_sim_time': False},
                    {'planning_pipelines': ['ompl']},
                    {'default_planning_pipeline': 'ompl'},
                    {'pre_grasp_hover': 0.12},
                    {'grasp_offset': 0.01},
                    {'lift_offset': 0.12},
                    {'min_reach_x': 0.15},
                    {'max_reach_x': 0.42},
                    {'min_reach_y': -0.25},
                    {'max_reach_y': 0.25}
                ]
            )
        ]
    )
    
    # =====================================================
    # 6. RViz2 Visualizer (Optional)
    # =====================================================
    rviz_config_file = os.path.join(pkg_moveit_config, 'config', 'moveit.rviz')
    
    rviz_node = TimerAction(
        period=9.0,
        actions=[
            Node(
                package='rviz2',
                executable='rviz2',
                name='rviz2',
                output='screen',
                arguments=['-d', rviz_config_file],
                parameters=[
                    moveit_dict,
                    {'use_sim_time': False}
                ],
                condition=IfCondition(LaunchConfiguration('use_rviz'))
            )
        ]
    )

    return LaunchDescription([
        serial_port_arg,
        baud_rate_arg,
        camera_index_arg,
        detector_mode_arg,
        use_rviz_arg,
        stable_frames_arg,
        robot_state_publisher,
        control_node,
        joint_state_broadcaster,
        arm_controller,
        gripper_controller,
        camera_publisher,
        mode_manager,
        vision_node,
        sorting_planner,
        rviz_node
    ])
