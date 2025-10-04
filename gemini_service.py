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
- Use emojis throughout the story to make it more engaging and fun
- Add emojis for characters, actions, emotions, and objects

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
