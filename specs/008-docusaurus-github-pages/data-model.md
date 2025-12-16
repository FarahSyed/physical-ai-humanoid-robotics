# Data Model: Docusaurus GitHub Pages Deployment

## Static Site Entities

### Docusaurus Configuration
- **Fields**:
  - title: string (site title)
  - tagline: string (site tagline)
  - url: string (production URL: https://FarahSyed.github.io)
  - baseUrl: string (base path: /physical-ai-humanoid-robotics/)
  - organizationName: string (GitHub org/user: FarahSyed)
  - projectName: string (repository name: physical-ai-humanoid-robotics)
  - favicon: string (path to favicon)
- **Relationships**: Source for static site generation

### Build Output Directory
- **Fields**:
  - name: string (frontend)
  - contents: array of files (HTML, CSS, JS, assets)
  - structure: directory tree
- **Relationships**: Contains the generated static site

### Static Assets
- **Fields**:
  - type: enum (html, css, js, image, asset)
  - path: string (relative path from root)
  - size: number (file size in bytes)
  - dependencies: array of strings (other assets this asset depends on)
- **Relationships**: Components of the deployed site

### GitHub Actions Workflow
- **Fields**:
  - name: string (deploy.yml)
  - trigger: string (push to main branch)
  - steps: array of objects (build and deployment steps)
  - permissions: object (GitHub Pages deployment permissions)
- **Relationships**: Automates the deployment process

## Relationships
- Docusaurus Configuration → Build Output Directory (generates)
- Build Output Directory → Static Assets (contains)
- GitHub Actions Workflow → Build Output Directory (deploys)

## Validation Rules
- baseUrl must start with "/"
- projectName must match repository name
- Build output directory must contain index.html
- All asset references in HTML files must exist in the build output
- .nojekyll file must be present in build output