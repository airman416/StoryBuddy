#!/usr/bin/env python3
"""
Manual test script for GeminiService
Run this script to test the GeminiService independently
"""

import asyncio
import logging
import os
from dotenv import load_dotenv
from gemini_service import GeminiService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_gemini_service():
    """Test the GeminiService functionality"""
    print("=" * 50)
    print("Testing GeminiService")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv()
    
    # Initialize service
    gemini_service = GeminiService()
    
    # Test 1: Check configuration
    print("\n1. Testing configuration...")
    is_configured = gemini_service.is_configured()
    print(f"   Service configured: {is_configured}")
    
    if not is_configured:
        print("   ❌ Service not configured. Please set GEMINI_API_KEY in your .env file.")
        return
    
    print("   ✅ Service is properly configured")
    
    # Test 2: Generate a simple story
    print("\n2. Testing story generation...")
    try:
        story = await gemini_service.generate_story("a friendly robot", "5-7")
        print(f"   Generated story: {story}")
        print("   ✅ Story generation successful")
    except Exception as e:
        print(f"   ❌ Story generation failed: {str(e)}")
    
    # Test 3: Generate another story with different parameters
    print("\n3. Testing story generation with different age group...")
    try:
        story = await gemini_service.generate_story("a magical forest", "8-10")
        print(f"   Generated story: {story}")
        print("   ✅ Story generation with different age group successful")
    except Exception as e:
        print(f"   ❌ Story generation failed: {str(e)}")
    
    # Test 4: Test reading evaluation
    print("\n4. Testing reading evaluation...")
    try:
        original_story = "Once upon a time, there was a little bunny who loved to hop in the garden."
        spoken_text = "Once upon a time, there was a little bunny who loved to hop in the garden."
        feedback = await gemini_service.evaluate_reading(original_story, spoken_text)
        print(f"   Original story: {original_story}")
        print(f"   Spoken text: {spoken_text}")
        print(f"   Feedback: {feedback}")
        print("   ✅ Reading evaluation successful")
    except Exception as e:
        print(f"   ❌ Reading evaluation failed: {str(e)}")
    
    # Test 5: Test reading evaluation with mistakes
    print("\n5. Testing reading evaluation with mistakes...")
    try:
        original_story = "The cat sat on the mat and purred happily."
        spoken_text = "The cat sat on the mat and purred happly."  # Intentional typo
        feedback = await gemini_service.evaluate_reading(original_story, spoken_text)
        print(f"   Original story: {original_story}")
        print(f"   Spoken text: {spoken_text}")
        print(f"   Feedback: {feedback}")
        print("   ✅ Reading evaluation with mistakes successful")
    except Exception as e:
        print(f"   ❌ Reading evaluation with mistakes failed: {str(e)}")
    
    print("\n" + "=" * 50)
    print("GeminiService testing completed!")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(test_gemini_service())
