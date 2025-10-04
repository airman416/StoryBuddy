# StoryBuddy Testing Guide

This document explains how to test the refactored StoryBuddy application with its separated services.

## Prerequisites

1. Make sure you have your API keys set in a `.env` file:
   ```
   GEMINI_API_KEY=your_gemini_api_key_here
   ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Service Architecture

The application has been refactored into three main components:

1. **GeminiService** (`gemini_service.py`) - Handles all Gemini API interactions
2. **ElevenLabsService** (`elevenlabs_service.py`) - Handles all ElevenLabs API interactions  
3. **Main Application** (`main.py`) - Orchestrates the services and provides FastAPI endpoints

## Manual Testing

### 1. Test GeminiService Independently

```bash
python test_gemini_service.py
```

This will test:
- Service configuration
- Story generation with different age groups
- Reading evaluation with correct and incorrect text
- Error handling

### 2. Test ElevenLabsService Independently

```bash
python test_elevenlabs_service.py
```

This will test:
- Service configuration
- Basic text-to-speech conversion
- Different voice models
- Custom voice settings
- Voice ID changes
- Long text handling

**Note**: This test generates several audio files that you can play to verify quality.

### 3. Test Main Application

First, start the server:
```bash
python main.py
```

Then in another terminal, run:
```bash
python test_main_app.py
```

This will test:
- Health endpoint
- Story generation API
- Text-to-speech API
- Reading evaluation API

## Service Benefits

### Separation of Concerns
- Each service handles only its specific API
- Main application focuses on orchestration
- Easier to maintain and debug

### Testability
- Services can be tested independently
- Mock services can be easily created for unit tests
- Clear interfaces between components

### Reusability
- Services can be used in other applications
- Easy to swap out implementations
- Clear API contracts

### Error Handling
- Centralized error handling in each service
- Consistent error messages
- Graceful fallbacks

## File Structure

```
StoryBuddy/
├── main.py                 # FastAPI application (orchestrator)
├── gemini_service.py       # Gemini API service
├── elevenlabs_service.py   # ElevenLabs API service
├── test_gemini_service.py  # Gemini service tests
├── test_elevenlabs_service.py # ElevenLabs service tests
├── test_main_app.py        # Main application tests
├── static/                 # Frontend files
└── requirements.txt        # Dependencies
```

## Running the Application

1. Set up your `.env` file with API keys
2. Install dependencies: `pip install -r requirements.txt`
3. Run the application: `python main.py`
4. Visit `http://localhost:8000` in your browser

## Troubleshooting

- **API Key Errors**: Make sure your `.env` file is in the project root and contains valid API keys
- **Import Errors**: Ensure all service files are in the same directory as `main.py`
- **Audio Issues**: Check that ElevenLabs API key has sufficient credits
- **Story Generation Issues**: Verify Gemini API key is valid and has access to the model
