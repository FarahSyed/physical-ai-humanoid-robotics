# API Contract: Privacy and Data Management

## Overview
This document defines the API contracts for privacy controls and data management in the conversational robotics system, ensuring compliance with user privacy preferences and data retention policies.

## Service Endpoints

### Privacy Settings Service

#### GetUserPrivacySettings
- **Method**: `GET` /privacy/settings/{user_id}
- **Description**: Retrieves user's privacy settings and preferences
- **Response**:
  ```json
  {
    "settings_id": "UUID",
    "user_id": "string",
    "data_retention_days": "integer",
    "record_audio": true|false,
    "record_video": true|false,
    "transcript_storage": true|false,
    "model_training_consent": true|false,
    "last_updated": "ISO 8601 datetime",
    "error_code": "string (if applicable)"
  }
  ```
- **Status Codes**:
  - 200: Success
  - 404: User settings not found
  - 500: Internal server error

#### UpdatePrivacySettings
- **Method**: `PUT` /privacy/settings
- **Description**: Updates user's privacy settings
- **Request**:
  ```json
  {
    "user_id": "string",
    "settings": {
      "data_retention_days": "integer (0-365)",
      "record_audio": true|false,
      "record_video": true|false,
      "transcript_storage": true|false,
      "model_training_consent": true|false
    }
  }
  ```
- **Response**:
  ```json
  {
    "settings_id": "UUID",
    "user_id": "string",
    "updated_settings": "object",
    "last_updated": "ISO 8601 datetime"
  }
  ```

#### ApplyPrivacyToSession
- **Method**: `POST` /privacy/apply-to-session
- **Description**: Applies privacy settings to an active conversation session
- **Request**:
  ```json
  {
    "session_id": "UUID",
    "user_id": "string"
  }
  ```
- **Response**:
  ```json
  {
    "session_id": "UUID",
    "applied_settings": "object",
    "status": "applied|failed"
  }
  ```

### Data Retention Service

#### GetDataRetentionPolicy
- **Method**: `GET` /data-retention/policy
- **Description**: Retrieves system-wide data retention policy
- **Response**:
  ```json
  {
    "policy": {
      "default_retention_days": "integer",
      "max_retention_days": "integer",
      "automatic_deletion_enabled": true|false,
      "deletion_schedule": "string (cron format)"
    }
  }
  ```

#### ScheduleDataDeletion
- **Method**: `POST` /data-retention/schedule-deletion
- **Description**: Schedules data deletion based on retention policy
- **Request**:
  ```json
  {
    "session_ids": ["UUID", ...],
    "deletion_date": "ISO 8601 datetime",
    "retention_reason": "string (if applicable)"
  }
  ```
- **Response**:
  ```json
  {
    "scheduled_deletions": [
      {
        "session_id": "UUID",
        "scheduled_time": "ISO 8601 datetime",
        "status": "scheduled|failed"
      }
    ]
  }
  ```

#### GetDataExpiry
- **Method**: `GET` /data-retention/expiry
- **Description**: Checks expiry status of conversation data
- **Request**:
  ```json
  {
    "session_ids": ["UUID", ...]
  }
  ```
- **Response**:
  ```json
  {
    "expiry_status": [
      {
        "session_id": "UUID",
        "expires_at": "ISO 8601 datetime",
        "days_remaining": "integer",
        "status": "active|expiring_soon|expired"
      }
    ]
  }
  ```

### Data Access Service

#### GetDataAccessLog
- **Method**: `GET` /data-access/log
- **Description**: Retrieves access log for specific session or user
- **Request**:
  ```json
  {
    "session_id": "UUID (optional)",
    "user_id": "string (optional)",
    "start_date": "ISO 8601 datetime (optional)",
    "end_date": "ISO 8601 datetime (optional)",
    "limit": "integer (optional)"
  }
  ```
- **Response**:
  ```json
  {
    "access_logs": [
      {
        "log_id": "UUID",
        "session_id": "UUID",
        "user_id": "string",
        "access_time": "ISO 8601 datetime",
        "access_type": "read|write|delete",
        "accessor": "string",
        "ip_address": "string"
      }
    ]
  }
  ```

#### GetDataExport
- **Method**: `POST` /data-access/export
- **Description**: Exports user conversation data for download
- **Request**:
  ```json
  {
    "user_id": "string",
    "session_ids": ["UUID", ...],
    "export_format": "json|csv|pdf",
    "include_media": true|false
  }
  ```
- **Response**:
  ```json
  {
    "export_id": "UUID",
    "download_url": "string",
    "status": "processing|ready|failed",
    "estimated_completion": "ISO 8601 datetime (if processing)"
  }
  ```

### Consent Management Service

#### GetUserConsentStatus
- **Method**: `GET` /consent/status/{user_id}
- **Description**: Retrieves user's consent status for data processing
- **Response**:
  ```json
  {
    "user_id": "string",
    "consents": {
      "data_collection": true|false,
      "model_training": true|false,
      "personalization": true|false,
      "third_party_sharing": true|false
    },
    "last_updated": "ISO 8601 datetime"
  }
  ```

#### UpdateUserConsent
- **Method**: `PUT` /consent/update
- **Description**: Updates user's consent preferences
- **Request**:
  ```json
  {
    "user_id": "string",
    "consents": {
      "data_collection": true|false,
      "model_training": true|false,
      "personalization": true|false,
      "third_party_sharing": true|false
    }
  }
  ```
- **Response**:
  ```json
  {
    "user_id": "string",
    "updated_consents": "object",
    "timestamp": "ISO 8601 datetime"
  }
  ```

## Message Formats (ROS 2)

### PrivacySettings Message
```yaml
settings_id: string
user_id: string
data_retention_days: int32
record_audio: bool
record_video: bool
transcript_storage: bool
model_training_consent: bool
last_updated: time
```

### DataRetentionPolicy Message
```yaml
policy_id: string
default_retention_days: int32
max_retention_days: int32
automatic_deletion_enabled: bool
deletion_schedule: string
last_updated: time
```

### DataAccessLog Message
```yaml
log_id: string
session_id: string
user_id: string
access_time: time
access_type: string
accessor: string
ip_address: string
```

## Error Handling

### Privacy-Specific Error Codes
- `PRIV_001`: User privacy settings not found
- `PRIV_002`: Privacy setting update failed
- `PRIV_003`: Data retention policy violation
- `PRIV_004`: Consent not provided for operation
- `PRIV_005`: Data deletion failed
- `PRIV_006`: Export request exceeds limits

### Standard Privacy Error Response
```json
{
  "error": {
    "code": "string",
    "message": "string",
    "details": {
      "violation_type": "string",
      "affected_data": "array",
      "recommended_action": "string"
    },
    "timestamp": "ISO 8601 datetime"
  }
}
```

## Compliance Requirements

### GDPR Compliance
- Right to data portability: Users can export their conversation data
- Right to erasure: Users can request deletion of their data
- Consent management: Clear consent mechanisms for data processing
- Data minimization: Only collect necessary data for conversation

### Data Encryption
- All stored conversation data must be encrypted at rest
- Data in transit must use TLS 1.3 or higher
- API keys and tokens must be stored securely
- Sensitive fields in logs must be masked

## Performance Requirements
- Privacy setting retrieval: <50ms for 95% of requests
- Consent status check: <25ms for 95% of requests
- Data export preparation: <30s for 95% of requests
- Data deletion: <5s for 95% of requests