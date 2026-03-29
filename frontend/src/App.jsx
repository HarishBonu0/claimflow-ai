import { useEffect, useMemo, useRef, useState } from 'react';
import { 
  Mic, 
  FileText, 
  Send, 
  Square,
  LogOut, 
  MessageSquare,
  User,
  Mail,
  Lock
} from 'lucide-react';
import { 
  getHistory, 
  getSessions, 
  deleteSession,
  sendChatMessage, 
  sendVoiceAudio, 
  uploadDocument,
  signup,
  login,
  logout,
  verifySession,
} from './api';

const LANGUAGES = [
  { label: 'English', code: 'en-IN' },
  { label: 'Telugu', code: 'te-IN' },
  { label: 'Hindi', code: 'hi-IN' },
  { label: 'Tamil', code: 'ta-IN' },
  { label: 'Kannada', code: 'kn-IN' },
];

const LANGUAGE_LABEL_TO_LOCALE = Object.fromEntries(
  LANGUAGES.map((lang) => [lang.label, lang.code])
);

const API_BASE =
  import.meta.env.VITE_API_BASE_URL || 'https://claimflow-api.onrender.com';

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

function buildChatTitleFromMessages(messages) {
  const firstUserMessage = messages.find((msg) => msg.role === 'user')?.content?.trim();
  if (!firstUserMessage) {
    return 'New Chat';
  }

  const normalized = firstUserMessage.replace(/\s+/g, ' ');
  const keywords = normalized.split(' ').slice(0, 6).join(' ');
  if (keywords.length <= 38) {
    return keywords;
  }
  return `${keywords.slice(0, 38)}...`;
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
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isMobileHistoryOpen, setIsMobileHistoryOpen] = useState(false);

  const [authForm, setAuthForm] = useState({ name: '', email: '', password: '' });

  const fileInputRef = useRef(null);
  const messageListRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const mediaStreamRef = useRef(null);
  const audioChunksRef = useRef([]);
  const autoStopTimerRef = useRef(null);
  const requestControllerRef = useRef(null);
  const activeAudioRef = useRef(null);
  const recognitionRef = useRef(null);

  const selectedSpeechLocale = useMemo(
    () => LANGUAGES.find((lang) => lang.label === selectedLanguage)?.code || 'en-IN',
    [selectedLanguage]
  );

  function getSpeechLocaleFromLabel(languageLabel) {
    return LANGUAGE_LABEL_TO_LOCALE[languageLabel] || selectedSpeechLocale;
  }

  function inferLanguageLabelFromTranscript(text) {
    if (!text || !text.trim()) {
      return null;
    }

    // Prefer script-based detection for reliable Indic language routing.
    for (const ch of text) {
      const code = ch.codePointAt(0);
      if (code >= 0x0900 && code <= 0x097f) return 'Hindi';
      if (code >= 0x0c00 && code <= 0x0c7f) return 'Telugu';
      if (code >= 0x0b80 && code <= 0x0bff) return 'Tamil';
      if (code >= 0x0c80 && code <= 0x0cff) return 'Kannada';
    }

    // Fallback heuristics for transliterated text from browser STT.
    const lower = text.toLowerCase();
    if (/\b(namaste|kaise|mujhe|kya|nahi|hain|hai|mera|meri|claim kaise)\b/.test(lower)) return 'Hindi';
    if (/\b(namaskaram|nenu|ela|chesi|cheyyali|naaku|meeru|claim ela)\b/.test(lower)) return 'Telugu';
    if (/\b(vanakkam|eppadi|naan|ungal|enakku|seyyalam|claim eppadi)\b/.test(lower)) return 'Tamil';
    if (/\b(namaskara|hegide|nanu|nanage|maadodu|hege|claim hege)\b/.test(lower)) return 'Kannada';

    return null;
  }

  function resolveVoiceLanguageLabel(transcript) {
    const inferred = inferLanguageLabelFromTranscript(transcript);
    if (inferred) {
      return inferred;
    }

    // If user explicitly selected a non-English language, honor it for voice response.
    if (selectedLanguage && selectedLanguage !== 'English') {
      return selectedLanguage;
    }

    // Undefined lets backend auto-detect from content.
    return undefined;
  }

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
    if (requestControllerRef.current) {
      requestControllerRef.current.abort();
      requestControllerRef.current = null;
    }
    if (activeAudioRef.current) {
      activeAudioRef.current.pause();
      activeAudioRef.current = null;
    }
    if (window.speechSynthesis) {
      window.speechSynthesis.cancel();
    }
    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch {
        // no-op
      }
      recognitionRef.current = null;
    }
  }, []);

  async function loadUserSessions(token) {
    if (!token) {
      setChatHistory([]);
      return;
    }

    try {
      const data = await getSessions(token);
      const sessions = (data.sessions || []).map((session) => ({
        id: session.id,
        title: session.title || 'New Chat',
        messages: [],
      }));
      setChatHistory(sessions);
    } catch {
      setChatHistory([]);
    }
  }

  useEffect(() => {
    // Check for existing session token
    const token = localStorage.getItem('sessionToken');
    const guestMode = localStorage.getItem('guestMode');
    
    if (guestMode === 'true') {
      setIsGuestMode(true);
      setIsAuthenticated(false);
    } else if (token) {
      verifyExistingSession(token);
    }
  }, []);

  async function verifyExistingSession(token) {
    try {
      const data = await verifySession(token);
      setSessionToken(token);
      setCurrentUser({ email: data.user_email, name: data.user_name });
      setIsAuthenticated(true);
      await loadUserSessions(token);
    } catch (err) {
      console.warn('Session verification failed:', err);
      localStorage.removeItem('sessionToken');
    }
  }

  async function handleAuth(e) {
    e.preventDefault();
    setError('');

    try {
      let data;
      if (authMode === 'login') {
        data = await login(authForm.email, authForm.password);
      } else {
        data = await signup(authForm.name, authForm.email, authForm.password);
      }

      setSessionToken(data.session_token);
      setCurrentUser({ email: data.user_email, name: data.user_name });
      setIsAuthenticated(true);
      setIsGuestMode(false);
      localStorage.setItem('sessionToken', data.session_token);
      localStorage.removeItem('guestMode');
      await loadUserSessions(data.session_token);
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
    if (sessionToken) {
      try {
        await logout(sessionToken);
      } catch (err) {
        console.warn('Logout request failed, proceeding with local cleanup:', err);
      }
    }

    localStorage.removeItem('guestMode');
    localStorage.removeItem('sessionToken');
    setIsAuthenticated(false);
    setIsGuestMode(false);
    setCurrentUser(null);
    setSessionToken(null);
    setSessionId(null);
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
      if (isGuestMode) {
        const newId = generateLocalSessionId();
        setSessionId(newId);
      }
    }
    setView('chat');
  }

  function syncChatHistory(currentSessionId, nextMessages) {
    setChatHistory((prev) => {
      const title = buildChatTitleFromMessages(nextMessages);

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

  function stopSpeechRecognition() {
    if (!recognitionRef.current) {
      return;
    }
    try {
      recognitionRef.current.stop();
    } catch {
      // no-op: recognition can already be stopped
    }
    recognitionRef.current = null;
    setIsListening(false);
  }

  function speakAssistantResponse(text, languageLabel) {
    if (!text || !window.speechSynthesis) {
      return;
    }

    window.speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = getSpeechLocaleFromLabel(languageLabel || selectedLanguage);

    utterance.onstart = () => {
      console.info('[TTS] Speech start', {
        language: utterance.lang,
        textPreview: text.slice(0, 120),
      });
      setIsSpeaking(true);
    };

    utterance.onend = () => {
      console.info('[TTS] Speech end');
      setIsSpeaking(false);
    };

    utterance.onerror = (event) => {
      console.warn('[TTS] Speech error', event?.error || event);
      setIsSpeaking(false);
    };

    window.speechSynthesis.speak(utterance);
  }

  function stopConversation() {
    stopSpeechRecognition();

    if (requestControllerRef.current) {
      requestControllerRef.current.abort();
      requestControllerRef.current = null;
    }

    if (activeAudioRef.current) {
      activeAudioRef.current.pause();
      activeAudioRef.current.currentTime = 0;
      activeAudioRef.current = null;
    }

    if (window.speechSynthesis) {
      window.speechSynthesis.cancel();
    }
    setIsSpeaking(false);

    setIsSending(false);
    setError('Response stopped. You can send a new question.');
  }

  function startNewChat() {
    setIsMobileHistoryOpen(false);
    if (isGuestMode) {
      const newId = generateLocalSessionId();
      setSessionId(newId);
      setChatHistory((prev) => [{ id: newId, title: 'New Chat', messages: [] }, ...prev]);
    } else {
      setSessionId(null);
    }
    setMessages([]);
    setInput('');
    setError('');
  }

  async function submitMessage(text, options = {}) {
    const { fromVoice = false } = options;
    const trimmed = text.trim();
    if (!trimmed || isSending) {
      return;
    }

    const requestLanguage = fromVoice ? resolveVoiceLanguageLabel(trimmed) : selectedLanguage;

    setError('');
    setIsSending(true);
    const controller = new AbortController();
    requestControllerRef.current = controller;

    const currentSessionId = sessionId || (isGuestMode ? generateLocalSessionId() : null);
    if (currentSessionId && !sessionId) {
      setSessionId(currentSessionId);
    }

    const nextMessages = [...messages, { role: 'user', content: trimmed }];
    setMessages(nextMessages);
    setInput('');

    try {
      const data = await sendChatMessage({ 
        message: trimmed, 
        session_id: currentSessionId,
        language: requestLanguage,
        session_token: sessionToken,
        include_audio: fromVoice,
      }, { signal: controller.signal });

      console.info('[Chat] API response', {
        source: fromVoice ? 'voice' : 'text',
        requestedLanguage: requestLanguage || 'auto-detect',
        sessionId: data.session_id,
        language: data.language,
        responsePreview: (data.response || '').slice(0, 160),
      });

      if (data.session_id !== currentSessionId) {
        setSessionId(data.session_id);
      }

      const withAssistant = [...nextMessages, { role: 'assistant', content: data.response }];
      setMessages(withAssistant);
      syncChatHistory(data.session_id || currentSessionId, withAssistant);

      // Only speak for mic-originated messages.
      if (fromVoice) {
        if (activeAudioRef.current) {
          activeAudioRef.current.pause();
          activeAudioRef.current.currentTime = 0;
          activeAudioRef.current = null;
        }

        if (data.audio_base64) {
          const audioResponseBlob = makeAudioBlob(data.audio_base64);
          const audioUrl = URL.createObjectURL(audioResponseBlob);
          const audio = new Audio(audioUrl);
          activeAudioRef.current = audio;

          audio.onplay = () => {
            console.info('[TTS] Playing backend audio response', { language: data.language });
            setIsSpeaking(true);
          };
          audio.onended = () => {
            URL.revokeObjectURL(audioUrl);
            setIsSpeaking(false);
            activeAudioRef.current = null;
          };
          audio.onerror = () => {
            URL.revokeObjectURL(audioUrl);
            setIsSpeaking(false);
            activeAudioRef.current = null;
            console.warn('[TTS] Backend audio playback failed, falling back to browser TTS');
            speakAssistantResponse(data.response, data.language);
          };

          audio.play().catch(() => {
            URL.revokeObjectURL(audioUrl);
            setIsSpeaking(false);
            activeAudioRef.current = null;
            console.warn('[TTS] Backend audio play() rejected, falling back to browser TTS');
            speakAssistantResponse(data.response, data.language);
          });
        } else {
          speakAssistantResponse(data.response, data.language);
        }
      }
    } catch (err) {
      if (err?.name === 'AbortError') {
        return;
      }
      setError(err.message || 'Failed to send message.');
    } finally {
      requestControllerRef.current = null;
      setIsSending(false);
    }
  }

  function startSpeechRecognition(retryCount = 0) {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
      // Fallback to backend audio upload pipeline when browser STT is unavailable.
      startAudioRecording();
      return;
    }

    // Ensure only one recognizer instance is active.
    stopSpeechRecognition();
    if (window.speechSynthesis) {
      window.speechSynthesis.cancel();
    }
    setIsSpeaking(false);

    setError('');

    const recognition = new SpeechRecognition();
    recognitionRef.current = recognition;
    recognition.lang = selectedSpeechLocale;
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    recognition.onstart = () => {
      console.info('[STT] Recognition started', { lang: recognition.lang });
      setIsListening(true);
    };

    recognition.onerror = (event) => {
      console.warn('[STT] Recognition error', event?.error || event);
      stopSpeechRecognition();
      if (retryCount < 1) {
        startSpeechRecognition(retryCount + 1);
      } else {
        setError(
          event?.error === 'language-not-supported'
            ? `${selectedLanguage} speech recognition is not fully supported in this browser.`
            : 'Speech recognition failed after retry. Please try again.'
        );
      }
    };

    recognition.onend = () => {
      console.info('[STT] Recognition ended');
      recognitionRef.current = null;
      setIsListening(false);
    };

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      console.info('[STT] Recognized text', { transcript });
      setInput(transcript);
      submitMessage(transcript, { fromVoice: true });
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
    const controller = new AbortController();
    requestControllerRef.current = controller;

    const currentSessionId = sessionId || (isGuestMode ? generateLocalSessionId() : null);
    if (currentSessionId && !sessionId) {
      setSessionId(currentSessionId);
    }

    const extension = (audioBlob.type.split('/')[1] || 'webm').split(';')[0];
    const formData = new FormData();
    if (currentSessionId) {
      formData.append('session_id', currentSessionId);
    }
    if (sessionToken) {
      formData.append('session_token', sessionToken);
    }
    formData.append('preferred_language', selectedLanguage);
    formData.append('audio', audioBlob, `voice-input.${extension}`);

    try {
      const data = await sendVoiceAudio(formData, { signal: controller.signal });

      if (data.session_id !== currentSessionId) {
        setSessionId(data.session_id);
      }

      const userTranscript = data.transcript_translated?.trim() || data.transcript?.trim() || 'Voice message received';
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
        activeAudioRef.current = audio;
        audio.onended = () => URL.revokeObjectURL(audioUrl);
        audio.play().catch(() => URL.revokeObjectURL(audioUrl));
      } else if (window.speechSynthesis) {
        const utterance = new SpeechSynthesisUtterance(data.response);
        utterance.lang = getSpeechLocaleFromLabel(data.language);
        window.speechSynthesis.cancel();
        window.speechSynthesis.speak(utterance);
      }
    } catch (err) {
      if (err?.name === 'AbortError') {
        return;
      }
      const message = err?.message || 'Voice request failed. Please try again.';
      if (message.toLowerCase().includes('could not clearly recognize')) {
        setError('Voice recognition fallback is active. Please speak again.');
        startSpeechRecognition(0);
      } else {
        setError(message);
      }
    } finally {
      requestControllerRef.current = null;
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
      stopSpeechRecognition();
      return;
    }
    // Primary path: browser STT is more reliable across environments without ffmpeg/whisper setup.
    // submitMessage(..., { fromVoice: true }) still uses backend TTS audio for multilingual speech output.
    startSpeechRecognition(0);
  }

  async function handleDocumentUpload(file) {
    if (!file || isSending) {
      return;
    }

    setError('');
    setIsSending(true);

    const currentSessionId = sessionId || (isGuestMode ? generateLocalSessionId() : null);
    if (currentSessionId && !sessionId) {
      setSessionId(currentSessionId);
    }

    const formData = new FormData();
    if (currentSessionId) {
      formData.append('session_id', currentSessionId);
    }
    if (sessionToken) {
      formData.append('session_token', sessionToken);
    }
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
    setIsMobileHistoryOpen(false);
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

  async function handleDeleteChat(chatId, event) {
    event.stopPropagation();

    if (!window.confirm('Delete this chat permanently? This will remove it from the database.')) {
      return;
    }

    setError('');

    // Guest mode has no server-backed history persistence in UI.
    if (isGuestMode) {
      setChatHistory((prev) => prev.filter((chat) => chat.id !== chatId));
      if (sessionId === chatId) {
        setSessionId(null);
        setMessages([]);
      }
      return;
    }

    if (!sessionToken) {
      setError('Please login again to delete chats.');
      return;
    }

    try {
      await deleteSession(chatId, sessionToken);
      setChatHistory((prev) => prev.filter((chat) => chat.id !== chatId));
      if (sessionId === chatId) {
        setSessionId(null);
        setMessages([]);
      }
    } catch (err) {
      setError(err.message || 'Failed to delete chat.');
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
            <span className="logo-icon" aria-hidden="true"></span>
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
            <h2>Your AI Assistant for Insurance and Finance</h2>
            <p className="hero-description">
              Get practical guidance on insurance claims, coverage, budgeting, investing,
              risk analysis, and financial planning. Speak in your preferred language and
              receive clear, actionable responses.
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
                <div className="preview-message user">How do I file a claim and plan my monthly budget?</div>
                <div className="preview-message assistant">I can guide you on both insurance steps and a practical finance plan.</div>
              </div>
              <div className="hero-graph">
                <div className="graph-title">Financial Progress Trend</div>
                <svg viewBox="0 0 320 90" role="img" aria-label="Financial progress trend rising over time">
                  <polyline points="10,70 70,62 120,55 170,48 220,36 270,28 310,18" />
                  <circle cx="10" cy="70" r="3" />
                  <circle cx="120" cy="55" r="3" />
                  <circle cx="220" cy="36" r="3" />
                  <circle cx="310" cy="18" r="4" />
                </svg>
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
              <p>Communicate in English, Telugu, Hindi, Tamil, or Kannada with voice and text support.</p>
            </div>
            <div className="feature-card">
              <div className="feature-icon">🎤</div>
              <h4>Voice Enabled</h4>
              <p>Ask finance questions by voice and get spoken responses in your selected language.</p>
            </div>
            <div className="feature-card">
              <div className="feature-icon">📄</div>
              <h4>Insurance + Finance Coverage</h4>
              <p>Get support for claims, policy questions, budgeting, investing, and financial planning.</p>
            </div>
            <div className="feature-card">
              <div className="feature-icon">💡</div>
              <h4>Safe Financial Insights</h4>
              <p>Risk-aware, practical guidance for money decisions with transparent limitations.</p>
            </div>
          </div>
        </section>

        <footer className="landing-footer">
          <p>© 2026 ClaimFlow AI. Powered by Google Gemini.</p>
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
              <span className="logo-icon" aria-hidden="true"></span>
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

          <div className="sidebar-section chat-history-section">
            <button
              type="button"
              className="mobile-history-toggle"
              onClick={() => setIsMobileHistoryOpen((prev) => !prev)}
              aria-expanded={isMobileHistoryOpen}
              aria-controls="mobile-history-panel"
            >
              <span>💬 Chat History</span>
              <span aria-hidden="true">{isMobileHistoryOpen ? '▲' : '▼'}</span>
            </button>

            <div
              id="mobile-history-panel"
              className={`history-list-wrapper ${isMobileHistoryOpen ? 'open' : ''}`}
            >
              <div className="sidebar-label desktop-history-label">💬 Chat History</div>
              <div className="history-list">
                {chatHistory.length === 0 ? (
                  <div className="empty-history">No chat history yet</div>
                ) : (
                  chatHistory.map((chat) => (
                    <div
                      key={chat.id}
                      style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
                    >
                      <button
                        type="button"
                        className={`history-item ${chat.id === sessionId ? 'active' : ''}`}
                        onClick={() => loadChat(chat)}
                        style={{ flex: 1 }}
                      >
                        {chat.title}
                      </button>
                      <button
                        type="button"
                        className="icon-btn"
                        onClick={(event) => handleDeleteChat(chat.id, event)}
                        title="Delete chat"
                        aria-label={`Delete chat ${chat.title}`}
                      >
                        ×
                      </button>
                    </div>
                  ))
                )}
              </div>
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
            <h2>Finance Assistant</h2>
            <button type="button" className="home-btn" onClick={() => setView('landing')}>
              🏠 Home
            </button>
          </div>

          <div className="message-list" ref={messageListRef}>
            {messages.length === 0 ? (
              <div className="empty-chat">
                <div className="empty-icon">💬</div>
                <h3>Start a Conversation</h3>
                <p>Ask about insurance, claims, budgeting, investing, risk analysis, or financial planning.</p>
                <div className="suggestion-chips">
                  <button onClick={() => submitMessage("How do I file an insurance claim?") }>
                    How do I file an insurance claim?
                  </button>
                  <button onClick={() => submitMessage("How should I start investing with low risk?")}>
                    How should I start investing with low risk?
                  </button>
                  <button onClick={() => submitMessage("Help me with claim settlement and monthly budgeting") }>
                    Help me with claim settlement and monthly budgeting
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
                placeholder="Ask about insurance claims, budgeting, investing, or financial planning..."
                disabled={isSending}
                className="message-input"
              />

              <button
                  type={isSending ? 'button' : 'submit'}
                  className={isSending ? 'stop-btn' : 'send-btn'}
                  onClick={isSending ? stopConversation : undefined}
                  disabled={!isSending && !input.trim()}
                  title={isSending ? 'Stop Response' : 'Send Message'}
              >
                  {isSending ? <Square size={20} /> : <Send size={20} />}
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
