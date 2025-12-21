---
description: "Task list for RAG Chatbot Website Content Extraction and Embedding"
---

# Tasks: RAG Chatbot - Website Content Extraction and Embedding

**Input**: Design documents from `/specs/009-rag-website-extraction/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: All features must have comprehensive unit and integration tests following TDD approach.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Initialize the uv project with `uv init backend/` command at project root
- [X] T002 [P] Create subfolders: `backend/src/`, `backend/data/raw_text/`, `backend/config/`, `backend/logs/`, `backend/tests/`
- [X] T003 Create `backend/README.md` explaining pipeline stages and execution order
- [X] T004 Create `backend/requirements.txt` with dependencies: requests, beautifulsoup4, cohere, qdrant-client, python-dotenv, lxml, playwright, pytest
- [X] T005 Create `backend/.env.example` with all required environment variables
- [X] T006 Create unit tests for setup components in `backend/tests/unit/test_setup.py`

---
## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T007 Create configuration management module at `backend/src/utils/config_loader.py`
- [X] T008 [P] Create unit tests for config loader in `backend/tests/unit/test_config_loader.py`
- [X] T009 Set up logging infrastructure at `backend/src/utils/logger.py`
- [X] T010 [P] Create unit tests for logger in `backend/tests/unit/test_logger.py`
- [X] T011 Create content hash utility for deduplication at `backend/src/utils/hash_utils.py`
- [X] T012 [P] Create unit tests for hash utils in `backend/tests/unit/test_hash_utils.py`
- [X] T013 Set up Qdrant client at `backend/src/embeddings/qdrant_client.py`
- [X] T014 [P] Create unit tests for Qdrant client in `backend/tests/unit/test_qdrant_client.py`
- [X] T015 Define Qdrant schema and ID strategy in `backend/src/models/qdrant_schema.py`
- [X] T016 [P] Create unit tests for schema definition in `backend/tests/unit/test_qdrant_schema.py`
- [X] T017 Create base data models at `backend/src/models/extracted_content.py`
- [X] T018 [P] Create unit tests for data models in `backend/tests/unit/test_extracted_content.py`
- [X] T019 Create sitemap parser at `backend/src/crawler/sitemap_parser.py`
- [X] T020 [P] Create unit tests for sitemap parser in `backend/tests/unit/test_sitemap_parser.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---
## Phase 3: Content Extraction Pipeline (Priority: P1) 🎯 MVP

**Goal**: Automatically extract all content from the deployed Docusaurus book website and store it temporarily for review before processing.

**Independent Test**: Can be fully tested by running the extraction process on a target website URL and verifying that content is captured and stored temporarily with complete metadata, delivering a complete dataset ready for embedding.

- [X] T021 Create website crawler module at `backend/src/crawler/website_crawler.py`
- [X] T022 [P] Create unit tests for website crawler in `backend/tests/unit/test_website_crawler.py`
- [X] T023 Create content extractor module at `backend/src/crawler/content_extractor.py`
- [X] T024 [P] Create unit tests for content extractor in `backend/tests/unit/test_content_extractor.py`
- [X] T025 Create raw text storage module at `backend/src/storage/raw_text_storage.py`
- [X] T026 [P] Create unit tests for raw text storage in `backend/tests/unit/test_raw_text_storage.py`
- [X] T027 Create metadata manager module at `backend/src/storage/metadata_manager.py`
- [X] T028 [P] Create unit tests for metadata manager in `backend/tests/unit/test_metadata_manager.py`
- [X] T029 Implement content normalization functionality in `backend/src/crawler/content_extractor.py`
- [X] T030 Add progress tracking to extraction process in `backend/src/crawler/website_crawler.py`
- [X] T031 Implement configurable extraction parameters in `backend/src/crawler/website_crawler.py`
- [X] T032 Create integration tests for extraction pipeline in `backend/tests/integration/test_extraction_pipeline.py`

**Checkpoint**: At this point, content extraction should be fully functional and testable independently

---
## Phase 4: Content Review and Validation (Blocking Gate)

**Goal**: Implement review mechanism to allow developers to validate extracted content before proceeding to embedding generation.

