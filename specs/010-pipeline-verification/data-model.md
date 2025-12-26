# Data Model: Pipeline Verification, Human Approval Gates, and Persisted State Control

## PipelineState Enum

### States
- `IDLE`: Initial state, pipeline not started
- `EXTRACTION_IN_PROGRESS`: Content extraction is in progress
- `EXTRACTION_COMPLETE`: Content extraction completed, awaiting approval
- `EXTRACTION_APPROVED`: Content extraction approved, ready for chunking
- `CHUNKING_IN_PROGRESS`: Content chunking is in progress
- `CHUNKING_COMPLETE`: Content chunking completed, awaiting approval
- `CHUNKING_APPROVED`: Content chunking approved, ready for embedding
- `EMBEDDING_IN_PROGRESS`: Embedding generation in progress
- `EMBEDDING_COMPLETE`: Embedding generation completed
- `FAILED`: Pipeline failed due to system error
- `REJECTED`: Pipeline rejected by human decision

### State Transitions
```
IDLE → EXTRACTION_IN_PROGRESS → EXTRACTION_COMPLETE → EXTRACTION_APPROVED →
CHUNKING_IN_PROGRESS → CHUNKING_COMPLETE → CHUNKING_APPROVED →
EMBEDDING_IN_PROGRESS → EMBEDDING_COMPLETE

EXTRACTION_COMPLETE → REJECTED
CHUNKING_COMPLETE → REJECTED
any_state → FAILED (on system error)
```

## State Persistence Schema (JSON)

```json
{
  "state": "PipelineState",
  "timestamp": "ISO 8601 datetime",
  "config_hash": "SHA256 hash of pipeline configuration",
  "artifact_paths": {
    "extracted_content": "path to extracted content file",
    "chunked_output": "path to chunked output file"
  },
  "approvals": {
    "extraction": {
      "status": "APPROVED|REJECTED|PENDING",
      "approver": "user identifier",
      "timestamp": "ISO 8601 datetime",
      "decision": "APPROVE|REJECT|REQUEST_CHANGE"
    },
    "chunking": {
      "status": "APPROVED|REJECTED|PENDING",
      "approver": "user identifier",
      "timestamp": "ISO 8601 datetime",
      "decision": "APPROVE|REJECT|REQUEST_CHANGE"
    }
  },
  "validation": {
    "determinism_check": "boolean",
    "config_consistency": "boolean"
  }
}
```

## Approval Record Model

### ApprovalRecord
- `approver_id`: String identifier for the approving user
- `timestamp`: ISO 8601 datetime of approval
- `decision`: Enum of APPROVE, REJECT, REQUEST_CHANGE
- `context`: String describing the approval context
- `pipeline_state`: PipelineState at time of approval

## Content Models

### ExtractedContent
- `content`: String of extracted text content
- `source_path`: Path to original source document
- `metadata`: Dictionary of extraction metadata
- `preview_sample`: String sample for preview

### ChunkedOutput
- `chunks`: Array of chunk objects
- `chunk_size`: Integer size of chunks
- `overlap`: Integer overlap between chunks
- `preview_sample`: String sample for preview

## Audit Log Model

### AuditEntry
- `timestamp`: ISO 8601 datetime
- `event_type`: String type of event (state_change, approval, rejection, etc.)
- `user`: User identifier if applicable
- `previous_state`: Previous PipelineState
- `new_state`: New PipelineState
- `details`: Additional details about the event