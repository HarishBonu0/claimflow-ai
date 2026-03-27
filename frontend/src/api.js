const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

function asUserFriendlyNetworkError(err, fallbackMessage) {
  const message = (err && err.message ? err.message : '').toLowerCase();
  if (message.includes('failed to fetch') || message.includes('networkerror')) {
    throw new Error(
      `Could not connect to server. Please ensure backend is running and reachable at ${API_BASE_URL}.`
    );
  }
  throw err || new Error(fallbackMessage);
}

export async function sendChatMessage(payload, options = {}) {
  let response;
  try {
    response = await fetch(`${API_BASE_URL}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
      signal: options.signal,
    });
  } catch (err) {
    if (err?.name === 'AbortError') {
      throw err;
    }
    asUserFriendlyNetworkError(err, 'Chat request failed');
  }

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Chat request failed' }));
    throw new Error(errorData.detail || 'Chat request failed');
  }

  return response.json();
}

export async function sendVoiceAudio(formData, options = {}) {
  let response;
  try {
    response = await fetch(`${API_BASE_URL}/voice`, {
      method: 'POST',
      body: formData,
      signal: options.signal,
    });
  } catch (err) {
    if (err?.name === 'AbortError') {
      throw err;
    }
    asUserFriendlyNetworkError(err, 'Voice request failed');
  }

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Voice request failed' }));
    throw new Error(errorData.detail || 'Voice request failed');
  }

  return response.json();
}

export async function uploadDocument(formData, options = {}) {
  let response;
  try {
    response = await fetch(`${API_BASE_URL}/upload`, {
      method: 'POST',
      body: formData,
      signal: options.signal,
    });
  } catch (err) {
    if (err?.name === 'AbortError') {
      throw err;
    }
    asUserFriendlyNetworkError(err, 'Upload failed');
  }

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Upload failed' }));
    throw new Error(errorData.detail || 'Upload failed');
  }

  return response.json();
}

export async function getHistory(sessionId) {
  let response;
  try {
    response = await fetch(`${API_BASE_URL}/history/${sessionId}`);
  } catch (err) {
    asUserFriendlyNetworkError(err, 'Failed to load history');
  }

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Failed to load history' }));
    throw new Error(errorData.detail || 'Failed to load history');
  }

  return response.json();
}

export async function getSessions(sessionToken) {
  let response;
  try {
    response = await fetch(
      `${API_BASE_URL}/sessions?session_token=${encodeURIComponent(sessionToken)}`
    );
  } catch (err) {
    asUserFriendlyNetworkError(err, 'Failed to load sessions');
  }

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Failed to load sessions' }));
    throw new Error(errorData.detail || 'Failed to load sessions');
  }

  return response.json();
}
