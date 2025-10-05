import httpx
import logging
import os
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from debug_config import get_debug_story, get_debug_feedback

# Load environment variables
load_dotenv()

class GeminiService:
    """Service class for handling Gemini API interactions"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize GeminiService
        
        Args:
            api_key: Gemini API key. If not provided, will load from environment
        """
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        self.api_url = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent'
        self.logger = logging.getLogger(__name__)
        self.debug_mode = os.getenv('DEBUG', 'false').lower() == 'true'
        
        if not self.api_key and not self.debug_mode:
            self.logger.warning("GEMINI_API_KEY is not set in environment variables")
        
        if self.debug_mode:
            self.logger.info("Debug mode enabled - using pre-defined stories instead of API calls")
    
    def is_configured(self) -> bool:
        """Check if the service is properly configured"""
        return bool(self.api_key) or self.debug_mode
    
    async def generate_story(self, prompt: str, age_group: str) -> str:
        """
        Generate a story using Gemini API or debug mode
        
        Args:
            prompt: The story prompt
            age_group: Target age group for the story
            
        Returns:
            Generated story text
            
        Raises:
            Exception: If API call fails or response is invalid
        """
        if not self.is_configured():
            raise Exception("Gemini API key not configured. Please set GEMINI_API_KEY in your .env file.")
        
        self.logger.info(f"Generating story for prompt: '{prompt}', age_group: '{age_group}'")
        
        # Use debug mode if enabled
        if self.debug_mode:
            self.logger.info("Using debug mode - returning pre-defined story")
            story = get_debug_story(prompt, age_group)
            self.logger.info(f"Debug story generated: {story[:100]}...")
            return story
        
        formatted_prompt = f"""Create a very short, engaging story for children aged {age_group} about: {prompt}. 

Requirements:
- Use simple, age-appropriate vocabulary
- Keep it to 2-3 sentences maximum (much shorter)
- Make it educational and fun
- Include descriptive but simple language
- End with a positive message
- Focus on one main character and one simple event
- DO NOT use any emojis in the story text - use only plain text words
- Keep the language simple and clear without any special characters

Story:"""

        request_body = {
            "contents": [{
                "parts": [{
                    "text": formatted_prompt
                }]
            }],
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 1000,
            }
        }

        self.logger.info(f"Making request to Gemini API: {self.api_url}")
        self.logger.debug(f"Request body: {request_body}")

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    f"{self.api_url}?key={self.api_key}",
                    json=request_body,
                    headers={"Content-Type": "application/json"}
                )
                self.logger.info(f"Gemini API response status: {response.status_code}")
                
                if response.status_code != 200:
                    self.logger.error(f"Gemini API error response: {response.status_code} - {response.text}")
                    raise Exception(f"Gemini API returned status {response.status_code}: {response.text}")
                
                response.raise_for_status()
                data = response.json()
                self.logger.info(f"Gemini API response data: {data}")
                
                # Extract story from response
                story = self._extract_story_from_response(data, prompt)
                self.logger.info(f"Successfully generated story: {story[:100]}...")
                
                return story
                
            except httpx.HTTPError as e:
                self.logger.error(f"HTTP error calling Gemini API: {str(e)}")
                if hasattr(e, 'response') and e.response is not None:
                    self.logger.error(f"Response status: {e.response.status_code}")
                    self.logger.error(f"Response text: {e.response.text}")
                raise Exception(f"Gemini API error: {str(e)}")
            except KeyError as e:
                self.logger.error(f"Key error parsing Gemini response: {str(e)}")
                raise Exception(f"Error parsing Gemini API response: {str(e)}")
            except Exception as e:
                self.logger.error(f"Unexpected error in generate_story: {str(e)}", exc_info=True)
                raise Exception(f"Unexpected error: {str(e)}")
    
    async def evaluate_reading(self, original_story: str, spoken_text: str) -> str:
        """
        Evaluate child's reading using Gemini API or debug mode
        
        Args:
            original_story: The original story text
            spoken_text: What the child read
            
        Returns:
            Feedback text
            
        Raises:
            Exception: If API call fails
        """
        if not self.is_configured():
            raise Exception("Gemini API key not configured. Please set GEMINI_API_KEY in your .env file.")
        
        self.logger.info(f"Evaluating reading for story: {original_story[:50]}...")
        
        # Use debug mode if enabled
        if self.debug_mode:
            self.logger.info("Using debug mode - returning pre-defined feedback")
            feedback = get_debug_feedback(original_story, spoken_text)
            self.logger.info(f"Debug feedback generated: {feedback[:50]}...")
            return feedback
        
        prompt = f"""Original story: "{original_story}"

Child read: "{spoken_text}"

Please provide encouraging feedback for a child learning to read. Compare what they read to the original story. Give positive reinforcement and gentle suggestions if needed. Keep it short, simple, and encouraging. Use emojis to make it fun.

Feedback:"""

        request_body = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }],
            "generationConfig": {
                "temperature": 0.3,
                "maxOutputTokens": 500,
            }
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    f"{self.api_url}?key={self.api_key}",
                    json=request_body,
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                
                data = response.json()
                self.logger.info(f"Gemini API response data for reading eval: {data}")
                
                # Extract feedback from response
                feedback = self._extract_feedback_from_response(data)
                return feedback
                
            except httpx.HTTPError as e:
                self.logger.error(f"HTTP error calling Gemini API for reading eval: {str(e)}")
                if hasattr(e, 'response') and e.response is not None:
                    self.logger.error(f"Response status: {e.response.status_code}")
                    self.logger.error(f"Response text: {e.response.text}")
                # Fallback to positive message if API fails
                return "Great job reading! Keep practicing! 🌟"
            except Exception as e:
                self.logger.error(f"Unexpected error in evaluate_reading: {str(e)}", exc_info=True)
                # Fallback to positive message if API fails
                return "Great job reading! Keep practicing! 🌟"
    
    def _extract_story_from_response(self, data: Dict[Any, Any], prompt: str) -> str:
        """Extract story text from Gemini API response"""
        # Check if response has candidates
        if "candidates" not in data or not data["candidates"]:
            self.logger.error(f"No candidates in Gemini response: {data}")
            raise Exception("Invalid response from Gemini API - no candidates found")
        
        # Check if candidate has content
        candidate = data["candidates"][0]
        if "content" not in candidate:
            self.logger.error(f"No content in candidate: {candidate}")
            raise Exception("Invalid response from Gemini API - no content in candidate")
        
        # Check finish reason
        if "finishReason" in candidate and candidate["finishReason"] == "MAX_TOKENS":
            self.logger.warning("Response was truncated due to token limit")
        
        # Check if content has parts
        content = candidate["content"]
        if "parts" not in content or not content["parts"]:
            self.logger.error(f"No parts in content: {content}")
            # Try to provide a fallback story
            fallback_story = f"Once upon a time, there was a {prompt.lower()}. It was a wonderful adventure that taught us about friendship and kindness. The end! 🌟"
            self.logger.info(f"Using fallback story: {fallback_story[:100]}...")
            return fallback_story
        
        # Check if the first part has text
        if not content["parts"][0].get("text"):
            self.logger.error(f"No text in first part: {content['parts'][0]}")
            # Try to provide a fallback story
            fallback_story = f"Once upon a time, there was a {prompt.lower()}. It was a wonderful adventure that taught us about friendship and kindness. The end! 🌟"
            self.logger.info(f"Using fallback story: {fallback_story[:100]}...")
            return fallback_story
        
        # Extract the text from parts
        return content["parts"][0]["text"].strip()
    
    def _extract_feedback_from_response(self, data: Dict[Any, Any]) -> str:
        """Extract feedback text from Gemini API response"""
        # Check if response has candidates
        if "candidates" not in data or not data["candidates"]:
            self.logger.error(f"No candidates in Gemini response: {data}")
            return "Great job reading! Keep practicing! 🌟"
        
        # Check if candidate has content
        candidate = data["candidates"][0]
        if "content" not in candidate:
            self.logger.error(f"No content in candidate: {candidate}")
            return "Great job reading! Keep practicing! 🌟"
        
        # Check finish reason
        if "finishReason" in candidate and candidate["finishReason"] == "MAX_TOKENS":
            self.logger.warning("Response was truncated due to token limit")
        
        # Check if content has parts
        content = candidate["content"]
        if "parts" not in content or not content["parts"]:
            self.logger.error(f"No parts in content: {content}")
            return "Great job reading! Keep practicing! 🌟"
        
        # Check if the first part has text
        if not content["parts"][0].get("text"):
            self.logger.error(f"No text in first part: {content['parts'][0]}")
            return "Great job reading! Keep practicing! 🌟"
        
        # Extract the text from parts
        return content["parts"][0]["text"].strip()
    
    async def generate_emoji_for_words(self, words: str) -> str:
        """
        Generate multiple emojis (3-5) that represent the given words
        
        Args:
            words: The text to generate emojis for
            
        Returns:
            A string of multiple emoji characters (3-5) that represent the words
        """
        if not self.is_configured():
            return "📖🌟✨"  # Default fallback emojis
        
        self.logger.info(f"Generating emojis for words: '{words}'")
        
        # Use debug mode if enabled
        if self.debug_mode:
            self.logger.info("Using debug mode - keyword-based emoji selection")
            return self._get_keyword_based_emojis(words)
        
        prompt = f"""Look at these exact words from a children's story: "{words}"

Task: Generate 3-5 emojis that directly represent what is happening in these specific words.
- Be specific to the actual nouns, verbs, and actions mentioned
- If animals are mentioned, use those animal emojis
- If actions are mentioned (running, jumping, playing), use action emojis
- If objects are mentioned, use those object emojis
- Match the mood and specific details of these words

Return ONLY the emoji characters directly, no spaces, no text, no explanations.
Example: For "cat played ball" return: 🐱⚽😸
Example: For "sun shone bright" return: ☀️✨🌞"""

        request_body = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }],
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 20,
            }
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.post(
                    f"{self.api_url}?key={self.api_key}",
                    json=request_body,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code != 200:
                    self.logger.error(f"Gemini API error for emoji: {response.status_code}")
                    self.logger.error(f"Response content: {response.text}")
                    self.logger.info("Using keyword-based emoji generation as fallback")
                    return self._get_keyword_based_emojis(words)
                
                data = response.json()
                self.logger.debug(f"API response received: {data}")
                
                # Check for safety blocks or errors
                if "error" in data:
                    self.logger.error(f"API returned error: {data['error']}")
                    self.logger.info("Using keyword-based emoji generation as fallback")
                    return self._get_keyword_based_emojis(words)
                
                emoji = self._extract_emoji_from_response(data)
                
                # If extraction failed, use keyword-based fallback
                if emoji is None:
                    self.logger.info("API response incomplete, using keyword-based emoji generation")
                    emoji = self._get_keyword_based_emojis(words)
                
                self.logger.info(f"Generated emojis: {emoji}")
                return emoji
                
            except Exception as e:
                self.logger.error(f"Error generating emojis: {str(e)}")
                import traceback
                self.logger.error(f"Traceback: {traceback.format_exc()}")
                self.logger.info("Using keyword-based emoji generation as fallback")
                return self._get_keyword_based_emojis(words)
    
    def _get_keyword_based_emojis(self, words: str) -> str:
        """Get emojis based on keyword matching as fallback"""
        words_lower = words.lower()
        emojis = []
        
        # Animals
        if any(word in words_lower for word in ['cat', 'cats', 'kitten', 'kitty', 'meow', 'feline']):
            emojis.extend(['🐱', '😺'])
        if any(word in words_lower for word in ['dog', 'dogs', 'puppy', 'pup', 'woof', 'bark']):
            emojis.extend(['🐶', '🐕'])
        if any(word in words_lower for word in ['bird', 'birds', 'fly', 'wing', 'tweet']):
            emojis.extend(['🐦', '🕊️'])
        if any(word in words_lower for word in ['fish', 'swim', 'ocean', 'sea']):
            emojis.extend(['🐠', '🐟'])
        if any(word in words_lower for word in ['bunny', 'rabbit', 'hop']):
            emojis.extend(['🐰', '🐇'])
        if any(word in words_lower for word in ['bear', 'teddy']):
            emojis.extend(['🐻', '🧸'])
        if any(word in words_lower for word in ['elephant']):
            emojis.extend(['🐘'])
        if any(word in words_lower for word in ['lion', 'roar']):
            emojis.extend(['🦁'])
        if any(word in words_lower for word in ['tiger']):
            emojis.extend(['🐯'])
        if any(word in words_lower for word in ['monkey', 'ape']):
            emojis.extend(['🐵', '🐒'])
        if any(word in words_lower for word in ['mouse', 'mice', 'rat']):
            emojis.extend(['🐭', '🐁'])
        
        # Nature & Weather
        if any(word in words_lower for word in ['sun', 'sunny', 'bright', 'shine', 'shone', 'shining']):
            emojis.extend(['☀️', '🌞'])
        if any(word in words_lower for word in ['moon', 'night', 'dark']):
            emojis.extend(['🌙', '🌛'])
        if any(word in words_lower for word in ['star', 'stars', 'twinkle']):
            emojis.extend(['⭐', '✨'])
        if any(word in words_lower for word in ['tree', 'trees', 'forest', 'wood']):
            emojis.extend(['🌳', '🌲'])
        if any(word in words_lower for word in ['flower', 'flowers', 'garden', 'bloom']):
            emojis.extend(['🌸', '🌺'])
        if any(word in words_lower for word in ['rain', 'rainy', 'wet']):
            emojis.extend(['🌧️', '☔'])
        if any(word in words_lower for word in ['cloud', 'cloudy']):
            emojis.extend(['☁️', '⛅'])
        if any(word in words_lower for word in ['rainbow']):
            emojis.extend(['🌈'])
        
        # Emotions & Actions
        if any(word in words_lower for word in ['happy', 'joy', 'smile', 'glad', 'excited']):
            emojis.extend(['😊', '😄'])
        if any(word in words_lower for word in ['sad', 'cry', 'tear']):
            emojis.extend(['😢', '😭'])
        if any(word in words_lower for word in ['love', 'heart', 'like', 'loved']):
            emojis.extend(['❤️', '💖'])
        if any(word in words_lower for word in ['play', 'playing', 'played', 'fun']):
            emojis.extend(['🎮', '🎨'])
        if any(word in words_lower for word in ['sleep', 'sleeping', 'tired', 'nap']):
            emojis.extend(['😴', '💤'])
        if any(word in words_lower for word in ['eat', 'eating', 'food', 'hungry']):
            emojis.extend(['🍽️', '🍴'])
        if any(word in words_lower for word in ['look', 'looking', 'see', 'saw', 'watch', 'watching', 'viewed']):
            emojis.extend(['👀', '👁️'])
        if any(word in words_lower for word in ['run', 'running', 'ran', 'race', 'fast']):
            emojis.extend(['🏃', '💨'])
        if any(word in words_lower for word in ['jump', 'jumping', 'jumped', 'leap']):
            emojis.extend(['🤸', '⬆️'])
        if any(word in words_lower for word in ['walk', 'walking', 'walked', 'stroll']):
            emojis.extend(['🚶', '🐾'])
        if any(word in words_lower for word in ['dance', 'dancing', 'danced']):
            emojis.extend(['💃', '🕺'])
        if any(word in words_lower for word in ['sing', 'singing', 'sang', 'song']):
            emojis.extend(['🎤', '🎵'])
        
        # Objects
        if any(word in words_lower for word in ['ball', 'balls']):
            emojis.extend(['⚽', '🏀'])
        if any(word in words_lower for word in ['book', 'books', 'read', 'story']):
            emojis.extend(['📖', '📚'])
        if any(word in words_lower for word in ['house', 'home']):
            emojis.extend(['🏠', '🏡'])
        if any(word in words_lower for word in ['car', 'cars', 'drive']):
            emojis.extend(['🚗', '🚙'])
        if any(word in words_lower for word in ['toy', 'toys']):
            emojis.extend(['🧸', '🎲'])
        
        # Descriptive words for animals
        if any(word in words_lower for word in ['fluffy', 'soft', 'fuzzy', 'furry']):
            if not any(emoji in emojis for emoji in ['🐱', '😺', '🐶', '🐕']):
                emojis.append('☁️')
        if any(word in words_lower for word in ['big', 'large', 'giant', 'huge']):
            emojis.append('📏')
        if any(word in words_lower for word in ['small', 'tiny', 'little', 'mini']):
            emojis.append('🐾')
        if any(word in words_lower for word in ['pretty', 'beautiful', 'cute', 'adorable']):
            emojis.append('✨')
        if any(word in words_lower for word in ['brave', 'strong', 'hero']):
            emojis.append('💪')
        if any(word in words_lower for word in ['magic', 'magical', 'spell']):
            emojis.append('✨')
        if any(word in words_lower for word in ['friend', 'friends', 'buddy', 'pal']):
            emojis.append('👫')
        
        # Return 3-5 emojis, or fallback if none found
        if emojis:
            # Remove duplicates while preserving order
            seen = set()
            unique_emojis = []
            for emoji in emojis:
                if emoji not in seen:
                    seen.add(emoji)
                    unique_emojis.append(emoji)
            return ''.join(unique_emojis[:5])  # Limit to 5 emojis
        else:
            return "📖🌟✨"
    
    def _extract_emoji_from_response(self, data: Dict[Any, Any]) -> str:
        """Extract emojis from Gemini API response"""
        import re
        
        try:
            # Log the full response for debugging
            self.logger.debug(f"Full API response: {data}")
            
            candidates = data.get("candidates", [])
            if not candidates:
                self.logger.error("No candidates found in response")
                self.logger.error(f"Response structure: {data}")
                return None  # Signal to use fallback
            
            candidate = candidates[0]
            self.logger.debug(f"Candidate: {candidate}")
            
            # Check for finish reason (safety blocks, etc)
            finish_reason = candidate.get("finishReason", "")
            if finish_reason and finish_reason != "STOP":
                self.logger.warning(f"API blocked response with reason: {finish_reason}")
                return None  # Signal to use fallback
            
            content = candidate.get("content", {})
            if not content or not isinstance(content, dict):
                self.logger.error("No content found in candidate")
                return None  # Signal to use fallback
            
            parts = content.get("parts", [])
            if not parts:
                self.logger.error("No parts found in content")
                self.logger.error(f"Content structure: {content}")
                return None  # Signal to use fallback
            
            text = parts[0].get("text", "").strip()
            self.logger.info(f"Extracted text from response: '{text}'")
            
            if not text:
                self.logger.error("Empty text in response")
                return None  # Signal to use fallback
            
            # Extract only emoji characters using comprehensive pattern
            emoji_pattern = r'[\U0001F300-\U0001F9FF\U00002600-\U000027BF\U0001F1E6-\U0001F1FF\U0001F600-\U0001F64F\U0001F680-\U0001F6FF]+'
            emojis = ''.join(re.findall(emoji_pattern, text))
            
            if emojis:
                self.logger.info(f"Successfully extracted emojis: {emojis}")
                return emojis
            else:
                # If no emojis found with regex, return original text if it looks like emojis
                if len(text) <= 30 and not text.isalpha():
                    self.logger.info(f"Using original text as emojis: {text}")
                    return text
                else:
                    self.logger.warning(f"No emojis found in text: '{text}'")
                    return None  # Signal to use fallback
                    
        except Exception as e:
            self.logger.error(f"Error extracting emojis: {str(e)}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            return None  # Signal to use fallback