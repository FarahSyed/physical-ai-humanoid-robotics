# Data Model: Conversational Robotics

## Overview
This document defines the data structures and relationships for the Conversational Robotics feature, focusing on conversation management, user input processing, and response generation in multi-modal human-robot interaction.

## Core Entities

### ConversationSession
Represents an ongoing dialogue between human and robot with maintained context information.

**Fields:**
- `session_id`: UUID (primary key) - Unique identifier for the conversation session
- `start_time`: DateTime - Timestamp when the conversation started
- `last_activity`: DateTime - Timestamp of the most recent interaction
- `context_state`: JSON - Serialized conversation context and history
- `user_id`: String (optional) - Identifier for the user (if known)
- `active_modality`: String - Current primary input modality ('speech', 'gesture', 'vision', 'multimodal')
- `privacy_settings`: PrivacySettings (embedded) - User-defined privacy preferences for this session
- `status`: String - Session status ('active', 'paused', 'ended')

**Relationships:**
- One-to-many with UserInput (conversation contains multiple inputs)
- One-to-many with RobotResponse (conversation contains multiple responses)

**Validation Rules:**
- `session_id` must be unique
- `start_time` must be before or equal to `last_activity`
- `active_modality` must be one of the allowed values
- `status` must be one of the allowed values

### UserInput
Captures speech, gesture, and visual data that serves as input to the conversational system.

**Fields:**
- `input_id`: UUID (primary key) - Unique identifier for the input
- `session_id`: UUID - Foreign key linking to ConversationSession
- `timestamp`: DateTime - Time when input was received
- `input_type`: String - Type of input ('speech', 'gesture', 'vision', 'multimodal')
- `raw_data`: String/JSON - Raw input data (transcript, gesture coordinates, etc.)
- `processed_data`: JSON - Processed interpretation of the input
- `confidence`: Float - Confidence level of input processing (0.0-1.0)
- `language`: String - Language of speech input (if applicable)
- `source_modality`: String - Original modality of input ('audio', 'visual', 'tactile')

**Relationships:**
- Many-to-one with ConversationSession (input belongs to a session)
- One-to-many with InputIntent (input may have multiple interpretations)

**Validation Rules:**
- `confidence` must be between 0.0 and 1.0
- `input_type` must be one of the allowed values
- `session_id` must reference an existing ConversationSession

### RobotResponse
Generated speech, gesture, and visual output from the robot in response to user input.

**Fields:**
- `response_id`: UUID (primary key) - Unique identifier for the response
- `session_id`: UUID - Foreign key linking to ConversationSession
- `input_id`: UUID - Foreign key linking to the triggering UserInput
- `timestamp`: DateTime - Time when response was generated
- `response_type`: String - Type of response ('text', 'gesture', 'multimodal')
- `content`: String/JSON - The actual response content
- `intended_modality`: String - Modalities used in the response ('speech', 'gesture', 'visual')
- `execution_status`: String - Status of response execution ('pending', 'executing', 'completed', 'failed')
- `execution_time`: Float - Time taken to execute the response (in seconds)

**Relationships:**
- Many-to-one with ConversationSession (response belongs to a session)
- Many-to-one with UserInput (response is in response to an input)

**Validation Rules:**
- `response_type` must be one of the allowed values
- `session_id` must reference an existing ConversationSession
- `input_id` must reference an existing UserInput

### ContextState
Information maintained across conversation turns to enable coherent dialogue, including references and conversation history.

**Fields:**
- `state_id`: UUID (primary key) - Unique identifier for the context state
- `session_id`: UUID - Foreign key linking to ConversationSession
- `entities`: JSON - Named entities mentioned in the conversation
- `references`: JSON - References to previous parts of the conversation
- `intent_history`: Array - Recent user intents in chronological order
- `topic_stack`: Array - Current topics being discussed
- `user_preferences`: JSON - Preferences inferred or explicitly set by user
- `context_summary`: String - Summary of the current conversation context

**Relationships:**
- One-to-one with ConversationSession (each session has one context state)

**Validation Rules:**
- `session_id` must reference an existing ConversationSession

### PrivacySettings
User-defined preferences for data retention and privacy controls for conversation data.

**Fields:**
- `settings_id`: UUID (primary key) - Unique identifier for the settings
- `user_id`: String - Identifier for the user (can be anonymous)
- `data_retention_days`: Integer - Number of days to retain conversation data (0 for delete immediately)
- `record_audio`: Boolean - Whether to record audio input
- `record_video`: Boolean - Whether to record visual input
- `transcript_storage`: Boolean - Whether to store conversation transcripts
- `model_training_consent`: Boolean - Whether user consents to data use for model improvement
- `last_updated`: DateTime - Time when settings were last modified

**Relationships:**
- One-to-many with ConversationSession (settings can apply to multiple sessions)

**Validation Rules:**
- `data_retention_days` must be >= 0
- If `data_retention_days` is 0, `record_audio` and `record_video` should be false

### InputIntent
Represents the interpreted intent from user input, used for natural language understanding.

**Fields:**
- `intent_id`: UUID (primary key) - Unique identifier for the intent
- `input_id`: UUID - Foreign key linking to UserInput
- `intent_type`: String - Type of intent ('question', 'command', 'statement', 'greeting', 'farewell')
- `confidence`: Float - Confidence in intent classification (0.0-1.0)
- `parameters`: JSON - Parameters extracted from the input
- `resolved_entities`: JSON - Entities extracted and resolved from the input
- `fallback_triggered`: Boolean - Whether a fallback response was needed

**Relationships:**
- Many-to-one with UserInput (intent is derived from input)

**Validation Rules:**
- `confidence` must be between 0.0 and 1.0
- `intent_type` must be one of the allowed values

## State Transitions

### ConversationSession States
- `active` → `paused`: When user steps away or indicates pause
- `paused` → `active`: When user resumes interaction
- `active` → `ended`: When conversation naturally ends or timeout occurs
- `paused` → `ended`: When timeout occurs in paused state

### RobotResponse Execution States
- `pending` → `executing`: When response generation begins
- `executing` → `completed`: When response execution finishes successfully
- `executing` → `failed`: When response execution encounters an error

## Relationships Summary

```
ConversationSession (1) ←→ (Many) UserInput
ConversationSession (1) ←→ (Many) RobotResponse
ConversationSession (1) ←→ (1) ContextState
PrivacySettings (1) ←→ (Many) ConversationSession
UserInput (1) ←→ (Many) InputIntent
```

## Indexing Strategy

- Index on `ConversationSession.session_id` (primary)
- Index on `UserInput.session_id` and `UserInput.timestamp` (for chronological retrieval)
- Index on `RobotResponse.session_id` and `RobotResponse.timestamp` (for response tracking)
- Index on `PrivacySettings.user_id` (for user-specific privacy lookups)