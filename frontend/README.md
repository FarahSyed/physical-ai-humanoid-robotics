# Physical AI & Humanoid Robotics: Embodied Intelligence in Action

## Overview

This project represents an AI-native educational initiative designed to bridge the gap between digital artificial intelligence and physical robotic systems. Our mission is to create an accessible, technically rigorous, and ethically grounded educational resource that empowers O/A Level, Science, and Engineering students and professionals to understand, design, simulate, and deploy humanoid robots with embodied intelligence.

## Project Vision

The future of AI lies in its physical manifestation—robots that interact with the real world, understand physical laws, and engage in natural human-robot interactions. Through Spec-Driven Development using Spec-Kit Plus and Claude Code, we aim to create a living, evolving educational resource that adapts to technological advances while maintaining educational excellence and ethical standards.

## Core Modules

### 1. Module 1: The Robotic Nervous System (ROS 2) - `003-ros2-nervous-system`
**Status**: Complete

This module focuses on ROS 2 as the nervous system for humanoid robots, covering:
- Core ROS 2 concepts (nodes, topics, services, actions)
- Python integration via rclpy
- URDF for humanoid robot descriptions
- Safety protocols and best practices
- Accessibility features following WCAG 2.1 guidelines
- Performance requirements and hardware validation

### 2. Module 2: Digital Twins for Humanoid Robotics - `TBD`
**Status**: Planned

Simulation and digital twin development for humanoid robotics applications.

### 3. Module 3: NVIDIA Isaac Integration - `TBD`
**Status**: Planned

Integration with NVIDIA Isaac for advanced robotics applications and simulation.

### 4. Module 4: Vision-Language-Action (VLA) Models - `TBD`
**Status**: Planned

Advanced AI integration combining vision, language, and action for embodied intelligence.

## Pre-Module Development Folders

The following folders were created prior to the official module structure for foundational work:

- `000-introduction-section`: Original introduction content
- `001-intro-section-v2`: Updated introduction with futuristic design
- `002-fix-docs-ux-issues`: Documentation UX improvements and site fixes

## Key Features

- **AI-Native Book Approach**: Using Claude Code + Spec-Kit Plus workflow for interactive learning
- **Open-Source Philosophy**: Community-driven improvements and contributions
- **Living Document**: Continuous updates with cutting-edge robotics knowledge
- **Interactive Learning**: Practical examples and hands-on implementation
- **Safety-First Design**: Comprehensive safety protocols for humanoid robotics applications
- **Accessibility Focused**: WCAG 2.1 compliance with progressive complexity from O/A Level fundamentals to professional applications

## Technical Stack

- **ROS 2**: Jazzy Jalisco LTS distribution
- **Programming Language**: Python (rclpy) for ROS 2 integration
- **Simulation**: RViz visualization (no physics simulation per module boundary)
- **Documentation**: Docusaurus v3.6+ with React
- **Hardware**: NVIDIA Jetson Orin Nano (minimum 8GB) as target platform
- **Development Environment**: Ubuntu 22.04 LTS with Python 3.10

## Getting Started

1. Clone the repository
2. Set up the development environment with Ubuntu 22.04 + ROS 2 Jazzy
3. Follow the introduction section to get started with ROS 2 basics
4. Progress through the modules in sequence for comprehensive learning

## Architecture

The project follows a modular architecture with clear boundaries between different aspects of humanoid robotics:

- **Module 1**: ROS 2 fundamentals and nervous system concepts
- **Module 2**: Digital twin simulation and visualization
- **Module 3**: NVIDIA Isaac integration
- **Module 4**: Vision-Language-Action (VLA) models

## Contributing

This project welcomes contributions from the community. We follow a Spec-Driven Development workflow using `/sp.specify`, `/sp.plan`, `/sp.tasks`, and `/sp.implement` commands. See our contribution guidelines in the documentation.

## Ethical Guidelines

- **AI Safety**: Mandatory safety modules covering physical robot deployment protocols
- **Responsible Robotics**: Addressing potential biases in robotic perception and decision-making systems
- **Environmental Responsibility**: Assessment of environmental impact and energy-efficient algorithms
- **Inclusive Design**: Diverse examples from global robotics applications and cultural contexts

## Target Audience

- **Primary**: O/A Level to professional level learners
- **Focus**: Engineers, researchers, and students with AI/robotics background
- **Goal**: Enable a motivated 16-year-old to get ROS 2 running by the end of the introduction section

## Project Status

- **Overall Progress**: Module 1 (ROS 2 Nervous System) completed
- **Next Priority**: Digital twins and simulation modules
- **Timeline**: 13-week quarter structure with progressive learning outcomes

## License

This project is open-source and follows the principles of community-driven development and knowledge sharing for the advancement of physical AI and humanoid robotics education.

## Deployment to GitHub Pages

This project is configured for deployment to GitHub Pages. The site will be automatically deployed when changes are pushed to the main branch.

### Deployment Configuration
- Site URL: `https://FarahSyed.github.io/physical-ai-humanoid-robotics/`
- Base URL: `/physical-ai-humanoid-robotics/`
- Organization: `FarahSyed`
- Project: `physical-ai-humanoid-robotics`

### Build Process
- The site is built using Docusaurus with the `npm run build:frontend` command
- Build output is placed in the `frontend/` directory
- A `.nojekyll` file is included to prevent GitHub Pages from processing files with underscores

### GitHub Actions Workflow
- Automated deployment triggered on push to main branch
- Workflow file: `.github/workflows/deploy.yml`
- Uses `actions/deploy-pages` for deployment
- Runs on Ubuntu with Node.js 20

### Manual Deployment
To build the site locally for testing:
```bash
npm run build:frontend
```

The built site will be available in the `frontend/` directory and can be served locally with:
```bash
npx serve frontend/
```

---

*This repository is maintained as part of the Physical AI & Humanoid Robotics educational initiative, designed to create the next generation of roboticists and AI practitioners while advancing the responsible development of embodied intelligence systems.*