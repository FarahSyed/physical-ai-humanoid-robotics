---
id: 2
title: "Update Constitution with Deployment Standards"
stage: "constitution"
date_iso: "2025-12-15"
surface: "agent"
model: "claude-sonnet-4-5-20250929"
feature: "none"
branch: "docs-initial-setup"
user: "user"
command: "/sp.constitution"
labels: ["constitution", "deployment", "github-pages", "docusaurus"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files_yaml:
  - ".specify/memory/constitution.md"
tests_yaml: []
prompt_text: |
  Project: [Your Project Name]

  Core Principles and Standards:
  - All code must adhere to consistent quality standards, including style, documentation, and testing.
  - All frontend artifacts must be buildable into a production static site folder and deployable without manual changes.
  - Deployment configurations for frontend projects must be fully specified and automated (no manual deployment steps).
  - All builds must produce optimized assets (minification, correct routing, correct relative paths).
  - All deployment workflows must be defined in version-controlled CI/CD configuration files.

  Deployment and Delivery Standards:
  - For Docusaurus frontends, `baseUrl`, `organizationName`, and `projectName` must be correctly configured for GitHub Pages hosting.
  - Production build output must be assembled into a single `frontend/` folder at the root and contain all static site assets and configuration files (including `.nojekyll` if necessary).
  - A clear automated deployment workflow for GitHub Pages (either via GitHub Actions or a `gh-pages` branch script) must be included and version-controlled.
  - Environment variable usage must be documented with an `.env.production.example` file stored in the repository.
  - A high-level deployment guide must be present in the repository README.

  Documentation and Quality Gates:
  - Every feature specification must include success criteria that reference constitutional rules (including deployment where relevant).
  - All automated tests and CI/CD checks must pass before any deployment is accepted.
  - No code or configuration that violates any constitutional rule may be merged into main.

  Constraints and Governance:
  - This Constitution governs all specifications, plans, tasks, and implementations in this project.
  - Any amendments to these rules must follow the defined amendment process in this document.

  Success Criteria:
  - Constitution includes testable, explicit conditions for deployment and quality standards.
  - All subsequent `/sp.specify` outputs automatically include checks aligning with these standards.
response_text: |
  I've successfully updated the existing project constitution to include the specified GitHub Pages deployment standards. The changes were made to the GitHub Pages Integration section of the Deployment Rules, adding:

  1. Requirement that all static frontends using Docusaurus must be configured for GitHub Pages hosting
  2. Requirement that `baseUrl`, `organizationName`, and `projectName` in Docusaurus config MUST be set correctly for GitHub Pages
  3. Requirement that a `.nojekyll` file MUST be included in build output to prevent pages ignoring files starting with `_`
  4. Requirement that production build output must be assembled into a single `frontend/` folder at the root and contain all static site assets and configuration files
  5. Requirement that a clear automated deployment workflow for GitHub Pages must be included and version-controlled
  6. Requirement that environment variable usage must be documented with an `.env.production.example` file

  The constitution file at .specify/memory/constitution.md has been updated with these deployment standards.
outcome: "Constitution updated with deployment and delivery standards for GitHub Pages"
evaluation: "All specified deployment requirements have been incorporated into the project constitution"
---