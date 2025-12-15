# Lifecycle Node Example for Humanoid Safety System

This example demonstrates a lifecycle node designed for humanoid safety system management with proper state transitions and safety protocols.

## Humanoid Safety Lifecycle Node

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

## Launch File for Lifecycle Node

```python
# launch/humanoid_safety_lifecycle.launch.py
from launch import LaunchDescription
from launch_ros.actions import LifecycleNode
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration

def generate_launch_description():
    use_sim_time = LaunchConfiguration('use_sim_time')

    return LaunchDescription([
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            description='Use simulation clock if true'
        ),

        LifecycleNode(
            package='humanoid_safety_nodes',
            executable='humanoid_safety_lifecycle_node',
            name='humanoid_safety_manager',
            namespace='',
            parameters=[{'use_sim_time': use_sim_time}],
            remappings=[
                ('joint_states', '/joint_states'),
                ('safety_status', '/safety_status'),
                ('emergency_stop', '/emergency_stop'),
                ('safety_violations', '/safety_violations'),
            ],
            output='screen',
        ),
    ])
```

## Package Configuration

```xml
<?xml version="1.0"?>
<?xml-model href="http://download.ros.org/schema/package_format3.xsd" schematypens="http://www.w3.org/2001/XMLSchema"?>
<package format="3">
  <name>humanoid_safety_nodes</name>
  <version>0.0.1</version>
  <description>Life cycle safety nodes for humanoid robotics</description>
  <maintainer email="maintainer@todo.todo">maintainer</maintainer>
  <license>Apache-2.0</license>

  <depend>rclpy</depend>
  <depend>std_msgs</depend>
  <depend>sensor_msgs</depend>
  <depend>builtin_interfaces</depend>

  <test_depend>ament_copyright</test_depend>
  <test_depend>ament_flake8</test_depend>
  <test_depend>ament_pep257</test_depend>
  <test_depend>python3-pytest</test_depend>

  <export>
    <build_type>ament_python</build_type>
  </export>
</package>
```

## Expected Behavior

This lifecycle node demonstrates:

1. **Proper State Transitions**: Follows the ROS 2 lifecycle state machine (unconfigured → inactive → active → finalized)
2. **Safety Monitoring**: Continuously monitors joint states for safety violations
3. **Emergency Procedures**: Automatically activates emergency stop when safety limits are exceeded
4. **Resource Management**: Properly manages lifecycle entities (publishers, subscribers, timers)
5. **Error Handling**: Handles errors appropriately with safety-first approach

The lifecycle approach ensures that the safety system can be properly configured, activated, and deactivated while maintaining safe states throughout all transitions.