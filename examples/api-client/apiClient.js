/**
 * API Client for AI Study Companion
 * Base client with authentication and error handling
 */

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

/**
 * Get authentication token from AWS Cognito
 * This is a placeholder - implement based on your Cognito setup
 */
function getAuthToken() {
  // In a real app, get from Cognito or localStorage
  return localStorage.getItem('authToken') || '';
}

/**
 * Get API key for service-to-service requests
 */
function getApiKey() {
  return process.env.REACT_APP_API_KEY || '';
}

/**
 * Make API request with error handling
 */
async function apiRequest(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint}`;
  const token = getAuthToken();
  const apiKey = getApiKey();

  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  // Add authentication
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  } else if (apiKey) {
    headers['X-API-Key'] = apiKey;
  }

  const config = {
    ...options,
    headers,
  };

  try {
    const response = await fetch(url, config);

    // Handle non-JSON responses
    const contentType = response.headers.get('content-type');
    if (!contentType || !contentType.includes('application/json')) {
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return { success: true, data: await response.text() };
    }

    const data = await response.json();

    // Handle API errors
    if (!response.ok) {
      const error = new Error(data.error?.message || `HTTP error! status: ${response.status}`);
      error.status = response.status;
      error.code = data.error?.code;
      error.details = data.error?.details;
      throw error;
    }

    return data;
  } catch (error) {
    // Network errors
    if (error.name === 'TypeError' && error.message.includes('fetch')) {
      throw new Error('Network error: Unable to connect to server');
    }
    throw error;
  }
}

/**
 * API Client with methods for each endpoint
 */
export const apiClient = {
  // Session Summaries
  async createSummary(summaryData) {
    return apiRequest('/summaries', {
      method: 'POST',
      body: JSON.stringify(summaryData),
    });
  },

  async getSummaries(userId, params = {}) {
    const queryString = new URLSearchParams(params).toString();
    return apiRequest(`/summaries/${userId}${queryString ? `?${queryString}` : ''}`);
  },

  // Practice Assignment
  async assignPractice(studentId, subject, options = {}) {
    const params = new URLSearchParams({
      student_id: studentId,
      subject,
      ...options,
    });
    return apiRequest(`/practice/assign?${params}`);
  },

  async completePractice(assignmentId, itemId, completionData) {
    const params = new URLSearchParams({
      assignment_id: assignmentId,
      item_id: itemId,
      ...completionData,
    });
    return apiRequest(`/practice/complete?${params}`, {
      method: 'POST',
    });
  },

  // Q&A
  async submitQuery(queryData) {
    return apiRequest('/qa/query', {
      method: 'POST',
      body: JSON.stringify(queryData),
    });
  },

  // Progress Dashboard
  async getProgress(userId, includeSuggestions = true) {
    return apiRequest(`/progress/${userId}?include_suggestions=${includeSuggestions}`);
  },

  // Nudges
  async checkNudges(studentId) {
    return apiRequest(`/nudges/check?student_id=${studentId}`);
  },

  async engageNudge(nudgeId) {
    return apiRequest(`/nudges/${nudgeId}/engage`, {
      method: 'POST',
    });
  },

  // Overrides
  async createOverride(overrideData) {
    return apiRequest('/overrides', {
      method: 'POST',
      body: JSON.stringify(overrideData),
    });
  },

  async getOverrides(studentId) {
    return apiRequest(`/overrides/${studentId}`);
  },
};

export default apiClient;

