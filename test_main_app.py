#!/usr/bin/env python3
"""
Manual test script for the main StoryBuddy application
Run this script to test the complete application with all services integrated
"""

import asyncio
import logging
import os
import httpx
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_main_app():
    """Test the main StoryBuddy application"""
    print("=" * 60)
    print("Testing StoryBuddy Main Application")
    print("=" * 60)
    
    # Load environment variables
    load_dotenv()
    
    # Test configuration
    print("\n1. Testing configuration...")
    gemini_key = os.getenv('GEMINI_API_KEY')
    elevenlabs_key = os.getenv('ELEVENLABS_API_KEY')
    
    print(f"   GEMINI_API_KEY configured: {'Yes' if gemini_key else 'No'}")
    print(f"   ELEVENLABS_API_KEY configured: {'Yes' if elevenlabs_key else 'No'}")
    
    if not gemini_key or not elevenlabs_key:
        print("   ❌ Missing API keys. Please set both GEMINI_API_KEY and ELEVENLABS_API_KEY in your .env file.")
        return
    
    print("   ✅ All API keys are configured")
    
    # Note: In a real test, you would start the FastAPI server here
    # For this manual test, we'll assume the server is running
    base_url = "http://localhost:8000"
    
    print(f"\n2. Testing API endpoints (assuming server is running at {base_url})...")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Test health endpoint
        print("\n   Testing health endpoint...")
        try:
            response = await client.get(f"{base_url}/health")
            if response.status_code == 200:
                health_data = response.json()
                print(f"   Health status: {health_data['status']}")
                print(f"   Gemini configured: {health_data['gemini_configured']}")
                print(f"   ElevenLabs configured: {health_data['elevenlabs_configured']}")
                print("   ✅ Health endpoint working")
            else:
                print(f"   ❌ Health endpoint failed: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Health endpoint error: {str(e)}")
        
        # Test story generation
        print("\n   Testing story generation...")
        try:
            story_request = {
                "prompt": "a brave little mouse",
                "age_group": "5-7"
            }
            response = await client.post(f"{base_url}/api/generate-story", json=story_request)
            if response.status_code == 200:
                story_data = response.json()
                print(f"   Generated story: {story_data['story']}")
                print("   ✅ Story generation working")
            else:
                print(f"   ❌ Story generation failed: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"   ❌ Story generation error: {str(e)}")
        
        # Test text-to-speech
        print("\n   Testing text-to-speech...")
        try:
            tts_request = {
                "text": "Hello, this is a test of the text-to-speech functionality."
            }
            response = await client.post(f"{base_url}/api/text-to-speech", json=tts_request)
            if response.status_code == 200:
                audio_data = response.content
                print(f"   Audio data size: {len(audio_data)} bytes")
                print("   ✅ Text-to-speech working")
                
                # Save audio for verification
                with open("test_main_tts.mp3", "wb") as f:
                    f.write(audio_data)
                print("   💾 Audio saved as 'test_main_tts.mp3'")
            else:
                print(f"   ❌ Text-to-speech failed: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"   ❌ Text-to-speech error: {str(e)}")
        
        # Test reading evaluation
        print("\n   Testing reading evaluation...")
        try:
            eval_request = {
                "original_story": "The cat sat on the mat and purred happily.",
                "spoken_text": "The cat sat on the mat and purred happly."
            }
            response = await client.post(f"{base_url}/api/evaluate-reading", json=eval_request)
            if response.status_code == 200:
                eval_data = response.json()
                print(f"   Original: {eval_request['original_story']}")
                print(f"   Spoken: {eval_request['spoken_text']}")
                print(f"   Feedback: {eval_data['feedback']}")
                print("   ✅ Reading evaluation working")
            else:
                print(f"   ❌ Reading evaluation failed: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"   ❌ Reading evaluation error: {str(e)}")
    
    print("\n" + "=" * 60)
    print("Main Application Testing Completed!")
    print("=" * 60)
    print("\nTo run the full application test:")
    print("1. Start the server: python main.py")
    print("2. Run this test script: python test_main_app.py")
    print("3. Check the generated audio file: test_main_tts.mp3")

if __name__ == "__main__":
    asyncio.run(test_main_app())
