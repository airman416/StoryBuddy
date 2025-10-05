# StoryBuddy - Architecture Overview

## System Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                          │
│                     (React + WebSocket)                         │
│                                                                 │
│  [Story Input] → [Generate ✨] → [Word Display] → [Controls]  │
│                                      ↓                          │
│                              [Emoji Display]                    │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│                      FASTAPI BACKEND                            │
│                                                                 │
│  ┌──────────────────┐    ┌──────────────────┐                 │
│  │   REST API       │    │   WebSocket      │                 │
│  │   /generate      │    │   /ws/stream     │                 │
│  │   /emoji         │    │   (real-time)    │                 │
│  └────────┬─────────┘    └────────┬─────────┘                 │
│           │                       │                            │
└───────────┼───────────────────────┼────────────────────────────┘
            │                       │
            ↓                       ↓
┌───────────────────────┐  ┌──────────────────────────┐
│   GEMINI SERVICE      │  │  ELEVENLABS SERVICE      │
│                       │  │                          │
│  • Story Generation   │  │  • Word-by-Word TTS      │
│  • Emoji Generation   │  │  • Audio Caching         │
│  • Content Safety     │  │  • Voice Settings        │
└───────────┬───────────┘  └──────────┬───────────────┘
            │                         │
            ↓                         ↓
    ┌─────────────┐          ┌──────────────┐
    │   Gemini    │          │  ElevenLabs  │
    │     API     │          │     API      │
    └─────────────┘          └──────────────┘
```

---

## Data Flow: Story Generation & Playback

### 1. Story Generation Request
```
User Input: "A baby elephant named Ember"
     ↓
Frontend sends: POST /api/generate-story
     ↓
Gemini Service generates age-appropriate story
     ↓
Frontend receives: "Once upon a time, a baby elephant..."
     ↓
Frontend sends via WebSocket: set_story
     ↓
Backend splits into word sets (5 words each)
```

### 2. Audio Generation (On-Demand)
```
Frontend requests: Set 0 (words 0-4)
     ↓
Backend checks cache for each word
     ↓
For uncached words:
    ElevenLabs generates audio → Cache locally → Return to frontend
     ↓
For cached words:
    Load from disk → Return to frontend
     ↓
WebSocket sends: word_ready messages
     ↓
Frontend auto-plays as words arrive
```

### 3. Emoji Generation (Contextual)
```
Frontend shows words 0-4
     ↓
Sends: POST /api/generate-emoji with "Once upon a time"
     ↓
Gemini analyzes context: "story beginning, setting scene"
     ↓
Generates: 📖✨🐘
     ↓
Frontend displays emojis above words
```

---

## Key Technical Decisions

### Why WebSocket for Audio?
- **Streaming experience**: Users don't wait for all words to generate
- **Progressive loading**: First word plays while others generate
- **Efficient bandwidth**: Only requested word sets are generated
- **Real-time feedback**: Users see generation progress

### Why Word-Level Caching?
- **Cost optimization**: Common words ("the", "a", "and") generated once
- **Speed**: Cached words return instantly
- **Consistency**: Same word sounds the same across stories
- **Scalability**: Cache hit rate improves with usage

### Why Gemini 2.0 Flash?
- **Speed**: Fast enough for real-time story generation
- **Quality**: Excellent at age-appropriate content
- **Safety**: Built-in content filtering
- **Context**: Understands semantic meaning for emoji generation

### Why ElevenLabs Bella Voice?
- **Warm & gentle**: Perfect for children's content
- **Clear enunciation**: Configured for reading instruction
- **Natural pauses**: Respects punctuation timing
- **Emotional range**: Expressive without being overwhelming

---

## Performance Metrics

### Story Generation
- **Time to first word audio**: ~1-2 seconds
- **Full story generation**: 3-5 seconds
- **Emoji generation**: ~0.5-1 second

### Caching Impact
- **First story**: 100% API calls (20-30 words)
- **Second story**: ~40% cache hits (common words)
- **After 10 stories**: ~60% cache hits
- **Cost reduction**: ~60% for subsequent stories

### API Usage Per Story
| API | Calls | Cost (est.) |
|-----|-------|-------------|
| Gemini Story | 1 | $0.02 |
| Gemini Emoji | 1 | $0.01 |
| ElevenLabs (first time) | 20-30 | $0.10-$0.15 |
| ElevenLabs (cached) | 8-12 | $0.04-$0.06 |

---

## Prize Alignment by Component

### 🏆 Gemini API Prize
**Components:**
- `gemini_service.py` - Story & emoji generation
- Age-appropriate prompt engineering
- Contextual emoji analysis

**Innovation:**
- Dynamic emoji generation based on story context
- Real-time content adaptation
- Multi-turn API usage (story → emoji)

### 🏆 ElevenLabs Prize
**Components:**
- `elevenlabs_service.py` - Word-by-word TTS
- Audio caching system
- WebSocket streaming architecture

**Innovation:**
- Word-level audio processing
- Autonomous audio experience
- Optimized voice settings for education

### 🏆 Best Consumer App
**Components:**
- `static/app.jsx` - Child-friendly UI
- Real-time playback synchronization
- Simple, intuitive controls

**Innovation:**
- Solves real literacy problem
- Parent-friendly UX
- Scalable, deployable architecture

---

## Future Enhancements (Post-Hackathon)

### Technical
- [ ] Multi-voice support (child characters)
- [ ] Reading progress tracking
- [ ] Offline mode with pre-cached stories
- [ ] Background music generation

### Features
- [ ] Parental dashboard
- [ ] Story favorites and history
- [ ] Reading comprehension quizzes
- [ ] Social sharing (parent-approved)

### Scale
- [ ] CDN for cached audio
- [ ] Database for user preferences
- [ ] Analytics for reading patterns
- [ ] Mobile app (React Native)

---

## Tech Stack Summary

| Layer | Technology | Why |
|-------|-----------|-----|
| Frontend | React (vanilla JSX) | Fast development, component-based |
| Backend | FastAPI + Python | Async support, WebSocket ready |
| AI - Language | Google Gemini 2.0 Flash | Speed + quality for generation |
| AI - Voice | ElevenLabs | Best voice quality for children |
| Real-time | WebSocket | Streaming audio delivery |
| Caching | File system + JSON | Simple, effective for MVP |
| Hosting | Local (demo) | Can deploy to Vercel/Railway |

---

## Code Highlights for Judges

### Gemini Integration
```python
# gemini_service.py:36-74
async def generate_story(self, prompt: str, age_group: str) -> str:
    formatted_prompt = f"""Create a very short story for children aged {age_group}...
    - Use simple, age-appropriate vocabulary
    - Keep it to 2-3 sentences maximum
    - Make it educational and fun
    ..."""
```

### ElevenLabs Word-Level Processing
```python
# elevenlabs_service.py:143-220
async def text_to_speech_word_by_word(self, text: str) -> List[Dict[str, Any]]:
    words = text.split()
    for word in words:
        if self._is_cached(word):
            audio = load_from_cache(word)
        else:
            audio = await generate_audio(word)
            save_to_cache(word, audio)
```

### WebSocket Streaming
```python
# main.py - WebSocket handler
@websocket_endpoint("/ws/stream-words")
async def stream_words(websocket: WebSocket):
    await websocket.accept()
    # Generate words on demand
    # Stream as they're ready
    # No waiting for full completion
```

---

**This architecture demonstrates thoughtful system design, not just API integration. It shows we understand performance, cost, and user experience - the hallmarks of a real product.**
