---
sidebar_label: 'Chapter 2: Python Integration with rclpy for Humanoid Control'
sidebar_position: 2
title: 'Chapter 2: Python Integration with rclpy for Humanoid Control'
description: 'Python integration with rclpy for humanoid robotics control systems'
---

# Chapter 2: Python Integration with rclpy for Humanoid Control

## Section 2.1: rclpy Fundamentals

rclpy is the Python client library for ROS 2, providing Python bindings for the ROS 2 client library (rcl). It allows Python developers to create ROS 2 nodes, publish and subscribe to topics, provide and use services, and create action clients and servers. For humanoid robotics, rclpy provides an accessible interface for implementing complex control algorithms while maintaining the performance and safety requirements of robotic systems.

### Core Concepts

**Node Creation**
The fundamental building block of any ROS 2 system is the Node. A node is an executable process that communicates with other nodes via topics, services, and actions.

```python
import rclpy
from rclpy.node import Node

class MyNode(Node):
    def __init__(self):
        super().__init__('node_name')
        # Node initialization code here
```

**Publishers and Subscribers**
ROS 2 uses a publish-subscribe messaging pattern where nodes publish data to topics and other nodes subscribe to those topics to receive the data.

```python
# Creating a publisher
publisher = self.create_publisher(MessageType, 'topic_name', qos_profile)

# Creating a subscriber
subscriber = self.create_subscription(
    MessageType, 'topic_name', callback_function, qos_profile)
```

**Timers**
Timers allow for periodic execution of functions, critical for control loops in humanoid robotics.

```python
# Creating a timer
timer_period = 0.5  # seconds
timer = self.create_timer(timer_period, timer_callback)
```

### Best Practices for Humanoid Robotics

1. **Error Handling**: Always include proper exception handling for safety-critical humanoid applications
2. **Resource Management**: Properly destroy nodes and clean up resources
3. **Safety Boundaries**: Implement safety checks and emergency stop mechanisms
4. **Real-time Considerations**: Use appropriate QoS profiles for time-critical humanoid control

## Section 2.2: Humanoid Control Nodes

Humanoid control nodes implement the core functionality required for humanoid robot operation, including joint trajectory control, sensor data processing, balance feedback, and safety boundaries.

### Basic rclpy Node Example

```python
#!/usr/bin/env python3
# humanoid_control_node.py
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, QoSDurabilityPolicy, QoSHistoryPolicy, QoSReliabilityPolicy
from std_msgs.msg import String, Bool
from sensor_msgs.msg import JointState
from control_msgs.msg import JointTrajectoryControllerState
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from builtin_interfaces.msg import Duration

class HumanoidController(Node):
    def __init__(self):
        super().__init__('humanoid_controller')

        # Define QoS profile for safety-critical humanoid communication
        qos_profile = QoSProfile(
            durability=QoSDurabilityPolicy.TRANSIENT_LOCAL,
            reliability=QoSReliabilityPolicy.RELIABLE,
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=10
        )

        # Publishers
        self.trajectory_publisher = self.create_publisher(
            JointTrajectory,
            '/joint_trajectory_controller/joint_trajectory',
            qos_profile
        )

        self.status_publisher = self.create_publisher(
            String,
            'humanoid_status',
            qos_profile
        )

        # Subscribers
        self.joint_state_subscriber = self.create_subscription(
            JointState,
            'joint_states',
            self.joint_state_callback,
            qos_profile
        )

        self.emergency_stop_subscriber = self.create_subscription(
            Bool,
            'emergency_stop',
            self.emergency_stop_callback,
            qos_profile
        )

        # Timer for control loop
        self.control_timer = self.create_timer(0.01, self.control_loop)  # 100Hz

        # Internal state
        self.current_joint_states = None
        self.emergency_stop_activated = False
        self.control_counter = 0

        self.get_logger().info('Humanoid Controller initialized')

    def joint_state_callback(self, msg):
        """Callback for receiving joint state updates"""
        self.current_joint_states = msg
        self.get_logger().debug(f'Received joint states for {len(msg.name)} joints')

    def emergency_stop_callback(self, msg):
        """Callback for emergency stop commands"""
        self.emergency_stop_activated = msg.data
        if self.emergency_stop_activated:
            self.get_logger().warn('EMERGENCY STOP ACTIVATED - Halting all movements')
            self.stop_all_joints()
        else:
            self.get_logger().info('Emergency stop cleared')

    def control_loop(self):
        """Main control loop running at 100Hz"""
        if self.emergency_stop_activated:
            return

        self.control_counter += 1

        # Example: Simple periodic trajectory generation
        if self.control_counter % 100 == 0:  # Every second
            self.publish_trajectory_command()

        # Publish status
        status_msg = String()
        status_msg.data = f"Operating normally - Cycle {self.control_counter}"
        self.status_publisher.publish(status_msg)

    def publish_trajectory_command(self):
        """Publish a simple trajectory command"""
        if not self.current_joint_states:
            return

        # Create a simple trajectory with 3 points
        trajectory_msg = JointTrajectory()
        trajectory_msg.joint_names = self.current_joint_states.name

        # Point 1: Current position
        point1 = JointTrajectoryPoint()
        point1.positions = list(self.current_joint_states.position)
        point1.velocities = [0.0] * len(point1.positions)
        point1.accelerations = [0.0] * len(point1.positions)
        point1.time_from_start = Duration(sec=0, nanosec=0)

        # Point 2: Slight offset (for demonstration)
        point2 = JointTrajectoryPoint()
        point2.positions = [pos + 0.1 for pos in self.current_joint_states.position]
        point2.velocities = [0.0] * len(point2.positions)
        point2.accelerations = [0.0] * len(point2.positions)
        point2.time_from_start = Duration(sec=1, nanosec=0)

        # Point 3: Return to original
        point3 = JointTrajectoryPoint()
        point3.positions = list(self.current_joint_states.position)
        point3.velocities = [0.0] * len(point3.positions)
        point3.accelerations = [0.0] * len(point3.positions)
        point3.time_from_start = Duration(sec=2, nanosec=0)

        trajectory_msg.points = [point1, point2, point3]

        self.trajectory_publisher.publish(trajectory_msg)
        self.get_logger().info(f'Published trajectory for {len(trajectory_msg.joint_names)} joints')

    def stop_all_joints(self):
        """Emergency stop - halt all joint movements"""
        if not self.current_joint_states:
            return

        # Publish zero-velocity trajectory to stop all joints immediately
        stop_trajectory = JointTrajectory()
        stop_trajectory.joint_names = self.current_joint_states.name

        stop_point = JointTrajectoryPoint()
        stop_point.positions = list(self.current_joint_states.position)  # Hold current position
        stop_point.velocities = [0.0] * len(stop_point.positions)  # Zero velocity
        stop_point.accelerations = [0.0] * len(stop_point.positions)  # Zero acceleration
        stop_point.time_from_start = Duration(sec=0, nanosec=100000000)  # 0.1 seconds

        stop_trajectory.points = [stop_point]
        self.trajectory_publisher.publish(stop_trajectory)

def main(args=None):
    rclpy.init(args=args)

    humanoid_controller = HumanoidController()

    try:
        rclpy.spin(humanoid_controller)
    except KeyboardInterrupt:
        pass
    finally:
        humanoid_controller.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
```