**Independent Test**: Can be fully tested by accessing the temporarily stored extracted content and verifying its quality and completeness, delivering confidence in the source material for embeddings.

- [X] T033 Create content quality validator at `backend/src/storage/content_validator.py`
- [X] T034 [P] Create unit tests for content validator in `backend/tests/unit/test_content_validator.py`
- [X] T035 Enhance metadata manager with quality metrics in `backend/src/storage/metadata_manager.py`
- [X] T036 Create review mechanism (file-based, no UI) at `backend/src/storage/review_checker.py`
- [X] T037 [P] Create unit tests for review mechanism in `backend/tests/unit/test_review_checker.py`
- [X] T038 Add content filtering before embedding in `backend/src/storage/content_validator.py`
- [X] T039 Implement quality assessment for extracted content in `backend/src/storage/metadata_manager.py`
- [X] T040 Create integration tests for validation pipeline in `backend/tests/integration/test_validation_pipeline.py`

**Checkpoint**: At this point, content validation must pass before proceeding to embedding generation

---
## Phase 5: Pre-Embedding Verification Checkpoint

**Goal**: Implement verification that all extracted content meets quality standards before embedding generation begins.

- [X] T041 Create pre-embedding verification module at `backend/src/validation/pre_embedding_checker.py`
- [X] T042 [P] Create unit tests for pre-embedding checker in `backend/tests/unit/test_pre_embedding_checker.py`
- [X] T043 Implement content quality gates in `backend/src/validation/pre_embedding_checker.py`
- [X] T044 Create verification report generator at `backend/src/validation/verification_reporter.py`
- [X] T045 [P] Create unit tests for verification reporter in `backend/tests/unit/test_verification_reporter.py`
- [X] T046 Create integration tests for pre-embedding verification in `backend/tests/integration/test_pre_embedding_verification.py`

**Checkpoint**: At this point, all content must pass verification before embedding generation

---
## Phase 6: Embedding Generation and Storage (Priority: P2)

**Goal**: Generate embeddings from the extracted website content using Cohere models and store them in Qdrant vector database with complete metadata, creating a queryable knowledge base for RAG applications.

**Independent Test**: Can be fully tested by providing extracted content to the embedding process and verifying that vectors are stored in Qdrant database with proper metadata, delivering a searchable knowledge base.

- [X] T047 Create embedding generator module at `backend/src/embeddings/embedding_generator.py`
- [X] T048 [P] Create unit tests for embedding generator in `backend/tests/unit/test_embedding_generator.py`
- [X] T049 Enhance Qdrant client with storage functionality in `backend/src/embeddings/qdrant_client.py`
- [X] T050 [P] Create unit tests for Qdrant storage functionality in `backend/tests/unit/test_qdrant_storage.py`
- [X] T051 Implement configurable batch size for embeddings in `backend/src/embeddings/embedding_generator.py`
- [X] T052 Add complete metadata storage to embeddings in `backend/src/embeddings/qdrant_client.py`
- [X] T053 Implement idempotent writes using content hash in `backend/src/embeddings/qdrant_client.py`
- [X] T054 Add validation for embedding success rate in `backend/src/embeddings/embedding_generator.py`
- [X] T055 Create integration tests for embedding pipeline in `backend/tests/integration/test_embedding_pipeline.py`

**Checkpoint**: At this point, embedding generation should be fully functional and testable independently

---
## Phase 7: Verification & Quality Assurance

**Goal**: Ensure the pipeline meets all acceptance criteria and functions correctly end-to-end

- [X] T056 Create end-to-end integration tests in `backend/tests/integration/test_e2e_pipeline.py`
- [X] T057 Verify all approved raw files have corresponding embeddings
- [X] T058 Run sample similarity queries to confirm retrievability
- [X] T059 Ensure no duplicate vectors exist in Qdrant
- [X] T060 Test pipeline idempotency - re-running does not create duplicate vectors
- [X] T061 Verify all stored embeddings map back to raw text and source URL
- [X] T062 Confirm raw text is reviewable before embedding
- [X] T063 Validate Qdrant contains only approved, deduplicated content
- [X] T064 Test pipeline reproduction from raw text alone

