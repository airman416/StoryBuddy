#!/usr/bin/env python3
"""
Test script for word-by-word TTS functionality
"""

import asyncio
import os
import sys
from elevenlabs_service import ElevenLabsService

async def test_word_by_word_tts():
    """Test the word-by-word TTS functionality"""
    print("🧪 Testing Word-by-Word TTS System")
    print("=" * 50)
    
    # Initialize service
    service = ElevenLabsService()
    
    if not service.is_configured():
        print("❌ ElevenLabs service not configured. Please set ELEVENLABS_API_KEY or enable DEBUG mode.")
        return False
    
    # Test with a very short story
    test_text = "The cat sat."
    print(f"📝 Test text: '{test_text}'")
    print(f"🔢 Number of words: {len(test_text.split())}")
    
    try:
        print("\n🎵 Generating word-by-word audio...")
        word_audio_list = await service.text_to_speech_word_by_word(test_text)
        
        print(f"✅ Successfully generated audio for {len(word_audio_list)} words")
        
        # Display results
        print("\n📊 Results:")
        for i, word_data in enumerate(word_audio_list):
            status = "📁 Cached" if word_data["cached"] else "🆕 New"
            audio_size = len(word_data["audio"])
            print(f"  {i+1}. '{word_data['word']}' - {audio_size} bytes - {status}")
        
        # Check cache directory
        if os.path.exists(service.word_cache_dir):
            cached_files = os.listdir(service.word_cache_dir)
            print(f"\n📂 Cache directory contains {len(cached_files)} files:")
            for file in cached_files:
                print(f"  - {file}")
        
        # Check config file
        if os.path.exists(service.config_file):
            print(f"\n⚙️ Configuration file exists: {service.config_file}")
        else:
            print(f"\n⚠️ Configuration file not found: {service.config_file}")
        
        print("\n🎉 Word-by-word TTS test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error during word-by-word TTS test: {str(e)}")
        return False

async def main():
    """Main test function"""
    success = await test_word_by_word_tts()
    
    if success:
        print("\n✅ All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