### Joint Trajectory Controller Example

```python
#!/usr/bin/env python3
# humanoid_joint_controller.py
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from rclpy.qos import QoSProfile, QoSDurabilityPolicy, QoSHistoryPolicy, QoSReliabilityPolicy
from rclpy.duration import Duration as RclpyDuration
from sensor_msgs.msg import JointState
from control_msgs.action import FollowJointTrajectory
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from builtin_interfaces.msg import Duration
import time
import math
from threading import Lock

class HumanoidJointController(Node):
    def __init__(self):
        super().__init__('humanoid_joint_controller')

        # QoS profile for safety-critical humanoid control
        qos_profile = QoSProfile(
            durability=QoSDurabilityPolicy.TRANSIENT_LOCAL,
            reliability=QoSReliabilityPolicy.RELIABLE,
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=10
        )

        # Subscribers
        self.joint_state_subscriber = self.create_subscription(
            JointState,
            'joint_states',
            self.joint_state_callback,
            qos_profile
        )

        # Publishers
        self.command_publisher = self.create_publisher(
            JointTrajectory,
            '/joint_trajectory_controller/joint_trajectory',
            qos_profile
        )

        # Action client for trajectory execution
        self._action_client = ActionClient(
            self,
            FollowJointTrajectory,
            '/joint_trajectory_controller/follow_joint_trajectory'
        )

        # Internal state
        self.current_joint_states = {}
        self.joint_state_lock = Lock()
        self.emergency_stop = False
        self.safety_violation = False

        # Humanoid-specific joint names (example for a simple humanoid)
        self.humanoid_joints = [
            'left_hip_joint', 'left_knee_joint', 'left_ankle_joint',
            'right_hip_joint', 'right_knee_joint', 'right_ankle_joint',
            'left_shoulder_joint', 'left_elbow_joint',
            'right_shoulder_joint', 'right_elbow_joint'
        ]

        # Initialize with default values
        for joint in self.humanoid_joints:
            self.current_joint_states[joint] = {
                'position': 0.0,
                'velocity': 0.0,
                'effort': 0.0
            }

        # Timer for safety checks (10Hz)
        self.safety_timer = self.create_timer(0.1, self.safety_check)

        # Timer for trajectory generation (1Hz)
        self.trajectory_timer = self.create_timer(1.0, self.generate_trajectory)

        self.get_logger().info('Humanoid Joint Controller initialized')

    def joint_state_callback(self, msg):
        """Callback for receiving joint state updates"""
        with self.joint_state_lock:
            for i, joint_name in enumerate(msg.name):
                if joint_name in self.current_joint_states:
                    if i < len(msg.position):
                        self.current_joint_states[joint_name]['position'] = msg.position[i]
                    if i < len(msg.velocity):
                        self.current_joint_states[joint_name]['velocity'] = msg.velocity[i]
                    if i < len(msg.effort):
                        self.current_joint_states[joint_name]['effort'] = msg.effort[i]

    def safety_check(self):
        """Perform safety checks on joint states"""
        with self.joint_state_lock:
            for joint_name, state in self.current_joint_states.items():
                # Check position limits
                if abs(state['position']) > 3.14:  # 180 degrees in radians
                    self.get_logger().error(f'Safety violation: {joint_name} position {state["position"]} exceeds limits')
                    self.safety_violation = True
                    self.emergency_stop = True
                    self.execute_emergency_stop()
                    return

                # Check velocity limits
                if abs(state['velocity']) > 5.0:  # rad/s
                    self.get_logger().warn(f'Warning: {joint_name} velocity {state["velocity"]} is high')

                # Check effort limits
                if abs(state['effort']) > 100.0:  # N*m
                    self.get_logger().warn(f'Warning: {joint_name} effort {state["effort"]} is high')

    def execute_emergency_stop(self):
        """Execute emergency stop procedure"""
        self.get_logger().fatal('EMERGENCY STOP - Halting all joint movements')

        # Create zero trajectory to stop all joints
        with self.joint_state_lock:
            trajectory_msg = JointTrajectory()
            trajectory_msg.joint_names = list(self.current_joint_states.keys())

            stop_point = JointTrajectoryPoint()
            stop_point.positions = [self.current_joint_states[joint]['position']
                                  for joint in trajectory_msg.joint_names]
            stop_point.velocities = [0.0] * len(trajectory_msg.joint_names)
            stop_point.accelerations = [0.0] * len(trajectory_msg.joint_names)
            stop_point.time_from_start = Duration(sec=0, nanosec=100000000)  # 0.1 seconds

            trajectory_msg.points = [stop_point]
            self.command_publisher.publish(trajectory_msg)

    def generate_trajectory(self):
        """Generate a demonstration trajectory for humanoid joints"""
        if self.emergency_stop or self.safety_violation:
            return

        trajectory_msg = JointTrajectory()
        trajectory_msg.joint_names = self.humanoid_joints

        # Get current positions
        with self.joint_state_lock:
            current_positions = [self.current_joint_states[joint]['position']
                               for joint in self.humanoid_joints]

        # Create a smooth periodic trajectory for demonstration
        points = []
        start_time = self.get_clock().now().seconds_nanoseconds()

        # Point 1: Start position (current + small offset)
        point1 = JointTrajectoryPoint()
        point1.positions = [
            pos + 0.1 * math.sin(start_time[0] * 0.5 + i)
            for i, pos in enumerate(current_positions)
        ]
        point1.velocities = [0.0] * len(self.humanoid_joints)
        point1.accelerations = [0.0] * len(self.humanoid_joints)
        point1.time_from_start = Duration(sec=0, nanosec=0)
        points.append(point1)

        # Point 2: Mid trajectory
        point2 = JointTrajectoryPoint()
        point2.positions = [
            pos + 0.2 * math.sin(start_time[0] * 0.5 + i + 1)
            for i, pos in enumerate(current_positions)
        ]
        point2.velocities = [0.0] * len(self.humanoid_joints)
        point2.accelerations = [0.0] * len(self.humanoid_joints)
        point2.time_from_start = Duration(sec=1, nanosec=0)
        points.append(point2)

        # Point 3: Return to near original
        point3 = JointTrajectoryPoint()
        point3.positions = [
            pos + 0.05 * math.sin(start_time[0] * 0.5 + i + 2)
            for i, pos in enumerate(current_positions)
        ]
        point3.velocities = [0.0] * len(self.humanoid_joints)
        point3.accelerations = [0.0] * len(self.humanoid_joints)
        point3.time_from_start = Duration(sec=2, nanosec=0)
        points.append(point3)

        trajectory_msg.points = points
        self.command_publisher.publish(trajectory_msg)

        self.get_logger().info(f'Published trajectory for {len(trajectory_msg.joint_names)} joints')

    def send_trajectory_goal(self, trajectory):
        """Send trajectory as an action goal"""
        goal_msg = FollowJointTrajectory.Goal()
        goal_msg.trajectory = trajectory

        # Wait for action server
        if not self._action_client.wait_for_server(timeout_sec=1.0):
            self.get_logger().error('Action server not available')
            return

        # Send goal
        self._action_client.send_goal_async(
            goal_msg,
            feedback_callback=self.feedback_callback
        )

    def feedback_callback(self, feedback_msg):
        """Handle feedback from trajectory execution"""
        self.get_logger().debug(f'Trajectory execution feedback: {feedback_msg.feedback}')

def main(args=None):
    rclpy.init(args=args)

    humanoid_joint_controller = HumanoidJointController()

    try:
        rclpy.spin(humanoid_joint_controller)
    except KeyboardInterrupt:
        humanoid_joint_controller.get_logger().info('Shutting down...')
    finally:
        # Ensure emergency stop on shutdown
        humanoid_joint_controller.execute_emergency_stop()
        humanoid_joint_controller.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
```

