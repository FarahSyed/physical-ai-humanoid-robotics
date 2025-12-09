# Data Model: Introduction Section v2

## Overview
Data model for the Physical AI & Humanoid Robotics book introduction section with futuristic cyberpunk design elements.

## Content Entities

### 1. HeroSection Component
- **Fields**:
  - title: string (main headline text)
  - subtitle: string (supporting text)
  - animationType: enum (rotating-silhouette, glowing-silhouette, static-silhouette)
  - backgroundColor: string (CSS color value, default: black)
  - accentColor1: string (primary accent, default: electric cyan)
  - accentColor2: string (secondary accent, default: electric magenta)
  - callToActionText: string (button text)
  - callToActionUrl: string (button link)
  - animationSpeed: number (rotation speed in seconds)
- **Validation**:
  - title must be 5-100 characters
  - backgroundColor must be valid CSS color
  - animationSpeed must be between 2-20 seconds

### 2. TimelineWeek Entity
- **Fields**:
  - weekNumber: integer (1-13)
  - title: string (week title)
  - category: enum (Intro, ROS 2, Gazebo, Isaac, Humanoid Dev, Conversational)
  - description: string (brief description of week content)
  - startDate: date (optional start date)
  - endDate: date (optional end date)
  - isActive: boolean (for current week highlighting)
  - isCompleted: boolean (for progress tracking)
- **Validation**:
  - weekNumber must be 1-13
  - title must be 5-50 characters
  - category must be one of the defined values
  - description must be 10-200 characters

### 3. TimelineVisualization
- **Fields**:
  - weeks: array of TimelineWeek entities
  - theme: enum (cyberpunk, standard, dark, light)
  - showHoverEffects: boolean (default: true)
  - showGlowingNodes: boolean (default: true)
  - nodeSize: enum (small, medium, large)
- **Validation**:
  - weeks array must contain exactly 13 elements
  - all weekNumbers must be unique and sequential 1-13

### 4. AboutThisBookContent
- **Fields**:
  - title: string (section title)
  - content: string (main content in markdown)
  - author: string (author name)
  - publicationDate: date
  - targetAudience: array of strings (e.g., "O Level", "A Level", "Engineering Students")
  - prerequisites: array of strings (knowledge requirements)
  - learningObjectives: array of strings (what users will learn)
- **Validation**:
  - title must be 5-100 characters
  - content must be 500-5000 characters
  - targetAudience must have 1-5 items

### 5. NextStepsSection
- **Fields**:
  - title: string (section title)
  - steps: array of objects containing:
    - stepTitle: string (title for the step)
    - stepUrl: string (URL for the step)
    - stepDescription: string (brief description)
    - stepPriority: enum (high, medium, low)
- **Validation**:
  - steps array must contain 1-2 elements
  - stepTitle must be 5-50 characters
  - stepUrl must be valid URL format

### 6. CyberpunkUIConfiguration
- **Fields**:
  - primaryColor: string (CSS color, default: #00FFFF - electric cyan)
  - secondaryColor: string (CSS color, default: #FF00FF - electric magenta)
  - backgroundColor: string (CSS color, default: #000000 - black)
  - fontFamily: string (font family, default: Rajdhani, Exo 2, or Orbitron)
  - glowIntensity: number (0-100, default: 75)
  - hologramEffect: boolean (default: true)
  - floatingPanels: boolean (default: true)
- **Validation**:
  - colors must be valid CSS colors
  - glowIntensity must be 0-100
  - fontFamily must be one of the approved futuristic fonts

## Relationships
- HeroSection is displayed on the main introduction page
- TimelineVisualization contains 13 TimelineWeek entities
- AboutThisBookContent provides context for the course
- NextStepsSection guides users to continue learning
- CyberpunkUIConfiguration applies styling to all components

## State Transitions
- TimelineWeek can transition from inactive → active → completed as user progresses
- HeroSection animation state can be paused/resumed based on user interaction