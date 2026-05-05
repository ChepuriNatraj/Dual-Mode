from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, TimerAction
from launch.substitutions import Command, FindExecutable, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node

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

    pkg_moveit = get_package_share_directory('robot_arm_moveit2')
    xacro_file = PathJoinSubstitution([pkg_moveit, 'config', 'robotic_arm.urdf.xacro'])
    initial_positions_file = PathJoinSubstitution([pkg_moveit, 'config', 'initial_positions.yaml'])
    controllers_file = PathJoinSubstitution([pkg_moveit, 'config', 'ros2_controllers.yaml'])

    robot_description_config = Command([
        FindExecutable(name='xacro'), ' ',
        xacro_file, ' ',
        'use_fake_hardware:=true', ' ',
        'initial_positions_file:=', initial_positions_file, ' ',
        'serial_port:=', LaunchConfiguration('serial_port'), ' ',
        'baud_rate:=', LaunchConfiguration('baud_rate'),
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
        robot_state_publisher,
        ros2_control_node,
        TimerAction(period=2.0, actions=[joint_state_broadcaster_spawner]),
        TimerAction(period=3.0, actions=[arm_controller_spawner, gripper_controller_spawner]),
    ])
