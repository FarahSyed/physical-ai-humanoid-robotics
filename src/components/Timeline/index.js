import React from 'react';
import styles from './styles.module.css';

// Define the 13-week timeline data with proper categorization
const weeks = [
  { number: 1, title: "Intro Week 1", category: "Intro", description: "Physical AI foundations" },
  { number: 2, title: "Intro Week 2", category: "Intro", description: "Robotics basics" },
  { number: 3, title: "ROS 2 Week 1", category: "ROS 2", description: "ROS 2 fundamentals" },
  { number: 4, title: "ROS 2 Week 2", category: "ROS 2", description: "Advanced ROS 2 concepts" },
  { number: 5, title: "ROS 2 Week 3", category: "ROS 2", description: "ROS 2 practical applications" },
  { number: 6, title: "Gazebo Week 1", category: "Gazebo", description: "Gazebo simulation basics" },
  { number: 7, title: "Gazebo Week 2", category: "Gazebo", description: "Advanced Gazebo techniques" },
  { number: 8, title: "Isaac Week 1", category: "Isaac", description: "NVIDIA Isaac fundamentals" },
  { number: 9, title: "Isaac Week 2", category: "Isaac", description: "Isaac simulation and deployment" },
  { number: 10, title: "Isaac Week 3", category: "Isaac", description: "Advanced Isaac applications" },
  { number: 11, title: "Humanoid Dev Week 1", category: "Humanoid Dev", description: "Humanoid robot development basics" },
  { number: 12, title: "Humanoid Dev Week 2", category: "Humanoid Dev", description: "Advanced humanoid robotics" },
  { number: 13, title: "Conversational AI", category: "Conversational", description: "Natural language interfaces for robots" },
];

function Timeline() {
  return (
    <div className={styles.timelineContainer}>
      <h2 className={styles.timelineTitle}>13-Week Journey</h2>
      <div className={styles.timeline}>
        {weeks.map((week) => (
          <div key={week.number} className={styles.timelineNode}>
            <div className={styles.nodeCircle}>
              <span className={styles.nodeNumber}>{week.number}</span>
            </div>
            <div className={styles.nodeContent}>
              <h3 className={styles.nodeTitle}>{week.title}</h3>
              <p className={styles.nodeCategory}>{week.category}</p>
              <p className={styles.nodeDescription}>{week.description}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default Timeline;