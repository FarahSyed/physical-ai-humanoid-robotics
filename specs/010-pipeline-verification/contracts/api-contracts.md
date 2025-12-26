# API Contracts: Pipeline Verification, Human Approval Gates, and Persisted State Control

## State Management API

### Get Pipeline State
- **Endpoint**: `GET /state`
- **Description**: Retrieve current pipeline state
- **Response**:
  ```json
  {
    "state": "PipelineState enum value",
    "timestamp": "ISO 8601 datetime",
    "progress": {
      "extraction": "completed|pending|approved",
      "chunking": "completed|pending|approved"
    },
    "approvals": {
      "extraction": "APPROVED|REJECTED|PENDING",
      "chunking": "APPROVED|REJECTED|PENDING"
    }
  }
  ```

### Update Pipeline State
- **Endpoint**: `POST /state`
- **Description**: Update pipeline state (internal use)
- **Request**:
  ```json
  {
    "new_state": "PipelineState enum value",
    "reason": "string reason for state change"
  }
  ```
- **Response**: Success or error message

## Approval API

### Approve Stage
- **Endpoint**: `POST /approve/{stage}`
- **Description**: Approve content at specified stage
- **Path Parameter**: `stage` (extraction|chunking)
- **Request**:
  ```json
  {
    "approver": "user identifier",
    "decision": "APPROVE|REJECT|REQUEST_CHANGE",
    "comments": "optional comments"
  }
  ```
- **Response**: Approval record with timestamp

### Get Approval Status
- **Endpoint**: `GET /approval/{stage}`
- **Description**: Get approval status for specified stage
- **Path Parameter**: `stage` (extraction|chunking)
- **Response**:
  ```json
  {
    "stage": "extraction|chunking",
    "status": "APPROVED|REJECTED|PENDING",
    "approver": "user identifier",
    "timestamp": "ISO 8601 datetime",
    "decision": "APPROVE|REJECT|REQUEST_CHANGE"
  }
  ```

## Preview API

### Get Content Preview
- **Endpoint**: `GET /preview/{stage}`
- **Description**: Get preview of content at specified stage
- **Path Parameter**: `stage` (extraction|chunking)
- **Query Parameters**:
  - `limit`: Number of characters/lines to return (default: 1000)
  - `offset`: Starting position (default: 0)
- **Response**: Preview content with metadata

## Resume API

### Resume Pipeline
- **Endpoint**: `POST /resume`
- **Description**: Resume pipeline from last approved state
- **Request**:
  ```json
  {
    "force_extraction": "boolean (optional)",
    "force_chunking": "boolean (optional)",
    "dry_run": "boolean (optional)"
  }
  ```
- **Response**: Resume status and next steps

## Validation API

### Validate Pipeline
- **Endpoint**: `POST /validate`
- **Description**: Validate pipeline configuration and state
- **Response**:
  ```json
  {
    "valid": "boolean",
    "issues": ["array of validation issues"],
    "config_consistency": "boolean",
    "determinism_check": "boolean"
  }
  ```

## Audit API

### Get Audit Log
- **Endpoint**: `GET /audit`
- **Description**: Retrieve audit log entries
- **Query Parameters**:
  - `start_time`: ISO 8601 datetime
  - `end_time`: ISO 8601 datetime
  - `event_type`: Filter by event type
  - `limit`: Number of entries to return
- **Response**: Array of audit entries

## CLI Commands Contract

### Pipeline CLI Commands
- `pipeline_cli start`: Start the pipeline with configuration
- `pipeline_cli status`: Get current pipeline status
- `pipeline_cli preview <stage>`: Preview content at stage
- `pipeline_cli approve <stage>`: Approve content at stage
- `pipeline_cli reject <stage>`: Reject content at stage
- `pipeline_cli resume`: Resume from last approved state
- `pipeline_cli validate`: Validate pipeline configuration
- `pipeline_cli audit`: Show audit log