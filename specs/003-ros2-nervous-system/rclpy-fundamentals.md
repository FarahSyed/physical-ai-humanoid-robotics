# rclpy Fundamentals for Humanoid Robotics

## Introduction to rclpy

rclpy is the Python client library for ROS 2, providing Python bindings for the ROS 2 client library (rcl). It allows Python developers to create ROS 2 nodes, publish and subscribe to topics, provide and use services, and create action clients and servers.

## Core Concepts

### Node Creation
The fundamental building block of any ROS 2 system is the Node. A node is an executable process that communicates with other nodes via topics, services, and actions.

### Publisher-Subscriber Pattern
ROS 2 uses a publish-subscribe messaging pattern where nodes publish data to topics and other nodes subscribe to those topics to receive the data.

### Services and Actions
Services provide request-response communication, while actions provide goal-oriented communication with feedback and status updates.

## Key Components

### Node Class
```python
import rclpy
from rclpy.node import Node

class MyNode(Node):
    def __init__(self):
        super().__init__('node_name')
        # Node initialization code here
```

### Publishers and Subscribers
```python
# Creating a publisher
publisher = self.create_publisher(MessageType, 'topic_name', qos_profile)

# Creating a subscriber
subscriber = self.create_subscription(
    MessageType, 'topic_name', callback_function, qos_profile)
```

### Timers
```python
# Creating a timer
timer_period = 0.5  # seconds
timer = self.create_timer(timer_period, timer_callback)
```

## Best Practices for Humanoid Robotics

1. **Error Handling**: Always include proper exception handling for safety-critical humanoid applications
2. **Resource Management**: Properly destroy nodes and clean up resources
3. **Safety Boundaries**: Implement safety checks and emergency stop mechanisms
4. **Real-time Considerations**: Use appropriate QoS profiles for time-critical humanoid control

## Example Structure

A typical rclpy node for humanoid robotics includes:
- Node initialization with proper parameters
- Publishers for sending control commands
- Subscribers for receiving sensor data
- Timers for periodic control updates
- Service clients/servers for configuration
- Proper cleanup in destructor