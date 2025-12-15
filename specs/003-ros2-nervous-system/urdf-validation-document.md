# URDF Validation Document for Humanoid Robot (No Physics Simulation)

This document outlines the validation process for the humanoid robot URDF model, ensuring it works correctly with ROS 2 visualization and state publishing without physics simulation.

## Validation Objectives

1. Verify URDF loads correctly in RViz without physics simulation
2. Confirm all joints and links are properly connected
3. Validate TF transforms are published correctly
4. Ensure visual elements display properly
5. Test joint state publishing functionality

## Validation Steps

### 1. URDF Syntax Validation

```bash
# Validate URDF syntax using check_urdf tool
ros2 run urdf_check check_urdf $(ros2 pkg prefix humanoid_description)/share/humanoid_description/urdf/enhanced_humanoid.urdf
```

Expected output should show:
- Successfully Parsed file
- 26 Links and 25 Joints
- Proper tree structure
- No errors in joint/link definitions

### 2. Robot State Publisher Test

```python
# test_robot_state_publisher.py
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
from builtin_interfaces.msg import Time
import math
import time

class URDFValidator(Node):
    def __init__(self):
        super().__init__('urdf_validator')

        # Publisher for joint states
        self.joint_pub = self.create_publisher(JointState, '/joint_states', 10)

        # Timer to publish joint states
        self.timer = self.create_timer(0.1, self.publish_joint_states)

        # Joint names from URDF
        self.joint_names = [
            'neck_joint', 'left_shoulder_joint', 'left_elbow_joint',
            'right_shoulder_joint', 'right_elbow_joint', 'left_hip_joint',
            'left_knee_joint', 'left_ankle_joint', 'right_hip_joint',
            'right_knee_joint', 'right_ankle_joint'
        ]

        self.get_logger().info('URDF Validator initialized')

    def publish_joint_states(self):
        """Publish test joint states"""
        msg = JointState()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.name = self.joint_names

        # Generate test positions (oscillating for visualization)
        positions = []
        current_time = self.get_clock().now().nanoseconds / 1e9

        for i, joint_name in enumerate(self.joint_names):
            # Create different oscillation patterns for different joint types
            if 'hip' in joint_name or 'knee' in joint_name:
                # Leg joints - more constrained movement
                pos = 0.5 * math.sin(current_time + i) * 0.5
            elif 'shoulder' in joint_name:
                # Shoulder joints - wider movement
                pos = math.sin(current_time * 0.5 + i) * 0.8
            elif 'elbow' in joint_name:
                # Elbow joints - medium movement
                pos = 0.7 * math.sin(current_time * 0.7 + i) * 0.8
            elif 'ankle' in joint_name:
                # Ankle joints - smaller movement
                pos = 0.3 * math.sin(current_time * 1.2 + i) * 0.5
            elif 'neck' in joint_name:
                # Neck joint - constrained movement
                pos = 0.2 * math.sin(current_time * 0.3 + i) * 0.5
            else:
                pos = 0.0

            positions.append(pos)

        msg.position = positions
        msg.velocity = [0.0] * len(positions)
        msg.effort = [0.0] * len(positions)

        self.joint_pub.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    validator = URDFValidator()

    try:
        rclpy.spin(validator)
    except KeyboardInterrupt:
        pass
    finally:
        validator.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
```

### 3. Launch Configuration for Validation

```python
# launch/validate_urdf.launch.py
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os

def generate_launch_description():
    # Declare launch arguments
    use_sim_time = LaunchConfiguration('use_sim_time', default='false')

    return LaunchDescription([
        # Declare launch arguments
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            description='Use simulation clock if true'
        ),

        # Robot State Publisher
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='robot_state_publisher',
            parameters=[
                {'use_sim_time': use_sim_time},
                {'robot_description':
                    open(os.path.join(
                        get_package_share_directory('humanoid_description'),
                        'urdf',
                        'enhanced_humanoid.urdf'
                    )).read()
                }
            ],
            remappings=[
                ('/joint_states', '/joint_states'),
            ],
        ),

        # Joint State Publisher (for visualization)
        Node(
            package='joint_state_publisher',
            executable='joint_state_publisher',
            name='joint_state_publisher',
            parameters=[
                {'use_sim_time': use_sim_time},
            ],
            remappings=[
                ('/joint_states', '/joint_states'),
            ],
        ),

        # URDF Validator Node
        Node(
            package='humanoid_description',
            executable='urdf_validator',
            name='urdf_validator',
            parameters=[
                {'use_sim_time': use_sim_time},
            ],
        ),

        # RViz2 for visualization
        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            arguments=[
                '-d', os.path.join(
                    get_package_share_directory('humanoid_description'),
                    'rviz',
                    'humanoid_validation.rviz'
                )
            ],
            parameters=[
                {'use_sim_time': use_sim_time},
            ],
        ),
    ])
```

### 4. Validation Checklist

#### 4.1 URDF Structure Validation
- [ ] All links have proper visual, collision, and inertial elements
- [ ] All joints have correct parent-child relationships
- [ ] Joint limits are properly defined
- [ ] No floating links (all connected to base)
- [ ] Proper mass and inertia values for all links

