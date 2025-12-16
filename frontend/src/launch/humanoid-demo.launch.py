from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, RegisterEventHandler
from launch.event_handlers import OnProcessStart
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
import os


def generate_launch_description():
    """
    Launch file for a complete humanoid nervous system demonstration.
    This launch file brings up all the essential nodes that form the
    'nervous system' of a humanoid robot, enabling coordinated behavior.
    """
    return LaunchDescription([
        # Declare launch arguments
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            description='Use simulation clock if true'
        ),

        DeclareLaunchArgument(
            'robot_description_path',
            default_value='$(find ros2_nervous_system)/urdf/humanoid.urdf',
            description='Path to robot URDF file'
        ),

        # Robot state publisher with humanoid model
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='humanoid_state_publisher',
            parameters=[
                {'use_sim_time': LaunchConfiguration('use_sim_time')},
                {'publish_frequency': 50.0}
            ],
            arguments=[LaunchConfiguration('robot_description_path')],
            output='screen'
        ),

        # Joint state publisher for humanoid
        Node(
            package='joint_state_publisher',
            executable='joint_state_publisher',
            name='humanoid_joint_publisher',
            parameters=[
                {'use_sim_time': LaunchConfiguration('use_sim_time')}
            ],
            output='screen'
        ),

        # Sensor data publisher (simulating humanoid sensors)
        Node(
            package='ros2_nervous_system',
            executable='sensor_publisher',
            name='humanoid_sensor_publisher',
            parameters=[
                {'use_sim_time': LaunchConfiguration('use_sim_time')},
                {'publish_frequency': 30.0}  # 30 Hz for sensor data
            ],
            output='screen'
        ),

        # Control command subscriber (receiving commands for humanoid)
        Node(
            package='ros2_nervous_system',
            executable='control_subscriber',
            name='humanoid_control_subscriber',
            parameters=[
                {'use_sim_time': LaunchConfiguration('use_sim_time')}
            ],
            output='screen'
        ),

        # Perception node (processing sensor data)
        Node(
            package='ros2_nervous_system',
            executable='perception_node',
            name='humanoid_perception',
            parameters=[
                {'use_sim_time': LaunchConfiguration('use_sim_time')}
            ],
            output='screen'
        ),

        # Decision making node (the 'brain' of the humanoid)
        Node(
            package='ros2_nervous_system',
            executable='decision_maker',
            name='humanoid_decision_maker',
            parameters=[
                {'use_sim_time': LaunchConfiguration('use_sim_time')}
            ],
            output='screen'
        )
    ])