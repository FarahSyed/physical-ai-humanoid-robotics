# Joint Trajectory Controller Example for Humanoid Robotics

This example demonstrates a Python-based joint trajectory controller specifically designed for humanoid robot applications with safety considerations.

## Humanoid Joint Trajectory Controller

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

## Configuration File

```yaml
# config/humanoid_joint_controller.yaml
/**:
  ros__parameters:
    # Joint limits
    joint_limits:
      position_min: -3.14
      position_max: 3.14
      velocity_max: 5.0
      effort_max: 100.0

    # Safety parameters
    safety:
      position_threshold: 3.14
      velocity_threshold: 5.0
      effort_threshold: 100.0
      emergency_stop_timeout: 0.1

    # Control parameters
    control:
      trajectory_execution_rate: 100  # Hz
      feedback_timeout: 5.0  # seconds
      goal_tolerance: 0.01  # radians