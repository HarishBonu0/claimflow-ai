const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

function asUserFriendlyNetworkError(err, fallbackMessage) {
  const message = (err && err.message ? err.message : '').toLowerCase();
  if (message.includes('failed to fetch') || message.includes('networkerror')) {
    throw new Error(
      'Could not connect to server. Please ensure backend is running on http://localhost:8000.'
    );
  }
  throw err || new Error(fallbackMessage);
}

export async function sendChatMessage(payload) {
  let response;
  try {
    response = await fetch(`${API_BASE_URL}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
  } catch (err) {
    asUserFriendlyNetworkError(err, 'Chat request failed');
  }

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Chat request failed' }));
    throw new Error(errorData.detail || 'Chat request failed');
  }

  return response.json();
}

export async function sendVoiceAudio(formData) {
  let response;
  try {
    response = await fetch(`${API_BASE_URL}/voice`, {
      method: 'POST',
      body: formData,
    });
  } catch (err) {
    asUserFriendlyNetworkError(err, 'Voice request failed');
  }

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Voice request failed' }));
    throw new Error(errorData.detail || 'Voice request failed');
  }

  return response.json();
}

export async function uploadDocument(formData) {
  let response;
  try {
    response = await fetch(`${API_BASE_URL}/upload`, {
      method: 'POST',
      body: formData,
    });
  } catch (err) {
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
