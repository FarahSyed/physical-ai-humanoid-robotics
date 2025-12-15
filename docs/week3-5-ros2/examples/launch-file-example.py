#!/usr/bin/env python3
# launch-file-example.py
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, LogInfo
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    # Declare launch arguments
    use_sim_time = DeclareLaunchArgument(
        'use_sim_time',
        default_value='false',
        description='Use simulation (Gazebo) clock if true'
    )

    robot_name = DeclareLaunchArgument(
        'robot_name',
        default_value='humanoid_robot',
        description='Name of the robot'
    )

    config_file = DeclareLaunchArgument(
        'config_file',
        default_value=PathJoinSubstitution([
            get_package_share_directory('humanoid_control'),
            'config',
            'default_params.yaml'
        ]),
        description='Path to configuration file'
    )

    # Get launch configurations
    use_sim_time_config = LaunchConfiguration('use_sim_time')
    robot_name_config = LaunchConfiguration('robot_name')
    config_file_config = LaunchConfiguration('config_file')

    # Robot state publisher node
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        parameters=[
            {'use_sim_time': use_sim_time_config},
            {'publish_frequency': 50.0}
        ],
        namespace=robot_name_config,
        output='screen'
    )

    # Joint state publisher node
    joint_state_publisher = Node(
        package='joint_state_publisher',
        executable='joint_state_publisher',
        name='joint_state_publisher',
        parameters=[
            {'use_sim_time': use_sim_time_config},
            {'rate': 50}
        ],
        namespace=robot_name_config,
        output='screen'
    )

    # Main controller node
    main_controller = Node(
        package='humanoid_control',
        executable='main_controller',
        name='main_controller',
        parameters=[
            {'use_sim_time': use_sim_time_config},
            config_file_config,
            {'robot_name': robot_name_config}
        ],
        namespace=robot_name_config,
        output='screen',
        respawn=True,
        respawn_delay=2
    )

    # Diagnostic aggregator node
    diagnostic_aggregator = Node(
        package='diagnostic_aggregator',
        executable='aggregator_node',
        name='diagnostic_aggregator',
        parameters=[
            PathJoinSubstitution([
                get_package_share_directory('humanoid_system'),
                'config',
                'diagnostics.yaml'
            ])
        ],
        namespace=robot_name_config,
        output='screen'
    )

    # Log startup information
    startup_log = LogInfo(
        msg=['Starting humanoid system for robot: ', robot_name_config]
    )

    return LaunchDescription([
        use_sim_time,
        robot_name,
        config_file,
        startup_log,
        robot_state_publisher,
        joint_state_publisher,
        main_controller,
        diagnostic_aggregator
    ])