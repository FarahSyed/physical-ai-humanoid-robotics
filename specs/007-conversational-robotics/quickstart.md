# Quickstart Guide: Conversational Robotics

## Overview
This guide provides a step-by-step introduction to setting up and using the conversational AI system for humanoid robots. The system integrates cloud-based GPT APIs for natural language processing, real-time speech recognition, and multi-modal interaction capabilities.

## Prerequisites

### System Requirements
- Ubuntu 22.04 LTS
- ROS 2 Humble Hawksbill
- Python 3.10 or higher
- NVIDIA Jetson Orin Nano or equivalent development platform
- Internet connection for cloud API access
- Microphone and camera for multi-modal input

### Software Dependencies
```bash
# ROS 2 Humble installation
sudo apt update
sudo apt install ros-humble-desktop

# Python dependencies
pip install openai azure-cognitiveservices-speech speech-recognition pocketsphinx opencv-python mediapipe
```

### API Keys and Configuration
- OpenAI API key (for GPT integration)
- Azure Cognitive Services key (alternative GPT provider)
- Google Cloud credentials (for speech-to-text if using)

## Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd physical-ai-humanoid-robotics
```

### 2. Install ROS 2 Dependencies
```bash
cd src
rosdep install --from-paths . --ignore-src -r -y
```

### 3. Build the Workspace
```bash
cd ..
colcon build --packages-select conversational_ai
source install/setup.bash
```

### 4. Configure API Keys
Create a `.env` file in the project root with your API credentials:
```env
OPENAI_API_KEY=your_openai_api_key_here
AZURE_OPENAI_KEY=your_azure_openai_key_here
AZURE_OPENAI_ENDPOINT=your_azure_openai_endpoint_here
GOOGLE_APPLICATION_CREDENTIALS=path_to_google_credentials.json
```

## Basic Usage

### 1. Launch the Conversational System
```bash
# Launch all conversational AI nodes
ros2 launch conversational_ai conversational_ai.launch.py
```

### 2. Test Speech Recognition
The system will automatically begin listening for speech input. Speak naturally to the robot:
- The robot will provide visual feedback when listening
- Response time should be under 3 seconds
- Verify that speech is being recognized by checking the console output

### 3. Test Multi-Modal Interaction
Combine speech with gestures:
- Point to an object while asking about it
- Use expressive gestures during conversation
- Observe how the robot integrates visual and audio input

### 4. Check Conversation State
Monitor the conversation context:
```bash
# View current conversation session data
ros2 topic echo /conversation_state
```

## Configuration Options

### Privacy Settings
Configure data retention and privacy preferences:
```bash
# Set privacy parameters via ROS parameters
ros2 param set /conversation_manager record_audio false
ros2 param set /conversation_manager data_retention_days 30
```

### Modality Preferences
Adjust primary input modality:
```bash
# Switch between input modalities
ros2 param set /conversation_manager active_modality speech      # Speech only
ros2 param set /conversation_manager active_modality multimodal  # Multi-modal
```

## Troubleshooting

### Common Issues

1. **Speech Recognition Not Working**
   - Check microphone permissions and connectivity
   - Verify audio input levels: `alsamixer`
   - Ensure API keys are properly configured

2. **High Latency (>3s)**
   - Check internet connection speed
   - Verify cloud API endpoint availability
   - Monitor system resource usage

3. **Gesture Recognition Issues**
   - Ensure camera is properly positioned
   - Check lighting conditions (avoid backlit scenarios)
   - Verify OpenCV and MediaPipe installations

### Performance Monitoring
Monitor system performance:
```bash
# Check node performance
ros2 run rqt_plot rqt_plot

# Monitor CPU and memory usage
htop
```

## Next Steps

1. **Customize Responses**: Modify the response templates in `src/conversational_ai/config/responses.yaml`
2. **Add Custom Intents**: Extend the NLP processor with domain-specific intents
3. **Integrate with Robot Actions**: Connect conversation outcomes to robot movement and behavior
4. **Configure Privacy Settings**: Set up user-specific privacy preferences for production use

## Example Commands

### Starting a conversation session:
```bash
ros2 service call /start_conversation conversational_ai_interfaces/srv/StartConversation "user_id: 'test_user'"
```

### Sending text input (for testing):
```bash
ros2 topic pub /user_input conversational_ai_interfaces/msg/UserInput "input_type: 'text' content: 'Hello, robot!'"
```

### Checking system status:
```bash
ros2 lifecycle list
```