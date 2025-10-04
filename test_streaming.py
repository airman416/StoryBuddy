#!/usr/bin/env python3
"""
Test script for streaming audio functionality
"""
import asyncio
import sys
import os

# Add the current directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from elevenlabs_service import ElevenLabsService

async def test_streaming():
    """Test the streaming functionality"""
    print("Testing ElevenLabs streaming functionality...")
    
    # Initialize the service
    service = ElevenLabsService()
    
    if not service.is_configured():
        print("❌ ElevenLabs API key not configured. Please set ELEVENLABS_API_KEY in your .env file.")
        return False
    
    print("✅ ElevenLabs service configured")
    
    # Test text
    test_text = "Hello! This is a test of the streaming audio functionality."
    print(f"Testing with text: {test_text}")
    
    try:
        chunk_count = 0
        total_bytes = 0
        
        print("🔄 Starting streaming audio generation...")
        async for chunk in service.text_to_speech_streaming(test_text):
            chunk_count += 1
            total_bytes += len(chunk)
            print(f"📦 Received chunk {chunk_count}: {len(chunk)} bytes")
        
        print(f"✅ Streaming completed successfully!")
        print(f"📊 Total chunks: {chunk_count}")
        print(f"📊 Total bytes: {total_bytes}")
        return True
        
    except Exception as e:
        print(f"❌ Error during streaming: {str(e)}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_streaming())
    if success:
        print("\n🎉 Streaming test passed!")
    else:
        print("\n💥 Streaming test failed!")
        sys.exit(1)
