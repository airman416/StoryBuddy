"""
Debug configuration file containing pre-defined stories and feedback for testing
"""

# Pre-defined stories for different age groups and prompts (very short versions for word-by-word testing)
DEBUG_STORIES = {
    "adventure": {
        "4-6": "Benny found a key. He opened a door. Benny made friends! 🌟",
        "6-8": "Ember breathed bubbles. She found a crystal. Ember saved the kingdom! 🐉✨",
        "8-10": "Alex built a bike. She helped a pharaoh. Alex got a scarab! ⚡🔧"
    },
    "friendship": {
        "4-6": "Luna and Star were friends. Star's light helped Luna. They played together! 🌙✨",
        "6-8": "Maya loved books. Jake loved soccer. They won the talent show! ⚽📚",
        "8-10": "Emma met Marcus. They started a club. Their robot helped students! 🤖💙"
    },
    "animals": {
        "4-6": "Pip was small. He found fish. Pip became a hero! 🐧❄️",
        "6-8": "Zara had silver stripes. She helped a baby elephant. Zara saved the day! 🦓🌞",
        "8-10": "Kai had different eyes. He found water. Kai saved his pack! 🐺💧"
    },
    "magic": {
        "4-6": "Willow had sparkles. She found a teddy bear. Willow helped! ✨🧸",
        "6-8": "Oliver found a crystal. It showed feelings. Oliver helped a friend! 🔮🌈",
        "8-10": "Sophie talked to plants. She saved the forest. Sophie made a difference! 🌳🌿"
    }
}

# Pre-defined feedback responses for reading evaluation
DEBUG_FEEDBACK = {
    "excellent": [
        "Wow! You read that story perfectly! Your pronunciation was amazing and you didn't miss a single word. You're becoming such a great reader! 🌟⭐️",
        "Fantastic reading! You spoke clearly and with such confidence. I'm so proud of how well you're doing! Keep up the excellent work! 🎉📚",
        "Outstanding! You read every word correctly and your voice was so expressive. You're definitely ready for even more challenging stories! 🏆✨"
    ],
    "good": [
        "Great job! You read most of the words correctly. There were just a few small mistakes, but that's totally normal when learning to read. You're doing wonderfully! 🌟",
        "Nice work! You got most of the story right. With a little more practice, you'll be reading perfectly in no time! Keep it up! 📖💪",
        "Well done! You're making great progress with your reading. A few tricky words are normal - you're learning and getting better every day! 🎯"
    ],
    "needs_practice": [
        "Good effort! Reading can be tricky sometimes, but you're trying really hard and that's what matters most. Let's practice a bit more together! 🌱",
        "You're doing your best and that's wonderful! Some words are harder than others, but with practice, you'll get them all. I believe in you! 💙",
        "Keep trying! Every great reader started exactly where you are now. You're learning and growing, and that's the most important thing! 🌈"
    ]
}

def get_debug_story(prompt: str, age_group: str) -> str:
    """
    Get a pre-defined story for debug mode based on prompt and age group
    
    Args:
        prompt: The story prompt (used to determine story category)
        age_group: Target age group
        
    Returns:
        Pre-defined story text
    """
    # Simple keyword matching to determine story category
    prompt_lower = prompt.lower()
    
    if any(word in prompt_lower for word in ['adventure', 'explore', 'journey', 'quest']):
        category = 'adventure'
    elif any(word in prompt_lower for word in ['friend', 'friendship', 'together', 'help']):
        category = 'friendship'
    elif any(word in prompt_lower for word in ['animal', 'dog', 'cat', 'bird', 'fish', 'pet']):
        category = 'animals'
    elif any(word in prompt_lower for word in ['magic', 'wizard', 'fairy', 'spell', 'enchanted']):
        category = 'magic'
    else:
        # Default to adventure if no clear category
        category = 'adventure'
    
    # Get story for the category and age group
    stories = DEBUG_STORIES.get(category, DEBUG_STORIES['adventure'])
    return stories.get(age_group, stories['6-8'])  # Default to 6-8 if age group not found

def get_debug_feedback(original_story: str, spoken_text: str) -> str:
    """
    Get pre-defined feedback for debug mode based on reading accuracy
    
    Args:
        original_story: The original story text
        spoken_text: What the child read
        
    Returns:
        Pre-defined feedback text
    """
    import random
    
    # Simple accuracy calculation (word matching)
    original_words = set(original_story.lower().split())
    spoken_words = set(spoken_text.lower().split())
    
    # Calculate accuracy percentage
    if len(original_words) == 0:
        accuracy = 0
    else:
        accuracy = len(spoken_words.intersection(original_words)) / len(original_words)
    
    # Choose feedback based on accuracy
    if accuracy >= 0.9:
        feedback_type = "excellent"
    elif accuracy >= 0.7:
        feedback_type = "good"
    else:
        feedback_type = "needs_practice"
    
    # Return random feedback from the appropriate category
    feedbacks = DEBUG_FEEDBACK[feedback_type]
    return random.choice(feedbacks)
