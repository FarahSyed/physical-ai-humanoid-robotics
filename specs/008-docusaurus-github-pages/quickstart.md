# Quickstart: Docusaurus GitHub Pages Deployment

## Prerequisites
- Node.js (version 18 or higher)
- Git
- GitHub repository access

## Local Development
```bash
# Install dependencies
npm install

# Start development server
npm run start
```

## Building for GitHub Pages
```bash
# Build the static site
npm run build:frontend

# The output will be in the frontend/ directory
```

## Local Testing
```bash
# Serve the built site locally
npx serve frontend/
```

## Deployment
The site is automatically deployed via GitHub Actions when changes are pushed to the main branch.

## Configuration
Key settings in `docusaurus.config.js`:
- `organizationName`: FarahSyed
- `projectName`: physical-ai-humanoid-robotics
- `baseUrl`: /physical-ai-humanoid-robotics/

## Directory Structure
After build:
```
frontend/
├── index.html
├── docs/
├── assets/
├── .nojekyll
└── [other static files]
```

## Troubleshooting
- If links don't work, check that `baseUrl` is correctly configured
- If assets don't load, verify they exist in the `frontend/` directory
- Check GitHub Actions logs for deployment failures