# Quickstart Guide: Fix Documentation UX Issues

## Prerequisites

- Node.js (v18 or higher)
- npm or yarn package manager
- Git for version control
- A modern web browser for testing

## Setup

1. **Clone the repository** (if not already done):
   ```bash
   git clone <repository-url>
   cd physical-ai-humanoid-robotics
   ```

2. **Install dependencies**:
   ```bash
   npm install
   # or
   yarn install
   ```

3. **Start the development server**:
   ```bash
   npm run start
   # or
   yarn start
   ```

## Implementation Steps

### 1. Fix Home Page 404 Error
- Navigate to `src/pages/index.tsx`
- Ensure the file has proper React component structure
- Add appropriate content to replace the 404 error

### 2. Add SVG Humanoid Robot
- Create a new component in `src/components/HumanoidRobot/HumanoidRobot.tsx`
- Implement a simple geometric humanoid robot using SVG
- Import and use the component on the welcome page

### 3. Apply New Color Palette
- Define CSS variables in `src/css/custom.css`:
  ```css
  :root {
    --ifm-color-primary: #3c339a;
    --ifm-color-primary-dark: #5a79c8;
    --ifm-color-primary-darker: #5fb7cf;
    --ifm-color-primary-darkest: #85ebd9;
    --ifm-color-primary-light: #eeeeee;
  }
  ```
- Apply these variables throughout the site

### 4. Implement Typography Changes
- Add Aileron font import in `docusaurus.config.js`
- Configure typography in the theme to use default + Aileron fonts
- Ensure no more than 2 fonts are used across the entire project

### 5. Update Next Steps Cards
- Locate the existing NextSteps component
- Apply consistent styling using the same CSS classes
- Remove excessive information from all Next Steps cards

### 6. Reorganize Intro Pages
- Update `sidebars.js` to reorder the intro folder pages
- Ensure prerequisites appear before other content
- Test navigation flow to verify proper sequence

### 7. Remove Duplicate Page
- Identify the 13 Week Journey page
- Remove it since the content exists in About This Book page
- Update any navigation that referenced the removed page

## Testing

1. **Visual Regression Checks**:
   - Verify theme application across all pages
   - Check that all pages use the new color palette consistently

2. **Navigation Continuity Tests**:
   - Ensure correct page order in the intro section
   - Verify deprecated pages have been properly removed

3. **Component Consistency Checks**:
   - Validate NextSteps card UI uniformity
   - Confirm all NextSteps cards have reduced content

4. **Rendering Validation**:
   - Test SVG humanoid robot displays correctly across devices
   - Verify responsive design works on mobile, tablet, and desktop

5. **Typography Consistency**:
   - Confirm only 2 fonts are used globally
   - Verify restricted use of Neuropol-X where applicable

6. **Home Page Test**:
   - Verify index.tsx loads without 404 error
   - Confirm proper content displays

## Deployment

1. **Build the site**:
   ```bash
   npm run build
   # or
   yarn build
   ```

2. **Serve the build locally** (optional verification):
   ```bash
   npm run serve
   # or
   yarn serve
   ```

3. **Deploy** to GitHub Pages following the project's deployment workflow