# Basic Node Communication Example for Humanoid Sensors

This example demonstrates the publisher/subscriber pattern for humanoid sensor data.

## Publisher: Joint State Publisher

```python
#!/usr/bin/env python3
# publisher_node.py
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
from std_msgs.msg import Header
import math
import random

class JointStatePublisher(Node):
    def __init__(self):
        super().__init__('joint_state_publisher')
        self.publisher_ = self.create_publisher(JointState, 'joint_states', 10)
        timer_period = 0.1  # seconds
        self.timer = self.create_timer(timer_period, self.timer_callback)
        self.i = 0

        # Initialize joint names for a simple humanoid model
        self.joint_names = [
            'left_hip_joint', 'left_knee_joint', 'left_ankle_joint',
            'right_hip_joint', 'right_knee_joint', 'right_ankle_joint',
            'left_shoulder_joint', 'left_elbow_joint',
            'right_shoulder_joint', 'right_elbow_joint'
        ]

    def timer_callback(self):
        msg = JointState()
        msg.header = Header()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = "base_link"

        msg.name = self.joint_names
        msg.position = []
        msg.velocity = []
        msg.effort = []

        # Generate simulated joint positions (in radians)
        for i, name in enumerate(self.joint_names):
            # Simulate periodic motion with some randomness
            pos = math.sin(self.i * 0.1 + i) * 0.5 + random.uniform(-0.1, 0.1)
            vel = math.cos(self.i * 0.1 + i) * 0.5
            eff = random.uniform(-0.01, 0.01)

            msg.position.append(pos)
            msg.velocity.append(vel)
            msg.effort.append(eff)

        self.publisher_.publish(msg)
        self.get_logger().info(f'Publishing joint states: {len(msg.name)} joints')
        self.i += 1

def main(args=None):
    rclpy.init(args=args)
    joint_state_publisher = JointStatePublisher()

    try:
        rclpy.spin(joint_state_publisher)
    except KeyboardInterrupt:
        pass
    finally:
        joint_state_publisher.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
```

## Subscriber: Joint State Subscriber

```python
#!/usr/bin/env python3
# subscriber_node.py
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
import time

class JointStateSubscriber(Node):
    def __init__(self):
        super().__init__('joint_state_subscriber')
        self.subscription = self.create_subscription(
            JointState,
            'joint_states',
            self.listener_callback,
            10)
        self.subscription  # prevent unused variable warning

    def listener_callback(self, msg):
        self.get_logger().info(f'Received {len(msg.name)} joint states')

        # Process the joint states for humanoid control
        for i, name in enumerate(msg.name):
            position = msg.position[i] if i < len(msg.position) else 0.0
            velocity = msg.velocity[i] if i < len(msg.velocity) else 0.0
            effort = msg.effort[i] if i < len(msg.effort) else 0.0

            # Example: Check for safety limits
            if abs(position) > 3.14:  # Check if joint is beyond safe limits
                self.get_logger().warn(f'Joint {name} position {position} exceeds safe range!')

            # Log joint information
            self.get_logger().debug(f'{name}: pos={position:.3f}, vel={velocity:.3f}, effort={effort:.3f}')

def main(args=None):
    rclpy.init(args=args)
    joint_state_subscriber = JointStateSubscriber()

    try:
        rclpy.spin(joint_state_subscriber)
    except KeyboardInterrupt:
        pass
    finally:
        joint_state_subscriber.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
```

## Launch File

```python
# launch/joint_state_demo.launch.py
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='demo_nodes_py',
            executable='joint_state_publisher',
            name='joint_state_publisher',
            output='screen',
        ),
        Node(
            package='demo_nodes_py',
            executable='joint_state_subscriber',
            name='joint_state_subscriber',
            output='screen',
        ),
    ])
```

## Package.xml

```xml
<?xml version="1.0"?>
<?xml-model href="http://download.ros.org/schema/package_format3.xsd" schematypens="http://www.w3.org/2001/XMLSchema"?>
<package format="3">
  <name>humanoid_sensor_demo</name>
  <version>0.0.1</version>
  <description>Basic ROS 2 publisher/subscriber example for humanoid sensor data</description>
  <maintainer email="maintainer@todo.todo">maintainer</maintainer>
  <license>Apache-2.0</license>

  <depend>rclpy</depend>
  <depend>std_msgs</depend>
  <depend>sensor_msgs</depend>

  <test_depend>ament_copyright</test_depend>
  <test_depend>ament_flake8</test_depend>
  <test_depend>ament_pep257</test_depend>
  <test_depend>python3-pytest</test_depend>

  <export>
    <build_type>ament_python</build_type>
  </export>
</package>
```

## Expected Terminal Output

When running the publisher and subscriber nodes:

```
[INFO] [1692345678.123456789] [joint_state_publisher]: Publishing joint states: 10 joints
[INFO] [1692345678.223456789] [joint_state_subscriber]: Received 10 joint states
[DEBUG] [1692345678.223456789] [joint_state_subscriber]: left_hip_joint: pos=0.123, vel=0.456, effort=-0.002
[DEBUG] [1692345678.223456789] [joint_state_subscriber]: left_knee_joint: pos=-0.234, vel=0.567, effort=0.001
...
```

This example demonstrates the core publish-subscribe pattern that forms the backbone of the ROS 2 nervous system for humanoid robotics, enabling real-time communication between sensor and control nodes.