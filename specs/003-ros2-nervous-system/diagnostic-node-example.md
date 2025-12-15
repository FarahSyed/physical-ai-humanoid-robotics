# Diagnostic Node Example for Humanoid System Monitoring

This example demonstrates a diagnostic node for monitoring humanoid system health and status.

## Humanoid Diagnostic Node

```python
#!/usr/bin/env python3
# humanoid_diagnostics_node.py
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, QoSDurabilityPolicy, QoSHistoryPolicy, QoSReliabilityPolicy
from diagnostic_msgs.msg import DiagnosticArray, DiagnosticStatus, KeyValue
from sensor_msgs.msg import JointState, Temperature, BatteryState
from std_msgs.msg import String, Bool, Float64
from builtin_interfaces.msg import Time
import threading
import time
from typing import Dict, List, Any
import psutil
import socket

class HumanoidDiagnosticsNode(Node):
    def __init__(self):
        super().__init__('humanoid_diagnostics_node')

        # QoS profile for diagnostic communication
        qos_profile = QoSProfile(
            durability=QoSDurabilityPolicy.TRANSIENT_LOCAL,
            reliability=QoSReliabilityPolicy.RELIABLE,
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=10
        )

        # Publishers
        self.diagnostic_publisher = self.create_publisher(
            DiagnosticArray,
            '/diagnostics',
            qos_profile
        )

        # Subscribers
        self.joint_state_subscriber = self.create_subscription(
            JointState,
            'joint_states',
            self.joint_state_callback,
            qos_profile
        )

        self.battery_subscriber = self.create_subscription(
            BatteryState,
            'battery_state',
            self.battery_callback,
            qos_profile
        )

        self.temperature_subscriber = self.create_subscription(
            Temperature,
            'system_temperature',
            self.temperature_callback,
            qos_profile
        )

        self.emergency_stop_subscriber = self.create_subscription(
            Bool,
            'emergency_stop',
            self.emergency_stop_callback,
            qos_profile
        )

        # Internal state
        self.joint_states = {}
        self.battery_state = None
        self.temperature = None
        self.emergency_stop_active = False
        self.system_monitoring_active = True

        # Diagnostic timers
        self.diagnostic_timer = self.create_timer(1.0, self.publish_diagnostics)  # 1Hz
        self.system_monitor_timer = self.create_timer(2.0, self.update_system_monitoring)  # 0.5Hz

        # Initialize diagnostic status
        self.last_diagnostics_time = self.get_clock().now()

        self.get_logger().info('Humanoid Diagnostics Node initialized')

    def joint_state_callback(self, msg):
        """Callback for receiving joint state updates"""
        for i, name in enumerate(msg.name):
            if i < len(msg.position) and i < len(msg.velocity) and i < len(msg.effort):
                self.joint_states[name] = {
                    'position': msg.position[i],
                    'velocity': msg.velocity[i],
                    'effort': msg.effort[i],
                    'timestamp': msg.header.stamp
                }

    def battery_callback(self, msg):
        """Callback for receiving battery state updates"""
        self.battery_state = {
            'voltage': msg.voltage,
            'current': msg.current,
            'charge': msg.charge,
            'capacity': msg.capacity,
            'design_capacity': msg.design_capacity,
            'percentage': msg.percentage,
            'power_supply_status': msg.power_supply_status,
            'power_supply_health': msg.power_supply_health,
            'power_supply_technology': msg.power_supply_technology,
            'present': msg.present
        }

    def temperature_callback(self, msg):
        """Callback for receiving temperature updates"""
        self.temperature = {
            'temperature': msg.temperature,
            'variance': msg.variance,
            'header': msg.header
        }

    def emergency_stop_callback(self, msg):
        """Callback for emergency stop status"""
        self.emergency_stop_active = msg.data

    def update_system_monitoring(self):
        """Update system-level monitoring data"""
        if not self.system_monitoring_active:
            return

        # Get system resource usage
        cpu_percent = psutil.cpu_percent(interval=None)
        memory_percent = psutil.virtual_memory().percent
        disk_percent = psutil.disk_usage('/').percent

        # Get network information
        try:
            hostname = socket.gethostname()
            ip_address = socket.gethostbyname(hostname)
        except Exception:
            hostname = "unknown"
            ip_address = "0.0.0.0"

        self.system_info = {
            'cpu_percent': cpu_percent,
            'memory_percent': memory_percent,
            'disk_percent': disk_percent,
            'hostname': hostname,
            'ip_address': ip_address,
            'timestamp': self.get_clock().now()
        }

    def publish_diagnostics(self):
        """Publish diagnostic information"""
        diagnostic_array = DiagnosticArray()
        diagnostic_array.header.stamp = self.get_clock().now().to_msg()

        # Add individual diagnostic statuses
        diagnostic_array.status = [
            self.get_hardware_diagnostics(),
            self.get_joint_diagnostics(),
            self.get_power_diagnostics(),
            self.get_thermal_diagnostics(),
            self.get_safety_diagnostics(),
            self.get_system_diagnostics()
        ]

        self.diagnostic_publisher.publish(diagnostic_array)
        self.last_diagnostics_time = self.get_clock().now()

    def get_hardware_diagnostics(self) -> DiagnosticStatus:
        """Get hardware-level diagnostics"""
        status = DiagnosticStatus()
        status.name = "Humanoid Hardware Status"
        status.hardware_id = "humanoid_platform"

        # Check if we're receiving joint states
        if not self.joint_states:
            status.level = DiagnosticStatus.ERROR
            status.message = "No joint state data received"
        else:
            status.level = DiagnosticStatus.OK
            status.message = f"Monitoring {len(self.joint_states)} joints"

        # Add key-value pairs for detailed information
        status.values = [
            KeyValue(key="Joint Count", value=str(len(self.joint_states))),
            KeyValue(key="Last Update", value=str(self.get_clock().now().seconds_nanoseconds()))
        ]

        return status

    def get_joint_diagnostics(self) -> DiagnosticStatus:
        """Get joint-specific diagnostics"""
        status = DiagnosticStatus()
        status.name = "Joint Health"
        status.hardware_id = "joint_system"

        if not self.joint_states:
            status.level = DiagnosticStatus.WARN
            status.message = "No joint data available"
            return status

        # Check joint health
        total_joints = len(self.joint_states)
        healthy_joints = 0
        warning_joints = 0
        error_joints = 0

        joint_details = []

        for joint_name, joint_data in self.joint_states.items():
            pos = joint_data['position']
            vel = joint_data['velocity']
            effort = joint_data['effort']

            # Check position limits
            pos_limit = 3.14  # radians
            vel_limit = 10.0  # rad/s
            effort_limit = 100.0  # N*m

            joint_status = "OK"
            if abs(pos) > pos_limit:
                joint_status = "POS_LIMIT"
                error_joints += 1
            elif abs(vel) > vel_limit:
                joint_status = "VEL_HIGH"
                warning_joints += 1
            elif abs(effort) > effort_limit:
                joint_status = "EFFORT_HIGH"
                warning_joints += 1
            else:
                healthy_joints += 1

            joint_details.append(f"{joint_name}: {joint_status}")

        # Determine overall status
        if error_joints > 0:
            status.level = DiagnosticStatus.ERROR
            status.message = f"{error_joints}/{total_joints} joints in error state"
        elif warning_joints > 0:
            status.level = DiagnosticStatus.WARN
            status.message = f"{warning_joints}/{total_joints} joints with warnings"
        else:
            status.level = DiagnosticStatus.OK
            status.message = f"All {healthy_joints}/{total_joints} joints healthy"

        # Add detailed information
        status.values = [
            KeyValue(key="Total Joints", value=str(total_joints)),
            KeyValue(key="Healthy Joints", value=str(healthy_joints)),
            KeyValue(key="Warning Joints", value=str(warning_joints)),
            KeyValue(key="Error Joints", value=str(error_joints)),
            KeyValue(key="Joint Details", value="; ".join(joint_details))
        ]

        return status

    def get_power_diagnostics(self) -> DiagnosticStatus:
        """Get power system diagnostics"""
        status = DiagnosticStatus()
        status.name = "Power System"
        status.hardware_id = "power_system"

        if not self.battery_state:
            status.level = DiagnosticStatus.WARN
            status.message = "No battery data available"
            return status

        # Determine power status
        battery_percent = self.battery_state['percentage']
        voltage = self.battery_state['voltage']

        if battery_percent < 0.1:  # Less than 10%
            status.level = DiagnosticStatus.ERROR
            status.message = f"Critical battery: {battery_percent*100:.1f}%"
        elif battery_percent < 0.2:  # Less than 20%
            status.level = DiagnosticStatus.WARN
            status.message = f"Low battery: {battery_percent*100:.1f}%"
        else:
            status.level = DiagnosticStatus.OK
            status.message = f"Normal battery: {battery_percent*100:.1f}%"

        # Add detailed information
        status.values = [
            KeyValue(key="Battery Percentage", value=f"{battery_percent*100:.2f}%"),
            KeyValue(key="Voltage", value=f"{voltage:.2f}V"),
            KeyValue(key="Current", value=f"{self.battery_state['current']:.2f}A"),
            KeyValue(key="Capacity", value=f"{self.battery_state['capacity']:.2f}Ah"),
            KeyValue(key="Status", value=str(self.battery_state['power_supply_status']))
        ]

        return status

    def get_thermal_diagnostics(self) -> DiagnosticStatus:
        """Get thermal system diagnostics"""
        status = DiagnosticStatus()
        status.name = "Thermal Management"
        status.hardware_id = "thermal_system"

        if not self.temperature:
            status.level = DiagnosticStatus.WARN
            status.message = "No temperature data available"
            return status

        temp = self.temperature['temperature']
        temp_limit = 80.0  # degrees Celsius

        if temp > temp_limit:
            status.level = DiagnosticStatus.ERROR
            status.message = f"Overheating: {temp:.1f}°C > {temp_limit}°C"
        elif temp > temp_limit * 0.8:  # 80% of limit
            status.level = DiagnosticStatus.WARN
            status.message = f"High temperature: {temp:.1f}°C"
        else:
            status.level = DiagnosticStatus.OK
            status.message = f"Normal temperature: {temp:.1f}°C"

        # Add detailed information
        status.values = [
            KeyValue(key="Temperature", value=f"{temp:.2f}°C"),
            KeyValue(key="Variance", value=f"{self.temperature['variance']:.2f}"),
            KeyValue(key="Limit", value=f"{temp_limit}°C")
        ]

        return status

    def get_safety_diagnostics(self) -> DiagnosticStatus:
        """Get safety system diagnostics"""
        status = DiagnosticStatus()
        status.name = "Safety System"
        status.hardware_id = "safety_system"

        if self.emergency_stop_active:
            status.level = DiagnosticStatus.ERROR
            status.message = "EMERGENCY STOP ACTIVATED"
        else:
            status.level = DiagnosticStatus.OK
            status.message = "Safety systems normal"

        # Add detailed information
        status.values = [
            KeyValue(key="Emergency Stop", value="ACTIVE" if self.emergency_stop_active else "INACTIVE"),
            KeyValue(key="Safety Status", value="OK" if not self.emergency_stop_active else "EMERGENCY")
        ]

        return status

    def get_system_diagnostics(self) -> DiagnosticStatus:
        """Get system-level diagnostics"""
        status = DiagnosticStatus()
        status.name = "System Resources"
        status.hardware_id = "system_resources"

        if not hasattr(self, 'system_info'):
            self.update_system_monitoring()

        if not hasattr(self, 'system_info'):
            status.level = DiagnosticStatus.WARN
            status.message = "System monitoring not initialized"
            return status

        # Check resource usage
        cpu_percent = self.system_info['cpu_percent']
        memory_percent = self.system_info['memory_percent']
        disk_percent = self.system_info['disk_percent']

        max_cpu = 80.0
        max_memory = 85.0
        max_disk = 90.0

        resource_issues = []
        if cpu_percent > max_cpu:
            resource_issues.append(f"CPU: {cpu_percent:.1f}% > {max_cpu}%")
        if memory_percent > max_memory:
            resource_issues.append(f"Memory: {memory_percent:.1f}% > {max_memory}%")
        if disk_percent > max_disk:
            resource_issues.append(f"Disk: {disk_percent:.1f}% > {max_disk}%")

        if resource_issues:
            status.level = DiagnosticStatus.WARN
            status.message = f"Resource issues: {', '.join(resource_issues)}"
        else:
            status.level = DiagnosticStatus.OK
            status.message = f"Resources OK: CPU {cpu_percent:.1f}%, Mem {memory_percent:.1f}%, Disk {disk_percent:.1f}%"

        # Add detailed information
        status.values = [
            KeyValue(key="CPU Usage", value=f"{cpu_percent:.2f}%"),
            KeyValue(key="Memory Usage", value=f"{memory_percent:.2f}%"),
            KeyValue(key="Disk Usage", value=f"{disk_percent:.2f}%"),
            KeyValue(key="Hostname", value=self.system_info['hostname']),
            KeyValue(key="IP Address", value=self.system_info['ip_address'])
        ]

        return status


def main(args=None):
    rclpy.init(args=args)

    diagnostics_node = HumanoidDiagnosticsNode()

    try:
        rclpy.spin(diagnostics_node)
    except KeyboardInterrupt:
        diagnostics_node.get_logger().info('Shutting down Humanoid Diagnostics Node...')
    finally:
        diagnostics_node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
```

