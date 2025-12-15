# AI Interface Example for Humanoid Robotics

This example demonstrates how to interface with AI services (like LLMs) within the ROS 2 framework for humanoid robotics applications.

## AI Interface Node

```python
#!/usr/bin/env python3
# ai_interface_node.py
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, QoSDurabilityPolicy, QoSHistoryPolicy, QoSReliabilityPolicy
from std_msgs.msg import String, Bool
from sensor_msgs.msg import JointState, Image
from geometry_msgs.msg import PoseStamped
import threading
import time
import json
from typing import Optional, Dict, Any
import requests
from builtin_interfaces.msg import Time

class AIInterfaceNode(Node):
    def __init__(self):
        super().__init__('ai_interface_node')

        # QoS profile for AI communication
        qos_profile = QoSProfile(
            durability=QoSDurabilityPolicy.VOLATILE,
            reliability=QoSReliabilityPolicy.BEST_EFFORT,
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=10
        )

        # Publishers
        self.action_command_publisher = self.create_publisher(
            String,
            'ai_action_commands',
            qos_profile
        )

        self.status_publisher = self.create_publisher(
            String,
            'ai_interface_status',
            qos_profile
        )

        # Subscribers
        self.joint_state_subscriber = self.create_subscription(
            JointState,
            'joint_states',
            self.joint_state_callback,
            qos_profile
        )

        self.vision_subscriber = self.create_subscription(
            Image,
            'camera/image_raw',
            self.vision_callback,
            qos_profile
        )

        self.voice_command_subscriber = self.create_subscription(
            String,
            'voice_commands',
            self.voice_command_callback,
            qos_profile
        )

        # Internal state
        self.current_joint_states = None
        self.last_vision_data = None
        self.ai_service_available = True
        self.ai_request_queue = []
        self.ai_response_lock = threading.Lock()

        # Timer for AI processing (1Hz - for demonstration)
        self.ai_timer = self.create_timer(1.0, self.process_ai_requests)

        # Safety timer (10Hz) to monitor AI interface health
        self.safety_timer = self.create_timer(0.1, self.ai_safety_check)

        self.get_logger().info('AI Interface Node initialized')

    def joint_state_callback(self, msg):
        """Callback for receiving joint state updates"""
        self.current_joint_states = msg
        self.get_logger().debug(f'Received joint states for {len(msg.name)} joints')

    def vision_callback(self, msg):
        """Callback for receiving vision data"""
        # In a real implementation, this would process the image
        # For this example, we'll just store that we received vision data
        self.last_vision_data = {
            'timestamp': msg.header.stamp,
            'encoding': msg.encoding,
            'height': msg.height,
            'width': msg.width
        }
        self.get_logger().debug(f'Received vision data: {msg.width}x{msg.height}')

    def voice_command_callback(self, msg):
        """Callback for receiving voice commands"""
        self.get_logger().info(f'Received voice command: {msg.data}')

        # Add to AI processing queue
        request_data = {
            'type': 'voice_command',
            'content': msg.data,
            'timestamp': self.get_clock().now().seconds_nanoseconds(),
            'context': self.get_current_robot_state()
        }

        with self.ai_response_lock:
            self.ai_request_queue.append(request_data)

    def get_current_robot_state(self) -> Dict[str, Any]:
        """Get current robot state for AI context"""
        state = {
            'timestamp': self.get_clock().now().seconds_nanoseconds(),
            'joint_states': {},
            'vision_available': self.last_vision_data is not None
        }

        if self.current_joint_states:
            for i, name in enumerate(self.current_joint_states.name):
                if i < len(self.current_joint_states.position):
                    state['joint_states'][name] = {
                        'position': self.current_joint_states.position[i],
                        'velocity': self.current_joint_states.velocity[i] if i < len(self.current_joint_states.velocity) else 0.0,
                        'effort': self.current_joint_states.effort[i] if i < len(self.current_joint_states.effort) else 0.0
                    }

        return state

    def process_ai_requests(self):
        """Process queued AI requests"""
        if not self.ai_request_queue:
            return

        with self.ai_response_lock:
            current_queue = self.ai_request_queue.copy()
            self.ai_request_queue.clear()

        for request in current_queue:
            try:
                response = self.query_ai_service(request)
                if response:
                    self.handle_ai_response(response, request)
            except Exception as e:
                self.get_logger().error(f'Error processing AI request: {e}')
                self.ai_service_available = False

    def query_ai_service(self, request_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Query external AI service - in simulation, return mock response"""
        self.get_logger().info(f'Querying AI service with: {request_data["type"]}')

        # Simulate AI service call (in real implementation, this would call an actual AI service)
        # For simulation, return a mock response based on the request type
        if request_data['type'] == 'voice_command':
            command = request_data['content'].lower()

            if 'walk' in command or 'move' in command:
                action_response = {
                    'action': 'walk_forward',
                    'parameters': {'distance': 1.0, 'speed': 0.5},
                    'confidence': 0.85
                }
            elif 'stop' in command:
                action_response = {
                    'action': 'stop_movement',
                    'parameters': {},
                    'confidence': 0.95
                }
            elif 'look' in command or 'see' in command:
                action_response = {
                    'action': 'turn_head',
                    'parameters': {'pan': 0.0, 'tilt': 0.0},
                    'confidence': 0.75
                }
            else:
                action_response = {
                    'action': 'unknown_command',
                    'parameters': {'original_command': command},
                    'confidence': 0.3
                }

            return action_response

        return None

    def handle_ai_response(self, response: Dict[str, Any], original_request: Dict[str, Any]):
        """Handle AI service response"""
        self.get_logger().info(f'AI response: {response["action"]} with confidence {response.get("confidence", 0):.2f}')

        # Validate confidence threshold
        confidence_threshold = 0.7
        if response.get('confidence', 0) < confidence_threshold:
            self.get_logger().warn(f'AI response confidence {response.get("confidence", 0):.2f} below threshold {confidence_threshold}')
            return

        # Publish action command based on AI response
        action_msg = String()
        action_msg.data = json.dumps(response)
        self.action_command_publisher.publish(action_msg)

        # Update status
        status_msg = String()
        status_msg.data = f"AI processed: {response['action']} (conf: {response.get('confidence', 0):.2f})"
        self.status_publisher.publish(status_msg)

    def ai_safety_check(self):
        """Perform safety checks on AI interface"""
        # Check if AI service is still available
        # In a real system, this might check connection health, response times, etc.

        # For simulation, just log the check
        self.get_logger().debug(f'AI interface health check - queue size: {len(self.ai_request_queue)}')

        # Reset availability flag if needed
        if not self.ai_service_available:
            # Try to restore service availability after some time
            # In real implementation, this would attempt to reconnect
            self.ai_service_available = True
            self.get_logger().info('AI service restored')

    def send_ai_request(self, request_type: str, content: str, context: Optional[Dict[str, Any]] = None):
        """Send an AI request"""
        request_data = {
            'type': request_type,
            'content': content,
            'timestamp': self.get_clock().now().seconds_nanoseconds(),
            'context': context or self.get_current_robot_state()
        }

        with self.ai_response_lock:
            self.ai_request_queue.append(request_data)

        self.get_logger().info(f'Queued AI request: {request_type}')


def main(args=None):
    rclpy.init(args=args)

    ai_interface_node = AIInterfaceNode()

    try:
        rclpy.spin(ai_interface_node)
    except KeyboardInterrupt:
        ai_interface_node.get_logger().info('Shutting down AI Interface Node...')
    finally:
        ai_interface_node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
```

