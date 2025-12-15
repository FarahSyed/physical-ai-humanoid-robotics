# Launch File Example for Humanoid System

This launch file demonstrates a complex multi-node setup for a humanoid system.

## Complex Launch File

```python
# launch/humanoid_system.launch.py
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    # Declare launch arguments
    use_sim_time = LaunchConfiguration('use_sim_time')
    config_file = LaunchConfiguration('config_file')

    return LaunchDescription([
        # Declare launch arguments
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            description='Use simulation (Gazebo) clock if true'
        ),
        DeclareLaunchArgument(
            'config_file',
            default_value=PathJoinSubstitution([
                get_package_share_directory('humanoid_control'),
                'config',
                'humanoid_params.yaml'
            ]),
            description='Path to configuration file'
        ),

        # Joint state publisher node
        Node(
            package='joint_state_publisher',
            executable='joint_state_publisher',
            name='joint_state_publisher',
            parameters=[{'use_sim_time': use_sim_time}],
            output='screen',
        ),

        # Robot state publisher node
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='robot_state_publisher',
            parameters=[
                {'use_sim_time': use_sim_time},
                PathJoinSubstitution([
                    get_package_share_directory('humanoid_description'),
                    'config',
                    'robot_state_publisher.yaml'
                ])
            ],
            output='screen',
        ),

        # Balance control node
        Node(
            package='humanoid_control',
            executable='balance_controller',
            name='balance_controller',
            parameters=[config_file],
            output='screen',
            # Add safety requirements
            on_exit=Node.SHOULD_EXIT,  # If balance controller fails, exit the system
        ),

        # Locomotion control node
        Node(
            package='humanoid_control',
            executable='locomotion_controller',
            name='locomotion_controller',
            parameters=[config_file],
            output='screen',
        ),

        # Perception node
        Node(
            package='humanoid_perception',
            executable='perception_node',
            name='perception_node',
            parameters=[{'use_sim_time': use_sim_time}],
            output='screen',
        ),

        # Emergency stop handler
        Node(
            package='humanoid_safety',
            executable='emergency_stop_handler',
            name='emergency_stop_handler',
            parameters=[{'use_sim_time': use_sim_time}],
            output='screen',
        ),
    ])
```

## Parameter Configuration File

```yaml
# config/humanoid_params.yaml
/**:
  ros__parameters:
    # Safety parameters
    safety:
      max_joint_velocity: 2.0  # rad/s
      max_joint_torque: 50.0   # N*m
      balance_threshold: 0.1   # meters
      emergency_stop_timeout: 0.5  # seconds

    # Control parameters
    control:
      loop_rate: 100  # Hz
      position_tolerance: 0.01  # radians
      velocity_tolerance: 0.05  # rad/s

    # Hardware parameters
    hardware:
      joint_limits:
        hip_min: -1.57  # radians
        hip_max: 1.57
        knee_min: 0.0
        knee_max: 2.35
        ankle_min: -0.78
        ankle_max: 0.78
```

## Namespace Hierarchy Example

The launch file demonstrates proper hierarchical organization for humanoid systems:

```
/humanoid_robot/
├── /sensors/
│   ├── /imu
│   ├── /cameras/
│   │   ├── /left_camera
│   │   └── /right_camera
│   └── /lidar
├── /control/
│   ├── /balance_controller
│   ├── /locomotion_controller
│   └── /arm_controller
├── /perception/
│   ├── /object_detection
│   └── /person_tracking
└── /safety/
    └── /emergency_stop_handler
```

This launch file structure enables proper organization of a complex humanoid system with clear separation of concerns, safety mechanisms, and parameter management.