## Diagnostic Analyzer Node

```python
#!/usr/bin/env python3
# diagnostic_analyzer_node.py
import rclpy
from rclpy.node import Node
from diagnostic_msgs.msg import DiagnosticArray, DiagnosticStatus
from std_msgs.msg import String
from rclpy.qos import QoSProfile

class DiagnosticAnalyzerNode(Node):
    def __init__(self):
        super().__init__('diagnostic_analyzer_node')

        # Subscribers
        self.diagnostic_subscriber = self.create_subscription(
            DiagnosticArray,
            '/diagnostics',
            self.diagnostic_callback,
            QoSProfile(depth=10)
        )

        # Publishers
        self.alert_publisher = self.create_publisher(
            String,
            'diagnostic_alerts',
            QoSProfile(depth=10)
        )

        self.get_logger().info('Diagnostic Analyzer Node initialized')

    def diagnostic_callback(self, msg):
        """Analyze incoming diagnostic messages"""
        alerts = []

        for status in msg.status:
            if status.level == DiagnosticStatus.ERROR:
                alert_msg = f"ERROR: {status.name} - {status.message}"
                alerts.append(alert_msg)
                self.get_logger().error(alert_msg)
            elif status.level == DiagnosticStatus.WARN:
                alert_msg = f"WARNING: {status.name} - {status.message}"
                alerts.append(alert_msg)
                self.get_logger().warn(alert_msg)

        # Publish alerts if any
        if alerts:
            alert_string = String()
            alert_string.data = "; ".join(alerts)
            self.alert_publisher.publish(alert_string)


def main(args=None):
    rclpy.init(args=args)

    analyzer_node = DiagnosticAnalyzerNode()

    try:
        rclpy.spin(analyzer_node)
    except KeyboardInterrupt:
        analyzer_node.get_logger().info('Shutting down Diagnostic Analyzer Node...')
    finally:
        analyzer_node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
```

