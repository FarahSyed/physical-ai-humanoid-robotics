# Quickstart Guide: Introduction Section v2

## Overview
Quickstart guide for setting up and customizing the futuristic cyberpunk introduction section for the Physical AI & Humanoid Robotics book.

## Prerequisites
- Node.js 18+ installed
- npm or yarn package manager
- Git for version control
- Basic knowledge of Markdown and React components

## Installation

### 1. Clone the Repository
```bash
git clone [repository-url]
cd [repository-name]
```

### 2. Install Dependencies
```bash
npm install
# OR
yarn install
```

### 3. Start Development Server
```bash
npm run start
# OR
yarn start
```

## Basic Configuration

### 1. Update Docusaurus Configuration
Edit `docusaurus.config.js` to include cyberpunk theme settings:

```javascript
module.exports = {
  // ... existing config
  themeConfig: {
    // ... existing theme config
    cyberpunk: {
      primaryColor: '#00FFFF',      // Electric cyan
      secondaryColor: '#FF00FF',    // Electric magenta
      backgroundColor: '#000000',   // Black background
      fontFamily: 'Rajdhani'        // Futuristic font
    }
  }
};
```

### 2. Add Custom CSS
Create or update `src/css/custom.css` with cyberpunk styling:

```css
/* Cyberpunk theme variables */
:root {
  --cyberpunk-primary: #00FFFF;
  --cyberpunk-secondary: #FF00FF;
  --cyberpunk-bg: #000000;
  --cyberpunk-glow: 0 0 10px var(--cyberpunk-primary), 0 0 20px var(--cyberpunk-primary);
}

/* Apply cyberpunk styling */
.cyberpunk-button {
  background: var(--cyberpunk-bg);
  border: 1px solid var(--cyberpunk-primary);
  color: var(--cyberpunk-primary);
  text-shadow: 0 0 5px var(--cyberpunk-primary);
  box-shadow: var(--cyberpunk-glow);
}
```

## Creating the Hero Section

### 1. Create Hero Component
Create `src/components/HeroSection/index.js`:

```javascript
import React from 'react';
import clsx from 'clsx';
import styles from './styles.module.css';

function HeroSection() {
  return (
    <div className={styles.hero}>
      <div className={styles.heroInner}>
        <h1 className={styles.heroProjectTagline}>
          Physical AI & <span className={styles.heroProjectKeywords}>Humanoid Robotics</span>
        </h1>
        <div className={styles.heroRotatingSilhouette}>
          <div className={styles.humanoidSilhouette}></div>
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
```

### 2. Add Hero Styles
Create `src/components/HeroSection/styles.module.css`:

```css
.hero {
  padding: 4rem 0;
  text-align: center;
  position: relative;
  overflow: hidden;
}

.humanoidSilhouette {
  width: 200px;
  height: 400px;
  margin: 0 auto;
  background: linear-gradient(45deg, var(--cyberpunk-primary), var(--cyberpunk-secondary));
  border-radius: 50% 50% 40% 40% / 60% 60% 40% 40%;
  animation: rotateSilhouette 10s linear infinite;
  box-shadow: var(--cyberpunk-glow);
  position: relative;
}

@keyframes rotateSilhouette {
  0% { transform: rotateY(0deg); }
  100% { transform: rotateY(360deg); }
}

.cyberpunkButton {
  background: transparent;
  border: 1px solid var(--cyberpunk-primary);
  color: var(--cyberpunk-primary);
  padding: 12px 24px;
  border-radius: 4px;
  font-family: var(--ifm-font-family-monospace);
  text-transform: uppercase;
  letter-spacing: 1px;
  transition: all 0.3s ease;
}

.cyberpunkButton:hover {
  box-shadow: var(--cyberpunk-glow);
  text-shadow: 0 0 10px var(--cyberpunk-primary);
}
```

## Creating the Timeline Component

### 1. Create Timeline Component
Create `src/components/Timeline/index.js`:

```javascript
import React from 'react';
import styles from './styles.module.css';

const weeks = [
  { number: 1, title: "Intro Week 1", category: "Intro", description: "Physical AI foundations" },
  { number: 2, title: "Intro Week 2", category: "Intro", description: "Robotics basics" },
  { number: 3, title: "ROS 2 Week 1", category: "ROS 2", description: "ROS 2 fundamentals" },
  // ... continue for all 13 weeks
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
              <h3>{week.title}</h3>
              <p className={styles.nodeCategory}>{week.category}</p>
              <p>{week.description}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default Timeline;
```

## Updating Content Files

### 1. Replace Introduction Content
Update `docs/intro/index.md` with futuristic hero content:

```markdown
---
title: Welcome to Physical AI & Humanoid Robotics
hide_table_of_contents: true
---

import HeroSection from '@site/src/components/HeroSection';

<HeroSection />

This is the beginning of your journey into the future of robotics...
```

### 2. Create Timeline Page
Create `docs/intro/timeline.md`:

```markdown
---
title: 13-Week Journey
---

import Timeline from '@site/src/components/Timeline';

<Timeline />

Follow this structured path to master Physical AI and Humanoid Robotics...
```

## Custom Fonts Setup

### 1. Add Fonts to Configuration
Update `docusaurus.config.js`:

```javascript
module.exports = {
  // ... existing config
  stylesheets: [
    {
      href: 'https://fonts.googleapis.com/css2?family=Rajdhani:wght@300;400;500;600;700&family=Exo+2:wght@300;400;500;600;700&family=Orbitron:wght@400;500;600;700&display=swap',
      rel: 'stylesheet',
    },
  ],
};
```

### 2. Apply Fonts in CSS
Add to `src/css/custom.css`:

```css
html {
  font-family: 'Rajdhani', 'Exo 2', 'Orbitron', sans-serif;
}

.cyberpunk-header {
  font-family: 'Orbitron', monospace;
  text-transform: uppercase;
  letter-spacing: 2px;
}
```

## Running in Production

### Build the Site
```bash
npm run build
# OR
yarn build
```

### Serve Locally
```bash
npm run serve
# OR
yarn serve
```

## Troubleshooting

### Common Issues
1. **Animations not working**: Check browser compatibility and CSS prefixes
2. **Fonts not loading**: Verify font URLs and network connectivity
3. **Glow effects not visible**: Ensure CSS variables are properly defined
4. **Responsive issues**: Test on multiple screen sizes and adjust media queries

### Performance Tips
- Optimize images and animations for faster loading
- Use CSS containment for complex animations
- Implement lazy loading for non-critical components