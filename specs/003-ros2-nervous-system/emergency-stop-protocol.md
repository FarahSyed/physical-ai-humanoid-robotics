# Emergency Stop Safety Protocol for Humanoid Robotics

This document outlines the emergency stop mechanisms and safety protocols for humanoid robotics applications.

## Emergency Stop System Architecture

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

## Safety State Machine

```python
#!/usr/bin/env python3
# safety_state_machine.py
from enum import Enum
import time

class SafetyState(Enum):
    NORMAL_OPERATION = "NORMAL_OPERATION"
    WARNING = "WARNING"
    PRE_EMERGENCY = "PRE_EMERGENCY"
    EMERGENCY_STOP = "EMERGENCY_STOP"
    SYSTEM_RESET = "SYSTEM_RESET"

class SafetyStateMachine:
    def __init__(self):
        self.current_state = SafetyState.NORMAL_OPERATION
        self.state_entry_time = time.time()
        self.violation_count = 0
        self.last_violation_time = None
        self.emergency_reason = "SYSTEM_INITIALIZED"

    def update_state(self, safety_conditions):
        """Update safety state based on current conditions"""
        current_time = time.time()

        if safety_conditions.get('critical_violation', False):
            # Immediate transition to emergency stop for critical violations
            if self.current_state != SafetyState.EMERGENCY_STOP:
                self.current_state = SafetyState.EMERGENCY_STOP
                self.state_entry_time = current_time
                self.emergency_reason = safety_conditions.get('violation_type', 'UNKNOWN_CRITICAL')
                self.violation_count += 1
                self.last_violation_time = current_time
        elif safety_conditions.get('warning_condition', False):
            # Warning state for non-critical issues
            if self.current_state == SafetyState.NORMAL_OPERATION:
                self.current_state = SafetyState.WARNING
                self.state_entry_time = current_time
        elif safety_conditions.get('pre_emergency_condition', False):
            # Pre-emergency for conditions approaching critical
            if self.current_state in [SafetyState.NORMAL_OPERATION, SafetyState.WARNING]:
                self.current_state = SafetyState.PRE_EMERGENCY
                self.state_entry_time = current_time
        elif self.current_state == SafetyState.EMERGENCY_STOP:
            # Remain in emergency stop until manual reset
            pass
        else:
            # Return to normal operation if conditions are safe
            self.current_state = SafetyState.NORMAL_OPERATION
            self.state_entry_time = current_time

    def can_reset_emergency(self):
        """Check if emergency stop can be reset"""
        if self.current_state != SafetyState.EMERGENCY_STOP:
            return True

        # In a real system, this would require additional safety checks
        # For example: joints in safe positions, no ongoing violations, etc.
        time_in_state = time.time() - self.state_entry_time
        return time_in_state > 5.0  # Wait 5 seconds minimum

    def get_state_info(self):
        """Get current state information"""
        return {
            'state': self.current_state.value,
            'time_in_state': time.time() - self.state_entry_time,
            'violation_count': self.violation_count,
            'emergency_reason': self.emergency_reason,
            'can_reset': self.can_reset_emergency()
        }
```

## Hardware Emergency Stop Interface

```python
#!/usr/bin/env python3
# hardware_emergency_interface.py
import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool
from rclpy.qos import QoSProfile

class HardwareEmergencyInterface(Node):
    def __init__(self):
        super().__init__('hardware_emergency_interface')

        # Publishers
        self.emergency_publisher = self.create_publisher(
            Bool,
            'emergency_stop_request',
            QoSProfile(depth=10)
        )

        # Simulate hardware button monitoring (in real system, this would interface with GPIO)
        self.hardware_button_state = False
        self.last_button_state = False

        # Timer to simulate hardware monitoring (100Hz)
        self.hardware_timer = self.create_timer(0.01, self.hardware_monitor_callback)

        self.get_logger().info('Hardware Emergency Interface initialized')

    def hardware_monitor_callback(self):
        """Monitor hardware emergency stop button"""
        # In a real system, this would read from GPIO or hardware interface
        # For simulation, we'll use a method to simulate button presses

        # This is where hardware-specific code would interface with physical emergency stop buttons
        # The interface would detect when the hardware emergency stop is activated
        # and publish the appropriate message to trigger the software emergency stop system
        pass

    def simulate_hardware_stop(self):
        """Simulate hardware emergency stop activation (for testing)"""
        stop_msg = Bool()
        stop_msg.data = True
        self.emergency_publisher.publish(stop_msg)
        self.get_logger().info('Hardware emergency stop simulated')


def main(args=None):
    rclpy.init(args=args)

    hardware_interface = HardwareEmergencyInterface()

    try:
        rclpy.spin(hardware_interface)
    except KeyboardInterrupt:
        hardware_interface.get_logger().info('Shutting down Hardware Emergency Interface...')
    finally:
        hardware_interface.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
```

## Package Configuration

```xml
<?xml version="1.0"?>
<?xml-model href="http://download.ros.org/schema/package_format3.xsd" schematypens="http://www.w3.org/2001/XMLSchema"?>
<package format="3">
  <name>humanoid_emergency_stop</name>
  <version>0.0.1</version>
  <description>Emergency stop and safety protocols for humanoid robotics</description>
  <maintainer email="maintainer@todo.todo">maintainer</maintainer>
  <license>Apache-2.0</license>

  <depend>rclpy</depend>
  <depend>std_msgs</depend>
  <depend>sensor_msgs</depend>
  <depend>trajectory_msgs</depend>
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

## Safety Protocol Documentation

### Emergency Stop Categories

1. **Category 0 (Immediate Stop)**: Highest priority - all power removed immediately
2. **Category 1 (Controlled Stop)**: Safe stop with controlled deceleration
3. **Category 2 (Normal Stop)**: Standard stop with normal deceleration

### Safety Requirements

1. **Response Time**: Emergency stop must activate within 50ms of trigger
2. **Redundancy**: Multiple independent emergency stop paths
3. **Fail-Safe**: System defaults to safe state if communication fails
4. **Manual Reset**: Critical emergencies require manual confirmation to reset
5. **Status Monitoring**: Continuous monitoring of safety system health

This emergency stop protocol ensures that humanoid robots can be safely stopped in emergency situations while maintaining the safety of both the robot and surrounding environment.