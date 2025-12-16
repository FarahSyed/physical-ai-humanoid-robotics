# Glossary: ROS 2 Fundamentals

## A

**Action**: A goal-based communication pattern in ROS 2 that provides asynchronous communication with feedback and status updates, ideal for long-running tasks like trajectory execution or navigation.

## D

**DDS (Data Distribution Service)**: The communication layer at the core of ROS 2 that provides the foundation for deterministic, real-time communication.

## J

**Joint**: Defines the connections between links in a URDF model with specific degrees of freedom. Humanoid robots require various joint types including revolute, prismatic, spherical, and universal joints.

**Joint State**: Message type that contains the current position, velocity, and effort values for a set of joints.

## L

**Launch File**: A configuration file that enables the coordinated startup of multiple nodes with appropriate parameters and configurations.

**Link**: A rigid body in a URDF model that represents a part of the robot, with visual, collision, and inertial properties.

## N

**Node**: The fundamental execution unit in ROS 2. Each node typically represents a specific function or subsystem in the humanoid robot.

## P

**Parameter**: Configuration values that can be set at runtime and modified dynamically during execution.

**Publisher**: A component that sends messages to topics in the publish-subscribe communication pattern.

## Q

**QoS (Quality of Service)**: Policies that determine the reliability and durability of communication between nodes, critical for safety-critical humanoid applications.

## S

**Service**: Provides synchronous communication with request-response semantics, ideal for operations that need a guaranteed response.

**Subscriber**: A component that receives messages from topics in the publish-subscribe communication pattern.

## T

**Topic**: Enables asynchronous communication through a publish-subscribe pattern where publishers send messages to topics, and subscribers receive messages from topics.

**Trajectory**: A sequence of waypoints that define the desired motion path for joints over time.

## U

**URDF (Unified Robot Description Format)**: The standard XML-based format for representing robot models in ROS, used for describing the physical structure, kinematic properties, and visual representation of robots.