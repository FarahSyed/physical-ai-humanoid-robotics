# Data Model: Weeks 6-7: Robot Simulation with Gazebo

## Educational Content Entities

### Chapter 1: Gazebo Simulation Environment Setup
- **Entity Name**: GazeboEnvironmentSetup
- **Description**: Educational content covering Gazebo simulation environment setup for humanoid robots
- **Attributes**:
  - theory_sections: Array of theoretical concepts
  - practical_examples: Array of minimal code examples
  - diagrams: Array of visual aids
  - citations: Array of references
- **Relationships**: Related to SimulationEnvironment, RobotModel entities

### Chapter 2: URDF/SDF and Physics/Sensor Simulation
- **Entity Name**: URDFSDFPhysicsSimulation
- **Description**: Educational content covering URDF/SDF robot description formats and physics/sensor simulation
- **Attributes**:
  - urdf_examples: Array of URDF format examples
  - sdf_examples: Array of SDF format examples
  - physics_concepts: Array of physics simulation concepts
  - sensor_simulation: Array of sensor simulation examples
  - citations: Array of references
- **Relationships**: Related to RobotModel, PhysicsSimulation, SensorSimulation entities

## Simulation Environment Entities

### Gazebo Simulation Environment
- **Entity Name**: SimulationEnvironment
- **Description**: The physics-based simulation framework that enables testing and validation of humanoid robot behaviors in virtual environments
- **Attributes**:
  - version: Gazebo version (Fortress)
  - physics_engine: Physics engine type (ODE, Bullet, etc.)
  - supported_formats: Array of supported model formats
  - configuration_options: Array of environment configuration options
- **Relationships**: Contains RobotModel entities, uses PhysicsSimulation

### Robot Description Model
- **Entity Name**: RobotModel
- **Description**: Robot description formats that define the physical structure, joints, and kinematic properties of humanoid robots for simulation
- **Attributes**:
  - format_type: Format type (URDF or SDF)
  - links: Array of robot links
  - joints: Array of robot joints
  - inertial_properties: Inertial properties of each link
  - visual_properties: Visual properties of each link
  - collision_properties: Collision properties of each link
- **Relationships**: Used by SimulationEnvironment, contains PhysicsProperties

### Physics Simulation
- **Entity Name**: PhysicsSimulation
- **Description**: System that models real-world physics including gravity, collisions, and material properties in the virtual environment
- **Attributes**:
  - gravity_settings: Gravity vector and magnitude
  - collision_detection: Collision detection algorithm
  - material_properties: Material properties for objects
  - friction_coefficients: Friction coefficients for surfaces
  - damping_factors: Damping factors for joints
- **Relationships**: Used by SimulationEnvironment, affects RobotModel

### Sensor Simulation
- **Entity Name**: SensorSimulation
- **Description**: System that models various robot sensors (LiDAR, cameras, IMUs) to provide realistic sensor data in simulation
- **Attributes**:
  - sensor_type: Type of sensor (LiDAR, camera, IMU, etc.)
  - sensor_parameters: Specific parameters for the sensor
  - noise_model: Noise model for sensor data
  - update_rate: Sensor data update rate
  - field_of_view: Field of view for sensor
- **Relationships**: Used by SimulationEnvironment, integrated with RobotModel

## Educational Resource Entities

### Learning Objectives
- **Entity Name**: LearningObjectives
- **Description**: Measurable learning objectives for the Gazebo simulation module
- **Attributes**:
  - objective_text: Text of the learning objective
  - priority: Priority level (P1, P2, P3)
  - assessment_method: Method for assessing objective achievement
  - success_criteria: Criteria for successful completion
- **Relationships**: Associated with Chapter entities

### Assessment Items
- **Entity Name**: AssessmentItems
- **Description**: Items used to assess student understanding of Gazebo simulation concepts
- **Attributes**:
  - question_type: Type of question (multiple choice, essay, practical)
  - difficulty_level: Difficulty level (O/A Level to professional)
  - content_area: Specific content area covered
  - answer_guidelines: Guidelines for acceptable answers
- **Relationships**: Associated with LearningObjectives, Chapter entities