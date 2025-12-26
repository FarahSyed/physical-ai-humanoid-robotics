# Quickstart: Pipeline Verification, Human Approval Gates, and Persisted State Control

## Overview
This guide shows how to set up and use the pipeline verification system with human approval gates and persisted state control.

## Prerequisites
- Python 3.11+
- Existing RAG pipeline environment
- Content to be processed through the pipeline

## Installation
The pipeline verification components are integrated into the existing RAG pipeline system. No additional installation required.

## Basic Usage

### 1. Start the Pipeline
```bash
python -m cli.pipeline_cli start --config pipeline_config.json
```

### 2. Check Pipeline Status
```bash
python -m cli.pipeline_cli status
```

### 3. Approve Content Extraction
When the pipeline reaches the extraction approval gate:
```bash
# Preview the extracted content
python -m cli.pipeline_cli preview extraction

# Approve the extracted content
python -m cli.pipeline_cli approve extraction

# Or reject the extracted content
python -m cli.pipeline_cli reject extraction
```

### 4. Approve Content Chunking
When the pipeline reaches the chunking approval gate:
```bash
# Preview the chunked output
python -m cli.pipeline_cli preview chunking

# Approve the chunked output
python -m cli.pipeline_cli approve chunking

# Or reject the chunked output
python -m cli.pipeline_cli reject chunking
```

### 5. Resume from State
If the pipeline was interrupted:
```bash
# Resume from the last approved state
python -m cli.pipeline_cli resume

# Force re-extraction (if needed)
python -m cli.pipeline_cli resume --force-extraction

# Force re-chunking (if needed)
python -m cli.pipeline_cli resume --force-chunking
```

### 6. Dry Run Mode
To simulate the pipeline without making irreversible changes:
```bash
python -m cli.pipeline_cli start --dry-run
```

### 7. Validation Mode
To validate the pipeline without processing:
```bash
python -m cli.pipeline_cli validate
```

## Configuration
The pipeline uses a configuration file (JSON/YAML) that includes:
- Input source paths
- Chunking parameters
- Output destination paths
- Approval settings

## State Management
- Pipeline state is automatically persisted to `pipeline_state.json`
- State includes current stage, approval status, and artifact locations
- On restart, pipeline resumes from the last approved state

## Approval Workflow
1. Pipeline processes content up to approval gate
2. Processing pauses and waits for human approval
3. User reviews content using preview commands
4. User approves, rejects, or requests changes
5. Pipeline continues based on approval decision

## Error Handling
- System failures result in FAILED state
- Human rejections result in REJECTED state
- Both states are handled appropriately on resume
- Audit logs track all state changes and decisions