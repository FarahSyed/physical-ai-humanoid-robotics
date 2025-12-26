# Research: Pipeline Verification, Human Approval Gates, and Persisted State Control

## Decision: Pipeline State Machine Design
**Rationale**: Based on the spec requirements, we need a comprehensive state machine that tracks pipeline progress through extraction, chunking, and embedding phases with approval gates. The PipelineState enum was designed with all required states and transitions as specified in FR-018 and FR-019.
**Alternatives considered**: Simple boolean flags vs. comprehensive state enum - chose enum for better visibility and control.

## Decision: Persisted State Schema
**Rationale**: JSON format chosen for persistence due to readability and wide support in Python. Schema includes state, approvals, timestamps, config hash, and artifact paths as required by the spec.
**Alternatives considered**: YAML vs. JSON vs. custom format - chose JSON for simplicity and standard tooling support.

## Decision: Artifact Authority Model
**Rationale**: Persisted state is authoritative for resume points, but artifact existence is validated before resume to prevent inconsistencies. This addresses FR-029 and FR-030 requirements.
**Alternatives considered**: Artifact existence vs. persisted state as authoritative - chose persisted state with validation.

## Decision: Human Approval Implementation
**Rationale**: CLI-based approval system using stdin prompts for user input, with approval records stored with audit information. This satisfies FR-007 and FR-010 requirements.
**Alternatives considered**: Web UI vs. CLI vs. file-based approvals - chose CLI for simplicity and consistency with single-process constraint.

## Decision: Preview Mechanisms
**Rationale**: Content preview with sampling and paging for large content to prevent memory issues, with configurable limits to address FR-005 and FR-006.
**Alternatives considered**: Full content display vs. sampled preview - chose sampled preview for safety.

## Decision: Resume and Restart Logic
**Rationale**: Resume logic based on persisted state with validation of artifacts before proceeding, handling both crash recovery and user rejection scenarios as specified in FR-027.
**Alternatives considered**: Always reprocess vs. smart resume - chose smart resume with validation.

## Decision: Determinism Guarantees
**Rationale**: Configuration hashing and input validation to ensure deterministic chunking behavior across runs as required by FR-013.
**Alternatives considered**: No validation vs. full content hashing - chose configuration-based hashing for efficiency.

## Decision: Dry-Run and Validation Paths
**Rationale**: Dry-run mode that simulates pipeline without making irreversible changes, with separate validation commands as specified in FR-009.
**Alternatives considered**: Full execution vs. simulation - chose simulation approach for safety.