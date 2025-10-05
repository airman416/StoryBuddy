const { useState, useEffect, useRef } = React;

// StoryInput Component - simplified for young children
function StoryInput({ onGenerate, isGenerating }) {
  const [prompt, setPrompt] = useState("A happy cat plays with a ball");

  const handleSubmit = () => {
    if (prompt.trim()) {
      onGenerate(prompt, "3-4");
    }
  };

  return (
    <div className="story-controls">
      <textarea
        className="story-input"
        placeholder="What story? 🐱🐶🐰"
        rows="2"
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
      />
      
      <button
        className="create-button"
        onClick={handleSubmit}
        disabled={isGenerating}
      >
        {isGenerating ? '⏳' : '✨'}
      </button>
    </div>
  );
}

// EmojiDisplay Component - now supports multiple emojis
function EmojiDisplay({ emojis }) {
  if (!emojis || emojis.length === 0) return null;

  return (
    <div className="emoji-display">
      <div className="emoji-content">
        {emojis.map((emoji, idx) => (
          <span key={idx} className="emoji-item" style={{ margin: '0 10px' }}>
            {emoji}
          </span>
        ))}
      </div>
    </div>
  );
}

// WordWindow Component
function WordWindow({ words, currentIndexInWindow }) {
  const displayWords = [...words];
  
  // Pad with empty strings if needed
  while (displayWords.length < 5) {
    displayWords.push('');
  }

  return (
    <div className="story-container">
      <div className="word-window">
        {displayWords.map((word, idx) => (
          <div
            key={idx}
            className={`word-slot ${idx === currentIndexInWindow ? 'highlight' : ''}`}
            style={{ display: word ? 'flex' : 'none' }}
          >
            {word}
          </div>
        ))}
      </div>
    </div>
  );
}

// PlaybackControls Component
function PlaybackControls({
  isPlaying,
  showControls,
  onPlay,
  onPause,
  onPrevious,
  onNext,
  onReplay
}) {
  if (!showControls) return null;

  return (
    <div className="progress-controls">
      <div className="main-controls">
        <button onClick={onPrevious} className="prev-button">⬅️</button>
        
        {isPlaying ? (
          <button onClick={onPause}>⏸️</button>
        ) : (
          <button onClick={onPlay}>▶️</button>
        )}
        
        <button onClick={onReplay} className="replay-button">🔄</button>
        <button onClick={onNext} className="next-button">➡️</button>
      </div>
    </div>
  );
}

