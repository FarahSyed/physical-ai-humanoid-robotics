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
      {/* Light lavender-silver alloy */}
      <defs>
        <linearGradient id="lightAlloy" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#f2f4ff" />
          <stop offset="100%" stopColor="#dde0f4" />
        </linearGradient>

        {/* Subtle glow */}
        <filter id="softGlow" x="-30%" y="-30%" width="160%" height="160%">
          <feGaussianBlur stdDeviation="1.2" />
          <feMerge>
            <feMergeNode />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>

      {/* Head */}
      <circle
        cx="100"
        cy="50"
        r="30"
        fill="url(#lightAlloy)"
        stroke="#00eaff"
        strokeWidth="2"
        filter="url(#softGlow)"
      />

      {/* Eyes - LED indicators */}
      <circle cx="85" cy="45" r="6" fill="#00eaff" stroke="#00eaff" strokeWidth="1">
        <animate attributeName="fill" values="#00eaff;#00aacc;#00eaff" dur="3s" repeatCount="indefinite" />
      </circle>
      <circle cx="87" cy="43" r="2" fill="#fff" />

      <circle cx="115" cy="45" r="6" fill="#00eaff" stroke="#00eaff" strokeWidth="1">
        <animate attributeName="fill" values="#00eaff;#00aacc;#00eaff" dur="3s" repeatCount="indefinite" />
      </circle>
      <circle cx="117" cy="43" r="2" fill="#fff" />

      {/* Mouth */}
      <path d="M90 65 Q100 70 110 65" stroke="#00eaff" strokeWidth="2" fill="none" />

      {/* Neck */}
      <rect
        x="95"
        y="80"
        width="10"
        height="10"
        fill="url(#lightAlloy)"
        stroke="#00eaff"
        strokeWidth="2"
      />

      {/* Torso */}
      <rect
        x="70"
        y="90"
        width="60"
        height="100"
        rx="10"
        fill="url(#lightAlloy)"
        stroke="#00eaff"
        strokeWidth="2"
        filter="url(#softGlow)"
      />

      {/* Chest panel */}
      <rect
        x="85"
        y="100"
        width="30"
        height="40"
        rx="5"
        fill="none"
        stroke="#ff2fd5"
        strokeWidth="1.4"
        strokeDasharray="3 2"
      />

      {/* Core lights */}
      <circle cx="95" cy="110" r="3" fill="#00ff88">
        <animate attributeName="r" values="2;3.5;2" dur="1.6s" repeatCount="indefinite" />
      </circle>
      <circle cx="105" cy="110" r="3" fill="#ff2fd5">
        <animate attributeName="r" values="2;3.5;2" dur="2s" repeatCount="indefinite" />
      </circle>

      {/* Arms */}
      <line
        x1="70"
        y1="110"
        x2="35"
        y2="140"
        stroke="#00eaff"
        strokeWidth="6"
        strokeLinecap="round"
      />
      <line
        x1="130"
        y1="110"
        x2="165"
        y2="140"
        stroke="#00eaff"
        strokeWidth="6"
        strokeLinecap="round"
      />

      {/* Hands */}
      <circle
        cx="35"
        cy="140"
        r="10"
        fill="url(#lightAlloy)"
        stroke="#00eaff"
        strokeWidth="2"
      />
      <circle
        cx="165"
        cy="140"
        r="10"
        fill="url(#lightAlloy)"
        stroke="#00eaff"
        strokeWidth="2"
      />

      {/* Legs */}
      <line
        x1="85"
        y1="190"
        x2="85"
        y2="250"
        stroke="#00eaff"
        strokeWidth="8"
        strokeLinecap="round"
      />
      <line
        x1="115"
        y1="190"
        x2="115"
        y2="250"
        stroke="#00eaff"
        strokeWidth="8"
        strokeLinecap="round"
      />

      {/* Feet */}
      <rect
        x="75"
        y="250"
        width="20"
        height="10"
        rx="3"
        fill="url(#lightAlloy)"
        stroke="#00eaff"
        strokeWidth="2"
      />
      <rect
        x="105"
        y="250"
        width="20"
        height="10"
        rx="3"
        fill="url(#lightAlloy)"
        stroke="#00eaff"
        strokeWidth="2"
      />

      {/* Antenna */}
      <line x1="100" y1="20" x2="100" y2="5" stroke="#00eaff" strokeWidth="2" />
      <circle cx="100" cy="3" r="4" fill="#ffcc00">
        <animate attributeName="opacity" values="0.7;1;0.7" dur="1.3s" repeatCount="indefinite" />
      </circle>
    </svg>
  );
};


export default HumanoidRobot;