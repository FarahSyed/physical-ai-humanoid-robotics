# Research: Docusaurus GitHub Pages Deployment

## Decision: Docusaurus Static Build Process
- **Rationale**: Docusaurus uses `npm run build` to generate static HTML, CSS, JS, and assets in a `build/` directory by default
- **Alternatives considered**: Using the built-in `docusaurus deploy` command vs custom build process

## Decision: GitHub Pages Configuration Settings
- **Rationale**:
  - `organizationName`: Set to `FarahSyed` (GitHub username)
  - `projectName`: Set to `physical-ai-humanoid-robotics` (repository name)
  - `baseUrl`: Set to `/physical-ai-humanoid-robotics/` (for GitHub Pages subdirectory routing)
- **Alternatives considered**: Different base URLs like `/` or other paths

## Decision: Deployment Method - GitHub Actions vs Direct Deploy
- **Rationale**: Using GitHub Actions workflow with `actions/deploy-pages` action for automated deployment on push to main
- **Alternatives considered**:
  - Direct deployment using `GIT_USER=<USERNAME> yarn deploy`
  - Manual deployment to `gh-pages` branch
  - Using third-party actions like `peaceiris/actions-gh-pages`

## Decision: Build Output Directory Structure
- **Rationale**: Build output needs to be moved from default `build/` to `frontend/` directory to match constitutional requirements
- **Implementation**: Custom build script that moves build output to `frontend/` directory

## Decision: .nojekyll File Requirement
- **Rationale**: GitHub Pages processes files starting with `_` using Jekyll by default, which interferes with Docusaurus-generated files
- **Solution**: Include empty `.nojekyll` file in build output to disable Jekyll processing

## Decision: Cleanup Strategy for frontend/ Directory
- **Rationale**: Remove any unnecessary files that don't belong to the static site output
- **Criteria**: Keep only static assets (HTML, CSS, JS, images) and required files like `.nojekyll`

## Best Practices for Docusaurus on GitHub Pages
- Use relative paths that account for the subdirectory structure
- Ensure all internal links work correctly with the base URL
- Optimize assets for fast loading
- Test locally before deployment using `npx serve frontend/`

## GitHub Actions Workflow Implementation
- Checkout repository
- Setup Node.js environment
- Install dependencies
- Build Docusaurus site
- Deploy using `actions/deploy-pages`
- Configure appropriate permissions for deployment