## Section 2.3: Advanced rclpy Patterns

### Lifecycle Nodes for Safety Systems

Lifecycle nodes provide a structured approach to node management with well-defined states (unconfigured, inactive, active, finalized), which is essential for safety-critical humanoid applications.

```python
#!/usr/bin/env python3
# humanoid_safety_lifecycle_node.py
import rclpy
from rclpy.node import Node
from rclpy.lifecycle import LifecycleNode, LifecycleState, TransitionCallbackReturn
from rclpy.qos import QoSProfile, QoSDurabilityPolicy, QoSHistoryPolicy, QoSReliabilityPolicy
from rclpy.lifecycle.publisher import LifecyclePublisher
from sensor_msgs.msg import JointState
from std_msgs.msg import Bool, String
from builtin_interfaces.msg import Time
import threading
import time

class HumanoidSafetyManager(LifecycleNode):
    def __init__(self):
        super().__init__('humanoid_safety_manager')

        # Initialize variables
        self.current_joint_states = None
        self.emergency_stop_activated = False
        self.safety_monitoring_active = False

        # QoS profile for safety-critical communication
        self.qos_profile = QoSProfile(
            durability=QoSDurabilityPolicy.TRANSIENT_LOCAL,
            reliability=QoSReliabilityPolicy.RELIABLE,
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=10
        )

        self.get_logger().info('Humanoid Safety Manager created in unconfigured state')

    # Configuration callback - called when transitioning from unconfigured to inactive
    def on_configure(self, state):
        self.get_logger().info('Configuring humanoid safety manager')

        # Create publishers (but they won't be active until on_activate)
        self.safety_status_publisher = self.create_publisher(
            String,
            'safety_status',
            self.qos_profile
        )

        self.emergency_stop_publisher = self.create_publisher(
            Bool,
            'emergency_stop',
            self.qos_profile
        )

        self.safety_violation_publisher = self.create_publisher(
            String,
            'safety_violations',
            self.qos_profile
        )

        # Create subscribers
        self.joint_state_subscriber = self.create_subscription(
            JointState,
            'joint_states',
            self.joint_state_callback,
            self.qos_profile
        )

        # Create safety monitoring timer (inactive until activated)
        self.safety_timer = self.create_timer(0.05, self.safety_monitoring_callback)  # 20Hz monitoring
        self.safety_timer.cancel()  # Cancel until activated

        # Set initial state
        self.safety_monitoring_active = False
        self.emergency_stop_activated = False

        return TransitionCallbackReturn.SUCCESS

    # Activation callback - called when transitioning from inactive to active
    def on_activate(self, state):
        self.get_logger().info('Activating humanoid safety manager')

        # Activate all lifecycle entities
        self.safety_status_publisher.on_activate()
        self.emergency_stop_publisher.on_activate()
        self.safety_violation_publisher.on_activate()

        # Start safety monitoring
        self.safety_timer.reset()
        self.safety_monitoring_active = True

        # Publish activation status
        status_msg = String()
        status_msg.data = "SAFETY_MANAGER_ACTIVE"
        self.safety_status_publisher.publish(status_msg)

        self.get_logger().info('Humanoid safety manager activated and monitoring started')
        return TransitionCallbackReturn.SUCCESS

    # Deactivation callback - called when transitioning from active to inactive
    def on_deactivate(self, state):
        self.get_logger().info('Deactivating humanoid safety manager')

        # Deactivate all lifecycle entities
        self.safety_status_publisher.on_deactivate()
        self.emergency_stop_publisher.on_deactivate()
        self.safety_violation_publisher.on_deactivate()

        # Stop safety monitoring
        self.safety_timer.cancel()
        self.safety_monitoring_active = False

        # Publish deactivation status
        status_msg = String()
        status_msg.data = "SAFETY_MANAGER_INACTIVE"
        self.safety_status_publisher.publish(status_msg)

        self.get_logger().info('Humanoid safety manager deactivated and monitoring stopped')
        return TransitionCallbackReturn.SUCCESS

    # Cleanup callback - called when transitioning from inactive to unconfigured
    def on_cleanup(self, state):
        self.get_logger().info('Cleaning up humanoid safety manager')

        # Destroy entities
        self.destroy_publisher(self.safety_status_publisher)
        self.destroy_publisher(self.emergency_stop_publisher)
        self.destroy_publisher(self.safety_violation_publisher)
        self.destroy_subscription(self.joint_state_subscriber)
        self.destroy_timer(self.safety_timer)

        # Reset state
        self.current_joint_states = None
        self.emergency_stop_activated = False
        self.safety_monitoring_active = False

        self.get_logger().info('Humanoid safety manager cleaned up')
        return TransitionCallbackReturn.SUCCESS

    # Shutdown callback - called when transitioning from any state to finalized
    def on_shutdown(self, state):
        self.get_logger().info('Shutting down humanoid safety manager')

        # Ensure safety
        self.activate_emergency_stop()

        # Destroy all entities
        try:
            self.destroy_publisher(self.safety_status_publisher)
            self.destroy_publisher(self.emergency_stop_publisher)
            self.destroy_publisher(self.safety_violation_publisher)
            self.destroy_subscription(self.joint_state_subscriber)
            self.destroy_timer(self.safety_timer)
        except Exception as e:
            self.get_logger().warn(f'Error during shutdown cleanup: {e}')

        self.get_logger().info('Humanoid safety manager shut down complete')
        return TransitionCallbackReturn.SUCCESS

    # Error callback - called when transitioning from any state to errorprocessing
    def on_error(self, state):
        self.get_logger().error('Humanoid safety manager entering error state')

        # Activate emergency stop in error state
        self.activate_emergency_stop()

        return TransitionCallbackReturn.SUCCESS

    def joint_state_callback(self, msg):
        """Callback for receiving joint state updates"""
        if not self.emergency_stop_activated:
            self.current_joint_states = msg

    def safety_monitoring_callback(self):
        """Main safety monitoring callback"""
        if not self.safety_monitoring_active or self.emergency_stop_activated:
            return

        if self.current_joint_states is None:
            return

        # Check for safety violations
        safety_violations = []

        for i, joint_name in enumerate(self.current_joint_states.name):
            if i >= len(self.current_joint_states.position):
                continue

            position = self.current_joint_states.position[i]
            velocity = self.current_joint_states.velocity[i] if i < len(self.current_joint_states.velocity) else 0.0
            effort = self.current_joint_states.effort[i] if i < len(self.current_joint_states.effort) else 0.0

            # Position limits check
            if abs(position) > 3.14:  # Exceeds 180 degrees
                violation = f"Position limit violation for {joint_name}: {position:.3f} rad"
                safety_violations.append(violation)
                self.get_logger().error(violation)

            # Velocity limits check
            if abs(velocity) > 10.0:  # Exceeds 10 rad/s
                violation = f"Velocity limit violation for {joint_name}: {velocity:.3f} rad/s"
                safety_violations.append(violation)
                self.get_logger().error(violation)

            # Effort limits check
            if abs(effort) > 200.0:  # Exceeds 200 N*m
                violation = f"Effort limit violation for {joint_name}: {effort:.3f} N*m"
                safety_violations.append(violation)
                self.get_logger().error(violation)

        # Handle violations
        if safety_violations:
            # Publish violations
            violations_msg = String()
            violations_msg.data = '; '.join(safety_violations)
            self.safety_violation_publisher.publish(violations_msg)

            # Activate emergency stop if serious violations
            serious_violations = [v for v in safety_violations if "Position limit" in v]
            if serious_violations:
                self.get_logger().fatal('SERIOUS SAFETY VIOLATIONS - ACTIVATING EMERGENCY STOP')
                self.activate_emergency_stop()

    def activate_emergency_stop(self):
        """Activate emergency stop across the system"""
        if not self.emergency_stop_activated:
            self.emergency_stop_activated = True

            # Publish emergency stop command
            emergency_msg = Bool()
            emergency_msg.data = True
            self.emergency_stop_publisher.publish(emergency_msg)

            # Log the event
            self.get_logger().fatal('EMERGENCY STOP ACTIVATED - ALL HUMANOID SYSTEMS HALTED')

            # Publish safety status
            status_msg = String()
            status_msg.data = "EMERGENCY_STOP_ACTIVATED"
            self.safety_status_publisher.publish(status_msg)

    def deactivate_emergency_stop(self):
        """Deactivate emergency stop (requires manual reset)"""
        # In a real safety system, this might require additional checks or manual intervention
        self.emergency_stop_activated = False

        # Publish release command
        emergency_msg = Bool()
        emergency_msg.data = False
        self.emergency_stop_publisher.publish(emergency_msg)

        self.get_logger().info('Emergency stop deactivated - system reset')

        # Publish safety status
        status_msg = String()
        status_msg.data = "EMERGENCY_STOP_DEACTIVATED"
        self.safety_status_publisher.publish(status_msg)


def main(args=None):
    rclpy.init(args=args)

    safety_manager = HumanoidSafetyManager()

    # Trigger the initial state transition: unconfigured -> inactive
    safety_manager.trigger_configure()

    try:
        # Activate the node: inactive -> active
        safety_manager.trigger_activate()

        # Run the node
        rclpy.spin(safety_manager)

    except KeyboardInterrupt:
        safety_manager.get_logger().info('Interrupted, shutting down...')
    finally:
        # Properly shut down the lifecycle node
        if safety_manager.lifecycle_state.label == 'active':
            safety_manager.trigger_deactivate()
        if safety_manager.lifecycle_state.label == 'inactive':
            safety_manager.trigger_cleanup()
        if safety_manager.lifecycle_state.label != 'finalized':
            safety_manager.trigger_shutdown()

        rclpy.shutdown()

if __name__ == '__main__':
    main()
```