## Service Interface Example (Alternative Implementation)

```python
#!/usr/bin/env python3
# ai_service_interface.py
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor
from std_msgs.msg import String
from example_interfaces.srv import Trigger, SetBool
import threading
import time
from typing import Dict, Any

class AIServiceInterface(Node):
    def __init__(self):
        super().__init__('ai_service_interface')

        # Create callback group for services
        self.service_callback_group = ReentrantCallbackGroup()

        # Publishers
        self.action_publisher = self.create_publisher(
            String,
            'ai_action_output',
            QoSProfile(depth=10)
        )

        # Services
        self.process_command_service = self.create_service(
            Trigger,
            'process_ai_command',
            self.process_command_callback,
            callback_group=self.service_callback_group
        )

        self.set_ai_mode_service = self.create_service(
            SetBool,
            'set_ai_mode',
            self.set_ai_mode_callback,
            callback_group=self.service_callback_group
        )

        # Internal state
        self.ai_enabled = True
        self.ai_mode = 'interactive'  # interactive, autonomous, manual

        self.get_logger().info('AI Service Interface initialized')

    def process_command_callback(self, request, response):
        """Service callback to process AI command"""
        self.get_logger().info('Processing AI command request')

        if not self.ai_enabled:
            response.success = False
            response.message = 'AI interface is disabled'
            return response

        # Simulate AI processing
        try:
            # In a real implementation, this would call the actual AI service
            ai_result = self.simulate_ai_processing()

            # Publish result
            result_msg = String()
            result_msg.data = ai_result
            self.action_publisher.publish(result_msg)

            response.success = True
            response.message = f'AI processed command: {ai_result}'
        except Exception as e:
            self.get_logger().error(f'Error processing AI command: {e}')
            response.success = False
            response.message = f'Error: {str(e)}'

        return response

    def set_ai_mode_callback(self, request, response):
        """Service callback to set AI mode"""
        mode = 'autonomous' if request.data else 'manual'
        self.ai_mode = mode
        self.ai_enabled = request.data

        response.success = True
        response.message = f'AI mode set to {mode} (enabled: {request.data})'

        self.get_logger().info(f'AI mode changed to {mode}')
        return response

    def simulate_ai_processing(self) -> str:
        """Simulate AI processing - in real implementation, this calls actual AI service"""
        # Simulate some processing time
        time.sleep(0.1)

        # Return a mock response
        import random
        actions = ['move_forward', 'turn_left', 'turn_right', 'stop', 'wave_arm', 'speak']
        return random.choice(actions)


def main(args=None):
    rclpy.init(args=args)

    ai_service_interface = AIServiceInterface()

    # Use multi-threaded executor to handle services and publishers
    executor = MultiThreadedExecutor()
    executor.add_node(ai_service_interface)

    try:
        executor.spin()
    except KeyboardInterrupt:
        ai_service_interface.get_logger().info('Shutting down AI Service Interface...')
    finally:
        ai_service_interface.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
```

## Package Configuration

```xml
<?xml version="1.0"?>
<?xml-model href="http://download.ros.org/schema/package_format3.xsd" schematypens="http://www.w3.org/2001/XMLSchema"?>
<package format="3">
  <name>humanoid_ai_interface</name>
  <version>0.0.1</version>
  <description>AI interface nodes for humanoid robotics</description>
  <maintainer email="maintainer@todo.todo">maintainer</maintainer>
  <license>Apache-2.0</license>

  <depend>rclpy</depend>
  <depend>std_msgs</depend>
  <depend>sensor_msgs</depend>
  <depend>geometry_msgs</depend>
  <depend>builtin_interfaces</depend>
  <depend>example_interfaces</depend>

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

This AI interface demonstrates:

1. **Multiple Communication Patterns**: Uses both topics and services for AI interaction
2. **Context Awareness**: Incorporates robot state into AI queries
3. **Safety Considerations**: Includes confidence thresholds and safety checks
4. **Asynchronous Processing**: Handles AI requests in a queue to prevent blocking
5. **Error Handling**: Manages AI service availability and errors appropriately

The interface allows humanoid robots to leverage AI capabilities while maintaining safety and real-time performance requirements.