import React from 'react';
import clsx from 'clsx';
import Link from '@docusaurus/Link';
import styles from './styles.module.css';

function NextStepCard({ title, description, to }) {
  return (
    <Link
      to={to}
      className={clsx('card', styles.nextStepCard)}
      style={{ textDecoration: 'none' }}
    >
      <div className="card__header">
        <h3 className={styles.nextStepTitle}>{title}</h3>
      </div>
      <div className="card__body">
        <p className={styles.nextStepDescription}>{description}</p>
      </div>
      <div className="card__footer">
        <span className={styles.nextStepLink}>Start Learning →</span>
      </div>
    </Link>
  );
}

export default function NextSteps({ steps }) {
  if (!steps || steps.length === 0) {
    // Default steps if none provided
    steps = [
      {
        title: "Week 1: Physical AI Foundations",
        description: "Begin your journey with the fundamentals of Physical AI",
        to: "/docs/week1-2-intro/"
      },
      {
        title: "Explore ROS 2",
        description: "Dive into Robot Operating System fundamentals",
        to: "/docs/week3-5-ros2/"
      },
      {
        title: "Simulate with Gazebo",
        description: "Learn physics simulation for robotics",
        to: "/docs/week6-7-gazebo/"
      }
    ];
  }

  return (
    <section className={styles.nextStepsContainer}>
      <h2 className={styles.nextStepsTitle}>Continue Your Journey</h2>
      <div className={styles.nextStepsGrid}>
        {steps.map((step, index) => (
          <div key={index} className="col col--4">
            <NextStepCard {...step} />
          </div>
        ))}
      </div>
    </section>
  );
}