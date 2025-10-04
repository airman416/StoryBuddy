import httpx
import logging
import os
import asyncio
import hashlib
import base64
import json
from typing import Optional, Dict, Any, AsyncGenerator, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class ElevenLabsService:
    """Service class for handling ElevenLabs API interactions"""
    
    def __init__(self, api_key: Optional[str] = None, voice_id: Optional[str] = None):
        """
        Initialize ElevenLabsService
        
        Args:
            api_key: ElevenLabs API key. If not provided, will load from environment
            voice_id: Voice ID to use. If not provided, uses default Adam voice
        """
        self.api_key = api_key or os.getenv('ELEVENLABS_API_KEY')
        self.voice_id = voice_id or 'JBFqnCBsd6RMkjVDRZzb'  # Adam voice from ElevenLabs docs
        self.api_url = 'https://api.elevenlabs.io/v1/text-to-speech'
        self.streaming_url = 'https://api.elevenlabs.io/v1/text-to-speech'
        self.logger = logging.getLogger(__name__)
        self.debug_mode = os.getenv('DEBUG', 'false').lower() == 'true'
        self.cache_dir = 'audio_cache'
        self.word_cache_dir = os.path.join(self.cache_dir, 'words')
        self.config_file = os.path.join(self.cache_dir, 'word_cache.json')
        
        # Create cache directories if they don't exist
        if self.debug_mode:
            os.makedirs(self.cache_dir, exist_ok=True)
            os.makedirs(self.word_cache_dir, exist_ok=True)
        
        if not self.api_key:
            self.logger.warning("ELEVENLABS_API_KEY is not set in environment variables")
    
    def is_configured(self) -> bool:
        """Check if the service is properly configured"""
        return bool(self.api_key) or self.debug_mode
    
    def _get_cache_path(self, text: str) -> str:
        """Get cache file path for a given text"""
        text_hash = hashlib.md5(text.encode()).hexdigest()
        return os.path.join(self.cache_dir, f"{text_hash}.mp3")
    
    def _save_to_cache(self, text: str, audio_data: bytes) -> None:
        """Save audio data to cache"""
        if not self.debug_mode:
            return
        
        cache_path = self._get_cache_path(text)
        try:
            with open(cache_path, 'wb') as f:
                f.write(audio_data)
            self.logger.info(f"Saved audio to cache: {cache_path}")
        except Exception as e:
            self.logger.error(f"Failed to save audio to cache: {str(e)}")
    
    def _load_from_cache(self, text: str) -> Optional[bytes]:
        """Load audio data from cache"""
        if not self.debug_mode:
            return None
        
        cache_path = self._get_cache_path(text)
        try:
            if os.path.exists(cache_path):
                with open(cache_path, 'rb') as f:
                    audio_data = f.read()
                self.logger.info(f"Loaded audio from cache: {cache_path}")
                return audio_data
        except Exception as e:
            self.logger.error(f"Failed to load audio from cache: {str(e)}")
        
        return None
    
    def _load_word_cache_config(self) -> Dict[str, str]:
        """Load word cache configuration from JSON file"""
        if not os.path.exists(self.config_file):
            return {}
        
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to load word cache config: {str(e)}")
            return {}
    
    def _save_word_cache_config(self, config: Dict[str, str]) -> None:
        """Save word cache configuration to JSON file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save word cache config: {str(e)}")
    
    def _get_word_cache_path(self, word: str) -> str:
        """Get cache file path for a specific word"""
        # Clean word for filename (remove punctuation, lowercase)
        clean_word = ''.join(c.lower() for c in word if c.isalnum())
        return os.path.join(self.word_cache_dir, f"{clean_word}.mp3")
    
    def _is_word_cached(self, word: str) -> bool:
        """Check if a word is already cached"""
        cache_path = self._get_word_cache_path(word)
        return os.path.exists(cache_path)
    
    def _save_word_to_cache(self, word: str, audio_data: bytes) -> None:
        """Save individual word audio to cache"""
        cache_path = self._get_word_cache_path(word)
        try:
            with open(cache_path, 'wb') as f:
                f.write(audio_data)
            
            # Update config
            config = self._load_word_cache_config()
            config[word] = cache_path
            self._save_word_cache_config(config)
            
            self.logger.info(f"Saved word '{word}' to cache: {cache_path}")
        except Exception as e:
            self.logger.error(f"Failed to save word '{word}' to cache: {str(e)}")
    
    def _load_word_from_cache(self, word: str) -> Optional[bytes]:
        """Load individual word audio from cache"""
        cache_path = self._get_word_cache_path(word)
        try:
            if os.path.exists(cache_path):
                with open(cache_path, 'rb') as f:
                    audio_data = f.read()
                self.logger.info(f"Loaded word '{word}' from cache: {cache_path}")
                return audio_data
        except Exception as e:
            self.logger.error(f"Failed to load word '{word}' from cache: {str(e)}")
        
        return None
    
    async def text_to_speech_word_by_word(self, text: str, model_id: str = "eleven_multilingual_v2") -> List[Dict[str, Any]]:
        """
        Convert text to speech word by word, creating individual MP3 files for each word
        Skips emojis and only generates audio for actual words
        
        Args:
            text: Text to convert to speech
            model_id: Model to use for TTS
            
        Returns:
            List of dictionaries containing word, audio data, and timing info
            
        Raises:
            Exception: If API call fails
        """
        if not self.is_configured():
            raise Exception("ElevenLabs API key not configured. Please set ELEVENLABS_API_KEY in your .env file.")
        
        # Split text into words and filter out emojis
        words = text.split()
        word_audio_list = []
        
        self.logger.info(f"Generating word-by-word audio for {len(words)} words (filtering emojis)")
        
        for i, word in enumerate(words):
            # Check if word is an emoji (contains only emoji characters)
            if self._is_emoji(word):
                self.logger.info(f"Skipping emoji at index {i}: '{word}'")
                word_audio_list.append({
                    "word": word,
                    "audio": None,  # No audio for emojis
                    "index": i,
                    "cached": False,
                    "is_emoji": True
                })
                continue
                
            self.logger.info(f"Processing word {i+1}/{len(words)}: '{word}'")
            
            # Check if word is already cached
            if self._is_word_cached(word):
                audio_data = self._load_word_from_cache(word)
                if audio_data:
                    word_audio_list.append({
                        "word": word,
                        "audio": audio_data,
                        "index": i,
                        "cached": True,
                        "is_emoji": False
                    })
                    continue
            
            # Generate audio for this word
            try:
                audio_data = await self._generate_word_audio(word, model_id)
                
                # Save to cache
                if self.debug_mode:
                    self._save_word_to_cache(word, audio_data)
                
                word_audio_list.append({
                    "word": word,
                    "audio": audio_data,
                    "index": i,
                    "cached": False,
                    "is_emoji": False
                })
                
                # Add a small delay between API calls to be respectful
                await asyncio.sleep(0.1)
                
            except Exception as e:
                self.logger.error(f"Failed to generate audio for word '{word}': {str(e)}")
                # Continue with other words even if one fails
                continue
        
        self.logger.info(f"Successfully generated word-by-word audio for {len(word_audio_list)} words")
        return word_audio_list
    
    def _is_emoji(self, text: str) -> bool:
        """
        Check if a string contains only emoji characters
        
        Args:
            text: String to check
            
        Returns:
            True if the string is only emojis, False otherwise
        """
        import re
        
        # Remove whitespace and check if remaining characters are emojis
        clean_text = text.strip()
        if not clean_text:
            return False
            
        # Unicode ranges for emojis
        emoji_pattern = re.compile(
            r"[\U0001F600-\U0001F64F"  # emoticons
            r"\U0001F300-\U0001F5FF"  # symbols & pictographs
            r"\U0001F680-\U0001F6FF"  # transport & map symbols
            r"\U0001F1E0-\U0001F1FF"  # flags (iOS)
            r"\U00002600-\U000026FF"  # miscellaneous symbols
            r"\U00002700-\U000027BF"  # dingbats
            r"\U0001F900-\U0001F9FF"  # supplemental symbols
            r"\U0001FA70-\U0001FAFF"  # symbols and pictographs extended-A
            r"]+$"
        )
        
        return bool(emoji_pattern.match(clean_text))
    
    async def _generate_word_audio(self, word: str, model_id: str = "eleven_multilingual_v2") -> bytes:
        """Generate audio for a single word with very slow, clear enunciation and elongation"""
        # Clean the word for better pronunciation
        clean_word = word.strip('.,!?;:"()[]{}')
        
        # Add elongation and pauses for punctuation
        if word.endswith(('.', '!', '?')):
            # Elongate the word and add a pause
            text_to_speak = f"{clean_word}... ."
        elif word.endswith((',', ';', ':')):
            # Elongate the word and add a shorter pause
            text_to_speak = f"{clean_word}... ,"
        else:
            # Elongate regular words for clear pronunciation
            text_to_speak = f"{clean_word}..."
        
        self.logger.info(f"Generating audio for word: '{text_to_speak}'")
        
        request_body = {
            "text": text_to_speak,
            "model_id": model_id,
            "voice_settings": {
                "stability": 0.98,  # Very high stability for consistent enunciation
                "similarity_boost": 0.95,  # Very high similarity for clear pronunciation
                "style": 0.0,  # No style exaggeration for clear enunciation
                "use_speaker_boost": True
            }
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    f"{self.api_url}/{self.voice_id}",
                    json=request_body,
                    headers={
                        "Accept": "audio/mpeg",
                        "Content-Type": "application/json",
                        "xi-api-key": self.api_key
                    }
                )
                
                if response.status_code != 200:
                    self.logger.error(f"ElevenLabs API error for word '{word}': {response.status_code} - {response.text}")
                    raise Exception(f"ElevenLabs API returned status {response.status_code}: {response.text}")
                
                response.raise_for_status()
                
                self.logger.info(f"Successfully generated audio for word '{word}', size: {len(response.content)} bytes")
                return response.content
                
            except httpx.HTTPError as e:
                self.logger.error(f"HTTP error calling ElevenLabs API for word '{word}': {str(e)}")
                raise Exception(f"ElevenLabs API error for word '{word}': {str(e)}")
            except Exception as e:
                self.logger.error(f"Unexpected error generating audio for word '{word}': {str(e)}", exc_info=True)
                raise Exception(f"Unexpected error for word '{word}': {str(e)}")
    
    async def text_to_speech(self, text: str, model_id: str = "eleven_multilingual_v2") -> bytes:
        """
        Convert text to speech using ElevenLabs API or cache
        
        Args:
            text: Text to convert to speech
            model_id: Model to use for TTS
            
        Returns:
            Audio data as bytes
            
        Raises:
            Exception: If API call fails
        """
        if not self.is_configured():
            raise Exception("ElevenLabs API key not configured. Please set ELEVENLABS_API_KEY in your .env file.")
        
        # Check cache first in debug mode
        if self.debug_mode:
            cached_audio = self._load_from_cache(text)
            if cached_audio:
                self.logger.info(f"Using cached audio for: {text[:100]}...")
                return cached_audio
        
        self.logger.info(f"Converting text to speech: {text[:100]}...")
        
        request_body = {
            "text": text,
            "model_id": model_id,
            "voice_settings": {
                "stability": 0.9,  # Very high stability for clear, enunciated speech
                "similarity_boost": 0.8,  # High similarity for clear pronunciation
                "style": 0.0,  # No style exaggeration for clear enunciation
                "use_speaker_boost": True
            }
        }

        self.logger.info(f"Making request to ElevenLabs API: {self.api_url}/{self.voice_id}")
        self.logger.debug(f"Request body: {request_body}")

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    f"{self.api_url}/{self.voice_id}",
                    json=request_body,
                    headers={
                        "Accept": "audio/mpeg",
                        "Content-Type": "application/json",
                        "xi-api-key": self.api_key
                    }
                )
                self.logger.info(f"ElevenLabs API response status: {response.status_code}")
                
                if response.status_code != 200:
                    self.logger.error(f"ElevenLabs API error response: {response.status_code} - {response.text}")
                    raise Exception(f"ElevenLabs API returned status {response.status_code}: {response.text}")
                
                response.raise_for_status()
                
                self.logger.info(f"Successfully generated audio, size: {len(response.content)} bytes")
                
                # Save to cache in debug mode
                if self.debug_mode:
                    self._save_to_cache(text, response.content)
                
                return response.content
                
            except httpx.HTTPError as e:
                self.logger.error(f"HTTP error calling ElevenLabs API: {str(e)}")
                if hasattr(e, 'response') and e.response is not None:
                    self.logger.error(f"Response status: {e.response.status_code}")
                    self.logger.error(f"Response text: {e.response.text}")
                raise Exception(f"ElevenLabs API error: {str(e)}")
            except Exception as e:
                self.logger.error(f"Unexpected error in text_to_speech: {str(e)}", exc_info=True)
                raise Exception(f"Unexpected error: {str(e)}")
    
    def get_voice_info(self) -> Dict[str, str]:
        """
        Get information about the current voice configuration
        
        Returns:
            Dictionary with voice information
        """
        return {
            "voice_id": self.voice_id,
            "api_url": self.api_url,
            "configured": self.is_configured()
        }
    
    def set_voice(self, voice_id: str) -> None:
        """
        Set a different voice ID
        
        Args:
            voice_id: New voice ID to use
        """
        self.voice_id = voice_id
        self.logger.info(f"Voice ID changed to: {voice_id}")
    
    def set_voice_settings(self, stability: float = 0.5, similarity_boost: float = 0.5, 
                          style: float = 0.2, use_speaker_boost: bool = True) -> None:
        """
        Set custom voice settings
        
        Args:
            stability: Voice stability (0.0 to 1.0)
            similarity_boost: Similarity boost (0.0 to 1.0)
            style: Style exaggeration (0.0 to 1.0)
            use_speaker_boost: Whether to use speaker boost
        """
        self.voice_settings = {
            "stability": stability,
            "similarity_boost": similarity_boost,
            "style": style,
            "use_speaker_boost": use_speaker_boost
        }
        self.logger.info(f"Voice settings updated: {self.voice_settings}")
    
    async def text_to_speech_with_custom_settings(self, text: str, model_id: str = "eleven_multilingual_v2") -> bytes:
        """
        Convert text to speech with custom voice settings
        
        Args:
            text: Text to convert to speech
            model_id: Model to use for TTS
            
        Returns:
            Audio data as bytes
        """
        if not self.is_configured():
            raise Exception("ElevenLabs API key not configured. Please set ELEVENLABS_API_KEY in your .env file.")
        
        # Use custom settings if available, otherwise use defaults
        voice_settings = getattr(self, 'voice_settings', {
            "stability": 0.9,  # Very high stability for clear, enunciated speech
            "similarity_boost": 0.8,  # High similarity for clear pronunciation
            "style": 0.0,  # No style exaggeration for clear enunciation
            "use_speaker_boost": True
        })
        
        self.logger.info(f"Converting text to speech with custom settings: {text[:100]}...")
        
        request_body = {
            "text": text,
            "model_id": model_id,
            "voice_settings": voice_settings
        }

        self.logger.info(f"Making request to ElevenLabs API: {self.api_url}/{self.voice_id}")
        self.logger.debug(f"Request body: {request_body}")

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    f"{self.api_url}/{self.voice_id}",
                    json=request_body,
                    headers={
                        "Accept": "audio/mpeg",
                        "Content-Type": "application/json",
                        "xi-api-key": self.api_key
                    }
                )
                self.logger.info(f"ElevenLabs API response status: {response.status_code}")
                
                if response.status_code != 200:
                    self.logger.error(f"ElevenLabs API error response: {response.status_code} - {response.text}")
                    raise Exception(f"ElevenLabs API returned status {response.status_code}: {response.text}")
                
                response.raise_for_status()
                
                self.logger.info(f"Successfully generated audio with custom settings, size: {len(response.content)} bytes")
                return response.content
                
            except httpx.HTTPError as e:
                self.logger.error(f"HTTP error calling ElevenLabs API: {str(e)}")
                if hasattr(e, 'response') and e.response is not None:
                    self.logger.error(f"Response status: {e.response.status_code}")
                    self.logger.error(f"Response text: {e.response.text}")
                raise Exception(f"ElevenLabs API error: {str(e)}")
            except Exception as e:
                self.logger.error(f"Unexpected error in text_to_speech_with_custom_settings: {str(e)}", exc_info=True)
                raise Exception(f"Unexpected error: {str(e)}")
    
    async def text_to_speech_streaming(self, text: str, model_id: str = "eleven_multilingual_v2") -> AsyncGenerator[bytes, None]:
        """
        Convert text to speech using ElevenLabs API with streaming support
        
        Args:
            text: Text to convert to speech
            model_id: Model to use for TTS
            
        Yields:
            Audio data chunks as bytes
            
        Raises:
            Exception: If API call fails
        """
        if not self.is_configured():
            raise Exception("ElevenLabs API key not configured. Please set ELEVENLABS_API_KEY in your .env file.")
        
        self.logger.info(f"Converting text to speech with streaming: {text[:100]}...")
        
        request_body = {
            "text": text,
            "model_id": model_id,
            "voice_settings": {
                "stability": 0.9,  # Very high stability for clear, enunciated speech
                "similarity_boost": 0.8,  # High similarity for clear pronunciation
                "style": 0.0,  # No style exaggeration for clear enunciation
                "use_speaker_boost": True
            }
        }

        self.logger.info(f"Making streaming request to ElevenLabs API: {self.streaming_url}/{self.voice_id}")

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                async with client.stream(
                    "POST",
                    f"{self.streaming_url}/{self.voice_id}",
                    json=request_body,
                    headers={
                        "Accept": "audio/mpeg",
                        "Content-Type": "application/json",
                        "xi-api-key": self.api_key
                    }
                ) as response:
                    self.logger.info(f"ElevenLabs streaming API response status: {response.status_code}")
                    
                    if response.status_code != 200:
                        error_text = await response.aread()
                        self.logger.error(f"ElevenLabs API error response: {response.status_code} - {error_text.decode()}")
                        raise Exception(f"ElevenLabs API returned status {response.status_code}: {error_text.decode()}")
                    
                    async for chunk in response.aiter_bytes(chunk_size=1024):
                        if chunk:
                            self.logger.debug(f"Received audio chunk: {len(chunk)} bytes")
                            yield chunk
                    
                    self.logger.info("Streaming audio generation completed")
                    
            except httpx.HTTPError as e:
                self.logger.error(f"HTTP error calling ElevenLabs streaming API: {str(e)}")
                raise Exception(f"ElevenLabs streaming API error: {str(e)}")
            except Exception as e:
                self.logger.error(f"Unexpected error in text_to_speech_streaming: {str(e)}", exc_info=True)
                raise Exception(f"Unexpected error: {str(e)}")
    
    async def text_to_speech_with_timestamps(self, text: str, model_id: str = "eleven_multilingual_v2") -> dict:
        """
        Convert text to speech with estimated word-level timing data using ElevenLabs
        
        Args:
            text: Text to convert to speech
            model_id: Model to use for TTS
            
        Returns:
            Dictionary containing audio data and estimated timing information
            
        Raises:
            Exception: If API call fails
        """
        if not self.is_configured():
            raise Exception("ElevenLabs API key not configured. Please set ELEVENLABS_API_KEY in your .env file.")
        
        self.logger.info(f"Converting text to speech with estimated timestamps: {text[:100]}...")
        
        # First get the audio using regular TTS (which handles caching)
        audio_data = await self.text_to_speech(text, model_id)
        
        # Estimate word timings based on text analysis
        words = text.split()
        estimated_timings = self._estimate_word_timings(words, len(audio_data))
        
        # Convert audio to base64 for frontend
        import base64
        audio_base64 = base64.b64encode(audio_data).decode('utf-8')
        
        result = {
            "audio": audio_base64,
            "word_timings": estimated_timings,
            "total_duration": estimated_timings[-1]["end_time"] if estimated_timings else 0
        }
        
        self.logger.info(f"Successfully generated audio with estimated timings, {len(words)} words")
        return result
    
    def _estimate_word_timings(self, words: list, audio_size_bytes: int) -> list:
        """
        Estimate word timings based on text analysis and audio size with improved alignment
        
        Args:
            words: List of words in the text
            audio_size_bytes: Size of the generated audio in bytes
            
        Returns:
            List of word timing dictionaries
        """
        # Estimate total duration based on audio size (rough approximation)
        # Assuming ~16kbps bitrate for MP3, but with slower, more enunciated speech settings
        estimated_duration_ms = (audio_size_bytes * 8) / 16000 * 1000 * 1.5  # 50% slower for enunciated speech
        
        # Calculate timing for each word based on character count and complexity
        timings = []
        current_time = 0
        
        for i, word in enumerate(words):
            # Base time per word (in milliseconds) - increased for enunciated speech
            base_time = 700  # 700ms base for clear enunciation
            
            # Adjust based on word length - more time per character for enunciation
            length_factor = len(word) * 100  # 100ms per character for clear pronunciation
            
            # Adjust based on word complexity (more syllables = longer for enunciation)
            syllable_count = self._estimate_syllables(word)
            complexity_factor = syllable_count * 200  # 200ms per syllable for clear enunciation
            
            # Adjust for punctuation - longer pauses
            punctuation_factor = 400 if word.endswith(('.', '!', '?')) else (200 if word.endswith((',', ';', ':')) else 0)
            
            # Add extra time for common words that are spoken slower
            common_words = ['the', 'and', 'but', 'or', 'so', 'then', 'when', 'where', 'why', 'how']
            common_word_factor = 200 if word.lower() in common_words else 0
            
            # Calculate word duration
            word_duration = base_time + length_factor + complexity_factor + punctuation_factor + common_word_factor
            
            # Ensure we don't exceed total estimated duration
            if current_time + word_duration > estimated_duration_ms:
                word_duration = max(150, estimated_duration_ms - current_time)
            
            timings.append({
                "word": word,
                "start_time": current_time,
                "end_time": current_time + word_duration,
                "index": i
            })
            
            current_time += word_duration
        
        return timings
    
    def _estimate_syllables(self, word: str) -> int:
        """
        Estimate syllable count for a word (simple heuristic)
        
        Args:
            word: Word to analyze
            
        Returns:
            Estimated syllable count
        """
        word = word.lower().strip('.,!?;:')
        if not word:
            return 1
        
        # Count vowel groups
        vowels = 'aeiouy'
        syllable_count = 0
        prev_was_vowel = False
        
        for char in word:
            is_vowel = char in vowels
            if is_vowel and not prev_was_vowel:
                syllable_count += 1
            prev_was_vowel = is_vowel
        
        # Handle silent 'e' at the end
        if word.endswith('e') and syllable_count > 1:
            syllable_count -= 1
        
        # Ensure at least 1 syllable
        return max(1, syllable_count)