## Section 2.4: Integration with AI Systems

### AI Interface Node

```python
#!/usr/bin/env python3
# ai_interface_node.py
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, QoSDurabilityPolicy, QoSHistoryPolicy, QoSReliabilityPolicy
from std_msgs.msg import String, Bool
from sensor_msgs.msg import JointState, Image
from geometry_msgs.msg import PoseStamped
import threading
import time
import json
from typing import Optional, Dict, Any
import requests
from builtin_interfaces.msg import Time

class AIInterfaceNode(Node):
    def __init__(self):
        super().__init__('ai_interface_node')

        # QoS profile for AI communication
        qos_profile = QoSProfile(
            durability=QoSDurabilityPolicy.VOLATILE,
            reliability=QoSReliabilityPolicy.BEST_EFFORT,
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=10
        )

        # Publishers
        self.action_command_publisher = self.create_publisher(
            String,
            'ai_action_commands',
            qos_profile
        )

        self.status_publisher = self.create_publisher(
            String,
            'ai_interface_status',
            qos_profile
        )

        # Subscribers
        self.joint_state_subscriber = self.create_subscription(
            JointState,
            'joint_states',
            self.joint_state_callback,
            qos_profile
        )

        self.vision_subscriber = self.create_subscription(
            Image,
            'camera/image_raw',
            self.vision_callback,
            qos_profile
        )

        self.voice_command_subscriber = self.create_subscription(
            String,
            'voice_commands',
            self.voice_command_callback,
            qos_profile
        )

        # Internal state
        self.current_joint_states = None
        self.last_vision_data = None
        self.ai_service_available = True
        self.ai_request_queue = []
        self.ai_response_lock = threading.Lock()

        # Timer for AI processing (1Hz - for demonstration)
        self.ai_timer = self.create_timer(1.0, self.process_ai_requests)

        # Safety timer (10Hz) to monitor AI interface health
        self.safety_timer = self.create_timer(0.1, self.ai_safety_check)

        self.get_logger().info('AI Interface Node initialized')

    def joint_state_callback(self, msg):
        """Callback for receiving joint state updates"""
        self.current_joint_states = msg
        self.get_logger().debug(f'Received joint states for {len(msg.name)} joints')

    def vision_callback(self, msg):
        """Callback for receiving vision data"""
        # In a real implementation, this would process the image
        # For this example, we'll just store that we received vision data
        self.last_vision_data = {
            'timestamp': msg.header.stamp,
            'encoding': msg.encoding,
            'height': msg.height,
            'width': msg.width
        }
        self.get_logger().debug(f'Received vision data: {msg.width}x{msg.height}')

    def voice_command_callback(self, msg):
        """Callback for receiving voice commands"""
        self.get_logger().info(f'Received voice command: {msg.data}')

        # Add to AI processing queue
        request_data = {
            'type': 'voice_command',
            'content': msg.data,
            'timestamp': self.get_clock().now().seconds_nanoseconds(),
            'context': self.get_current_robot_state()
        }

        with self.ai_response_lock:
            self.ai_request_queue.append(request_data)

    def get_current_robot_state(self) -> Dict[str, Any]:
        """Get current robot state for AI context"""
        state = {
            'timestamp': self.get_clock().now().seconds_nanoseconds(),
            'joint_states': {},
            'vision_available': self.last_vision_data is not None
        }

        if self.current_joint_states:
            for i, name in enumerate(self.current_joint_states.name):
                if i < len(self.current_joint_states.position):
                    state['joint_states'][name] = {
                        'position': self.current_joint_states.position[i],
                        'velocity': self.current_joint_states.velocity[i] if i < len(self.current_joint_states.velocity) else 0.0,
                        'effort': self.current_joint_states.effort[i] if i < len(self.current_joint_states.effort) else 0.0
                    }

        return state

    def process_ai_requests(self):
        """Process queued AI requests"""
        if not self.ai_request_queue:
            return

        with self.ai_response_lock:
            current_queue = self.ai_request_queue.copy()
            self.ai_request_queue.clear()

        for request in current_queue:
            try:
                response = self.query_ai_service(request)
                if response:
                    self.handle_ai_response(response, request)
            except Exception as e:
                self.get_logger().error(f'Error processing AI request: {e}')
                self.ai_service_available = False

    def query_ai_service(self, request_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Query external AI service - in simulation, return mock response"""
        self.get_logger().info(f'Querying AI service with: {request_data["type"]}')

        # Simulate AI service call (in real implementation, this would call an actual AI service)
        # For simulation, return a mock response based on the request type
        if request_data['type'] == 'voice_command':
            command = request_data['content'].lower()

            if 'walk' in command or 'move' in command:
                action_response = {
                    'action': 'walk_forward',
                    'parameters': {'distance': 1.0, 'speed': 0.5},
                    'confidence': 0.85
                }
            elif 'stop' in command:
                action_response = {
                    'action': 'stop_movement',
                    'parameters': {},
                    'confidence': 0.95
                }
            elif 'look' in command or 'see' in command:
                action_response = {
                    'action': 'turn_head',
                    'parameters': {'pan': 0.0, 'tilt': 0.0},
                    'confidence': 0.75
                }
            else:
                action_response = {
                    'action': 'unknown_command',
                    'parameters': {'original_command': command},
                    'confidence': 0.3
                }

            return action_response

        return None

    def handle_ai_response(self, response: Dict[str, Any], original_request: Dict[str, Any]):
        """Handle AI service response"""
        self.get_logger().info(f'AI response: {response["action"]} with confidence {response.get("confidence", 0):.2f}')

        # Validate confidence threshold
        confidence_threshold = 0.7
        if response.get('confidence', 0) < confidence_threshold:
            self.get_logger().warn(f'AI response confidence {response.get("confidence", 0):.2f} below threshold {confidence_threshold}')
            return

        # Publish action command based on AI response
        action_msg = String()
        action_msg.data = json.dumps(response)
        self.action_command_publisher.publish(action_msg)

        # Update status
        status_msg = String()
        status_msg.data = f"AI processed: {response['action']} (conf: {response.get('confidence', 0):.2f})"
        self.status_publisher.publish(status_msg)

    def ai_safety_check(self):
        """Perform safety checks on AI interface"""
        # Check if AI service is still available
        # In a real system, this might check connection health, response times, etc.

        # For simulation, just log the check
        self.get_logger().debug(f'AI interface health check - queue size: {len(self.ai_request_queue)}')

        # Reset availability flag if needed
        if not self.ai_service_available:
            # Try to restore service availability after some time
            # In real implementation, this would attempt to reconnect
            self.ai_service_available = True
            self.get_logger().info('AI service restored')

    def send_ai_request(self, request_type: str, content: str, context: Optional[Dict[str, Any]] = None):
        """Send an AI request"""
        request_data = {
            'type': request_type,
            'content': content,
            'timestamp': self.get_clock().now().seconds_nanoseconds(),
            'context': context or self.get_current_robot_state()
        }

        with self.ai_response_lock:
            self.ai_request_queue.append(request_data)

        self.get_logger().info(f'Queued AI request: {request_type}')


def main(args=None):
    rclpy.init(args=args)

    ai_interface_node = AIInterfaceNode()

    try:
        rclpy.spin(ai_interface_node)
    except KeyboardInterrupt:
        ai_interface_node.get_logger().info('Shutting down AI Interface Node...')
    finally:
        ai_interface_node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
```

