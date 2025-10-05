from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel
import logging
import base64
import json
import asyncio
from dotenv import load_dotenv
from gemini_service import GeminiService
from elevenlabs_service import ElevenLabsService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Initialize services
gemini_service = GeminiService()
elevenlabs_service = ElevenLabsService()

# Log service configuration status
logger.info(f"Gemini service configured: {gemini_service.is_configured()}")
logger.info(f"ElevenLabs service configured: {elevenlabs_service.is_configured()}")

app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Pydantic models
class StoryRequest(BaseModel):
    prompt: str
    age_group: str

class TTSRequest(BaseModel):
    text: str

class ReadingEvalRequest(BaseModel):
    original_story: str
    spoken_text: str

class EmojiRequest(BaseModel):
    words: str

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "gemini_configured": gemini_service.is_configured(),
        "elevenlabs_configured": elevenlabs_service.is_configured()
    }

@app.get("/", response_class=HTMLResponse)
async def serve_app():
    """Serve the main HTML application"""
    with open("static/index.html", "r") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)

@app.post("/api/generate-story")
async def generate_story(request: StoryRequest):
    """Generate a story using Gemini API"""
    logger.info(f"Received story generation request: prompt='{request.prompt}', age_group='{request.age_group}'")
    
    try:
        story = await gemini_service.generate_story(request.prompt, request.age_group)
        return {"story": story}
    except Exception as e:
        logger.error(f"Error generating story: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/text-to-speech")
async def text_to_speech(request: TTSRequest):
    """Convert text to speech using ElevenLabs API"""
    logger.info(f"Received TTS request for text: {request.text[:100]}...")
    
    try:
        audio_data = await elevenlabs_service.text_to_speech(request.text)
        return audio_data
    except Exception as e:
        logger.error(f"Error converting text to speech: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/text-to-speech-stream")
async def text_to_speech_stream(request: TTSRequest):
    """Convert text to speech using ElevenLabs API with streaming"""
    logger.info(f"Received streaming TTS request for text: {request.text[:100]}...")
    
    try:
        async def generate_audio():
            async for chunk in elevenlabs_service.text_to_speech_streaming(request.text):
                yield chunk
        
        return StreamingResponse(
            generate_audio(),
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": "attachment; filename=story.mp3",
                "Cache-Control": "no-cache"
            }
        )
    except Exception as e:
        logger.error(f"Error converting text to speech with streaming: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/text-to-speech-timestamps")
async def text_to_speech_timestamps(request: TTSRequest):
    """Convert text to speech with word-level timing data using ElevenLabs API"""
    logger.info(f"Received TTS with timestamps request for text: {request.text[:100]}...")
    
    try:
        result = await elevenlabs_service.text_to_speech_with_timestamps(request.text)
        return result
    except Exception as e:
        logger.error(f"Error converting text to speech with timestamps: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/text-to-speech-word-by-word")
async def text_to_speech_word_by_word(request: TTSRequest):
    """Convert text to speech word by word with individual MP3 files"""
    logger.info(f"Received word-by-word TTS request for text: {request.text[:100]}...")
    
    try:
        word_audio_list = await elevenlabs_service.text_to_speech_word_by_word(request.text)
        
        # Convert audio data to base64 for frontend
        result = []
        for word_data in word_audio_list:
            # Handle emojis (no audio) and regular words
            if word_data.get("is_emoji", False) or word_data["audio"] is None:
                result.append({
                    "word": word_data["word"],
                    "audio": None,  # No audio for emojis
                    "index": word_data["index"],
                    "cached": word_data["cached"],
                    "is_emoji": True
                })
            else:
                audio_base64 = base64.b64encode(word_data["audio"]).decode('utf-8')
                result.append({
                    "word": word_data["word"],
                    "audio": audio_base64,
                    "index": word_data["index"],
                    "cached": word_data["cached"],
                    "is_emoji": False
                })
        
        return {
            "word_audio_list": result,
            "total_words": len(result)
        }
    except Exception as e:
        logger.error(f"Error converting text to speech word by word: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/evaluate-reading")
async def evaluate_reading(request: ReadingEvalRequest):
    """Evaluate child's reading using Gemini API"""
    try:
        feedback = await gemini_service.evaluate_reading(request.original_story, request.spoken_text)
        return {"feedback": feedback}
    except Exception as e:
        logger.error(f"Error evaluating reading: {str(e)}")
        # Fallback to positive message if API fails
        return {"feedback": "Great job reading! Keep practicing! 🌟"}

