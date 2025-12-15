# Research: ROS 2 Nervous System Module

## Decision: ROS 2 Distribution Selection
**Rationale**: ROS 2 Jazzy Jalisco (May 2024 LTS) was selected as the primary distribution based on the specification. Despite the May 2025 release of Kilted Kaiju, Jazzy remains the recommended LTS for industrial and educational deployment through 2029. NVIDIA Isaac ROS officially supports Jazzy as of Q3 2025, and Ubuntu 22.04 is fully compatible with Jazzy.

## Decision: Theory vs Practice Balance
**Rationale**: Based on updated requirements, the balance was adjusted from 40/60 to 70/30 (70% theory, 30% practice) to reduce code-heavy content. This aligns with the request to focus on theoretical understanding with minimal code snippets for reference only.

## Decision: Target Platform
**Rationale**: Ubuntu 22.04 LTS with Python 3.10 was selected as the target platform based on the locked hardware/OS context in the specification. Target deployment is on NVIDIA Jetson Orin Nano (8GB) as the minimal edge platform, with development on RTX 4070 Ti+ workstation or AWS g5.2xlarge.

## Decision: Content Structure
**Rationale**: The content is organized into 3 chapters distributed across weeks 1-9:
- Chapter 1 (weeks 1-3): ROS 2 fundamentals - nodes, topics, services, actions
- Chapter 2 (weeks 4-6): Python integration using rclpy
- Chapter 3 (weeks 7-9): URDF for humanoid robot descriptions

## Decision: Code Example Approach
**Rationale**: Following the updated requirements to reduce code-heavy examples, all code examples will be minimal and for reference only, focusing on conceptual understanding rather than requiring full implementation. Each example includes concise, illustrative Python code snippets using rclpy for reference only without requiring full implementation.

## Decision: Citation and Quality Standards
**Rationale**: IEEE citation format is used for all technical references, with a requirement for 20+ sources and 50%+ from official documentation and peer-reviewed journals. This ensures technical accuracy and verifiability as required by the project constitution.

## Alternatives Considered:
1. **Higher code implementation**: Rejected in favor of theoretical focus to meet the requirement of reducing code-heavy content
2. **Different ROS distributions**: Kilted Kaiju was considered but Jazzy Jalisco was selected due to LTS status and broader compatibility
3. **Different theory-practice balance**: Various ratios were considered but 70/30 was selected based on explicit requirements to reduce code examples