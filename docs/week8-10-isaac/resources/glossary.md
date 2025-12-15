# Glossary: NVIDIA Isaac Platform

## A

**Actor-Critic**: A reinforcement learning algorithm that uses two neural networks - an actor that selects actions and a critic that evaluates action values.

**Application Configuration**: JSON-based configuration files that define Isaac applications, including modules, connections, and parameters.

**Artificial Potential Fields**: A path planning method that treats the robot as a particle moving under the influence of attractive forces toward goals and repulsive forces away from obstacles.

## B

**Bipedal Locomotion**: The ability of humanoid robots to walk on two legs, requiring complex balance and coordination control.

**Bridge Protocol**: A communication protocol that connects Isaac Sim with Isaac applications, enabling real-time data exchange between simulation and application environments.

## C

**Computer Vision**: The field of AI that enables machines to interpret and understand visual information from the world.

**Convolutional Neural Network (CNN)**: A type of deep learning network particularly effective for processing visual data.

**Curriculum Learning**: A training approach where models learn from simple to complex tasks progressively.

## D

**Deep Q-Network (DQN)**: A reinforcement learning algorithm that combines Q-learning with deep neural networks for learning policies.

**Domain Randomization**: A technique for improving sim-to-real transfer by randomizing simulation parameters during training.

**Domain Transfer**: The process of transferring learned behaviors from simulation to real-world robots.

## E

**Environment (RL)**: The world in which a reinforcement learning agent operates and learns.

**Embodiment Transfer**: The process of transferring learned behaviors from one robot embodiment to another with different physical characteristics.

## F

**Force Control**: A control approach that regulates the forces applied by a robot during interaction tasks, as opposed to position control.

**Forward Kinematics**: The process of determining the position and orientation of the end-effector based on known joint angles.

## G

**Grasp Planning**: The process of determining how to grasp an object with a robotic manipulator.

**Graph Neural Network**: A type of neural network designed to operate on graph-structured data.

**Gym Environment**: A standardized interface for reinforcement learning environments in Isaac Gym.

## H

**Humanoid Robot**: A robot with human-like form and capabilities, typically featuring a head, torso, two arms, and two legs.

**Human-Robot Interaction (HRI)**: The study of how humans and robots interact and communicate with each other.

## I

**Isaac SDK**: NVIDIA's software development kit for creating AI-powered robotics applications.

**Isaac Sim**: NVIDIA's photorealistic simulation environment built on Omniverse for robotics applications.

**Isaac Gym**: NVIDIA's high-performance RL training environment integrated with Isaac Sim.

**Inverse Kinematics**: The process of determining joint angles required to achieve a desired end-effector position and orientation.

**Intrinsic Parameters**: Camera parameters that describe the internal characteristics of a camera, including focal length, principal point, and lens distortion.

## J

**Joint Limits**: The physical or software-imposed constraints on the range of motion of robot joints.

**Jacobians**: Mathematical matrices that describe the relationship between joint velocities and end-effector velocities in robotic systems.

## K

**Kinematics**: The study of motion without considering the forces that cause the motion.

**Kinodynamic Planning**: Motion planning that considers both kinematic and dynamic constraints of the robot system.

## L

**Locomotion**: The ability of a robot to move from one place to another.

**LIDAR**: Light Detection and Ranging - a sensing technology that uses laser light to measure distances.

## M

**Manipulation**: The ability of robots to interact with and control objects in their environment.

**Model Predictive Control (MPC)**: A control strategy that uses a model of the system to predict future behavior and optimize control actions.

**Multi-modal Perception**: The integration of information from multiple sensor modalities (e.g., vision, touch, sound) for comprehensive environmental understanding.

## N

**Neural Radiance Fields (NeRF)**: A technique for synthesizing novel views of complex 3D scenes using neural networks.

**Navigation Mesh**: A data structure used in path planning that represents the walkable areas of an environment.

## O

**Observation Space**: The set of all possible observations that an RL agent can receive from the environment.

**Omniverse**: NVIDIA's platform for 3D design collaboration and simulation.

## P

**Perception**: The ability of robots to sense and understand their environment using various sensors.

**Policy (RL)**: A strategy that maps states to actions in reinforcement learning.

**Proximal Policy Optimization (PPO)**: A policy gradient method for reinforcement learning that uses a clipped objective function.

**Point Cloud**: A collection of data points in 3D space, typically generated by 3D scanning devices like LIDAR.

## R

**Recurrent Neural Network**: A type of neural network with connections that form directed cycles, suitable for sequential data.

**Reinforcement Learning (RL)**: A type of machine learning where agents learn to take actions in an environment to maximize cumulative reward.

**Reward Function**: A function that provides feedback to an RL agent about the quality of actions taken.

**Robot State**: The current configuration of a robot including joint positions, velocities, and other relevant information.

**Reactive Navigation**: A navigation approach that responds immediately to sensor inputs without long-term planning.

**Reachability Analysis**: A method for determining whether a robot can reach a particular configuration or location given its constraints.

## S

**Scene Understanding**: The ability to interpret and comprehend the meaning and relationships of objects in a visual scene.

**Sensor Fusion**: The process of combining data from multiple sensors to improve perception accuracy.

**Sim-to-Real Transfer**: The process of transferring behaviors learned in simulation to real-world robots.

**Soft Actor-Critic (SAC)**: A maximum entropy RL algorithm for continuous control tasks.

**State Space**: The set of all possible states in which an RL environment can exist.

**Stereo Vision**: The process of extracting 3D information from two or more 2D images taken from different viewpoints.

**Safety Filter**: A system that ensures robot actions remain within safe operational bounds.

**Symbolic Planning**: High-level planning that uses symbolic representations of the world and actions.

## T

**TensorRT**: NVIDIA's SDK for high-performance deep learning inference optimization.

**Twin Delayed DDPG (TD3)**: An improved version of the DDPG algorithm for continuous control.

**Teleoperation**: The remote control of a robot by a human operator.

**Task Space**: The space of possible end-effector positions and orientations for a robotic manipulator.

## V

**Value Function**: A function in RL that estimates the expected cumulative reward from a given state.

**Velocity Obstacles**: A method for collision avoidance that defines forbidden velocity regions to prevent future collisions.

**Visual Servoing**: A control strategy that uses visual feedback to control robot motion.

## Z

**Zero Moment Point (ZMP)**: A criterion for dynamic balance in bipedal locomotion, representing the point where the net moment of ground reaction forces is zero.

**ZMP Controller**: A control system that maintains robot balance by keeping the ZMP within the support polygon.