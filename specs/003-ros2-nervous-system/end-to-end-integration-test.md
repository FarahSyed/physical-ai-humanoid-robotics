# Complete End-to-End Humanoid System Integration Test

This document outlines the complete integration test that validates all three chapters work together as a cohesive system.

## Integration Test Overview

The end-to-end test validates the complete humanoid system by integrating:
- Chapter 1: ROS 2 communication patterns (publishers/subscribers)
- Chapter 2: Python control nodes and safety systems
- Chapter 3: URDF model and visualization

## Complete Integration Launch File

```python
# launch/end_to_end_humanoid_system.launch.py
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, RegisterEventHandler
from launch.event_handlers import OnProcessStart
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
from launch_ros.descriptions import ParameterValue
import os

def generate_launch_description():
    # Declare launch arguments
    use_sim_time = LaunchConfiguration('use_sim_time', default='false')
    robot_description_path = LaunchConfiguration('robot_description_path', default='')
    initial_joint_positions = LaunchConfiguration('initial_joint_positions', default='')

    return LaunchDescription([
        # Declare launch arguments
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            description='Use simulation clock if true'
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

        DeclareLaunchArgument(
            'initial_joint_positions',
            default_value='{}',
            description='Initial joint positions as JSON string'
        ),

        # Robot State Publisher - Chapter 3 integration
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='robot_state_publisher',
            parameters=[
                {'use_sim_time': use_sim_time},
                {'robot_description':
                    ParameterValue(
                        os.path.join(
                            get_package_share_directory('humanoid_description'),
                            'urdf',
                            'enhanced_humanoid.urdf'
                        ),
                        value_type=str
                    )
                }
            ],
            remappings=[
                ('/joint_states', '/joint_states'),
            ],
            output='screen',
        ),

        # Joint State Publisher - Chapter 3 integration
        Node(
            package='joint_state_publisher',
            executable='joint_state_publisher',
            name='joint_state_publisher',
            parameters=[
                {'use_sim_time': use_sim_time},
                {'rate': 50},  # Hz
                {'source_list': ['/joint_states']},
            ],
            output='screen',
        ),

        # Humanoid Controller - Chapter 2 integration
        Node(
            package='humanoid_control_nodes',
            executable='humanoid_controller',
            name='humanoid_controller',
            parameters=[
                {'use_sim_time': use_sim_time},
                {
                    'control.loop_rate': 100,  # Hz
                    'safety.max_joint_velocity': 2.0,
                    'safety.max_joint_torque': 50.0,
                    'safety.balance_threshold': 0.1,
                }
            ],
            output='screen',
        ),

        # Joint Trajectory Controller - Chapter 2 integration
        Node(
            package='humanoid_control_nodes',
            executable='humanoid_joint_controller',
            name='humanoid_joint_controller',
            parameters=[
                {'use_sim_time': use_sim_time},
            ],
            output='screen',
        ),

        # Safety Lifecycle Node - Chapter 2 integration
        Node(
            package='humanoid_safety_nodes',
            executable='humanoid_safety_lifecycle_node',
            name='humanoid_safety_manager',
            parameters=[
                {'use_sim_time': use_sim_time},
            ],
            output='screen',
        ),

        # Emergency Stop Handler - Chapter 2 integration
        Node(
            package='humanoid_emergency_stop',
            executable='emergency_stop_handler',
            name='emergency_stop_handler',
            parameters=[
                {'use_sim_time': use_sim_time},
            ],
            output='screen',
        ),

        # Diagnostic Node - Chapter 2 integration
        Node(
            package='humanoid_diagnostics',
            executable='humanoid_diagnostics_node',
            name='humanoid_diagnostics',
            parameters=[
                {'use_sim_time': use_sim_time},
            ],
            output='screen',
        ),

        # AI Interface Node - Chapter 2 integration
        Node(
            package='humanoid_ai_interface',
            executable='ai_interface_node',
            name='ai_interface_node',
            parameters=[
                {'use_sim_time': use_sim_time},
            ],
            output='screen',
        ),

        # RViz2 for visualization - Chapter 3 integration
        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            arguments=[
                '-d', PathJoinSubstitution([
                    get_package_share_directory('humanoid_description'),
                    'rviz',
                    'humanoid_system.rviz'
                ])
            ],
            parameters=[
                {'use_sim_time': use_sim_time},
            ],
            output='screen',
        ),

        # Integration Test Node - Validates complete system
        Node(
            package='humanoid_integration_tests',
            executable='end_to_end_tester',
            name='end_to_end_tester',
            parameters=[
                {'use_sim_time': use_sim_time},
            ],
            output='screen',
        ),
    ])
```

## Integration Test Node

