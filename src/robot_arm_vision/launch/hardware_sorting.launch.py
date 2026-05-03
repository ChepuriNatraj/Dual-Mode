"""
Complete Hardware Autonomous Sorting Launch
===========================================

Launches the full autonomous sorting pipeline on real hardware:
1. Hardware initialization (ros2_control, controller manager, controllers)
2. Robot state publisher and joint state broadcaster
3. Vision processing node (YOLO object detection + calibration)
4. Sorting planner node (MoveIt trajectory planning + execution)
5. Mode manager (set to AUTONOMOUS for autonomous control)
6. RViz2 with camera display from /camera/image_raw topic

Usage:
    ros2 launch robot_arm_vision hardware_sorting.launch.py \
        serial_port:=/dev/ttyUSB0 \
        baud_rate:=115200

Parameters:
    serial_port: Serial port for Arduino (default: /dev/ttyUSB0)
    baud_rate: Serial baud rate (default: 115200)
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, TimerAction, RegisterEventHandler
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch.event_handlers import OnProcessStart
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
        description='Serial port for hardware controller (ESP32/PCA9685)'
    )
    
    baud_rate_arg = DeclareLaunchArgument(
        'baud_rate',
        default_value='115200',
        description='Serial port baud rate'
    )
    
    # =====================================================
    # Config Builder Setup
    # =====================================================
    moveit_config = MoveItConfigsBuilder("robotic_arm", package_name="robot_arm_moveit2").to_moveit_configs()

    # Load OMPL explicit configs for MoveItPy
    ompl_planning_yaml_file = os.path.join(
        get_package_share_directory('robot_arm_moveit2'),
        'config',
        'ompl_planning.yaml'
    )
    with open(ompl_planning_yaml_file, 'r') as file:
        ompl_planning_yaml = yaml.safe_load(file)
        
    if 'ompl' not in moveit_config.planning_pipelines:
        moveit_config.planning_pipelines['ompl'] = ompl_planning_yaml

    moveit_dict = moveit_config.to_dict()
    # Ensure ompl parameters are properly nested under pipelines
    if 'ompl' in ompl_planning_yaml:
        moveit_dict['ompl'] = ompl_planning_yaml['ompl']

    # =====================================================
    # 1. Hardware Bringup
    # =====================================================
    
    ros2_controllers_path = os.path.join(
        get_package_share_directory('robot_arm_moveit2'),
        'config',
        'ros2_controllers.yaml'
    )
    
    # Robot State Publisher with URDF + xacro parameters
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[
            moveit_config.robot_description,
            {'use_sim_time': False},
            {
                'robot_description_xacro_extra_args': {
                    'serial_port': LaunchConfiguration('serial_port'),
                    'baud_rate': LaunchConfiguration('baud_rate')
                }
            }
        ]
    )
    
    # Controller Manager Node
    control_node = Node(
        package='controller_manager',
        executable='ros2_control_node',
        parameters=[
            moveit_config.robot_description,
            ros2_controllers_path,
            {'use_sim_time': False},
        ],
        output='screen',
        remappings=[
            ('/controller_manager/robot_description', '/robot_description'),
        ]
    )
    
    # Joint State Broadcaster
    joint_state_broadcaster = TimerAction(
        period=2.0,
        actions=[
            Node(
                package='controller_manager',
                executable='spawner',
                arguments=['joint_state_broadcaster', '--controller-manager', '/controller_manager'],
                output='screen',
            )
        ]
    )
    
    # Arm Trajectory Controller
    arm_controller = TimerAction(
        period=3.0,
        actions=[
            Node(
                package='controller_manager',
                executable='spawner',
                arguments=['arm_controller', '--controller-manager', '/controller_manager'],
                output='screen',
            )
        ]
    )
    
    # Gripper Controller
    gripper_controller = TimerAction(
        period=4.0,
        actions=[
            Node(
                package='controller_manager',
                executable='spawner',
                arguments=['gripper_controller', '--controller-manager', '/controller_manager'],
                output='screen',
            )
        ]
    )
    
    # =====================================================
    # 2. Simple USB Camera Publisher
    # =====================================================
    camera_publisher = TimerAction(
        period=5.0,
        actions=[
            Node(
                package='robot_arm_vision',
                executable='simple_camera_publisher',
                name='camera_publisher',
                output='screen',
                parameters=[
                    {'camera_index': 0},
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
    # 3. Mode Manager (set to AUTONOMOUS mode)
    # =====================================================
    mode_manager = Node(
        package='robot_arm_mode_manager',
        executable='mode_manager_node',
        name='mode_manager',
        output='screen',
        parameters=[
            {'timeout_sec': 3.0}
        ]
    )
    
    # =====================================================
    # 4. Vision Processing Node
    # =====================================================
    vision_node = TimerAction(
        period=6.0,
        actions=[
            Node(
                package='robot_arm_vision',
                executable='vision_node',
                name='vision_node',
                output='screen',
                parameters=[
                    # Camera calibration (must match camera intrinsics)
                    {'camera_height': 0.8},
                    {'workspace_z': 0.02},
                    {'min_world_x': 0.15},
                    {'max_world_x': 0.45},
                    {'min_world_y': -0.25},
                    {'max_world_y': 0.25},
                ]
            )
        ]
    )
    
    # =====================================================
    # 5. Sorting Planner Node
    # =====================================================
    sorting_planner = TimerAction(
        period=7.0,
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
                    # Target pose remap to autonomous controller
                    {'pre_grasp_hover': 0.12},
                    {'grasp_offset': 0.01},
                    {'lift_offset': 0.12},
                ],
                remappings=[
                    ('/arm_controller/joint_trajectory', '/auto_controller/joint_trajectory'),
                ]
            )
        ]
    )
    
    # =====================================================
    # 6. RViz2 Visualizer
    # =====================================================
    pkg_moveit_config = get_package_share_directory('robot_arm_moveit2')
    rviz_config_file = os.path.join(pkg_moveit_config, 'config', 'moveit.rviz')
    
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', rviz_config_file],
        parameters=[
            moveit_config.robot_description,
            moveit_config.robot_description_semantic,
            moveit_config.robot_description_kinematics,
            moveit_config.planning_pipelines,
            {'use_sim_time': False}
        ]
    )

    # =====================================================
    # Compose Launch Description
    # =====================================================
    launch_description = LaunchDescription([
        # Arguments
        serial_port_arg,
        baud_rate_arg,
        
        # Hardware Bringup
        robot_state_publisher,
        control_node,
        joint_state_broadcaster,
        arm_controller,
        gripper_controller,
        
        # Camera Publisher (early, so images are available)
        camera_publisher,
        
        # Mode Manager (early, so modes are always available)
        mode_manager,
        
        # Vision and Sorting (staggered start for clean initialization)
        vision_node,
        sorting_planner,
        
        # RViz
        rviz_node,
    ])
    
    return launch_description
