import React from 'react';
import clsx from 'clsx';
import styles from './styles.module.css';

function HeroSection({ children }) {
  return (
    <div className={styles.hero}>
      <div className={styles.heroInner}>
        <h1 className={clsx(styles.heroProjectTagline, styles.cyberpunkHeader)}>
          Physical AI & <span className={styles.heroProjectKeywords}>Humanoid Robotics</span>
        </h1>
        <div className={styles.heroRotatingSilhouette}>
          {children ? children : <div className={clsx(styles.humanoidSilhouette, styles.cyberpunkGlow)}></div>}
        </div>
        <div className={styles.indexCtas}>
          <button className={clsx(styles.heroButton, styles.cyberpunkButton)}>
            Begin Journey
          </button>
        </div>
      </div>
    </div>
  );
}

export default HeroSection;