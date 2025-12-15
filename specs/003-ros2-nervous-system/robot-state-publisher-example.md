# Robot State Publisher Example for Humanoid

This example demonstrates how to set up robot state publishing for a humanoid robot using ROS 2.

## Launch File for Robot State Publishing

```python
# launch/robot_state_publisher.launch.py
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    # Declare launch arguments
    use_sim_time = LaunchConfiguration('use_sim_time')
    robot_description_path = LaunchConfiguration('robot_description_path')

    return LaunchDescription([
        # Declare launch arguments
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            description='Use simulation (Gazebo) clock if true'
        ),

        DeclareLaunchArgument(
            'robot_description_path',
            default_value=PathJoinSubstitution([
                get_package_share_directory('humanoid_description'),
                'urdf',
                'enhanced_humanoid.urdf'
            ]),
            description='Path to robot description file'
        ),

        # Robot State Publisher
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='robot_state_publisher',
            parameters=[
                {'use_sim_time': use_sim_time},
                {'robot_description': LaunchConfiguration('robot_description_path')},
                {
                    'publish_frequency': 50.0,  # Hz
                    'ignore_timestamp': False,
                    'tf_prefix': '',
                    'use_smallest_joint_limits': True,
                    'publish_joints_frequency': 10.0,
                }
            ],
            remappings=[
                ('/joint_states', '/joint_states'),
            ],
            output='screen',
        ),

        # Joint State Publisher (for visualization without real hardware)
        Node(
            package='joint_state_publisher',
            executable='joint_state_publisher',
            name='joint_state_publisher',
            parameters=[
                {'use_sim_time': use_sim_time},
                {'rate': 50},  # Hz
                {'source_list': ['/joint_states']},  # Listen to real joint states if available
            ],
            output='screen',
        ),
    ])
```

## Configuration File

```yaml
# config/robot_state_publisher.yaml
/**:
  ros__parameters:
    # Robot description
    robot_description: ''  # Will be loaded from URDF file

    # Publishing parameters
    publish_frequency: 50.0  # Hz - how often to publish TF transforms
    ignore_timestamp: false  # Whether to ignore timestamps in joint state messages
    tf_prefix: ''  # Prefix for TF frame names (usually empty for single robot)

    # Joint publishing parameters
    publish_joints_frequency: 10.0  # Hz - how often to publish joint states
    use_smallest_joint_limits: true  # Use the most restrictive joint limits

    # Frame parameters
    frame_prefix: ''  # Prefix for all frames published
    broadcast_tf: true  # Whether to broadcast TF transforms

    # Advanced parameters
    enable_axis: false  # Enable/disable axis visualization
    enable_gui: false  # Enable/disable GUI for joint state publisher
```

## Joint State Publisher Node Configuration

```yaml
# config/joint_state_publisher.yaml
/**:
  ros__parameters:
    # Joint state publishing parameters
    rate: 50  # Hz - publishing rate
    use_mimic: true  # Enable mimic joints
    use_small: false  # Use small values for uninitialized joints
    zeros: {}  # Initial joint positions

    # Source parameters
    source_list: ['/joint_states']  # List of topics to listen to for joint states
    ignore_timestamp: false  # Whether to ignore timestamps in joint state messages

    # Joint parameters
    publish_default_positions: true  # Publish default positions for uninitialized joints
    publish_default_velocities: false  # Publish default velocities
    publish_default_efforts: false  # Publish default efforts
```

## Robot Description Launch

```python
# launch/humanoid_description.launch.py
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():
    # Declare launch arguments
    use_sim_time = LaunchConfiguration('use_sim_time')

    return LaunchDescription([
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            description='Use simulation clock if true'
        ),

        # Include robot state publisher launch
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource([
                PathJoinSubstitution([
                    FindPackageShare('humanoid_description'),
                    'launch',
                    'robot_state_publisher.launch.py'
                ])
            ]),
            launch_arguments={
                'use_sim_time': use_sim_time
            }.items()
        ),
    ])
```

## Package Configuration

```xml
<?xml version="1.0"?>
<?xml-model href="http://download.ros.org/schema/package_format3.xsd" schematypens="http://www.w3.org/2001/XMLSchema"?>
<package format="3">
  <name>humanoid_description</name>
  <version>0.0.1</version>
  <description>URDF description and state publishing for humanoid robot</description>
  <maintainer email="maintainer@todo.todo">maintainer</maintainer>
  <license>Apache-2.0</license>

  <depend>robot_state_publisher</depend>
  <depend>joint_state_publisher</depend>
  <depend>joint_state_publisher_gui</depend>
  <depend>rviz2</depend>
  <depend>xacro</depend>

  <export>
    <build_type>ament_cmake</build_type>
  </export>
</package>
```

## URDF File Structure

The URDF file should be placed in `urdf/` directory:

```
humanoid_description/
├── urdf/
│   ├── basic_humanoid.urdf
│   ├── enhanced_humanoid.urdf
│   └── humanoid.xacro
├── launch/
│   ├── robot_state_publisher.launch.py
│   └── humanoid_description.launch.py
├── config/
│   ├── robot_state_publisher.yaml
│   └── joint_state_publisher.yaml
└── CMakeLists.txt
```

## Expected Behavior

This robot state publisher setup will:

1. **Load the URDF**: Read the robot description from the URDF file
2. **Publish TF transforms**: Continuously publish the transforms between all links based on joint states
3. **Handle joint states**: Subscribe to `/joint_states` topic and update the transforms accordingly
4. **Maintain frame relationships**: Ensure all coordinate frames maintain proper relationships as defined in the URDF
5. **Support visualization**: Work with RViz for proper robot visualization

The robot state publisher is essential for humanoid robotics as it provides the spatial relationships between all robot parts, which is critical for perception, planning, and control systems.