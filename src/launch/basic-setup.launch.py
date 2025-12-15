from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    """
    Launch file for basic ROS 2 nervous system setup for humanoid robotics.
    This launch file sets up the fundamental nodes that form the 'nervous system'
    of a humanoid robot, including state publishing and basic communication.
    """
    return LaunchDescription([
        # Declare launch arguments
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            description='Use simulation clock if true'
        ),

        # Robot state publisher node
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='robot_state_publisher',
            parameters=[
                {'use_sim_time': LaunchConfiguration('use_sim_time')},
                {'publish_frequency': 50.0}
            ],
            arguments=['$(find ros2_nervous_system)/urdf/humanoid.urdf'],
            output='screen'
        ),

        # Joint state publisher node
        Node(
            package='joint_state_publisher',
            executable='joint_state_publisher',
            name='joint_state_publisher',
            parameters=[
                {'use_sim_time': LaunchConfiguration('use_sim_time')}
            ],
            output='screen'
        ),

        # Example communication node (publisher)
        Node(
            package='ros2_nervous_system',
            executable='sensor_data_publisher',
            name='sensor_data_publisher',
            parameters=[
                {'use_sim_time': LaunchConfiguration('use_sim_time')}
            ],
            output='screen'
        ),

        # Example communication node (subscriber)
        Node(
            package='ros2_nervous_system',
            executable='control_command_subscriber',
            name='control_command_subscriber',
            parameters=[
                {'use_sim_time': LaunchConfiguration('use_sim_time')}
            ],
            output='screen'
        )
    ])