// Main App Component
function App() {
  const [story, setStory] = useState('');
  const [words, setWords] = useState([]);
  const [currentWordIndex, setCurrentWordIndex] = useState(0);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [showControls, setShowControls] = useState(false);
  const [feedback, setFeedback] = useState({ message: '', type: '' });
  const [wordAudioList, setWordAudioList] = useState([]);
  const [streamingWords, setStreamingWords] = useState([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [generatedSets, setGeneratedSets] = useState(new Set());
  const [requestedSets, setRequestedSets] = useState(new Set());
  const [currentEmojis, setCurrentEmojis] = useState([]);
  
  const wsRef = useRef(null);
  const currentAudioRef = useRef(null);
  const isPlayingRef = useRef(false);
  const streamingWordsRef = useRef([]);
  const generatedSetsRef = useRef(new Set());
  const requestedSetsRef = useRef(new Set());

  // Keep refs in sync with state
  useEffect(() => {
    streamingWordsRef.current = streamingWords;
  }, [streamingWords]);

  useEffect(() => {
    generatedSetsRef.current = generatedSets;
  }, [generatedSets]);

  useEffect(() => {
    requestedSetsRef.current = requestedSets;
  }, [requestedSets]);

  // Initialize WebSocket
  useEffect(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/stream-words`;
    
    try {
      const ws = new WebSocket(wsUrl);
      
      ws.onopen = () => {
        console.log('WebSocket connected');
      };
      
      ws.onmessage = (event) => {
        const message = JSON.parse(event.data);
        handleWebSocketMessage(message);
      };
      
      ws.onclose = () => {
        console.log('WebSocket disconnected');
      };
      
      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
      
      wsRef.current = ws;
      
      return () => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.close();
        }
      };
    } catch (error) {
      console.error('Failed to create WebSocket:', error);
    }
  }, []);

  const handleWebSocketMessage = (message) => {
    switch (message.type) {
      case 'story_set':
        console.log(`Story set with ${message.total_words} words`);
        setStreamingWords(new Array(message.total_words).fill(null));
        streamingWordsRef.current = new Array(message.total_words).fill(null);
        
        // Request the first set (set 0) immediately
        requestSetIfNeeded(0);
        break;
        
      case 'set_generation_started':
        console.log(`Starting generation of set ${message.set_index} (words ${message.start_index}-${message.end_index-1})`);
        setIsStreaming(true);
        break;
        
      case 'word_ready':
        setStreamingWords(prev => {
          const updated = [...prev];
          updated[message.index] = {
            word: message.word,
            audio: message.audio,
            index: message.index,
            cached: message.cached,
            is_emoji: message.is_emoji
          };
          
          // Auto-start playback when first word is ready
          if (message.index === 0 && !isPlayingRef.current) {
            console.log('Starting auto-playback with first word');
            setIsPlaying(true);
            isPlayingRef.current = true;
            setCurrentWordIndex(0);
            
            // Use setTimeout to ensure ref is updated
            setTimeout(() => {
              playNextStreamingWordFromRef(0, 0);
            }, 150);
          }
          
          return updated;
        });
        break;
        
      case 'set_generation_complete':
        console.log(`Set ${message.set_index} generation complete`);
        setGeneratedSets(prev => {
          const updated = new Set(prev);
          updated.add(message.set_index);
          return updated;
        });
        setIsStreaming(false);
        break;
        
      case 'word_error':
        console.error(`Error generating word ${message.index}: ${message.error}`);
        break;
    }
  };

  const requestSetIfNeeded = (setIndex) => {
    // Check if set is already requested or generated
    if (requestedSetsRef.current.has(setIndex) || generatedSetsRef.current.has(setIndex)) {
      return;
    }
    
    // Mark as requested
    setRequestedSets(prev => {
      const updated = new Set(prev);
      updated.add(setIndex);
      return updated;
    });
    
    // Send request to websocket
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      console.log(`Requesting set ${setIndex}`);
      wsRef.current.send(JSON.stringify({
        type: 'generate_set',
        set_index: setIndex
      }));
    }
  };

  const ensureSetsLoaded = (currentSetIndex) => {
    // Ensure current set and next set are loaded
    requestSetIfNeeded(currentSetIndex);
    requestSetIfNeeded(currentSetIndex + 1);
  };

  const playNextStreamingWordFromRef = async (wordIndex, startIndex) => {
    if (!isPlayingRef.current) {
      return;
    }
    
    // Check if we've finished the current 5-word set BEFORE playing
    const wordsPlayedInSet = wordIndex - startIndex;
    if (wordsPlayedInSet >= 5) {
      setIsPlaying(false);
      isPlayingRef.current = false;
      // Keep the index at the last word of the completed set
      setCurrentWordIndex(wordIndex - 1);
      return;
    }
    
    const wordsList = streamingWordsRef.current;
    if (wordIndex >= wordsList.length) {
      setIsPlaying(false);
      isPlayingRef.current = false;
      return;
    }

    const wordData = wordsList[wordIndex];
    if (!wordData) {
      // Word not ready yet, wait a bit and try again
      setTimeout(() => {
        playNextStreamingWordFromRef(wordIndex, startIndex);
      }, 100);
      return;
    }

    // Update current word for display
    setCurrentWordIndex(wordIndex);

    // Skip emojis
    if (wordData.is_emoji || !wordData.audio) {
      setTimeout(() => {
        playNextStreamingWordFromRef(wordIndex + 1, startIndex);
      }, 300);
      return;
    }

    try {
      const audioBlob = new Blob(
        [Uint8Array.from(atob(wordData.audio), c => c.charCodeAt(0))],
        { type: 'audio/mpeg' }
      );
      const audioUrl = URL.createObjectURL(audioBlob);
      const audio = new Audio(audioUrl);
      
      currentAudioRef.current = audio;
      
      await audio.play();
      
      await new Promise((resolve) => {
        audio.onended = resolve;
        audio.onerror = resolve;
      });
      
      URL.revokeObjectURL(audioUrl);
      currentAudioRef.current = null;
      
      // Calculate pause based on punctuation
      let pauseDuration = 200;
      if (wordData.word.match(/[.!?]$/)) {
        pauseDuration = 800;
      } else if (wordData.word.match(/[,;:]$/)) {
        pauseDuration = 400;
      }
      
      setTimeout(() => {
        playNextStreamingWordFromRef(wordIndex + 1, startIndex);
      }, pauseDuration);
      
    } catch (error) {
      console.error('Error playing word:', error);
      playNextStreamingWordFromRef(wordIndex + 1, startIndex);
    }
  };

  const showFeedbackMessage = (message, type) => {
    // No feedback messages for young children
  };

  const fetchEmojiForCurrentWindow = async (windowWords) => {
    if (windowWords.length === 0) return;
    
    const wordsText = windowWords.join(' ');
    try {
      const response = await fetch('/api/generate-emoji', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ words: wordsText })
      });

      if (response.ok) {
        const data = await response.json();
        // Parse multiple emojis from response
        const emojiString = data.emoji || '📖🌟✨';
        // Extract all emojis using regex (handles most emoji ranges including combined emojis)
        const emojiRegex = /[\u{1F300}-\u{1F9FF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}\u{FE00}-\u{FE0F}\u{1F900}-\u{1F9FF}\u{1F018}-\u{1F270}\u{238C}-\u{2454}\u{20D0}-\u{20FF}]+/gu;
        const matches = emojiString.match(emojiRegex) || ['📖', '🌟', '✨'];
        // Split into individual emojis (handling combined emojis)
        const emojis = matches.join('').match(/[\u{1F600}-\u{1F64F}\u{1F300}-\u{1F5FF}\u{1F680}-\u{1F6FF}\u{1F700}-\u{1F77F}\u{1F780}-\u{1F7FF}\u{1F800}-\u{1F8FF}\u{1F900}-\u{1F9FF}\u{1FA00}-\u{1FA6F}\u{1FA70}-\u{1FAFF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}\u{FE00}-\u{FE0F}](?:\u{FE0F})?(?:\u{200D}[\u{1F000}-\u{1FFFF}](?:\u{FE0F})?)*|[\u{2600}-\u{27BF}]/gu) || ['📖', '🌟', '✨'];
        setCurrentEmojis(emojis.slice(0, 5)); // Limit to 5 emojis max
      }
    } catch (error) {
      console.error('Error fetching emoji:', error);
      setCurrentEmojis(['📖']);
    }
  };

  // Update emoji when window changes
  useEffect(() => {
    if (words.length > 0 && showControls) {
      const windowStart = Math.floor(currentWordIndex / 5) * 5;
      const windowWords = words.slice(windowStart, windowStart + 5);
      fetchEmojiForCurrentWindow(windowWords);
    }
  }, [Math.floor(currentWordIndex / 5), words.length, showControls]);

  const handleGenerate = async (prompt, ageGroup) => {
    setIsGenerating(true);
    setStory('');
    setWords([]);
    setCurrentWordIndex(0);
    setStreamingWords([]);
    setWordAudioList([]);
    setGeneratedSets(new Set());
    setRequestedSets(new Set());
    generatedSetsRef.current = new Set();
    requestedSetsRef.current = new Set();
    
    try {
      const response = await fetch('/api/generate-story', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt, age_group: ageGroup })
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }

      const data = await response.json();
      setStory(data.story);
      
      const storyWords = data.story.split(/\s+/).filter(w => w.length > 0);
      setWords(storyWords);
      setShowControls(true);
      
      // Send story to WebSocket for on-demand generation
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({
          type: 'set_story',
          text: data.story
        }));
      } else {
        // Fallback to regular generation
        generateAudioFallback(data.story);
      }
      
    } catch (error) {
      console.error('Error generating story:', error);
    }
    
    setIsGenerating(false);
  };

  const generateAudioFallback = async (text) => {
    try {
      const response = await fetch('/api/text-to-speech-word-by-word', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text })
      });

      if (!response.ok) {
        throw new Error(`TTS API error: ${response.status}`);
      }

      const data = await response.json();
      setWordAudioList(data.word_audio_list);
      
      // Auto-start playback from the beginning
      setCurrentWordIndex(0);
      setIsPlaying(true);
      isPlayingRef.current = true;
      
      setTimeout(() => {
        playNextWord(0, data.word_audio_list, 0);
      }, 100);
    } catch (error) {
      console.error('Error generating audio:', error);
    }
  };

  const handlePlay = () => {
    setIsPlaying(true);
    isPlayingRef.current = true;
    
    const startIndex = Math.floor(currentWordIndex / 5) * 5;
    const currentSet = Math.floor(currentWordIndex / 5);
    
    // Ensure current set and next set are loaded
    ensureSetsLoaded(currentSet);
    
    if (streamingWords.length > 0) {
      playNextStreamingWordFromRef(currentWordIndex, startIndex);
    } else if (wordAudioList.length > 0) {
      playNextWord(currentWordIndex, wordAudioList, startIndex);
    }
  };

  const playNextWord = async (wordIndex, audioList, startIndex) => {
    if (!isPlayingRef.current) {
      return;
    }
    
    // Check if we've finished the current 5-word set BEFORE playing
    const wordsPlayedInSet = wordIndex - startIndex;
    if (wordsPlayedInSet >= 5) {
      setIsPlaying(false);
      isPlayingRef.current = false;
      // Keep the index at the last word of the completed set
      setCurrentWordIndex(wordIndex - 1);
      return;
    }
    
    if (wordIndex >= audioList.length) {
      setIsPlaying(false);
      isPlayingRef.current = false;
      return;
    }

    const wordData = audioList[wordIndex];
    setCurrentWordIndex(wordIndex);

    if (wordData.is_emoji || !wordData.audio) {
      setTimeout(() => playNextWord(wordIndex + 1, audioList, startIndex), 300);
      return;
    }

    try {
      const audioBlob = new Blob(
        [Uint8Array.from(atob(wordData.audio), c => c.charCodeAt(0))],
        { type: 'audio/mpeg' }
      );
      const audioUrl = URL.createObjectURL(audioBlob);
      const audio = new Audio(audioUrl);
      
      currentAudioRef.current = audio;
      await audio.play();
      
      await new Promise((resolve) => {
        audio.onended = resolve;
        audio.onerror = resolve;
      });
      
      URL.revokeObjectURL(audioUrl);
      currentAudioRef.current = null;
      
      let pauseDuration = 200;
      if (wordData.word.match(/[.!?]$/)) {
        pauseDuration = 800;
      } else if (wordData.word.match(/[,;:]$/)) {
        pauseDuration = 400;
      }
      
      setTimeout(() => playNextWord(wordIndex + 1, audioList, startIndex), pauseDuration);
    } catch (error) {
      console.error('Error playing word:', error);
      playNextWord(wordIndex + 1, audioList, startIndex);
    }
  };

  const handlePause = () => {
    setIsPlaying(false);
    isPlayingRef.current = false;
    
    if (currentAudioRef.current) {
      currentAudioRef.current.pause();
    }
  };

  const handlePrevious = () => {
    const prevSetStart = Math.floor(currentWordIndex / 5) * 5 - 5;
    if (prevSetStart < 0) {
      return;
    }
    
    if (currentAudioRef.current) {
      currentAudioRef.current.pause();
    }
    
    const prevSet = Math.floor(prevSetStart / 5);
    
    // Ensure previous set is loaded
    ensureSetsLoaded(prevSet);
    
    setCurrentWordIndex(prevSetStart);
    setIsPlaying(true);
    isPlayingRef.current = true;
    
    setTimeout(() => {
      if (streamingWords.length > 0) {
        playNextStreamingWordFromRef(prevSetStart, prevSetStart);
      } else {
        playNextWord(prevSetStart, wordAudioList, prevSetStart);
      }
    }, 100);
  };

  const handleNext = () => {
    // Check if we're already at the start of the current set
    // If so, play this set. Otherwise, move to next set.
    const currentSetStart = Math.floor(currentWordIndex / 5) * 5;
    let nextSetStart;
    
    if (currentWordIndex === currentSetStart) {
      // We're at the start of a set, play it
      nextSetStart = currentSetStart;
    } else {
      // We're in the middle, go to next set
      nextSetStart = currentSetStart + 5;
    }
    
    if (nextSetStart >= words.length) {
      return;
    }
    
    if (currentAudioRef.current) {
      currentAudioRef.current.pause();
    }
    
    const nextSet = Math.floor(nextSetStart / 5);
    
    // Ensure next set and the one after are loaded
    ensureSetsLoaded(nextSet);
    
    setCurrentWordIndex(nextSetStart);
    setIsPlaying(true);
    isPlayingRef.current = true;
    
    setTimeout(() => {
      if (streamingWords.length > 0) {
        playNextStreamingWordFromRef(nextSetStart, nextSetStart);
      } else {
        playNextWord(nextSetStart, wordAudioList, nextSetStart);
      }
    }, 100);
  };

  const handleReplay = () => {
    const currentSet = Math.floor(currentWordIndex / 5);
    const replayStart = currentSet * 5;
    
    if (currentAudioRef.current) {
      currentAudioRef.current.pause();
    }
    
    // Ensure current set is loaded
    ensureSetsLoaded(currentSet);
    
    setCurrentWordIndex(replayStart);
    setIsPlaying(true);
    isPlayingRef.current = true;
    
    setTimeout(() => {
      if (streamingWords.length > 0) {
        playNextStreamingWordFromRef(replayStart, replayStart);
      } else {
        playNextWord(replayStart, wordAudioList, replayStart);
      }
    }, 100);
  };

  // Calculate window words for display
  const windowStart = Math.floor(currentWordIndex / 5) * 5;
  const windowWords = words.slice(windowStart, windowStart + 5);
  const currentWordInWindow = currentWordIndex % 5;

  return (
    <div className="container">
      <div className="header">
        <h1>✨ Story Magic ✨</h1>
      </div>

      <StoryInput 
        onGenerate={handleGenerate}
        isGenerating={isGenerating}
      />

      <EmojiDisplay emojis={currentEmojis} />

      <WordWindow 
        words={windowWords}
        currentIndexInWindow={currentWordInWindow}
      />

      <PlaybackControls
        isPlaying={isPlaying}
        showControls={showControls}
        onPlay={handlePlay}
        onPause={handlePause}
        onPrevious={handlePrevious}
        onNext={handleNext}
        onReplay={handleReplay}
      />
    </div>
  );
}

// Render the app
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
