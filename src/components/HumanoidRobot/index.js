import React from 'react';

const HumanoidRobot = ({ width = 200, height = 300, className = '' }) => {
  return (
    <svg
      width={width}
      height={height}
      viewBox="0 0 200 300"
      className={className}
      xmlns="http://www.w3.org/2000/svg"
    >
      {/* Head */}
      <circle cx="100" cy="50" r="30" fill="none" stroke="var(--ifm-color-primary)" strokeWidth="2" />

      {/* Eyes */}
      <circle cx="85" cy="45" r="5" fill="var(--ifm-color-primary)" />
      <circle cx="115" cy="45" r="5" fill="var(--ifm-color-primary)" />

      {/* Body */}
      <rect x="75" y="80" width="50" height="100" rx="5" fill="none" stroke="var(--ifm-color-primary)" strokeWidth="2" />

      {/* Arms */}
      <line x1="75" y1="90" x2="40" y2="120" stroke="var(--ifm-color-primary)" strokeWidth="2" />
      <line x1="125" y1="90" x2="160" y2="120" stroke="var(--ifm-color-primary)" strokeWidth="2" />
      <circle cx="40" cy="120" r="8" fill="none" stroke="var(--ifm-color-primary)" strokeWidth="2" />
      <circle cx="160" cy="120" r="8" fill="none" stroke="var(--ifm-color-primary)" strokeWidth="2" />

      {/* Legs */}
      <line x1="90" y1="180" x2="90" y2="240" stroke="var(--ifm-color-primary)" strokeWidth="2" />
      <line x1="110" y1="180" x2="110" y2="240" stroke="var(--ifm-color-primary)" strokeWidth="2" />
      <rect x="80" y="240" width="15" height="20" fill="none" stroke="var(--ifm-color-primary)" strokeWidth="2" />
      <rect x="105" y="240" width="15" height="20" fill="none" stroke="var(--ifm-color-primary)" strokeWidth="2" />

      {/* Antenna */}
      <line x1="100" y1="20" x2="100" y2="5" stroke="var(--ifm-color-primary)" strokeWidth="2" />
      <circle cx="100" cy="3" r="3" fill="var(--ifm-color-primary)" />
    </svg>
  );
};

export default HumanoidRobot;