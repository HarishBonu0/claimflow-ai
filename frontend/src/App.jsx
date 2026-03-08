import { useEffect, useMemo, useRef, useState } from 'react';
import { 
  Mic, 
  FileText, 
  Send, 
  LogOut, 
  MessageSquare,
  User,
  Mail,
  Lock
} from 'lucide-react';
import { getHistory, sendChatMessage, sendVoiceAudio, uploadDocument } from './api';

const LANGUAGES = [
  { label: 'English', code: 'en-IN' },
  { label: 'Telugu', code: 'te-IN' },
  { label: 'Hindi', code: 'hi-IN' },
  { label: 'Tamil', code: 'ta-IN' },
  { label: 'Kannada', code: 'kn-IN' },
];

const API_BASE = 'http://localhost:8000';

function generateLocalSessionId() {
  return `${Date.now()}-${Math.floor(Math.random() * 100000)}`;
}

function makeAudioBlob(base64Data) {
  const binary = atob(base64Data);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i += 1) {
    bytes[i] = binary.charCodeAt(i);
  }
  return new Blob([bytes], { type: 'audio/mpeg' });
}

// Helper function to convert base64 to Blob
function base64ToBlob(base64, mimeType) {
  const binary = atob(base64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) {
    bytes[i] = binary.charCodeAt(i);
  }
  return new Blob([bytes], { type: mimeType });
}

