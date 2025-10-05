# StoryBuddy - DevPost Submission

## Elevator Pitch
**Turn any prompt into a personalized reading lesson**

---

## Inspiration

My dad teaching me to read when I was young was pivotal to my growth. I remember his finger slowly moving under each word as he read aloud, celebrating when I got it right. That patient, one-on-one attention made all the difference.

But not every child has someone who can sit with them for hours, reading at their pace. What if we could give every child that same personalized reading experience? That's why I built StoryBuddy—an AI companion that reads word by word, at each kid's own pace.

---

## What It Does

StoryBuddy transforms any prompt into an interactive reading lesson for ages 3-6:

1. **Gemini generates** age-appropriate stories from prompts like "a baby elephant named Ember"
2. **ElevenLabs creates** natural narration for each word individually
3. **Words highlight** as they're spoken, connecting text with sound
4. **Contextual visuals update** based on story segments—Gemini analyzes content
5. **Kids control** their pace with play/pause and navigation

Result: Unlimited personalized stories that teach reading through content kids actually care about.

---

## How We Built It

**Stack:** React + FastAPI + WebSockets + Gemini 2.0 Flash + ElevenLabs

**Key Architecture:**
- **WebSocket streaming** - Stories split into 5-word sets, generated on-demand. First word plays in ~2 seconds while others generate in background
- **Word-level caching** - Common words cached after first use, reducing costs by 60% and improving speed
- **Optimized voice settings** - Tuned ElevenLabs for clear enunciation (stability 0.98, similarity 0.95) perfect for learning
- **Smart timing** - Natural pauses based on punctuation (800ms for periods, 400ms for commas)

---

## Challenges We Ran Into

**Real-time streaming:** Generating all audio upfront took 20 seconds. Solved with WebSocket streaming—split into sets, start playback immediately, generate in background. Wait time: 2 seconds.

**Voice enunciation:** Default TTS too fast for kids. Maxed stability/similarity settings and appended ellipses to force elongation. Result: remarkably clear pronunciation.

**Caching complexity:** Normalizing words for cache keys while preserving originals. Built JSON-based system with 60% hit rate after 10 stories.

**WebSocket state:** Audio wouldn't pause correctly. Used refs for immediate state alongside React state for rendering.

---

## Accomplishments We're Proud Of

- **Tested with real kids** - A 4-year-old asked for multiple stories (unicorns, then her dog). It works.
- **Production-ready** - WebSocket streaming, caching, error handling built to scale
- **Smart API orchestration** - Multi-turn Gemini (story generation + contextual analysis), word-level ElevenLabs, learning cache
- **Natural voice** - Sounds like a patient teacher, not a robot

---

## What We Learned

- **WebSockets are powerful but tricky** - State management between React, WebSocket, and audio refs requires careful coordination
- **Voice AI is surprisingly tunable** - Small setting adjustments dramatically improve output for specific use cases
- **Caching is critical** - AI economics don't work without it. Costs dropped from $0.15 to $0.05 per story
- **Kids need simplicity** - Big buttons, visual feedback, minimal text
- **Multimodal AI is powerful** - Gemini + ElevenLabs creates experiences neither could alone

---

## What's Next for StoryBuddy

- **AI-generated images/videos** that sync with the story
- **Interactive choices** - Kids decide what happens next
- **Expressive animations** - Words bounce, shimmer based on meaning
- **Read-along mode** - Kids read aloud, get gentle feedback
- **Reading progress tracking** for parents
- **Multiple voices** for character dialogue
- **Multilingual support** - Help kids learn in any language

---

## Try It Out
- **GitHub:** [Your repo link]
- **Live Demo:** [If deployed]
- **Video Demo:** [If you make one]

## Prize Tracks
- Google Gemini API Prize
- ElevenLabs Prize  
- Best Consumer-Facing Application

---

*Built for young readers everywhere*
