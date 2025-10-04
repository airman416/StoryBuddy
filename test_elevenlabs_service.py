#!/usr/bin/env python3
"""
Manual test script for ElevenLabsService
Run this script to test the ElevenLabsService independently
"""

import asyncio
import logging
import os
from dotenv import load_dotenv
from elevenlabs_service import ElevenLabsService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_elevenlabs_service():
    """Test the ElevenLabsService functionality"""
    print("=" * 50)
    print("Testing ElevenLabsService")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv()
    
    # Initialize service
    elevenlabs_service = ElevenLabsService()
    
    # Test 1: Check configuration
    print("\n1. Testing configuration...")
    is_configured = elevenlabs_service.is_configured()
    print(f"   Service configured: {is_configured}")
    
    if not is_configured:
        print("   ❌ Service not configured. Please set ELEVENLABS_API_KEY in your .env file.")
        return
    
    print("   ✅ Service is properly configured")
    
    # Test 2: Get voice information
    print("\n2. Testing voice information...")
    voice_info = elevenlabs_service.get_voice_info()
    print(f"   Voice ID: {voice_info['voice_id']}")
    print(f"   API URL: {voice_info['api_url']}")
    print(f"   Configured: {voice_info['configured']}")
    print("   ✅ Voice information retrieved successfully")
    
    # Test 3: Basic text-to-speech
    print("\n3. Testing basic text-to-speech...")
    try:
        test_text = "Hello, this is a test of the ElevenLabs text-to-speech service."
        audio_data = await elevenlabs_service.text_to_speech(test_text)
        print(f"   Text: {test_text}")
        print(f"   Audio data size: {len(audio_data)} bytes")
        print("   ✅ Basic text-to-speech successful")
        
        # Save audio to file for verification
        with open("test_audio_basic.mp3", "wb") as f:
            f.write(audio_data)
        print("   💾 Audio saved as 'test_audio_basic.mp3'")
        
    except Exception as e:
        print(f"   ❌ Basic text-to-speech failed: {str(e)}")
    
    # Test 4: Text-to-speech with different model
    print("\n4. Testing text-to-speech with different model...")
    try:
        test_text = "This is a test using a different model for text-to-speech conversion."
        audio_data = await elevenlabs_service.text_to_speech(test_text, model_id="eleven_multilingual_v2")
        print(f"   Text: {test_text}")
        print(f"   Audio data size: {len(audio_data)} bytes")
        print("   ✅ Text-to-speech with different model successful")
        
        # Save audio to file for verification
        with open("test_audio_model.mp3", "wb") as f:
            f.write(audio_data)
        print("   💾 Audio saved as 'test_audio_model.mp3'")
        
    except Exception as e:
        print(f"   ❌ Text-to-speech with different model failed: {str(e)}")
    
    # Test 5: Custom voice settings
    print("\n5. Testing custom voice settings...")
    try:
        # Set custom voice settings
        elevenlabs_service.set_voice_settings(
            stability=0.8,
            similarity_boost=0.7,
            style=0.3,
            use_speaker_boost=True
        )
        
        test_text = "This is a test with custom voice settings for more expressive speech."
        audio_data = await elevenlabs_service.text_to_speech_with_custom_settings(test_text)
        print(f"   Text: {test_text}")
        print(f"   Audio data size: {len(audio_data)} bytes")
        print("   ✅ Custom voice settings successful")
        
        # Save audio to file for verification
        with open("test_audio_custom.mp3", "wb") as f:
            f.write(audio_data)
        print("   💾 Audio saved as 'test_audio_custom.mp3'")
        
    except Exception as e:
        print(f"   ❌ Custom voice settings failed: {str(e)}")
    
    # Test 6: Change voice ID
    print("\n6. Testing voice ID change...")
    try:
        # Note: This uses the same voice ID, but demonstrates the functionality
        original_voice = elevenlabs_service.voice_id
        elevenlabs_service.set_voice("JBFqnCBsd6RMkjVDRZzb")  # Same voice, but tests the method
        print(f"   Original voice ID: {original_voice}")
        print(f"   New voice ID: {elevenlabs_service.voice_id}")
        print("   ✅ Voice ID change successful")
        
    except Exception as e:
        print(f"   ❌ Voice ID change failed: {str(e)}")
    
    # Test 7: Long text (stress test)
    print("\n7. Testing with longer text...")
    try:
        long_text = """
        This is a longer text to test how the ElevenLabs service handles more substantial content.
        It includes multiple sentences and should provide a good test of the service's capabilities.
        The text should be converted to speech without any issues, demonstrating the robustness
        of the implementation. This test helps ensure that the service can handle real-world
        usage scenarios where longer stories or content need to be converted to audio.
        """
        audio_data = await elevenlabs_service.text_to_speech(long_text.strip())
        print(f"   Text length: {len(long_text)} characters")
        print(f"   Audio data size: {len(audio_data)} bytes")
        print("   ✅ Long text conversion successful")
        
        # Save audio to file for verification
        with open("test_audio_long.mp3", "wb") as f:
            f.write(audio_data)
        print("   💾 Audio saved as 'test_audio_long.mp3'")
        
    except Exception as e:
        print(f"   ❌ Long text conversion failed: {str(e)}")
    
    print("\n" + "=" * 50)
    print("ElevenLabsService testing completed!")
    print("=" * 50)
    print("\nGenerated audio files:")
    print("- test_audio_basic.mp3 (basic TTS)")
    print("- test_audio_model.mp3 (different model)")
    print("- test_audio_custom.mp3 (custom settings)")
    print("- test_audio_long.mp3 (long text)")
    print("\nYou can play these files to verify the audio quality.")

if __name__ == "__main__":
    asyncio.run(test_elevenlabs_service())