## Package Configuration

```xml
<?xml version="1.0"?>
<?xml-model href="http://download.ros.org/schema/package_format3.xsd" schematypens="http://www.w3.org/2001/XMLSchema"?>
<package format="3">
  <name>humanoid_diagnostics</name>
  <version>0.0.1</version>
  <description>Diagnostic nodes for humanoid robotics systems</description>
  <maintainer email="maintainer@todo.todo">maintainer</maintainer>
  <license>Apache-2.0</license>

  <depend>rclpy</depend>
  <depend>std_msgs</depend>
  <depend>sensor_msgs</depend>
  <depend>diagnostic_msgs</depend>
  <depend>builtin_interfaces</depend>

  <exec_depend>python3-psutil</exec_depend>

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

This diagnostic system demonstrates:

1. **Comprehensive Monitoring**: Monitors joints, power, thermal, safety, and system resources
2. **Standard Diagnostic Format**: Uses ROS 2 diagnostic messages for compatibility
3. **Hierarchical Status**: Provides both overall system status and detailed component information
4. **Alert Generation**: Can generate alerts for errors and warnings
5. **Resource Monitoring**: Tracks CPU, memory, and disk usage for the humanoid system
6. **Safety Integration**: Includes safety system status in diagnostics

The diagnostic system provides operators and autonomous systems with critical information about the humanoid robot's health and operational status.