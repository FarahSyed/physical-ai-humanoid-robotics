#!/usr/bin/env python3
# service-server-client.py
import rclpy
from rclpy.node import Node
from example_interfaces.srv import AddTwoInts


class ServiceServer(Node):
    def __init__(self):
        super().__init__('service_server')

        # Create a service
        self.srv = self.create_service(AddTwoInts, 'add_two_ints', self.add_two_ints_callback)

    def add_two_ints_callback(self, request, response):
        response.sum = request.a + request.b
        self.get_logger().info(f'Returning {request.a} + {request.b} = {response.sum}')
        return response


class ServiceClient(Node):
    def __init__(self):
        super().__init__('service_client')

        # Create a client
        self.cli = self.create_client(AddTwoInts, 'add_two_ints')

        # Wait for service to be available
        while not self.cli.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('Service not available, waiting again...')

        self.req = AddTwoInts.Request()

    def send_request(self, a, b):
        self.req.a = a
        self.req.b = b

        # Call the service asynchronously
        self.future = self.cli.call_async(self.req)
        rclpy.spin_until_future_complete(self, self.future)

        return self.future.result()


def main(args=None):
    rclpy.init(args=args)

    # Create server and client nodes
    server_node = ServiceServer()
    client_node = ServiceClient()

    try:
        # Send a request from the client
        result = client_node.send_request(42, 36)
        if result is not None:
            server_node.get_logger().info(f'Result: {result.sum}')
        else:
            server_node.get_logger().info('Service call failed')

    except KeyboardInterrupt:
        pass
    finally:
        server_node.destroy_node()
        client_node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()