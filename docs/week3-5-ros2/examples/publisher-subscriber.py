#!/usr/bin/env python3
# publisher-subscriber.py
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

class SensorPublisher(Node):
    def __init__(self):
        super().__init__('sensor_publisher')

        # Create a publisher for sensor data
        self.publisher_ = self.create_publisher(String, 'humanoid_sensor_data', 10)

        # Create a timer to simulate sensor data publishing
        timer_period = 0.1  # 10Hz
        self.timer = self.create_timer(timer_period, self.timer_callback)

        self.i = 0

        self.get_logger().info('Sensor publisher node initialized')

    def timer_callback(self):
        msg = String()
        msg.data = f'Sensor reading {self.i}: joint_positions=[0.1, 0.2, 0.3, 0.4, 0.5]'
        self.publisher_.publish(msg)
        self.i += 1


class ControlSubscriber(Node):
    def __init__(self):
        super().__init__('control_subscriber')

        # Create a subscription to sensor data
        self.subscription = self.create_subscription(
            String,
            'humanoid_sensor_data',
            self.listener_callback,
            10)
        self.subscription  # prevent unused variable warning

        self.get_logger().info('Control subscriber node initialized')

    def listener_callback(self, msg):
        self.get_logger().info(f'Received sensor data: {msg.data}')


def main(args=None):
    rclpy.init(args=args)

    publisher_node = SensorPublisher()
    subscriber_node = ControlSubscriber()

    try:
        # Create executor and add both nodes
        executor = rclpy.executors.MultiThreadedExecutor()
        executor.add_node(publisher_node)
        executor.add_node(subscriber_node)

        # Spin both nodes
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        publisher_node.destroy_node()
        subscriber_node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()