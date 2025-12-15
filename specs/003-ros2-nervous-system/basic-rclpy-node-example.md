# Basic rclpy Node Example for Humanoid Control

This example demonstrates a simple Python node with publisher and subscriber for humanoid applications.

## Humanoid Control Node

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

## Package Configuration

```xml
<?xml version="1.0"?>
<?xml-model href="http://download.ros.org/schema/package_format3.xsd" schematypens="http://www.w3.org/2001/XMLSchema"?>
<package format="3">
  <name>humanoid_control_nodes</name>
  <version>0.0.1</version>
  <description>Basic ROS 2 control nodes for humanoid robotics</description>
  <maintainer email="maintainer@todo.todo">maintainer</maintainer>
  <license>Apache-2.0</license>

  <depend>rclpy</depend>
  <depend>std_msgs</depend>
  <depend>sensor_msgs</depend>
  <depend>control_msgs</depend>
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

## Expected Behavior

This node demonstrates key rclpy concepts:
- Proper node initialization and lifecycle management
- QoS profile configuration for safety-critical applications
- Publisher and subscriber setup with callbacks
- Timer-based control loop for real-time operation
- Emergency stop functionality for safety
- Proper resource cleanup

The node maintains a 100Hz control loop, publishes trajectory commands, subscribes to joint states, and includes safety mechanisms appropriate for humanoid robotics applications.