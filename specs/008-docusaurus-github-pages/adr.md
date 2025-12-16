# ADR: Deployment Strategy for Docusaurus GitHub Pages

## Status
Accepted

## Context
We need to deploy a Docusaurus documentation site to GitHub Pages. The project constitution specifies requirements for deployment including correct configuration, build output to a `frontend/` directory, and automated deployment via GitHub Actions. We need to make decisions about the specific tools, configuration, and deployment process.

## Decision

### 1. GitHub Actions Deployment Tool
We will use `actions/deploy-pages` as the GitHub Actions deployment action rather than alternatives like `peaceiris/actions-gh-pages`.

**Rationale**:
- `actions/deploy-pages` is the official GitHub action for deploying to GitHub Pages
- It's maintained by GitHub and has better integration with GitHub Pages features
- It has simpler configuration requirements
- It uses GitHub's built-in deployment infrastructure which is more reliable

### 2. Deployment Trigger
We will configure the deployment to trigger on push to the main branch.

**Rationale**:
- This follows CI/CD best practices for documentation sites
- Provides immediate deployment of approved changes
- Reduces manual intervention requirements
- Aligns with the need for up-to-date documentation

### 3. Build Output Directory
We will ensure the build process outputs to the `frontend/` directory as specified in the project constitution, rather than the default `build/` directory.

**Rationale**:
- Required by project constitutional standards
- Provides consistency across the project
- Makes deployment process explicit and clear

### 4. Base URL Configuration
We will configure the Docusaurus `baseUrl` to `/physical-ai-humanoid-robotics/` to match the GitHub Pages subdirectory structure.

**Rationale**:
- Required for proper routing when site is served from subdirectory
- GitHub Pages serves user sites at `https://<username>.github.io/<repository>/`
- Without correct base URL, links and assets will be broken

### 5. .nojekyll File
We will include a `.nojekyll` file in the build output to prevent GitHub Pages from processing files with underscores.

**Rationale**:
- Docusaurus generates files with underscore prefixes (e.g., `_next`, `_nuxt`)
- GitHub Pages processes files starting with `_` using Jekyll by default
- This interferes with Docusaurus-generated files and breaks the site
- The `.nojekyll` file disables Jekyll processing

## Consequences

### Positive:
- Standard, well-supported deployment approach
- Automated deployment reduces manual errors
- Proper routing and asset loading on GitHub Pages
- Compliance with project constitutional requirements
- Simpler maintenance and troubleshooting

### Negative:
- Less flexibility compared to custom deployment scripts
- Dependent on GitHub's deployment infrastructure
- May have limitations compared to more advanced deployment tools

### Neutral:
- Requires GitHub repository with appropriate permissions
- Build times may increase slightly due to copying to custom directory
- Requires understanding of GitHub Pages URL structure

## Alternatives Considered

### Deployment Actions:
- `peaceiris/actions-gh-pages`: More features but more complex setup
- Manual deployment to `gh-pages` branch: More control but requires manual intervention

### Deployment Triggers:
- Manual dispatch: More control but requires manual intervention
- Release-based: More formal but may delay documentation updates

## Links
- Docusaurus deployment documentation
- GitHub Pages documentation
- actions/deploy-pages documentation
- Project constitution deployment requirements