---
## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T065 [P] Create main pipeline script at `backend/src/main.py`
- [X] T066 [P] Add comprehensive logging throughout pipeline in `backend/src/utils/logger.py`
- [X] T067 Add error handling and graceful failure mechanisms across all modules
- [X] T068 [P] Create documentation for pipeline execution in `backend/README.md`
- [X] T069 Add configuration examples to `backend/README.md`
- [X] T070 Describe re-run and recovery behavior in `backend/README.md`
- [X] T071 Run quickstart validation with full pipeline execution
- [X] T072 Create system tests in `backend/tests/system/test_full_pipeline.py`

---
## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **Content Extraction (Phase 3)**: Depends on Foundational completion
- **Content Review (Phase 4)**: Depends on Content Extraction completion - BLOCKING gate
- **Pre-Embedding Verification (Phase 5)**: Depends on Content Review completion - BLOCKING gate
- **Embedding Generation (Phase 6)**: Depends on Pre-Embedding Verification completion
- **Verification (Phase 7)**: Depends on all functional phases being complete
- **Polish (Phase 8)**: Depends on all functional phases being complete

### Within Each Phase

- Tests MUST be written and FAIL before implementation
- Models before services
- Services before main execution logic
- Core implementation before integration
- Phase complete before moving to next phase

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- All test tasks can run in parallel with implementation tasks
- Different phases cannot run in parallel due to blocking dependencies

---
## Implementation Strategy

### MVP First (Phases 1-4)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: Content Extraction
4. Complete Phase 4: Content Review (BLOCKING gate)
5. **STOP and VALIDATE**: Content extraction and review pipeline works independently
6. Deploy/demo if ready

### Incremental Delivery

1. Complete MVP (Phases 1-4) → Test independently → Deploy/Demo (MVP!)
2. Add Pre-Embedding Verification (Phase 5) → Test → Deploy/Demo
3. Add Embedding Generation (Phase 6) → Test → Deploy/Demo
4. Add Verification & Polish (Phases 7-8) → Complete system

### Single Developer Strategy

1. Complete Setup + Foundational
2. Add Content Extraction
3. Add Content Review (blocking gate)
4. Add Pre-Embedding Verification
5. Add Embedding Generation
6. Complete with Verification and Polish

---
## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each phase should be independently completable and testable
- Tests must be written first using TDD approach
- Content Review is a blocking gate before embedding generation
- Review mechanism is file-based (no UI required)
- Qdrant schema and ID strategy defined in Phase 2
- Pre-embedding verification checkpoint added as Phase 5
- Commit after each task or logical group
- Stop at any checkpoint to validate phase independently

## Additional Requirements from User Input

The following specific requirements were mentioned in the user's request and are addressed by the tasks above:

**Phase 1: Backend Initialization and Environment Setup**
- Tasks T001-T006 cover creating backend directory, virtual environment, and project structure
- Task T004 includes all required dependencies (requests, beautifulsoup4, cohere, qdrant-client, python-dotenv, lxml, playwright, pytest)
- Task T005 creates .env.example with placeholders for required environment variables

**Phase 2: Sitemap Discovery and URL Extraction**
- Task T019 creates sitemap parser at `backend/src/crawler/sitemap_parser.py`
- Task T020 creates unit tests for sitemap parser
- Tasks in Phase 3 (T021-T032) implement website crawling and URL extraction

**Phase 3: Content Scraping and Text Extraction**
- Tasks T023-T029 implement content extractor with main article content extraction
- Tasks include stripping navigation, footer, ads, and scripts
- Content normalization and encoding handling is included

**Phase 4: Deduplication and Validation**
- Task T011 creates content hash utility for deduplication
- Task T012 creates unit tests for hash utilities
- Tasks T053 and T060 implement idempotent writes and test pipeline idempotency

**Phase 5: Embedding Generation**
- Tasks T047-T054 implement embedding generation with Cohere models
- Configurable batch size is implemented in Task T051
- API retry and rate limit handling is included in Task T054

**Phase 6: Vector Storage in Qdrant**
- Tasks T013-T016 and T049-T052 implement Qdrant client and storage functionality
- Complete metadata storage with URL, title, section, etc. is included in Task T052
- Content hash-based deduplication is implemented in Task T053