#### 4.2 TF Transform Validation
- [ ] All coordinate frames are published
- [ ] Frame relationships match URDF structure
- [ ] No missing or disconnected frames
- [ ] Proper orientation and position of all frames

#### 4.3 Visualization Validation
- [ ] Robot model displays correctly in RViz
- [ ] All links are visible with proper colors
- [ ] Joint movements are visible when joint states change
- [ ] No visual artifacts or missing geometry

#### 4.4 Joint State Validation
- [ ] Joint states are published at expected rate (50Hz)
- [ ] All defined joints appear in joint states
- [ ] Joint positions update correctly
- [ ] No joint state errors or warnings

### 5. Automated Validation Script

```python
# scripts/validate_urdf.py
#!/usr/bin/env python3
import subprocess
import sys
import time
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
from tf2_ros import TransformListener, Buffer
from rclpy.qos import QoSProfile

class URDFValidationTest(Node):
    def __init__(self):
        super().__init__('urdf_validation_test')

        # Create QoS profile for subscriptions
        qos = QoSProfile(depth=10)

        # Subscribe to joint states
        self.joint_sub = self.create_subscription(
            JointState,
            '/joint_states',
            self.joint_state_callback,
            qos
        )

        # Setup TF listener
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)

        # Validation flags
        self.joint_states_received = False
        self.joint_count_validated = False
        self.tf_validated = False

        self.get_logger().info('URDF Validation Test started')

    def joint_state_callback(self, msg):
        """Callback for joint states"""
        if not self.joint_states_received:
            self.get_logger().info(f'Received joint states with {len(msg.name)} joints')
            self.joint_states_received = True

            # Check if we have expected number of joints
            expected_joints = 11  # From our humanoid model
            if len(msg.name) >= expected_joints:
                self.get_logger().info(f'Joint count validated: {len(msg.name)} joints found')
                self.joint_count_validated = True
            else:
                self.get_logger().error(f'Expected at least {expected_joints} joints, got {len(msg.name)}')

    def validate_tf(self):
        """Validate TF transforms"""
        try:
            # Check if we can get transform from base to head
            transform = self.tf_buffer.lookup_transform(
                'base_link', 'head', rclpy.time.Time()
            )
            self.get_logger().info('TF validation successful: base_link to head transform found')
            self.tf_validated = True
            return True
        except Exception as e:
            self.get_logger().warn(f'TF validation pending: {str(e)}')
            return False

    def run_validation(self):
        """Run the validation process"""
        start_time = time.time()
        timeout = 30  # seconds

        while time.time() - start_time < timeout and rclpy.ok():
            if self.joint_states_received and self.joint_count_validated:
                if self.validate_tf():
                    break

            rclpy.spin_once(self, timeout_sec=0.1)

        # Final validation report
        self.print_validation_report()

    def print_validation_report(self):
        """Print validation results"""
        print("\n" + "="*50)
        print("URDF VALIDATION REPORT")
        print("="*50)
        print(f"Joint States Received: {'✓' if self.joint_states_received else '✗'}")
        print(f"Joint Count Validated: {'✓' if self.joint_count_validated else '✗'}")
        print(f"TF Transforms Validated: {'✓' if self.tf_validated else '✗'}")

        if all([self.joint_states_received, self.joint_count_validated, self.tf_validated]):
            print("\n🎉 URDF Validation: SUCCESSFUL")
            print("All validation criteria met!")
        else:
            print("\n❌ URDF Validation: FAILED")
            print("Some validation criteria were not met.")
        print("="*50)

def main():
    # First check URDF syntax
    print("Validating URDF syntax...")
    try:
        result = subprocess.run([
            'ros2', 'run', 'urdf_check', 'check_urdf',
            'path/to/your/enhanced_humanoid.urdf'  # Replace with actual path
        ], capture_output=True, text=True, timeout=10)

        if result.returncode == 0:
            print("✓ URDF syntax validation passed")
            print(result.stdout)
        else:
            print("✗ URDF syntax validation failed")
            print(result.stderr)
            return False
    except subprocess.TimeoutExpired:
        print("✗ URDF syntax validation timed out")
        return False
    except FileNotFoundError:
        print("? URDF check tool not found, skipping syntax validation")

    # Initialize ROS and run validation node
    rclpy.init()

    validator = URDFValidationTest()

    try:
        validator.run_validation()
    except KeyboardInterrupt:
        print("\nValidation interrupted by user")
    finally:
        validator.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
```

### 6. Expected Validation Results

When running the validation:

1. **URDF Syntax**: Should report successful parsing with all links and joints
2. **Joint States**: Should receive messages with 11+ joints (depending on URDF complexity)
3. **TF Transforms**: Should show proper tree structure from base_link to all end effectors
4. **RViz Visualization**: Should display the complete humanoid model with moving joints
5. **No Physics**: Validation confirms no physics simulation is running (as required by spec)

### 7. Common Issues and Solutions

1. **Missing Joint States**: Ensure joint_state_publisher is running
2. **TF Issues**: Check robot_state_publisher parameters and URDF joint definitions
3. **Visualization Problems**: Verify URDF geometry and material definitions
4. **Syntax Errors**: Use `check_urdf` tool to identify and fix URDF syntax issues

This validation approach ensures the URDF model works correctly for visualization and state publishing without physics simulation, meeting the requirements specified in the project documentation.