function App() {
  const [view, setView] = useState('landing');
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [authMode, setAuthMode] = useState('login');
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isGuestMode, setIsGuestMode] = useState(false);
  const [currentUser, setCurrentUser] = useState(null);
  const [sessionToken, setSessionToken] = useState(null);

  const [sessionId, setSessionId] = useState(null);
  const [chatHistory, setChatHistory] = useState([]);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [error, setError] = useState('');
  const [selectedLanguage, setSelectedLanguage] = useState(LANGUAGES[0].label);
  const [isSending, setIsSending] = useState(false);
  const [isListening, setIsListening] = useState(false);

  const [authForm, setAuthForm] = useState({ name: '', email: '', password: '' });

  const fileInputRef = useRef(null);
  const messageListRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const mediaStreamRef = useRef(null);
  const audioChunksRef = useRef([]);
  const autoStopTimerRef = useRef(null);

  const selectedSpeechLocale = useMemo(
    () => LANGUAGES.find((lang) => lang.label === selectedLanguage)?.code || 'en-IN',
    [selectedLanguage]
  );

  useEffect(() => {
    if (messageListRef.current) {
      messageListRef.current.scrollTop = messageListRef.current.scrollHeight;
    }
  }, [messages]);

  useEffect(() => () => {
    if (autoStopTimerRef.current) {
      clearTimeout(autoStopTimerRef.current);
    }
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach((track) => track.stop());
    }
  }, []);

  useEffect(() => {
    // Check for existing session token
    const token = localStorage.getItem('sessionToken');
    const guestMode = localStorage.getItem('guestMode');
    
    if (guestMode === 'true') {
      setIsGuestMode(true);
      setIsAuthenticated(false);
    } else if (token) {
      verifySession(token);
    }
  }, []);

  async function verifySession(token) {
    try {
      const response = await fetch(`${API_BASE}/auth/verify?session_token=${token}`);
      if (response.ok) {
        const data = await response.json();
        setSessionToken(token);
        setCurrentUser({ email: data.user_email, name: data.user_name });
        setIsAuthenticated(true);
      } else {
        localStorage.removeItem('sessionToken');
      }
    } catch {
      localStorage.removeItem('sessionToken');
    }
  }

  async function handleAuth(e) {
    e.preventDefault();
    setError('');

    const endpoint = authMode === 'login' ? '/auth/login' : '/auth/signup';
    const payload = authMode === 'login'
      ? { email: authForm.email, password: authForm.password }
      : { name: authForm.name, email: authForm.email, password: authForm.password };

    try {
      const response = await fetch(`${API_BASE}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Authentication failed');
      }

      const data = await response.json();
      setSessionToken(data.session_token);
      setCurrentUser({ email: data.user_email, name: data.user_name });
      setIsAuthenticated(true);
      setIsGuestMode(false);
      localStorage.setItem('sessionToken', data.session_token);
      localStorage.removeItem('guestMode');
      setShowAuthModal(false);
      setAuthForm({ name: '', email: '', password: '' });
      setView('chat');
    } catch (err) {
      setError(err.message || 'Authentication failed');
    }
  }

  function handleGuestMode() {
    setIsGuestMode(true);
    setIsAuthenticated(false);
    setCurrentUser(null);
    setSessionToken(null);
    localStorage.setItem('guestMode', 'true');
    localStorage.removeItem('sessionToken');
    setShowAuthModal(false);
    setView('chat');
  }

  async function handleLogout() {
    localStorage.removeItem('guestMode');
    setIsAuthenticated(false);
    setIsGuestMode(false);
    setCurrentUser(null);
    setSessionToken(null);
    setChatHistory([]);
    setMessages([]);
    setView('landing');
  }

  function goToChat() {
    if (!isAuthenticated && !isGuestMode) {
      setShowAuthModal(true);
      setAuthMode('login');
      return;
    }

    if (!sessionId) {
      const newId = generateLocalSessionId();
      setSessionId(newId);
      // Only save to history if not in guest mode
      if (!isGuestMode) {
        setChatHistory((prev) => [{ id: newId, title: 'New Chat', messages: [] }, ...prev]);
      }
    }
    setView('chat');
  }

  function syncChatHistory(currentSessionId, nextMessages) {
    // Don't save chat history in guest mode
    if (isGuestMode) return;

    setChatHistory((prev) => {
      const titleSource = nextMessages.find((msg) => msg.role === 'user')?.content || 'New Chat';
      const title = titleSource.length > 40 ? `${titleSource.slice(0, 40)}...` : titleSource;

      let found = false;
      const updated = prev.map((chat) => {
        if (chat.id === currentSessionId) {
          found = true;
          return { ...chat, title, messages: nextMessages };
        }
        return chat;
      });

      if (!found) {
        updated.unshift({ id: currentSessionId, title, messages: nextMessages });
      }

      return updated;
    });
  }

  function playBrowserTTS(text) {
    if (window.speechSynthesis) {
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = selectedSpeechLocale;
      window.speechSynthesis.cancel();
      window.speechSynthesis.speak(utterance);
    }
  }

  function startNewChat() {
    const newId = generateLocalSessionId();
    setSessionId(newId);
    setMessages([]);
    setInput('');
    setError('');
    // Only save to history if not in guest mode
    if (!isGuestMode) {
      setChatHistory((prev) => [{ id: newId, title: 'New Chat', messages: [] }, ...prev]);
    }
  }

  async function submitMessage(text) {
    const trimmed = text.trim();
    if (!trimmed || isSending) {
      return;
    }

    setError('');
    setIsSending(true);

    const currentSessionId = sessionId || generateLocalSessionId();
    if (!sessionId) {
      setSessionId(currentSessionId);
    }

    const nextMessages = [...messages, { role: 'user', content: trimmed }];
    setMessages(nextMessages);
    setInput('');

    try {
      const data = await sendChatMessage({ 
        message: trimmed, 
        session_id: currentSessionId,
        language: selectedLanguage  // Pass selected language to backend
      });

      if (data.session_id !== currentSessionId) {
        setSessionId(data.session_id);
      }
      if (data.language) {
        setSelectedLanguage(data.language);
      }

      const withAssistant = [...nextMessages, { role: 'assistant', content: data.response }];
      setMessages(withAssistant);
      syncChatHistory(data.session_id || currentSessionId, withAssistant);

      // Use backend-generated audio if available, otherwise fallback to browser TTS
      if (data.audio_base64) {
        try {
          const audioBlob = base64ToBlob(data.audio_base64, 'audio/mpeg');
          const audioUrl = URL.createObjectURL(audioBlob);
          const audio = new Audio(audioUrl);
          audio.play();
          // Clean up the URL after playing
          audio.onended = () => URL.revokeObjectURL(audioUrl);
        } catch (audioErr) {
          // Fallback to browser TTS
          playBrowserTTS(data.response);
        }
      } else {
        // Fallback to browser TTS if backend didn't provide audio
        playBrowserTTS(data.response);
      }
    } catch (err) {
      setError(err.message || 'Failed to send message.');
    } finally {
      setIsSending(false);
    }
  }

  function startSpeechRecognition(retryCount = 0) {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
      setError('Speech recognition is not supported in this browser.');
      return;
    }

    setError('');

    const recognition = new SpeechRecognition();
    recognition.lang = selectedSpeechLocale;
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    recognition.onstart = () => {
      setIsListening(true);
    };

    recognition.onerror = (event) => {
      recognition.stop();
      if (retryCount < 1) {
        startSpeechRecognition(retryCount + 1);
      } else {
        setIsListening(false);
        setError(
          event?.error === 'language-not-supported'
            ? `${selectedLanguage} speech recognition is not fully supported in this browser.`
            : 'Speech recognition failed after retry. Please try again.'
        );
      }
    };

    recognition.onend = () => {
      setIsListening(false);
    };

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      submitMessage(transcript);
    };

    recognition.start();
  }

  function getRecordingMimeType() {
    if (typeof MediaRecorder === 'undefined' || !MediaRecorder.isTypeSupported) {
      return '';
    }

    const supportedTypes = [
      'audio/webm;codecs=opus',
      'audio/webm',
      'audio/mp4',
      'audio/ogg;codecs=opus',
    ];

    return supportedTypes.find((type) => MediaRecorder.isTypeSupported(type)) || '';
  }

  function releaseMediaResources() {
    if (autoStopTimerRef.current) {
      clearTimeout(autoStopTimerRef.current);
      autoStopTimerRef.current = null;
    }

    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach((track) => track.stop());
      mediaStreamRef.current = null;
    }

    mediaRecorderRef.current = null;
  }

  async function submitRecordedAudio(audioBlob) {
    if (!audioBlob || !audioBlob.size || isSending) {
      return;
    }

    setError('');
    setIsSending(true);

    const currentSessionId = sessionId || generateLocalSessionId();
    if (!sessionId) {
      setSessionId(currentSessionId);
    }

    const extension = (audioBlob.type.split('/')[1] || 'webm').split(';')[0];
    const formData = new FormData();
    formData.append('session_id', currentSessionId);
    formData.append('preferred_language', selectedLanguage);
    formData.append('audio', audioBlob, `voice-input.${extension}`);

    try {
      const data = await sendVoiceAudio(formData);

      if (data.session_id !== currentSessionId) {
        setSessionId(data.session_id);
      }
      if (data.language) {
        setSelectedLanguage(data.language);
      }

      const userTranscript = data.transcript?.trim() || 'Voice message received';
      setMessages((prevMessages) => {
        const nextMessages = [
          ...prevMessages,
          { role: 'user', content: userTranscript },
          { role: 'assistant', content: data.response },
        ];
        syncChatHistory(data.session_id || currentSessionId, nextMessages);
        return nextMessages;
      });

      if (data.audio_base64) {
        const audioResponseBlob = makeAudioBlob(data.audio_base64);
        const audioUrl = URL.createObjectURL(audioResponseBlob);
        const audio = new Audio(audioUrl);
        audio.onended = () => URL.revokeObjectURL(audioUrl);
        audio.play().catch(() => URL.revokeObjectURL(audioUrl));
      } else if (window.speechSynthesis) {
        const utterance = new SpeechSynthesisUtterance(data.response);
        utterance.lang = selectedSpeechLocale;
        window.speechSynthesis.cancel();
        window.speechSynthesis.speak(utterance);
      }
    } catch (err) {
      setError(err.message || 'Voice request failed. Please try again.');
    } finally {
      setIsSending(false);
    }
  }

  async function startAudioRecording() {
    if (isSending) {
      return;
    }

    const mediaDevices = navigator.mediaDevices;
    if (!mediaDevices?.getUserMedia || typeof MediaRecorder === 'undefined') {
      startSpeechRecognition(0);
      return;
    }

    setError('');

    try {
      const stream = await mediaDevices.getUserMedia({ audio: true });
      mediaStreamRef.current = stream;
      audioChunksRef.current = [];

      const mimeType = getRecordingMimeType();
      const recorder = mimeType ? new MediaRecorder(stream, { mimeType }) : new MediaRecorder(stream);
      mediaRecorderRef.current = recorder;

      recorder.onstart = () => {
        setIsListening(true);
      };

      recorder.ondataavailable = (event) => {
        if (event.data && event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      recorder.onerror = () => {
        setIsListening(false);
        releaseMediaResources();
        setError('Microphone recording failed. Trying browser speech mode...');
        startSpeechRecognition(0);
      };

      recorder.onstop = () => {
        setIsListening(false);
        const completeBlob = new Blob(audioChunksRef.current, { type: recorder.mimeType || 'audio/webm' });
        releaseMediaResources();

        if (!completeBlob.size) {
          setError('No clear audio captured. Please try again.');
          return;
        }

        submitRecordedAudio(completeBlob);
      };

      recorder.start();
      autoStopTimerRef.current = setTimeout(() => {
        if (mediaRecorderRef.current?.state === 'recording') {
          mediaRecorderRef.current.stop();
        }
      }, 9000);
    } catch {
      setIsListening(false);
      releaseMediaResources();
      setError('Microphone permission was denied or unavailable.');
    }
  }

  function stopAudioRecording() {
    if (mediaRecorderRef.current?.state === 'recording') {
      mediaRecorderRef.current.stop();
    }
  }

  function handleMicClick() {
    if (isListening) {
      stopAudioRecording();
      return;
    }
    startAudioRecording();
  }

  async function handleDocumentUpload(file) {
    if (!file || isSending) {
      return;
    }

    setError('');
    setIsSending(true);

    const currentSessionId = sessionId || generateLocalSessionId();
    if (!sessionId) {
      setSessionId(currentSessionId);
    }

    const formData = new FormData();
    formData.append('session_id', currentSessionId);
    formData.append('file', file);

    try {
      const data = await uploadDocument(formData);
      const docMessage = {
        role: 'assistant',
        content: `📄 Document processed: ${data.file_name}\n\n${data.summary}`,
      };
      const nextMessages = [...messages, docMessage];
      setMessages(nextMessages);
      syncChatHistory(data.session_id || currentSessionId, nextMessages);
    } catch (err) {
      setError(err.message || 'Document upload failed.');
    } finally {
      setIsSending(false);
    }
  }

  async function loadChat(chat) {
    setSessionId(chat.id);
    setMessages(chat.messages || []);
    setView('chat');

    try {
      const data = await getHistory(chat.id);
      setMessages(data.messages || []);
      if (data.last_detected_language) {
        setSelectedLanguage(data.last_detected_language);
      }
    } catch {
      // Keep local history if backend session has expired.
    }
  }

  function renderAuthModal() {
    if (!showAuthModal) return null;

    return (
      <div className="modal-overlay" onClick={() => setShowAuthModal(false)}>
        <div className="modal-content" onClick={(e) => e.stopPropagation()}>
          <button className="modal-close" onClick={() => setShowAuthModal(false)}>
            ×
          </button>
          
          <h2>{authMode === 'login' ? 'Login to ClaimFlow AI' : 'Create Account'}</h2>
          
          <div className="auth-toggle">
            <button
              className={authMode === 'login' ? 'active' : ''}
              onClick={() => {
                setAuthMode('login');
                setError('');
              }}
            >
              <User size={16} />
              Login
            </button>
            <button
              className={authMode === 'signup' ? 'active' : ''}
              onClick={() => {
                setAuthMode('signup');
                setError('');
              }}
            >
              <User size={16} />
              Sign Up
            </button>
          </div>

          <form onSubmit={handleAuth} className="auth-form">
            {authMode === 'signup' && (
              <div className="form-group">
                <label>
                  <User size={16} />
                  Name
                </label>
                <input
                  type="text"
                  value={authForm.name}
                  onChange={(e) => setAuthForm({ ...authForm, name: e.target.value })}
                  placeholder="Enter your name"
                  required={authMode === 'signup'}
                  minLength={2}
                />
              </div>
            )}
            
            <div className="form-group">
              <label>
                <Mail size={16} />
                Email
              </label>
              <input
                type="email"
                value={authForm.email}
                onChange={(e) => setAuthForm({ ...authForm, email: e.target.value })}
                placeholder="Enter your email"
                required
              />
            </div>
            
            <div className="form-group">
              <label>
                <Lock size={16} />
                Password
              </label>
              <input
                type="password"
                value={authForm.password}
                onChange={(e) => setAuthForm({ ...authForm, password: e.target.value })}
                placeholder="Enter your password"
                required
                minLength={6}
              />
            </div>

            {error && <div className="error-message">{error}</div>}

            <button type="submit" className="primary-btn full">
              {authMode === 'login' ? 'Login' : 'Sign Up'}
            </button>

          </form>

          <div className="guest-divider">
            <span>or</span>
          </div>

          <button
            type="button"
            className="guest-btn"
            onClick={handleGuestMode}
          >
            <MessageSquare size={16} />
            Continue as Guest
            <span className="guest-note">(Chat history won't be saved)</span>
          </button>
        </div>
      </div>
    );
  }

  function renderLandingPage() {
    return (
      <div className="landing-page">
        <header className="navbar">
          <div className="brand">
            <span className="logo-icon">🛡️</span>
            ClaimFlow AI
          </div>
          <div className="nav-actions">
            {isAuthenticated ? (
              <>
                <span className="user-name">Hello, {currentUser?.name}</span>
                <button type="button" className="secondary-btn" onClick={goToChat}>
                  Go to Chat
                </button>
                <button type="button" className="secondary-btn" onClick={handleLogout}>
                  Logout
                </button>
              </>
            ) : (
              <button type="button" className="primary-btn" onClick={goToChat}>
                Start Chat
              </button>
            )}
          </div>
        </header>

        <section className="hero">
          <div className="hero-left">
            <h1>ClaimFlow AI</h1>
            <h2>Your AI Assistant for Insurance Claims</h2>
            <p className="hero-description">
              Get instant answers about insurance claims, upload policy documents, 
              and speak in your preferred language. Our AI-powered assistant helps 
              you navigate the claims process with ease.
            </p>
            <div className="hero-actions">
              <button type="button" className="primary-btn large" onClick={goToChat}>
                Start Chat Now
              </button>
              <button type="button" className="secondary-btn large" onClick={goToChat}>
                Try Voice Assistant
              </button>
            </div>
            <div className="hero-stats">
              <div className="stat-item">
                <div className="stat-number">5</div>
                <div className="stat-label">Languages</div>
              </div>
              <div className="stat-item">
                <div className="stat-number">24/7</div>
                <div className="stat-label">Available</div>
              </div>
              <div className="stat-item">
                <div className="stat-number">AI</div>
                <div className="stat-label">Powered</div>
              </div>
            </div>
          </div>
          <div className="hero-right">
            <div className="hero-visual">
              <div className="chat-preview">
                <div className="preview-message user">What documents do I need for a claim?</div>
                <div className="preview-message assistant">I'll help you with that! For most insurance claims, you'll need...</div>
              </div>
            </div>
          </div>
        </section>

        <section className="features">
          <h3 className="section-title">Powerful Features</h3>
          <div className="feature-grid">
            <div className="feature-card">
              <div className="feature-icon">🌐</div>
              <h4>Multilingual Support</h4>
              <p>Communicate in English, Telugu, Hindi, Tamil, or Kannada with automatic language detection.</p>
            </div>
            <div className="feature-card">
              <div className="feature-icon">🎤</div>
              <h4>Voice Enabled</h4>
              <p>Ask questions using your voice and receive spoken responses in your language.</p>
            </div>
            <div className="feature-card">
              <div className="feature-icon">📄</div>
              <h4>Document Analysis</h4>
              <p>Upload policy documents (PDF, JPG, PNG) and get instant answers about their content.</p>
            </div>
            <div className="feature-card">
              <div className="feature-icon">💡</div>
              <h4>Smart Guidance</h4>
              <p>Step-by-step assistance for claim filing, verification, and settlement processes.</p>
            </div>
          </div>
        </section>

        <footer className="landing-footer">
          <p>© 2026 ClaimFlow AI. Powered by Google Gemini 2.5 Flash.</p>
        </footer>

        {renderAuthModal()}
      </div>
    );
  }

  function renderChatInterface() {
    return (
      <div className="chat-app">
        <aside className="chat-sidebar">
          <div className="sidebar-header">
            <div className="brand-small">
              <span className="logo-icon">🛡️</span>
              ClaimFlow AI
            </div>
          </div>

          <button type="button" className="new-chat-btn" onClick={startNewChat}>
            <span className="btn-icon">+</span> New Chat
          </button>

          <div className="sidebar-section">
            <label htmlFor="language-select" className="sidebar-label">
              🌐 Language
            </label>
            <select
              id="language-select"
              value={selectedLanguage}
              onChange={(event) => setSelectedLanguage(event.target.value)}
              className="language-select"
            >
              {LANGUAGES.map((language) => (
                <option key={language.label} value={language.label}>
                  {language.label}
                </option>
              ))}
            </select>
          </div>

          <div className="sidebar-section">
            <div className="sidebar-label">💬 Chat History</div>
            <div className="history-list">
              {chatHistory.length === 0 ? (
                <div className="empty-history">No chat history yet</div>
              ) : (
                chatHistory.map((chat) => (
                  <button
                    type="button"
                    key={chat.id}
                    className={`history-item ${chat.id === sessionId ? 'active' : ''}`}
                    onClick={() => loadChat(chat)}
                  >
                    {chat.title}
                  </button>
                ))
              )}
            </div>
          </div>

          <div className="sidebar-footer">
            {isGuestMode ? (
              <div className="guest-info">
                <div className="guest-badge">
                  <MessageSquare size={16} />
                  Guest Mode
                </div>
                <p className="guest-warning">Chat history not saved</p>
                <button className="logout-btn" onClick={handleLogout}>
                  <User size={16} />
                  Sign In
                </button>
              </div>
            ) : (
              <>
                <div className="user-info">
                  <div className="user-avatar">{currentUser?.name?.charAt(0).toUpperCase() || 'U'}</div>
                  <div className="user-details">
                    <div className="user-name">{currentUser?.name || 'User'}</div>
                    <div className="user-email">{currentUser?.email || ''}</div>
                  </div>
                </div>
                <button className="logout-btn" onClick={handleLogout}>
                  <LogOut size={16} />
                  Logout
                </button>
              </>
            )}
          </div>
        </aside>

        <main className="chat-main">
          <div className="chat-header">
            <h2>Chat Assistant</h2>
            <button type="button" className="home-btn" onClick={() => setView('landing')}>
              🏠 Home
            </button>
          </div>

          <div className="message-list" ref={messageListRef}>
            {messages.length === 0 ? (
              <div className="empty-chat">
                <div className="empty-icon">💬</div>
                <h3>Start a Conversation</h3>
                <p>Ask about insurance claims, upload documents, or use voice queries.</p>
                <div className="suggestion-chips">
                  <button onClick={() => submitMessage("What is insurance?")}>
                    What is insurance?
                  </button>
                  <button onClick={() => submitMessage("How do I file a claim?")}>
                    How do I file a claim?
                  </button>
                  <button onClick={() => submitMessage("What documents do I need?")}>
                    What documents do I need?
                  </button>
                </div>
              </div>
            ) : (
              messages.map((msg, index) => (
                <div key={`${msg.role}-${index}`} className={`message-row ${msg.role}`}>
                  <div className="message-avatar">
                    {msg.role === 'user' ? (currentUser?.name?.charAt(0).toUpperCase() || 'U') : '🤖'}
                  </div>
                  <div className="message-content">
                    <div className="message-bubble">{msg.content}</div>
                  </div>
                </div>
              ))
            )}
            {isSending && (
              <div className="message-row assistant">
                <div className="message-avatar">🤖</div>
                <div className="message-content">
                  <div className="message-bubble typing">
                    <span></span><span></span><span></span>
                  </div>
                </div>
              </div>
            )}
          </div>

          {error && (
            <div className="error-banner">
              <span className="error-icon">⚠️</span>
              {error}
              <button onClick={() => setError('')}>×</button>
            </div>
          )}

          <div className="chat-input-container">
            <form
              className="chat-input-form"
              onSubmit={(event) => {
                event.preventDefault();
                submitMessage(input);
              }}
            >
              <div className="input-actions-left">
                <button
                  type="button"
                  className="icon-btn"
                  onClick={() => fileInputRef.current?.click()}
                  disabled={isSending}
                  title="Upload Document"
                >
                  <FileText size={20} />
                </button>
                <button
                  type="button"
                  className={`icon-btn ${isListening ? 'listening' : ''}`}
                  onClick={handleMicClick}
                  disabled={isSending}
                  title={isListening ? 'Stop Recording' : 'Voice Input'}
                >
                  <Mic size={20} />
                </button>
              </div>

              <input
                type="text"
                value={input}
                onChange={(event) => setInput(event.target.value)}
                placeholder="Ask about insurance claims..."
                disabled={isSending}
                className="message-input"
              />

              <button
                type="submit"
                className="send-btn"
                disabled={isSending || !input.trim()}
                title="Send Message"
              >
                <Send size={20} />
              </button>
            </form>

            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.jpg,.jpeg,.png"
              className="hidden-input"
              onChange={(event) => {
                const file = event.target.files?.[0];
                if (file) {
                  handleDocumentUpload(file);
                  event.target.value = '';
                }
              }}
            />
          </div>
        </main>
      </div>
    );
  }

  return view === 'landing' ? renderLandingPage() : renderChatInterface();
}

export default App;
