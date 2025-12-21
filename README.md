# Physical AI &amp; Humanoid Robotics: Embodied Intelligence in Action

## Overview
This project is an AI-native educational initiative designed to bridge the gap between digital artificial intelligence and physical robotic systems. Our mission is to create an accessible, technically rigorous, and ethically grounded educational resource that empowers O/A Level, Science, and Engineering students and professionals to understand, design, simulate, and deploy humanoid robots with embodied intelligence.

## Features

### Educational Curriculum
- 4 core modules across 13 weeks
- Technical depth with practical examples
- Progressive complexity from fundamentals to professional applications

### RAG Chatbot System
- **Website Content Extraction**: Automatically crawl and extract content from Docusaurus websites
- **Embedding Generation**: Create vector embeddings using Cohere models
- **Vector Storage**: Store embeddings in Qdrant vector database with complete metadata
- **Quality Assurance**: Content validation, deduplication, and quality scoring
- **Review Process**: Temporary storage for content review before embedding

### Technical Implementation
- Docusaurus-based documentation site
- GitHub Pages deployment
- Spec-Driven Development with Spec-Kit Plus
- Claude Code integration for AI-assisted development

## Quick Start

### RAG Website Extraction
To run the RAG website extraction pipeline:

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Install dependencies:
   ```bash
   uv sync
   ```

3. Set up environment variables (see `backend/.env.example`)

4. Run the full pipeline:
   ```bash
   python src/main.py --full-pipeline
   ```

For detailed instructions, see the [backend README](backend/README.md).

## Project Structure
- `backend/` - RAG extraction pipeline and backend services
- `frontend/` - Docusaurus documentation site
- `specs/` - Feature specifications and plans
- `history/` - Architecture decision records and prompt history
- `.specify/` - SpecKit Plus templates and scripts

## Contributing
Please read our [Project Constitution](.specify/memory/constitution.md) for guidelines on contributing to this project.

## License
[Specify license here]