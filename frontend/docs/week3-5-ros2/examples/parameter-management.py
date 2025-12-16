#!/usr/bin/env python3
# parameter-management.py
import rclpy
from rclpy.node import Node
from rcl_interfaces.msg import ParameterType, ParameterDescriptor
from std_msgs.msg import String


class ParameterManagementNode(Node):
    def __init__(self):
        super().__init__('parameter_management_node')

        # Declare parameters with descriptions and constraints
        self.declare_parameter(
            'robot_name',
            'humanoid_robot',
            ParameterDescriptor(
                description='Name of the robot',
                type=ParameterType.PARAMETER_STRING
            )
        )

        self.declare_parameter(
            'control_frequency',
            100,
            ParameterDescriptor(
                description='Control loop frequency in Hz',
                type=ParameterType.PARAMETER_INTEGER
            )
        )

        self.declare_parameter(
            'max_joint_velocity',
            2.0,
            ParameterDescriptor(
                description='Maximum joint velocity in rad/s',
                type=ParameterType.PARAMETER_DOUBLE
            )
        )

        self.declare_parameter(
            'enable_safety',
            True,
            ParameterDescriptor(
                description='Enable safety checks',
                type=ParameterType.PARAMETER_BOOL
            )
        )

        # Get parameter values
        self.robot_name = self.get_parameter('robot_name').value
        self.control_frequency = self.get_parameter('control_frequency').value
        self.max_joint_velocity = self.get_parameter('max_joint_velocity').value
        self.enable_safety = self.get_parameter('enable_safety').value

        # Create a publisher for status
        self.status_publisher = self.create_publisher(String, 'parameter_status', 10)

        # Timer for periodic parameter checking
        self.timer = self.create_timer(1.0, self.check_parameters)

        self.get_logger().info(f'Parameter management node initialized')
        self.get_logger().info(f'Robot name: {self.robot_name}')
        self.get_logger().info(f'Control frequency: {self.control_frequency} Hz')
        self.get_logger().info(f'Max joint velocity: {self.max_joint_velocity} rad/s')
        self.get_logger().info(f'Safety enabled: {self.enable_safety}')

    def check_parameters(self):
        """Periodically check parameters and publish status"""
        status_msg = String()
        status_msg.data = f'Robot: {self.robot_name}, Freq: {self.control_frequency}Hz, Safety: {self.enable_safety}'
        self.status_publisher.publish(status_msg)

        # Check if parameters have changed
        current_robot_name = self.get_parameter('robot_name').value
        current_control_freq = self.get_parameter('control_frequency').value
        current_max_vel = self.get_parameter('max_joint_velocity').value
        current_safety = self.get_parameter('enable_safety').value

        if current_robot_name != self.robot_name:
            self.get_logger().info(f'Robot name changed from {self.robot_name} to {current_robot_name}')
            self.robot_name = current_robot_name

        if current_control_freq != self.control_frequency:
            self.get_logger().info(f'Control frequency changed from {self.control_frequency} to {current_control_freq}')
            self.control_frequency = current_control_freq
            # Adjust timer if frequency changes significantly
            if abs(current_control_freq - 100) > 10:  # If different by more than 10Hz
                new_period = 1.0 / current_control_freq
                self.timer.timer_period_ns = int(new_period * 1e9)  # Update timer period

        if current_max_vel != self.max_joint_velocity:
            self.get_logger().info(f'Max joint velocity changed from {self.max_joint_velocity} to {current_max_vel}')
            self.max_joint_velocity = current_max_vel

        if current_safety != self.enable_safety:
            self.get_logger().info(f'Safety setting changed from {self.enable_safety} to {current_safety}')
            self.enable_safety = current_safety


def main(args=None):
    rclpy.init(args=args)

    param_node = ParameterManagementNode()

    try:
        rclpy.spin(param_node)
    except KeyboardInterrupt:
        pass
    finally:
        param_node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()