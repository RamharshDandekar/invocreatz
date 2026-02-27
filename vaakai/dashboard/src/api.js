const API_BASE = '/api/v1';

async function request(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'API Error');
  }
  return res.json();
}

// ── Analytics ──────────────────────────────────────────────
export const getAnalyticsSummary = (hours = 24) =>
  request(`/analytics/summary?hours=${hours}`);

export const getCallList = (limit = 50, offset = 0) =>
  request(`/analytics/calls?limit=${limit}&offset=${offset}`);

export const getSentimentTrends = (hours = 168) =>
  request(`/analytics/sentiment-trends?hours=${hours}`);

export const getLanguageDistribution = (hours = 720) =>
  request(`/analytics/language-distribution?hours=${hours}`);

export const getTopIntents = (limit = 10) =>
  request(`/analytics/top-intents?limit=${limit}`);

export const getFraudAlerts = (limit = 50) =>
  request(`/analytics/fraud-alerts?limit=${limit}`);

export const getPerformanceMetrics = (hours = 24) =>
  request(`/analytics/performance?hours=${hours}`);

// ── Admin ──────────────────────────────────────────────────
export const getActiveSessions = () =>
  request('/admin/sessions');

export const forceEndSession = (sessionId) =>
  request(`/admin/sessions/${sessionId}/end`, { method: 'POST' });

export const getRetrainQueue = () =>
  request('/admin/retrain-queue');

// ── Health ─────────────────────────────────────────────────
export const getHealth = () =>
  request('/health');