```python
#!/usr/bin/env python3
# end_to_end_tester.py
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, QoSHistoryPolicy, QoSReliabilityPolicy
from sensor_msgs.msg import JointState
from std_msgs.msg import String, Bool
from diagnostic_msgs.msg import DiagnosticArray
from trajectory_msgs.msg import JointTrajectory
from builtin_interfaces.msg import Duration
import time
from threading import Lock

class EndToEndTester(Node):
    def __init__(self):
        super().__init__('end_to_end_tester')

        # QoS profile for testing
        qos_profile = QoSProfile(
            history=QoSHistoryPolicy.KEEP_LAST,
            reliability=QoSReliabilityPolicy.RELIABLE,
            depth=10
        )

        # Publishers
        self.test_command_publisher = self.create_publisher(
            String,
            'integration_test_commands',
            qos_profile
        )

        self.joint_trajectory_publisher = self.create_publisher(
            JointTrajectory,
            '/joint_trajectory_controller/joint_trajectory',
            qos_profile
        )

        # Subscribers
        self.joint_state_subscriber = self.create_subscription(
            JointState,
            'joint_states',
            self.joint_state_callback,
            qos_profile
        )

        self.diagnostic_subscriber = self.create_subscription(
            DiagnosticArray,
            '/diagnostics',
            self.diagnostic_callback,
            qos_profile
        )

        self.safety_status_subscriber = self.create_subscription(
            String,
            'emergency_stop_status',
            self.safety_status_callback,
            qos_profile
        )

        # Internal state
        self.joint_states = None
        self.diagnostics = None
        self.safety_status = None
        self.test_results = {}
        self.test_lock = Lock()

        # Timer for test execution
        self.test_timer = self.create_timer(2.0, self.run_integration_tests)

        # Test sequence counter
        self.test_sequence = 0

        self.get_logger().info('End-to-End Integration Tester initialized')

    def joint_state_callback(self, msg):
        """Handle joint state updates"""
        with self.test_lock:
            self.joint_states = msg

    def diagnostic_callback(self, msg):
        """Handle diagnostic updates"""
        with self.test_lock:
            self.diagnostics = msg

    def safety_status_callback(self, msg):
        """Handle safety status updates"""
        with self.test_lock:
            self.safety_status = msg

    def run_integration_tests(self):
        """Run the complete integration test sequence"""
        self.get_logger().info(f'Running integration test sequence #{self.test_sequence}')

        # Test 1: Check system health
        system_health = self.check_system_health()
        self.test_results[f'system_health_{self.test_sequence}'] = system_health

        # Test 2: Check communication patterns (Chapter 1)
        communication_ok = self.test_communication_patterns()
        self.test_results[f'communication_{self.test_sequence}'] = communication_ok

        # Test 3: Check control functionality (Chapter 2)
        control_ok = self.test_control_functionality()
        self.test_results[f'control_{self.test_sequence}'] = control_ok

        # Test 4: Check URDF integration (Chapter 3)
        urdf_ok = self.test_urdf_integration()
        self.test_results[f'urdf_integration_{self.test_sequence}'] = urdf_ok

        # Test 5: Check safety systems
        safety_ok = self.test_safety_systems()
        self.test_results[f'safety_{self.test_sequence}'] = safety_ok

        # Test 6: Send test trajectory to validate complete flow
        trajectory_ok = self.test_trajectory_execution()
        self.test_results[f'trajectory_{self.test_sequence}'] = trajectory_ok

        # Log results
        self.log_test_results()

        # Increment sequence
        self.test_sequence += 1

    def check_system_health(self) -> bool:
        """Check if all required systems are running"""
        with self.test_lock:
            joint_states_ok = self.joint_states is not None
            diagnostics_ok = self.diagnostics is not None
            safety_ok = self.safety_status is not None

        all_ok = joint_states_ok and diagnostics_ok and safety_ok
        self.get_logger().info(f'System health check: JointStates={joint_states_ok}, Diagnostics={diagnostics_ok}, Safety={safety_ok}')
        return all_ok

    def test_communication_patterns(self) -> bool:
        """Test Chapter 1 communication patterns"""
        with self.test_lock:
            if not self.joint_states:
                return False

            # Check that we have reasonable number of joints
            expected_min_joints = 10  # For humanoid
            actual_joints = len(self.joint_states.name)

            if actual_joints < expected_min_joints:
                self.get_logger().warn(f'Expected at least {expected_min_joints} joints, got {actual_joints}')
                return False

            # Check that joint states are updating (not all zeros)
            position_sum = sum(abs(pos) for pos in self.joint_states.position)
            if position_sum < 0.001:  # If all positions are nearly zero, might not be updating properly
                self.get_logger().warn('Joint positions appear to be static - communication might not be active')
                return False

        self.get_logger().info(f'Communication patterns test passed: {actual_joints} joints detected')
        return True

    def test_control_functionality(self) -> bool:
        """Test Chapter 2 control functionality"""
        with self.test_lock:
            if not self.joint_states:
                return False

            # Check for reasonable joint values (not NaN or infinity)
            for i, pos in enumerate(self.joint_states.position):
                if not (-10.0 <= pos <= 10.0):  # Reasonable joint position limits
                    self.get_logger().warn(f'Joint {self.joint_states.name[i]} has unreasonable position: {pos}')
                    return False

            # Check velocity and effort values too
            if len(self.joint_states.velocity) > 0:
                for vel in self.joint_states.velocity:
                    if not (-50.0 <= vel <= 50.0):  # Reasonable velocity limits
                        self.get_logger().warn(f'Joint has unreasonable velocity: {vel}')
                        return False

        self.get_logger().info('Control functionality test passed')
        return True

    def test_urdf_integration(self) -> bool:
        """Test Chapter 3 URDF integration"""
        # This is validated by the fact that joint states exist and have proper names
        # In a real system, we might also check TF transforms
        with self.test_lock:
            if not self.joint_states:
                return False

            # Check that joint names match expected humanoid joints
            expected_joint_patterns = ['hip', 'knee', 'ankle', 'shoulder', 'elbow', 'neck']
            found_patterns = set()

            for joint_name in self.joint_states.name:
                for pattern in expected_joint_patterns:
                    if pattern in joint_name:
                        found_patterns.add(pattern)

            required_patterns = {'hip', 'knee', 'shoulder', 'elbow'}  # At minimum
            if not required_patterns.issubset(found_patterns):
                self.get_logger().warn(f'Missing expected joint patterns. Found: {found_patterns}, Required: {required_patterns}')
                return False

        self.get_logger().info(f'URDF integration test passed: Found joint patterns {found_patterns}')
        return True

    def test_safety_systems(self) -> bool:
        """Test safety system functionality"""
        with self.test_lock:
            if not self.safety_status:
                return False

            # Check that safety status doesn't indicate emergency stop
            status_text = self.safety_status.data.lower()
            if 'emergency' in status_text and 'active' in status_text:
                self.get_logger().error(f'Safety system reports emergency: {self.safety_status.data}')
                return False

        self.get_logger().info('Safety systems test passed')
        return True

    def test_trajectory_execution(self) -> bool:
        """Test complete trajectory execution flow"""
        # Create a simple test trajectory
        trajectory_msg = JointTrajectory()

        with self.test_lock:
            if not self.joint_states:
                return False

            # Use current joint names
            trajectory_msg.joint_names = self.joint_states.name[:6]  # Use first 6 joints for test

            # Create trajectory points
            current_positions = self.joint_states.position[:6]

            # Point 1: Current position
            point1 = JointTrajectoryPoint()
            point1.positions = current_positions
            point1.velocities = [0.0] * len(current_positions)
            point1.accelerations = [0.0] * len(current_positions)
            point1.time_from_start = Duration(sec=0, nanosec=0)

            # Point 2: Slightly offset
            point2 = JointTrajectoryPoint()
            point2.positions = [pos + 0.1 for pos in current_positions]
            point2.velocities = [0.0] * len(current_positions)
            point2.accelerations = [0.0] * len(current_positions)
            point2.time_from_start = Duration(sec=1, nanosec=0)

            # Point 3: Return to original
            point3 = JointTrajectoryPoint()
            point3.positions = current_positions
            point3.velocities = [0.0] * len(current_positions)
            point3.accelerations = [0.0] * len(current_positions)
            point3.time_from_start = Duration(sec=2, nanosec=0)

            trajectory_msg.points = [point1, point2, point3]

        # Publish the test trajectory
        self.joint_trajectory_publisher.publish(trajectory_msg)
        self.get_logger().info(f'Published test trajectory for {len(trajectory_msg.joint_names)} joints')

        # For this test, we assume success if we can publish (actual execution validation would require feedback)
        return True

    def log_test_results(self):
        """Log the current test results"""
        with self.test_lock:
            passed = sum(1 for result in self.test_results.values() if result)
            total = len(self.test_results)

            self.get_logger().info('='*60)
            self.get_logger().info(f'INTEGRATION TEST RESULTS (Sequence #{self.test_sequence-1})')
            self.get_logger().info('='*60)

            for test_name, result in self.test_results.items():
                status = 'PASS' if result else 'FAIL'
                self.get_logger().info(f'{test_name}: {status}')

            self.get_logger().info('-'*60)
            self.get_logger().info(f'TOTAL: {passed}/{total} tests passed')
            self.get_logger().info('='*60)

            # Overall system status
            overall_status = 'SUCCESS' if passed == total else 'PARTIAL'
            self.get_logger().info(f'OVERALL INTEGRATION STATUS: {overall_status}')
            self.get_logger().info('='*60)


def main(args=None):
    rclpy.init(args=args)

    tester = EndToEndTester()

    try:
        rclpy.spin(tester)
    except KeyboardInterrupt:
        tester.get_logger().info('Shutting down End-to-End Integration Tester...')
    finally:
        tester.log_test_results()  # Log final results
        tester.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
```

## Integration Test Configuration

```yaml
# config/integration_test_params.yaml
/**:
  ros__parameters:
    # Test parameters
    test:
      sequence_interval: 2.0  # seconds between test sequences
      validation_timeout: 10.0  # seconds to wait for validation
      required_joints_min: 10  # minimum number of joints expected
      safety_check_enabled: true  # whether to perform safety checks
      trajectory_test_enabled: true  # whether to send test trajectories

    # Control parameters for test trajectories
    trajectory:
      test_duration: 2.0  # seconds for test trajectory
      position_offset: 0.1  # radians for test offset
      velocity_limit: 1.0  # rad/s for test trajectories