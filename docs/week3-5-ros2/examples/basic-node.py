#!/usr/bin/env python3
# basic-node.py
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

class BasicNode(Node):
    def __init__(self):
        super().__init__('basic_node')

        # Create a publisher
        self.publisher_ = self.create_publisher(String, 'basic_topic', 10)

        # Create a timer
        timer_period = 0.5  # seconds
        self.timer = self.create_timer(timer_period, self.timer_callback)

        self.i = 0

        self.get_logger().info('Basic node initialized')

    def timer_callback(self):
        msg = String()
        msg.data = f'Hello World: {self.i}'
        self.publisher_.publish(msg)
        self.get_logger().info(f'Publishing: "{msg.data}"')
        self.i += 1

def main(args=None):
    rclpy.init(args=args)

    basic_node = BasicNode()

    try:
        rclpy.spin(basic_node)
    except KeyboardInterrupt:
        pass
    finally:
        basic_node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()