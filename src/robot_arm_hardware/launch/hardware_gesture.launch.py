from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, TimerAction, OpaqueFunction
from launch.substitutions import Command, FindExecutable, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node


def launch_gesture_conditional(context, *args, **kwargs):
    """Conditionally launch gesture node if enable_gesture is true"""
    enable_gesture = LaunchConfiguration('enable_gesture').perform(context)
    
    if enable_gesture.lower() == 'false':
        return []
    
    gesture_node = Node(
        package='robot_arm_gesture',
        executable='gesture_node',
        output='screen',
        parameters=[
            {'camera_index': LaunchConfiguration('camera_index')},
            {'model_path': LaunchConfiguration('model_path')},
            {'arm_topic': '/arm_controller/joint_trajectory'},
            {'gripper_topic': '/gripper_controller/joint_trajectory'},
            {'mirror_to_local_controller': False},
        ],
    )
    return [TimerAction(period=5.0, actions=[gesture_node])]


def generate_launch_description():
    serial_port_arg = DeclareLaunchArgument(
        'serial_port',
        default_value='/dev/ttyUSB0',
        description='Serial port connected to Arduino/ESP controller',
    )

    baud_rate_arg = DeclareLaunchArgument(
        'baud_rate',
        default_value='115200',
        description='Serial baud rate used by Arduino/ESP firmware',
    )

    camera_index_arg = DeclareLaunchArgument(
        'camera_index',
        default_value='0',
        description='OpenCV camera index for gesture node',
    )

    model_path_arg = DeclareLaunchArgument(
        'model_path',
        default_value='/home/natraj/file/src/hand gesture/hand_landmarker.task',
        description='Path to MediaPipe hand_landmarker.task file',
    )
    
    enable_gesture_arg = DeclareLaunchArgument(
        'enable_gesture',
        default_value='true',
        description='Enable gesture control (requires webcam at camera_index)',
    )

    pkg_moveit = get_package_share_directory('robot_arm_moveit2')
    xacro_file = PathJoinSubstitution([pkg_moveit, 'config', 'robotic_arm.urdf.xacro'])
    initial_positions_file = PathJoinSubstitution([pkg_moveit, 'config', 'initial_positions.yaml'])
    controllers_file = PathJoinSubstitution([pkg_moveit, 'config', 'ros2_controllers.yaml'])

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

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[{'robot_description': robot_description_config}],
    )

    ros2_control_node = Node(
        package='controller_manager',
        executable='ros2_control_node',
        output='screen',
        parameters=[
            {'robot_description': robot_description_config},
            controllers_file,
        ],
    )

    joint_state_broadcaster_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['joint_state_broadcaster', '--controller-manager', '/controller_manager'],
        output='screen',
    )

    arm_controller_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['arm_controller', '--controller-manager', '/controller_manager'],
        output='screen',
    )

    gripper_controller_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['gripper_controller', '--controller-manager', '/controller_manager'],
        output='screen',
    )

    return LaunchDescription([
        serial_port_arg,
        baud_rate_arg,
        camera_index_arg,
        model_path_arg,
        enable_gesture_arg,
        robot_state_publisher,
        ros2_control_node,
        TimerAction(period=2.0, actions=[joint_state_broadcaster_spawner]),
        TimerAction(period=3.0, actions=[arm_controller_spawner, gripper_controller_spawner]),
        OpaqueFunction(function=launch_gesture_conditional),
    ])