@app.post("/api/generate-emoji")
async def generate_emoji(request: EmojiRequest):
    """Generate an emoji for the given words"""
    logger.info(f"Received emoji generation request for: {request.words}")
    
    try:
        emoji = await gemini_service.generate_emoji_for_words(request.words)
        return {"emoji": emoji}
    except Exception as e:
        logger.error(f"Error generating emoji: {str(e)}")
        return {"emoji": "📖"}

@app.websocket("/ws/stream-words")
async def websocket_stream_words(websocket: WebSocket):
    """WebSocket endpoint for streaming word-by-word audio generation on-demand"""
    await websocket.accept()
    logger.info("WebSocket connection established for streaming words")
    
    story_words = []
    
    try:
        while True:
            # Wait for client to send request
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "set_story":
                # Store the story words for on-demand generation
                story_text = message.get("text", "")
                if not story_text:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": "No story text provided"
                    }))
                    continue
                
                story_words = story_text.split()
                logger.info(f"Story set with {len(story_words)} words")
                
                # Send confirmation
                await websocket.send_text(json.dumps({
                    "type": "story_set",
                    "total_words": len(story_words)
                }))
                
            elif message.get("type") == "generate_set":
                # Generate audio for a specific set of words (5 words)
                set_index = message.get("set_index", 0)
                start_index = set_index * 5
                end_index = min(start_index + 5, len(story_words))
                
                if start_index >= len(story_words):
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": f"Set index {set_index} out of bounds"
                    }))
                    continue
                
                logger.info(f"Generating set {set_index} (words {start_index}-{end_index-1})")
                
                # Send start message
                await websocket.send_text(json.dumps({
                    "type": "set_generation_started",
                    "set_index": set_index,
                    "start_index": start_index,
                    "end_index": end_index
                }))
                
                # Generate words for this set
                for i in range(start_index, end_index):
                    word = story_words[i]
                    try:
                        # Check if word is emoji (skip audio generation)
                        if elevenlabs_service._is_emoji(word):
                            await websocket.send_text(json.dumps({
                                "type": "word_ready",
                                "word": word,
                                "index": i,
                                "audio": None,
                                "is_emoji": True,
                                "cached": False
                            }))
                            continue
                        
                        # Check cache first
                        cached_audio = None
                        is_cached = False
                        if elevenlabs_service._is_word_cached(word):
                            cached_audio = elevenlabs_service._load_word_from_cache(word)
                            is_cached = True
                        
                        if cached_audio:
                            # Send cached word
                            audio_base64 = base64.b64encode(cached_audio).decode('utf-8')
                            await websocket.send_text(json.dumps({
                                "type": "word_ready",
                                "word": word,
                                "index": i,
                                "audio": audio_base64,
                                "is_emoji": False,
                                "cached": True
                            }))
                        else:
                            # Generate new audio for word
                            audio_data = await elevenlabs_service._generate_word_audio(word)
                            
                            # Save to cache if in debug mode
                            if elevenlabs_service.debug_mode:
                                elevenlabs_service._save_word_to_cache(word, audio_data)
                            
                            # Convert to base64 and send
                            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
                            await websocket.send_text(json.dumps({
                                "type": "word_ready",
                                "word": word,
                                "index": i,
                                "audio": audio_base64,
                                "is_emoji": False,
                                "cached": False
                            }))
                        
                        # Small delay between words to prevent overwhelming the client
                        await asyncio.sleep(0.05)
                        
                    except Exception as e:
                        logger.error(f"Error generating word '{word}': {str(e)}")
                        # Send error word but continue
                        await websocket.send_text(json.dumps({
                            "type": "word_error",
                            "word": word,
                            "index": i,
                            "error": str(e)
                        }))
                
                # Send completion message for this set
                await websocket.send_text(json.dumps({
                    "type": "set_generation_complete",
                    "set_index": set_index,
                    "start_index": start_index,
                    "end_index": end_index
                }))
                
            elif message.get("type") == "ping":
                # Handle ping for connection health
                await websocket.send_text(json.dumps({
                    "type": "pong"
                }))
                
    except WebSocketDisconnect:
        logger.info("WebSocket connection disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        try:
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": f"Server error: {str(e)}"
            }))
        except:
            pass

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting StoryBuddy server...")
    logger.info(f"Server will be available at: http://0.0.0.0:8000")
    logger.info(f"Health check available at: http://0.0.0.0:8000/health")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")