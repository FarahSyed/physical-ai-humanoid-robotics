// @ts-check

/** @type {import('@docusaurus/plugin-content-docs').SidebarsConfig} */
const sidebars = {
  introSidebar: [
    {
      type: 'category',
      label: 'Introduction',
      items: [
        'intro/welcome',
        'intro/prerequisites',
        'intro/timeline',
        'intro/about-this-book',
        'intro/next-steps',
      ],
    },
    {
      type: 'category',
      label: 'Weeks 1-2: Introduction to Physical AI',
      items: [
        'week1-2-intro/physical-ai-foundations',
        'week1-2-intro/humanoid-robotics-landscape',
        'week1-2-intro/sensor-systems',
      ],
    },
    {
      type: 'category',
      label: 'Weeks 3-5: ROS 2 Fundamentals',
      items: [
        'week3-5-ros2/README',
        'week3-5-ros2/chapter-1-fundamentals',
        'week3-5-ros2/chapter-2-python-integration',
        'week3-5-ros2/chapter-3-launch-files',
      ],
    },
    {
      type: 'category',
      label: 'Weeks 6-7: Robot Simulation with Gazebo',
      items: [
        'week6-7-gazebo/README',
        'week6-7-gazebo/chapter-1-gazebo-setup',
        'week6-7-gazebo/chapter-2-urdf-sdf-physics',
      ],
    },
    {
      type: 'category',
      label: 'Weeks 8-10: NVIDIA Isaac Platform',
      items: [
        'week8-10-isaac/README',
        'week8-10-isaac/chapter-1-isaac-sdk-setup',
        'week8-10-isaac/chapter-2-ai-perception-manipulation',
        'week8-10-isaac/chapter-3-reinforcement-learning-transfer',
      ],
    },
    {
      type: 'category',
      label: 'Weeks 11-12: Humanoid Robot Development',
      items: [
        'week11-12-humanoid/README',
        'week11-12-humanoid/chapter-1-kinematics-dynamics',
        'week11-12-humanoid/chapter-2-locomotion-balance-control',
        'week11-12-humanoid/chapter-3-manipulation-grasping',
        'week11-12-humanoid/chapter-4-human-robot-interaction',
      ],
    },
    {
      type: 'category',
      label: 'Week 13: Conversational Robotics',
      items: [
        'week13-conversational-robotics/chapter-1-conversational-ai',
        'week13-conversational-robotics/chapter-2-implementation-integration',
        'week13-conversational-robotics/glossary',
        'week13-conversational-robotics/resources',
      ],
    },
  ],
};

module.exports = sidebars;