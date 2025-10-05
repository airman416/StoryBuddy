const { useState, useEffect, useRef } = React;

// StoryInput Component
function StoryInput({ onGenerate, isGenerating }) {
  const [prompt, setPrompt] = useState("A curious cat exploring a magical garden");
  const [ageGroup, setAgeGroup] = useState("6-8");

  const handleSubmit = () => {
    if (prompt.trim()) {
      onGenerate(prompt, ageGroup);
    }
  };

  return (
    <div className="controls">
      <div className="input-group story-input-group">
        <label htmlFor="storyPrompt">📖 Story Idea</label>
        <textarea
          id="storyPrompt"
          placeholder="A brave little mouse..."
          rows="3"
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && e.ctrlKey) {
              handleSubmit();
            }
          }}
        />
      </div>
      
      <div className="input-group">
        <label htmlFor="ageGroup">👶 Age</label>
        <select
          id="ageGroup"
          value={ageGroup}
          onChange={(e) => setAgeGroup(e.target.value)}
        >
          <option value="4-6">4-6 👶</option>
          <option value="6-8">6-8 🧒</option>
          <option value="8-10">8-10 👦</option>
        </select>
      </div>
      
      <button
        onClick={handleSubmit}
        disabled={isGenerating}
      >
        {isGenerating ? '✨ Creating...' : '✨ Create Story'}
      </button>
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
  currentWordIndex,
  totalWords,
  onPlay,
  onPause,
  onPrevious,
  onNext,
  onReplay
}) {
  if (!showControls) return null;

  const currentSet = Math.floor(currentWordIndex / 5) + 1;
  const totalSets = Math.ceil(totalWords / 5);
  const remainingWords = totalWords - currentWordIndex;

  return (
    <div className="progress-controls">
      <div className="progress-indicator">
        {currentWordIndex >= totalWords 
          ? '🎉 All done!'
          : `📖 Set ${currentSet}/${totalSets} - ${remainingWords} words left`
        }
      </div>
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

// Feedback Component
function Feedback({ message, type }) {
  if (!message) return null;

  return (
    <div className={`feedback ${type}`}>
      {message}
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
  
  const wsRef = useRef(null);
  const currentAudioRef = useRef(null);
  const isPlayingRef = useRef(false);
  const streamingWordsRef = useRef([]);

  // Keep ref in sync with state
  useEffect(() => {
    streamingWordsRef.current = streamingWords;
  }, [streamingWords]);

  // Initialize WebSocket
  useEffect(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/stream-words`;
    
    try {
      const ws = new WebSocket(wsUrl);
      
      ws.onopen = () => {
        console.log('WebSocket connected');
        showFeedbackMessage('🎵 Connected for streaming audio!', 'success');
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
      case 'generation_started':
        console.log(`Starting streaming generation of ${message.total_words} words`);
        setStreamingWords([]);
        streamingWordsRef.current = [];
        setIsStreaming(true);
        showFeedbackMessage(`🎵 Starting streaming generation of ${message.total_words} words...`, 'success');
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
        
      case 'generation_complete':
        console.log(`Streaming generation complete: ${message.total_words} words`);
        setIsStreaming(false);
        showFeedbackMessage(`🎉 All ${message.total_words} words generated!`, 'success');
        break;
        
      case 'word_error':
        console.error(`Error generating word ${message.index}: ${message.error}`);
        break;
    }
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
      showFeedbackMessage('🎉 Set complete! Click ➡️ for next or 🔄 to replay!', 'success');
      return;
    }
    
    const wordsList = streamingWordsRef.current;
    if (wordIndex >= wordsList.length) {
      setIsPlaying(false);
      isPlayingRef.current = false;
      showFeedbackMessage('🎉 Story finished!', 'success');
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
    setFeedback({ message, type });
    setTimeout(() => {
      setFeedback({ message: '', type: '' });
    }, 5000);
  };

  const handleGenerate = async (prompt, ageGroup) => {
    setIsGenerating(true);
    setStory('');
    setWords([]);
    setCurrentWordIndex(0);
    setStreamingWords([]);
    setWordAudioList([]);
    
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
      
      showFeedbackMessage('Story created! Starting audio generation... 🎉', 'success');
      
      // Start streaming audio generation via WebSocket
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({
          type: 'generate_story',
          text: data.story
        }));
      } else {
        // Fallback to regular generation
        generateAudioFallback(data.story);
      }
      
    } catch (error) {
      console.error('Error generating story:', error);
      showFeedbackMessage('Error creating story. Please try again.', 'error');
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
      
      showFeedbackMessage(`🎵 Audio ready! ${data.word_audio_list.length} words generated!`, 'success');
      
      // Auto-start playback from the beginning
      setCurrentWordIndex(0);
      setIsPlaying(true);
      isPlayingRef.current = true;
      
      setTimeout(() => {
        playNextWord(0, data.word_audio_list, 0);
      }, 100);
    } catch (error) {
      console.error('Error generating audio:', error);
      showFeedbackMessage('Error generating audio.', 'error');
    }
  };

  const handlePlay = () => {
    setIsPlaying(true);
    isPlayingRef.current = true;
    
    const startIndex = Math.floor(currentWordIndex / 5) * 5;
    
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
      showFeedbackMessage('🎉 Set complete! Click ➡️ for next or 🔄 to replay!', 'success');
      return;
    }
    
    if (wordIndex >= audioList.length) {
      setIsPlaying(false);
      isPlayingRef.current = false;
      showFeedbackMessage('🎉 Story finished!', 'success');
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
    
    showFeedbackMessage('Paused ⏸️', 'success');
  };

  const handlePrevious = () => {
    const prevSetStart = Math.floor(currentWordIndex / 5) * 5 - 5;
    if (prevSetStart < 0) {
      showFeedbackMessage('Already at the beginning! 🎯', 'success');
      return;
    }
    
    if (currentAudioRef.current) {
      currentAudioRef.current.pause();
    }
    
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
    
    showFeedbackMessage('⬅️ Playing previous 5 words!', 'success');
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
      showFeedbackMessage('No more words! Story is complete! 🎉', 'success');
      return;
    }
    
    if (currentAudioRef.current) {
      currentAudioRef.current.pause();
    }
    
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
    
    showFeedbackMessage('➡️ Playing next 5 words!', 'success');
  };

  const handleReplay = () => {
    const currentSet = Math.floor(currentWordIndex / 5);
    const replayStart = currentSet * 5;
    
    if (currentAudioRef.current) {
      currentAudioRef.current.pause();
    }
    
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
    
    showFeedbackMessage('🔄 Replaying current 5 words!', 'success');
  };

  // Calculate window words for display
  const windowStart = Math.floor(currentWordIndex / 5) * 5;
  const windowWords = words.slice(windowStart, windowStart + 5);
  const currentWordInWindow = currentWordIndex % 5;

  return (
    <div className="container">
      <div className="header">
        <h1>🌟 Story Magic 🌟</h1>
        <p>Let's read together and have fun! 🎉</p>
      </div>

      <StoryInput 
        onGenerate={handleGenerate}
        isGenerating={isGenerating}
      />

      <WordWindow 
        words={windowWords}
        currentIndexInWindow={currentWordInWindow}
      />

      <PlaybackControls
        isPlaying={isPlaying}
        showControls={showControls}
        currentWordIndex={currentWordIndex}
        totalWords={words.length}
        onPlay={handlePlay}
        onPause={handlePause}
        onPrevious={handlePrevious}
        onNext={handleNext}
        onReplay={handleReplay}
      />

      <Feedback 
        message={feedback.message}
        type={feedback.type}
      />
    </div>
  );
}

// Render the app
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
