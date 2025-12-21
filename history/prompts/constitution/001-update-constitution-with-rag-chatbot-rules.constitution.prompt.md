---
id: 1
title: "Update Constitution with RAG Chatbot Rules"
stage: constitution
date: "2025-12-20"
surface: "agent"
model: "Claude Sonnet 4.5"
feature: "none"
branch: "docs-initial-setup"
user: "user"
command: "/sp.constitution update"
labels: ["constitution", "rag-chatbot", "governance"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - ".specify/memory/constitution.md"
  - ".specify/templates/plan-template.md"
tests: []
---

# Update Constitution with RAG Chatbot Rules

## PROMPT_TEXT

update
Objective: Integrate RAG Chatbot rules into the existing "Physical AI & Humanoid Robotics" constitution while preserving all existing book creation, code, and content standards.

Additions:

1. RAG Chatbot Global Principles
- Accuracy through selective retrieval: always prefer user-selected text when available.
- Grounding: answers must be traceable to embeddings stored in Neon Postgres and Qdrant, or explicitly flagged as speculative if outside available context.
- Scope enforcement: respond only within the context of the book and related verified content; refuse to answer unrelated topics.
- Deterministic refusal: chatbot must return a clear refusal statement if context is insufficient, avoiding hallucinations.
- Confidence tracking: maintain a confidence score and log for every response.

2. RAG Chatbot Content Standards
- Index all book modules, chapters, and supplementary materials into Qdrant embeddings with semantic similarity and metadata tags.
- Maintain strict versioning of embeddings aligned with book versions.
- Validate all embedding updates and query responses against primary source citations in the book.
- Include fallback rules for unanswered queries, e.g., suggest user review the relevant section.

3. RAG Chatbot Operational Rules
- API Layer: FastAPI endpoints must validate input length, sanitize queries, and ensure embeddings retrieval efficiency.
- Database: Neon Postgres stores structured metadata for chapters, sections, and embeddings; ensure transactional integrity during updates.
- Logging: capture query text, selected text references, model output, and timestamp for audit.
- Security: restrict access to embeddings and book content to authorized endpoints.

4. Deployment Integration
- Embed chatbot in Docusaurus frontend with clear attribution of source text.
- Include automated tests for retrieval accuracy, refusal behavior, and performance benchmarks.
- Document RAG system architecture and operational guidelines in book appendix.

Success Criteria
- Zero unverified or hallucinated answers for queries within book content.
- Accurate, traceable responses for selected text queries.
- Logs and metrics showing confidence, retrieval success, and error handling.

Constraints
- Chatbot must only operate on content included in the book and its verified supplementary sources.
- Do not allow responses based on external web data unless explicitly authorized and documented.

End of update

## RESPONSE_TEXT

Successfully updated the project constitution to integrate RAG Chatbot rules while preserving all existing content. The constitution version was updated from 1.2.0 to 1.3.0 to reflect the addition of new principles.

Key changes made:
1. Added new "RAG Chatbot Principles" section with four subsections:
   - RAG Chatbot Global Principles
   - RAG Chatbot Content Standards
   - RAG Chatbot Operational Rules
   - RAG Chatbot Deployment Integration
2. Updated the version to 1.3.0 and last amended date to 2025-12-20
3. Updated the Sync Impact Report in the header
4. Added RAG system compliance check to the Compliance Monitoring section
5. Added RAG Chatbot Success Criteria and Constraints sections
6. Updated the plan template to include RAG Chatbot Compliance Check when applicable

The update maintains all existing principles and content while adding the new RAG Chatbot rules as required.

## OUTCOME

The constitution has been successfully updated with RAG Chatbot principles integrated into the document structure. The update preserves all existing content while adding the new requirements. The plan template was also updated to include compliance checks for RAG Chatbot features when applicable.

## EVALUATION

The update successfully met all requirements:
- RAG Chatbot rules were integrated into the constitution
- All existing content was preserved
- Version was properly incremented
- Dependent templates were updated where needed
- No unverified or hallucinated content was added