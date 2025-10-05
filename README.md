# StoryBuddy 📚✨

An interactive storytelling app for young children that generates personalized stories and reads them aloud word-by-word, helping kids learn to read while having fun.

## Screenshot

![StoryBuddy Screenshot](main.png)
*Coming soon*

## Project Intent

StoryBuddy creates an engaging reading experience for children by:
- Generating age-appropriate stories based on simple prompts
- Reading stories aloud with word-by-word audio highlighting
- Providing visual feedback with emojis and animations
- Making reading practice fun and interactive

Built for a hackathon as a minimum presentable product to demonstrate AI-powered educational tools for early childhood literacy.

## Technical Stack

**Backend:**
- FastAPI (Python)
- WebSocket for real-time audio streaming

**Frontend:**
- React (vanilla JSX)
- CSS3 for animations and styling

**APIs:**
- Google Gemini API - Story generation and reading evaluation
- ElevenLabs API - Text-to-speech with word-level audio

**Other:**
- Audio caching for improved performance
- Word-by-word playback synchronization

## Quick Start

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
- `GEMINI_API_KEY` - Your Google Gemini API key
- `ELEVENLABS_API_KEY` - Your ElevenLabs API key

3. Run the server:
```bash
python main.py
```

4. Open http://localhost:8000 in your browser

---

*Made with ❤️ for young readers*