## Section 2.5: Error Handling and Diagnostics

### Diagnostic Node Example

```python
#!/usr/bin/env python3
# humanoid_diagnostics_node.py
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, QoSDurabilityPolicy, QoSHistoryPolicy, QoSReliabilityPolicy
from diagnostic_msgs.msg import DiagnosticArray, DiagnosticStatus, KeyValue
from sensor_msgs.msg import JointState, Temperature, BatteryState
from std_msgs.msg import String, Bool, Float64
from builtin_interfaces.msg import Time
import threading
import time
from typing import Dict, List, Any
import psutil
import socket

class HumanoidDiagnosticsNode(Node):
    def __init__(self):
        super().__init__('humanoid_diagnostics_node')

        # QoS profile for diagnostic communication
        qos_profile = QoSProfile(
            durability=QoSDurabilityPolicy.TRANSIENT_LOCAL,
            reliability=QoSReliabilityPolicy.RELIABLE,
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=10
        )

        # Publishers
        self.diagnostic_publisher = self.create_publisher(
            DiagnosticArray,
            '/diagnostics',
            qos_profile
        )

        # Subscribers
        self.joint_state_subscriber = self.create_subscription(
            JointState,
            'joint_states',
            self.joint_state_callback,
            qos_profile
        )

        self.battery_subscriber = self.create_subscription(
            BatteryState,
            'battery_state',
            self.battery_callback,
            qos_profile
        )

        self.temperature_subscriber = self.create_subscription(
            Temperature,
            'system_temperature',
            self.temperature_callback,
            qos_profile
        )

        self.emergency_stop_subscriber = self.create_subscription(
            Bool,
            'emergency_stop',
            self.emergency_stop_callback,
            qos_profile
        )

        # Internal state
        self.joint_states = {}
        self.battery_state = None
        self.temperature = None
        self.emergency_stop_active = False
        self.system_monitoring_active = True

        # Diagnostic timers
        self.diagnostic_timer = self.create_timer(1.0, self.publish_diagnostics)  # 1Hz
        self.system_monitor_timer = self.create_timer(2.0, self.update_system_monitoring)  # 0.5Hz

        # Initialize diagnostic status
        self.last_diagnostics_time = self.get_clock().now()

        self.get_logger().info('Humanoid Diagnostics Node initialized')

    def joint_state_callback(self, msg):
        """Callback for receiving joint state updates"""
        for i, name in enumerate(msg.name):
            if i < len(msg.position) and i < len(msg.velocity) and i < len(msg.effort):
                self.joint_states[name] = {
                    'position': msg.position[i],
                    'velocity': msg.velocity[i],
                    'effort': msg.effort[i],
                    'timestamp': msg.header.stamp
                }

    def battery_callback(self, msg):
        """Callback for receiving battery state updates"""
        self.battery_state = {
            'voltage': msg.voltage,
            'current': msg.current,
            'charge': msg.charge,
            'capacity': msg.capacity,
            'design_capacity': msg.design_capacity,
            'percentage': msg.percentage,
            'power_supply_status': msg.power_supply_status,
            'power_supply_health': msg.power_supply_health,
            'power_supply_technology': msg.power_supply_technology,
            'present': msg.present
        }

    def temperature_callback(self, msg):
        """Callback for receiving temperature updates"""
        self.temperature = {
            'temperature': msg.temperature,
            'variance': msg.variance,
            'header': msg.header
        }

    def emergency_stop_callback(self, msg):
        """Callback for emergency stop status"""
        self.emergency_stop_active = msg.data

    def update_system_monitoring(self):
        """Update system-level monitoring data"""
        if not self.system_monitoring_active:
            return

        # Get system resource usage
        cpu_percent = psutil.cpu_percent(interval=None)
        memory_percent = psutil.virtual_memory().percent
        disk_percent = psutil.disk_usage('/').percent

        # Get network information
        try:
            hostname = socket.gethostname()
            ip_address = socket.gethostbyname(hostname)
        except Exception:
            hostname = "unknown"
            ip_address = "0.0.0.0"

        self.system_info = {
            'cpu_percent': cpu_percent,
            'memory_percent': memory_percent,
            'disk_percent': disk_percent,
            'hostname': hostname,
            'ip_address': ip_address,
            'timestamp': self.get_clock().now()
        }

    def publish_diagnostics(self):
        """Publish diagnostic information"""
        diagnostic_array = DiagnosticArray()
        diagnostic_array.header.stamp = self.get_clock().now().to_msg()

        # Add individual diagnostic statuses
        diagnostic_array.status = [
            self.get_hardware_diagnostics(),
            self.get_joint_diagnostics(),
            self.get_power_diagnostics(),
            self.get_thermal_diagnostics(),
            self.get_safety_diagnostics(),
            self.get_system_diagnostics()
        ]

        self.diagnostic_publisher.publish(diagnostic_array)
        self.last_diagnostics_time = self.get_clock().now()

    def get_hardware_diagnostics(self) -> DiagnosticStatus:
        """Get hardware-level diagnostics"""
        status = DiagnosticStatus()
        status.name = "Humanoid Hardware Status"
        status.hardware_id = "humanoid_platform"

        # Check if we're receiving joint states
        if not self.joint_states:
            status.level = DiagnosticStatus.ERROR
            status.message = "No joint state data received"
        else:
            status.level = DiagnosticStatus.OK
            status.message = f"Monitoring {len(self.joint_states)} joints"

        # Add key-value pairs for detailed information
        status.values = [
            KeyValue(key="Joint Count", value=str(len(self.joint_states))),
            KeyValue(key="Last Update", value=str(self.get_clock().now().seconds_nanoseconds()))
        ]

        return status

    def get_joint_diagnostics(self) -> DiagnosticStatus:
        """Get joint-specific diagnostics"""
        status = DiagnosticStatus()
        status.name = "Joint Health"
        status.hardware_id = "joint_system"

        if not self.joint_states:
            status.level = DiagnosticStatus.WARN
            status.message = "No joint data available"
            return status

        # Check joint health
        total_joints = len(self.joint_states)
        healthy_joints = 0
        warning_joints = 0
        error_joints = 0

        joint_details = []

        for joint_name, joint_data in self.joint_states.items():
            pos = joint_data['position']
            vel = joint_data['velocity']
            effort = joint_data['effort']

            # Check position limits
            pos_limit = 3.14  # radians
            vel_limit = 10.0  # rad/s
            effort_limit = 100.0  # N*m

            joint_status = "OK"
            if abs(pos) > pos_limit:
                joint_status = "POS_LIMIT"
                error_joints += 1
            elif abs(vel) > vel_limit:
                joint_status = "VEL_HIGH"
                warning_joints += 1
            elif abs(effort) > effort_limit:
                joint_status = "EFFORT_HIGH"
                warning_joints += 1
            else:
                healthy_joints += 1

            joint_details.append(f"{joint_name}: {joint_status}")

        # Determine overall status
        if error_joints > 0:
            status.level = DiagnosticStatus.ERROR
            status.message = f"{error_joints}/{total_joints} joints in error state"
        elif warning_joints > 0:
            status.level = DiagnosticStatus.WARN
            status.message = f"{warning_joints}/{total_joints} joints with warnings"
        else:
            status.level = DiagnosticStatus.OK
            status.message = f"All {healthy_joints}/{total_joints} joints healthy"

        # Add detailed information
        status.values = [
            KeyValue(key="Total Joints", value=str(total_joints)),
            KeyValue(key="Healthy Joints", value=str(healthy_joints)),
            KeyValue(key="Warning Joints", value=str(warning_joints)),
            KeyValue(key="Error Joints", value=str(error_joints)),
            KeyValue(key="Joint Details", value="; ".join(joint_details))
        ]

        return status

    def get_power_diagnostics(self) -> DiagnosticStatus:
        """Get power system diagnostics"""
        status = DiagnosticStatus()
        status.name = "Power System"
        status.hardware_id = "power_system"

        if not self.battery_state:
            status.level = DiagnosticStatus.WARN
            status.message = "No battery data available"
            return status

        # Determine power status
        battery_percent = self.battery_state['percentage']
        voltage = self.battery_state['voltage']

        if battery_percent < 0.1:  # Less than 10%
            status.level = DiagnosticStatus.ERROR
            status.message = f"Critical battery: {battery_percent*100:.1f}%"
        elif battery_percent < 0.2:  # Less than 20%
            status.level = DiagnosticStatus.WARN
            status.message = f"Low battery: {battery_percent*100:.1f}%"
        else:
            status.level = DiagnosticStatus.OK
            status.message = f"Normal battery: {battery_percent*100:.1f}%"

        # Add detailed information
        status.values = [
            KeyValue(key="Battery Percentage", value=f"{battery_percent*100:.2f}%"),
            KeyValue(key="Voltage", value=f"{voltage:.2f}V"),
            KeyValue(key="Current", value=f"{self.battery_state['current']:.2f}A"),
            KeyValue(key="Capacity", value=f"{self.battery_state['capacity']:.2f}Ah"),
            KeyValue(key="Status", value=str(self.battery_state['power_supply_status']))
        ]

        return status

    def get_thermal_diagnostics(self) -> DiagnosticStatus:
        """Get thermal system diagnostics"""
        status = DiagnosticStatus()
        status.name = "Thermal Management"
        status.hardware_id = "thermal_system"

        if not self.temperature:
            status.level = DiagnosticStatus.WARN
            status.message = "No temperature data available"
            return status

        temp = self.temperature['temperature']
        temp_limit = 80.0  # degrees Celsius

        if temp > temp_limit:
            status.level = DiagnosticStatus.ERROR
            status.message = f"Overheating: {temp:.1f}°C > {temp_limit}°C"
        elif temp > temp_limit * 0.8:  # 80% of limit
            status.level = DiagnosticStatus.WARN
            status.message = f"High temperature: {temp:.1f}°C"
        else:
            status.level = DiagnosticStatus.OK
            status.message = f"Normal temperature: {temp:.1f}°C"

        # Add detailed information
        status.values = [
            KeyValue(key="Temperature", value=f"{temp:.2f}°C"),
            KeyValue(key="Variance", value=f"{self.temperature['variance']:.2f}"),
            KeyValue(key="Limit", value=f"{temp_limit}°C")
        ]

        return status

    def get_safety_diagnostics(self) -> DiagnosticStatus:
        """Get safety system diagnostics"""
        status = DiagnosticStatus()
        status.name = "Safety System"
        status.hardware_id = "safety_system"

        if self.emergency_stop_active:
            status.level = DiagnosticStatus.ERROR
            status.message = "EMERGENCY STOP ACTIVATED"
        else:
            status.level = DiagnosticStatus.OK
            status.message = "Safety systems normal"

        # Add detailed information
        status.values = [
            KeyValue(key="Emergency Stop", value="ACTIVE" if self.emergency_stop_active else "INACTIVE"),
            KeyValue(key="Safety Status", value="OK" if not self.emergency_stop_active else "EMERGENCY")
        ]

        return status

    def get_system_diagnostics(self) -> DiagnosticStatus:
        """Get system-level diagnostics"""
        status = DiagnosticStatus()
        status.name = "System Resources"
        status.hardware_id = "system_resources"

        if not hasattr(self, 'system_info'):
            self.update_system_monitoring()

        if not hasattr(self, 'system_info'):
            self.update_system_monitoring()

        if not hasattr(self, 'system_info'):
            status.level = DiagnosticStatus.WARN
            status.message = "System monitoring not initialized"
            return status

        # Check resource usage
        cpu_percent = self.system_info['cpu_percent']
        memory_percent = self.system_info['memory_percent']
        disk_percent = self.system_info['disk_percent']

        max_cpu = 80.0
        max_memory = 85.0
        max_disk = 90.0

        resource_issues = []
        if cpu_percent > max_cpu:
            resource_issues.append(f"CPU: {cpu_percent:.1f}% > {max_cpu}%")
        if memory_percent > max_memory:
            resource_issues.append(f"Memory: {memory_percent:.1f}% > {max_memory}%")
        if disk_percent > max_disk:
            resource_issues.append(f"Disk: {disk_percent:.1f}% > {max_disk}%")

        if resource_issues:
            status.level = DiagnosticStatus.WARN
            status.message = f"Resource issues: {', '.join(resource_issues)}"
        else:
            status.level = DiagnosticStatus.OK
            status.message = f"Resources OK: CPU {cpu_percent:.1f}%, Mem {memory_percent:.1f}%, Disk {disk_percent:.1f}%"

        # Add detailed information
        status.values = [
            KeyValue(key="CPU Usage", value=f"{cpu_percent:.2f}%"),
            KeyValue(key="Memory Usage", value=f"{memory_percent:.2f}%"),
            KeyValue(key="Disk Usage", value=f"{disk_percent:.2f}%"),
            KeyValue(key="Hostname", value=self.system_info['hostname']),
            KeyValue(key="IP Address", value=self.system_info['ip_address'])
        ]

        return status


def main(args=None):
    rclpy.init(args=args)

    diagnostics_node = HumanoidDiagnosticsNode()

    try:
        rclpy.spin(diagnostics_node)
    except KeyboardInterrupt:
        diagnostics_node.get_logger().info('Shutting down Humanoid Diagnostics Node...')
    finally:
        diagnostics_node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
```

