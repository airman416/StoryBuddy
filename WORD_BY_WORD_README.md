# Word-by-Word TTS System

## Overview
This system generates individual MP3 files for each word in a story, ensuring very slow, clear enunciation for learning to read.

## Features
- **Individual MP3 files** for each word
- **Intelligent caching** to avoid excessive API calls
- **Clear enunciation** with optimized voice settings
- **Configuration tracking** of cached words
- **Debug mode support** for testing without API keys

## How It Works

### 1. Word Processing
- Splits story text into individual words
- Cleans words (removes punctuation for filenames)
- Generates unique cache paths for each word

### 2. Audio Generation
- Creates separate API calls for each word
- Uses optimized voice settings for clear enunciation:
  - Stability: 0.95 (very consistent)
  - Similarity Boost: 0.9 (clear pronunciation)
  - Style: 0.0 (no exaggeration)
- Adds small delays between API calls

### 3. Caching System
- **Cache Directory**: `audio_cache/words/`
- **Config File**: `audio_cache/word_cache.json`
- **File Naming**: `{clean_word}.mp3`
- **Automatic cleanup** of audio blobs after playback

### 4. Frontend Integration
- Shows only current word being spoken
- Plays words sequentially with proper timing
- Visual highlighting for each word
- Pause/resume functionality

## API Endpoints

### `/api/text-to-speech-word-by-word`
```json
{
  "text": "The cat sat."
}
```

**Response:**
```json
{
  "word_audio_list": [
    {
      "word": "The",
      "audio": "base64_encoded_mp3_data",
      "index": 0,
      "cached": false
    },
    {
      "word": "cat",
      "audio": "base64_encoded_mp3_data", 
      "index": 1,
      "cached": true
    },
    {
      "word": "sat.",
      "audio": "base64_encoded_mp3_data",
      "index": 2,
      "cached": false
    }
  ],
  "total_words": 3
}
```

## File Structure
```
audio_cache/
├── words/
│   ├── the.mp3
│   ├── cat.mp3
│   ├── sat.mp3
│   └── ...
└── word_cache.json
```

## Configuration File Format
```json
{
  "The": "/path/to/audio_cache/words/the.mp3",
  "cat": "/path/to/audio_cache/words/cat.mp3",
  "sat.": "/path/to/audio_cache/words/sat.mp3"
}
```

## Testing
Run the test script to verify functionality:
```bash
python test_word_by_word.py
```

## Benefits
- **Very slow speech** - Each word is spoken individually
- **Clear enunciation** - Optimized voice settings
- **Efficient caching** - Avoids repeated API calls
- **Better learning** - Focus on one word at a time
- **Cost effective** - Reuses cached words across stories

## Debug Mode
When `DEBUG=true`:
- Uses cached files when available
- Saves new audio to cache
- Logs detailed information
- Works without API key (uses cached files only)

## Voice Settings for Clear Enunciation
- **Stability**: 0.95 (very high for consistent speech)
- **Similarity Boost**: 0.9 (high for clear pronunciation)  
- **Style**: 0.0 (no exaggeration for clear enunciation)
- **Speaker Boost**: Enabled for clarity
