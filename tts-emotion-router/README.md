# TTS Emotion Router

Detect emotion in bot replies and automatically route TTS synthesis to matching voices and speeds. Supports any OpenAI-compatible TTS API.

## Features

- **Emotion Detection**: Analyze bot replies using LLM or keyword-based fallback
- **Voice Routing**: Map emotions (happy, sad, angry, excited, neutral) to different TTS voices
- **Speed Control**: Automatically adjust speech speed based on emotion
- **Flexible TTS Backend**: Works with any OpenAI-compatible TTS API (SiliconFlow, Azure, etc.)

## Configuration

| Setting | Description | Required |
|---------|-------------|----------|
| TTS API Base URL | OpenAI-compatible TTS endpoint | ✅ |
| TTS API Key | API authentication key | ✅ |
| Default Voice | Voice ID for neutral emotion | ✅ |
| Happy/Sad/Angry/Excited Voice | Voice IDs for each emotion | ❌ |
| TTS Model | Model name (default: tts-1) | ❌ |
| Emotion Detection Model | LLM for emotion classification | ❌ |
| Speed Multiplier (Excited) | Speech speed for excited emotion | ❌ |

## How It Works

1. Bot sends a text reply
2. Plugin detects the emotion of the reply text
3. Selects the matching voice and speed
4. Synthesizes speech via TTS API
5. Sends the audio as a voice message

## Supported Emotions

| Emotion | Default Speed | Example Triggers |
|---------|--------------|------------------|
| 😊 Happy | 1.0x | 哈哈, 太好了, awesome |
| 😢 Sad | 0.9x | 难过, 遗憾, unfortunately |
| 😡 Angry | 1.0x | 生气, 烦, damn |
| 🔥 Excited | 1.15x | 太棒了, amazing, wow |
| 😐 Neutral | 1.0x | (default) |
