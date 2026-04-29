"""
Complete Hardware Autonomous Sorting Launch
===========================================

Launches the full autonomous sorting pipeline on real hardware:
1. Hardware initialization (ros2_control, controller manager, controllers)
2. Robot state publisher and joint state broadcaster
3. ESP32 camera MJPEG stream bridge
4. Vision processing node (YOLO object detection + calibration)
5. Sorting planner node (MoveIt trajectory planning + execution)
6. Mode manager (set to AUTONOMOUS for autonomous control)

Usage:
    ros2 launch robot_arm_vision hardware_sorting.launch.py \
        serial_port:=/dev/ttyUSB0 \
        baud_rate:=115200 \
        esp32_camera_url:=http://192.168.1.100:81/stream

Parameters:
    serial_port: Serial port for ESP32/Arduino (default: /dev/ttyUSB0)
    baud_rate: Serial baud rate (default: 115200)
    esp32_camera_url: HTTP URL of ESP32-CAM MJPEG stream
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, TimerAction, RegisterEventHandler
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch.event_handlers import OnProcessStart
from moveit_configs_utils import MoveItConfigsBuilder
import os

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
    
    esp32_camera_url_arg = DeclareLaunchArgument(
        'esp32_camera_url',
        default_value='http://192.168.1.100:81/stream',
        description='HTTP URL of ESP32-CAM MJPEG stream'
    )
    
    camera_frame_arg = DeclareLaunchArgument(
        'camera_frame',
        default_value='camera_link',
        description='TF frame name for the camera'
    )
    
    # =====================================================
    # Config Builder Setup
    # =====================================================
    moveit_config = MoveItConfigsBuilder("robotic_arm", package_name="robot_arm_moveit2").to_moveit_configs()

    # =====================================================
    # 1. Hardware Bringup
    # =====================================================
    
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
    # 2. ESP32 Camera Bridge
    # =====================================================
    esp32_camera_bridge = TimerAction(
        period=5.0,
        actions=[
            Node(
                package='robot_arm_vision',
                executable='esp32_camera_bridge',
                name='esp32_camera_bridge',
                output='screen',
                parameters=[
                    {'esp32_url': LaunchConfiguration('esp32_camera_url')},
                    {'camera_frame': LaunchConfiguration('camera_frame')},
                    {'frame_width': 640},
                    {'frame_height': 480},
                    # Calibration parameters - ADJUST THESE FOR YOUR CAMERA
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
                    moveit_config.to_dict(),
                    {'use_sim_time': False},
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
    # Compose Launch Description
    # =====================================================
    launch_description = LaunchDescription([
        # Arguments
        serial_port_arg,
        baud_rate_arg,
        esp32_camera_url_arg,
        camera_frame_arg,
        
        # Hardware Bringup
        robot_state_publisher,
        control_node,
        joint_state_broadcaster,
        arm_controller,
        gripper_controller,
        
        # Mode Manager (early, so modes are always available)
        mode_manager,
        
        # Vision and Sorting (staggered start for clean initialization)
        esp32_camera_bridge,
        vision_node,
        sorting_planner,
    ])
    
    return launch_description
