# API Contract: Conversation Service

## Overview
This document defines the API contracts for the conversational robotics system, specifying the interfaces between different components and external services.

## Service Endpoints

### Conversation Management Service

#### StartConversation
- **Method**: `POST` /conversation/start
- **Description**: Initiates a new conversation session with the robot
- **Request**:
  ```json
  {
    "user_id": "string (optional)",
    "session_preferences": {
      "active_modality": "speech|gesture|vision|multimodal",
      "privacy_settings": {
        "record_audio": true|false,
        "record_video": true|false,
        "transcript_storage": true|false
      }
    }
  }
  ```
- **Response**:
  ```json
  {
    "session_id": "UUID",
    "start_time": "ISO 8601 datetime",
    "status": "active",
    "error_code": "string (if applicable)"
  }
  ```
- **Status Codes**:
  - 200: Success
  - 400: Invalid request parameters
  - 500: Internal server error

#### EndConversation
- **Method**: `POST` /conversation/end
- **Description**: Ends an active conversation session
- **Request**:
  ```json
  {
    "session_id": "UUID"
  }
  ```
- **Response**:
  ```json
  {
    "session_id": "UUID",
    "end_time": "ISO 8601 datetime",
    "status": "ended",
    "summary": "string (conversation summary)"
  }
  ```

### User Input Service

#### ProcessSpeechInput
- **Method**: `POST` /input/speech
- **Description**: Processes speech input and returns recognized text with confidence
- **Request**:
  ```json
  {
    "session_id": "UUID",
    "audio_data": "base64 encoded audio",
    "language": "string (e.g., 'en-US')",
    "source_modality": "audio"
  }
  ```
- **Response**:
  ```json
  {
    "input_id": "UUID",
    "session_id": "UUID",
    "transcript": "string",
    "confidence": "float (0.0-1.0)",
    "processed_data": {
      "intent": "string",
      "entities": "array",
      "language": "string"
    }
  }
  ```

#### ProcessGestureInput
- **Method**: `POST` /input/gesture
- **Description**: Processes gesture input from camera feed
- **Request**:
  ```json
  {
    "session_id": "UUID",
    "gesture_data": {
      "coordinates": {
        "x": "float",
        "y": "float",
        "z": "float (optional)"
      },
      "gesture_type": "point|wave|other",
      "timestamp": "ISO 8601 datetime"
    }
  }
  ```
- **Response**:
  ```json
  {
    "input_id": "UUID",
    "session_id": "UUID",
    "gesture_type": "string",
    "confidence": "float (0.0-1.0)",
    "processed_data": {
      "target_object": "string (if applicable)",
      "intended_action": "string"
    }
  }
  ```

### Response Generation Service

#### GenerateResponse
- **Method**: `POST` /response/generate
- **Description**: Generates robot response based on user input and conversation context
- **Request**:
  ```json
  {
    "session_id": "UUID",
    "input_id": "UUID",
    "input_context": {
      "text": "string",
      "intent": "string",
      "entities": "array",
      "modality": "speech|gesture|vision|multimodal"
    }
  }
  ```
- **Response**:
  ```json
  {
    "response_id": "UUID",
    "session_id": "UUID",
    "input_id": "UUID",
    "content": {
      "text": "string",
      "speech": "base64 audio (if applicable)",
      "gesture": "string (gesture command)"
    },
    "response_type": "text|speech|gesture|multimodal",
    "execution_status": "pending|executing|completed|failed"
  }
  ```

### Context Management Service

#### GetContext
- **Method**: `GET` /context/{session_id}
- **Description**: Retrieves current conversation context
- **Response**:
  ```json
  {
    "session_id": "UUID",
    "context_state": {
      "entities": "object",
      "references": "object",
      "intent_history": "array",
      "topic_stack": "array",
      "user_preferences": "object",
      "context_summary": "string"
    }
  }
  ```

#### UpdateContext
- **Method**: `PUT` /context/{session_id}
- **Description**: Updates conversation context with new information
- **Request**:
  ```json
  {
    "session_id": "UUID",
    "context_updates": {
      "entities": "object (partial update)",
      "references": "object (partial update)",
      "new_topic": "string (optional)",
      "user_preference": "object (optional)"
    }
  }
  ```

## Message Formats (ROS 2)

### UserInput Message
```yaml
input_id: string
session_id: string
timestamp: time
input_type: string
raw_data: string
processed_data: string
confidence: float
language: string
source_modality: string
```

### RobotResponse Message
```yaml
response_id: string
session_id: string
input_id: string
timestamp: time
response_type: string
content: string
intended_modality: string
execution_status: string
execution_time: float
```

### ConversationSession Message
```yaml
session_id: string
start_time: time
last_activity: time
context_state: string
user_id: string
active_modality: string
privacy_settings: string
status: string
```

## Error Handling

### Standard Error Response
```json
{
  "error": {
    "code": "string",
    "message": "string",
    "details": "object (optional)",
    "timestamp": "ISO 8601 datetime"
  }
}
```

### Common Error Codes
- `CONV_001`: Invalid session ID
- `CONV_002`: Session not active
- `CONV_003`: Input processing failed
- `CONV_004`: Response generation timeout
- `CONV_005`: Context retrieval failed
- `CONV_006`: Privacy restriction violation

## Performance Requirements
- Response generation: <1s for 95% of requests
- Speech recognition: <2s for 95% of requests
- Context retrieval: <100ms for 95% of requests
- Service availability: 99.5% uptime

## Security Requirements
- All API calls must include valid authentication tokens
- Sensitive data must be encrypted in transit and at rest
- Input validation required for all endpoints
- Rate limiting implemented per IP/user