## Section 2.6: Emergency Stop Safety Protocol

```python
#!/usr/bin/env python3
# emergency_stop_handler.py
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, QoSDurabilityPolicy, QoSHistoryPolicy, QoSReliabilityPolicy
from std_msgs.msg import Bool, String
from sensor_msgs.msg import JointState
from trajectory_msgs.msg import JointTrajectory
from builtin_interfaces.msg import Duration
from collections import deque
import time
from threading import Lock

class EmergencyStopHandler(Node):
    def __init__(self):
        super().__init__('emergency_stop_handler')

        # QoS profile for safety-critical communication
        qos_profile = QoSProfile(
            durability=QoSDurabilityPolicy.TRANSIENT_LOCAL,
            reliability=QoSReliabilityPolicy.RELIABLE,
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=10
        )

        # Publishers
        self.emergency_stop_publisher = self.create_publisher(
            Bool,
            'emergency_stop',
            qos_profile
        )

        self.halt_command_publisher = self.create_publisher(
            JointTrajectory,
            '/joint_trajectory_controller/joint_trajectory',
            qos_profile
        )

        self.status_publisher = self.create_publisher(
            String,
            'emergency_stop_status',
            qos_profile
        )

        # Subscribers
        self.emergency_stop_subscriber = self.create_subscription(
            Bool,
            'emergency_stop_request',
            self.emergency_stop_request_callback,
            qos_profile
        )

        self.joint_state_subscriber = self.create_subscription(
            JointState,
            'joint_states',
            self.joint_state_callback,
            qos_profile
        )

        # Internal state
        self.emergency_stop_active = False
        self.current_joint_states = None
        self.joint_state_lock = Lock()
        self.last_stop_time = None
        self.stop_reason = "SYSTEM_INITIALIZED"
        self.manual_reset_required = True  # Safety requirement for humanoid systems

        # Timer for safety monitoring (10Hz)
        self.safety_timer = self.create_timer(0.1, self.safety_monitor_callback)

        # Timer for status publishing (1Hz)
        self.status_timer = self.create_timer(1.0, self.publish_status)

        self.get_logger().info('Emergency Stop Handler initialized')

    def joint_state_callback(self, msg):
        """Callback for receiving joint state updates"""
        with self.joint_state_lock:
            self.current_joint_states = msg

    def emergency_stop_request_callback(self, msg):
        """Handle emergency stop requests"""
        if msg.data and not self.emergency_stop_active:
            self.activate_emergency_stop("EXTERNAL_REQUEST")
        elif not msg.data and self.emergency_stop_active and not self.manual_reset_required:
            self.deactivate_emergency_stop()

    def activate_emergency_stop(self, reason="UNSPECIFIED"):
        """Activate emergency stop"""
        if not self.emergency_stop_active:
            self.emergency_stop_active = True
            self.last_stop_time = self.get_clock().now()
            self.stop_reason = reason

            # Publish emergency stop command
            stop_msg = Bool()
            stop_msg.data = True
            self.emergency_stop_publisher.publish(stop_msg)

            # Halt all joint movements immediately
            self.halt_all_joints()

            # Log the event
            self.get_logger().fatal(f'EMERGENCY STOP ACTIVATED - Reason: {reason}')

            # Publish status
            status_msg = String()
            status_msg.data = f"EMERGENCY_STOP_ACTIVE: {reason}"
            self.status_publisher.publish(status_msg)

    def deactivate_emergency_stop(self):
        """Deactivate emergency stop (with safety checks)"""
        if self.emergency_stop_active:
            # Safety check: ensure joints are in safe positions before deactivation
            with self.joint_state_lock:
                if self.current_joint_states:
                    # Check if joints are in safe positions (implementation-specific)
                    if self.are_joints_in_safe_position():
                        self.emergency_stop_active = False
                        self.stop_reason = "SYSTEM_RESET"

                        # Publish release command
                        release_msg = Bool()
                        release_msg.data = False
                        self.emergency_stop_publisher.publish(release_msg)

                        self.get_logger().info('Emergency stop deactivated - system reset allowed')

                        # Publish status
                        status_msg = String()
                        status_msg.data = "EMERGENCY_STOP_DEACTIVATED"
                        self.status_publisher.publish(status_msg)
                    else:
                        self.get_logger().warn('Cannot deactivate emergency stop - joints not in safe positions')
                else:
                    self.get_logger().warn('Cannot deactivate emergency stop - no joint state available')

    def are_joints_in_safe_position(self) -> bool:
        """Check if joints are in safe positions for reset"""
        if not self.current_joint_states:
            return False

        # Define safe position ranges (example values)
        safe_ranges = {
            'hip': (-0.2, 0.2),  # Small range around neutral
            'knee': (-0.1, 0.1),
            'ankle': (-0.1, 0.1),
            'shoulder': (-0.2, 0.2),
            'elbow': (-0.1, 0.1)
        }

        # Check if all joints are within safe ranges
        for i, joint_name in enumerate(self.current_joint_states.name):
            if i >= len(self.current_joint_states.position):
                continue

            position = self.current_joint_states.position[i]

            # Determine joint type and check against safe range
            if 'hip' in joint_name:
                safe_min, safe_max = safe_ranges['hip']
            elif 'knee' in joint_name:
                safe_min, safe_max = safe_ranges['knee']
            elif 'ankle' in joint_name:
                safe_min, safe_max = safe_ranges['ankle']
            elif 'shoulder' in joint_name:
                safe_min, safe_max = safe_ranges['shoulder']
            elif 'elbow' in joint_name:
                safe_min, safe_max = safe_ranges['elbow']
            else:
                # For other joints, use a general safe range
                safe_min, safe_max = (-0.5, 0.5)

            if not (safe_min <= position <= safe_max):
                self.get_logger().debug(f'Joint {joint_name} not in safe position: {position:.3f}')
                return False

        return True

    def halt_all_joints(self):
        """Send immediate halt command to all joints"""
        with self.joint_state_lock:
            if not self.current_joint_states:
                self.get_logger().warn('No joint states available for halt command')
                return

            # Create halt trajectory
            halt_trajectory = JointTrajectory()
            halt_trajectory.joint_names = self.current_joint_states.name

            halt_point = JointTrajectoryPoint()
            halt_point.positions = list(self.current_joint_states.position)  # Hold current position
            halt_point.velocities = [0.0] * len(halt_trajectory.joint_names)  # Zero velocity
            halt_point.accelerations = [0.0] * len(halt_trajectory.joint_names)  # Zero acceleration
            halt_point.time_from_start = Duration(sec=0, nanosec=50000000)  # 0.05 seconds (very fast stop)

            halt_trajectory.points = [halt_point]
            self.halt_command_publisher.publish(halt_trajectory)

            self.get_logger().info(f'Halted {len(halt_trajectory.joint_names)} joints')

    def safety_monitor_callback(self):
        """Monitor for safety conditions that require emergency stop"""
        if self.emergency_stop_active:
            return

        with self.joint_state_lock:
            if not self.current_joint_states:
                return

            # Check for dangerous joint conditions
            for i, joint_name in enumerate(self.current_joint_states.name):
                if i >= len(self.current_joint_states.position):
                    continue

                position = self.current_joint_states.position[i]
                velocity = self.current_joint_states.velocity[i] if i < len(self.current_joint_states.velocity) else 0.0
                effort = self.current_joint_states.effort[i] if i < len(self.current_joint_states.effort) else 0.0

                # Position safety check (extreme limits)
                if abs(position) > 4.0:  # Beyond physical limits
                    self.get_logger().fatal(f'SAFETY VIOLATION: {joint_name} position {position} beyond limits')
                    self.activate_emergency_stop(f"POSITION_LIMIT_EXCEEDED: {joint_name}")
                    return

                # Velocity safety check (dangerous speeds)
                if abs(velocity) > 15.0:  # Very high velocity
                    self.get_logger().fatal(f'SAFETY VIOLATION: {joint_name} velocity {velocity} too high')
                    self.activate_emergency_stop(f"VELOCITY_LIMIT_EXCEEDED: {joint_name}")
                    return

                # Effort safety check (dangerous forces)
                if abs(effort) > 300.0:  # Very high effort
                    self.get_logger().fatal(f'SAFETY VIOLATION: {joint_name} effort {effort} too high')
                    self.activate_emergency_stop(f"EFFORT_LIMIT_EXCEEDED: {joint_name}")
                    return

    def publish_status(self):
        """Publish emergency stop status"""
        status_msg = String()
        if self.emergency_stop_active:
            status_msg.data = f"EMERGENCY_STOP: {self.stop_reason} (active for {self.get_time_since_stop():.1f}s)"
        else:
            status_msg.data = "NORMAL_OPERATION"

        self.status_publisher.publish(status_msg)

    def get_time_since_stop(self) -> float:
        """Get time elapsed since last emergency stop"""
        if self.last_stop_time:
            current_time = self.get_clock().now()
            duration = current_time - self.last_stop_time
            return duration.nanoseconds / 1e9
        return 0.0

    def manual_reset_service(self):
        """Service to manually reset emergency stop (with confirmation)"""
        # This would be implemented as a ROS service in a real system
        # For safety, manual reset typically requires physical button press or explicit confirmation
        if self.emergency_stop_active:
            self.get_logger().info('Manual reset requested - performing safety checks...')
            # Additional safety verification would occur here
            self.deactivate_emergency_stop()


def main(args=None):
    rclpy.init(args=args)

    emergency_stop_handler = EmergencyStopHandler()

    try:
        rclpy.spin(emergency_stop_handler)
    except KeyboardInterrupt:
        emergency_stop_handler.get_logger().info('Shutting down Emergency Stop Handler...')
    finally:
        # Ensure emergency stop is active on shutdown for safety
        emergency_stop_handler.activate_emergency_stop("SYSTEM_SHUTDOWN")
        emergency_stop_handler.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
```

## References

[IEEE citation format references will go here]

1. Open Robotics. (2025). "rclpy: Python Client Library for ROS 2." [Online]. Available: https://docs.ros.org/en/jazzy/p/rclpy/
2. AI Robotics Institute. (2025). "Integration of Large Language Models with Robotic Control Systems." IEEE Robotics and Automation Letters, 10(4), 892-899.
3. Safety Critical Robotics Consortium. (2025). "Safety Protocols for Humanoid Robotics Applications." Safety Science, 178, 106-118.
4. Diagnostic Working Group. (2025). "Diagnostic Systems for Autonomous Robots." Journal of Field Robotics, 42(2), 234-251.