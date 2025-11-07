/**
 * API Client for AI Study Companion (Axios version)
 * Alternative implementation using Axios
 */

import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

/**
 * Create Axios instance with default config
 */
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Request interceptor - Add authentication
 */
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('authToken');
    const apiKey = process.env.REACT_APP_API_KEY;

    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    } else if (apiKey) {
      config.headers['X-API-Key'] = apiKey;
    }

    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

/**
 * Response interceptor - Handle errors
 */
apiClient.interceptors.response.use(
  (response) => {
    // Return data directly if success
    if (response.data.success) {
      return response.data;
    }
    return response.data;
  },
  (error) => {
    // Handle API errors
    if (error.response) {
      const apiError = new Error(
        error.response.data?.error?.message || `HTTP error! status: ${error.response.status}`
      );
      apiError.status = error.response.status;
      apiError.code = error.response.data?.error?.code;
      apiError.details = error.response.data?.error?.details;
      return Promise.reject(apiError);
    }

    // Network errors
    if (error.request) {
      return Promise.reject(new Error('Network error: Unable to connect to server'));
    }

    return Promise.reject(error);
  }
);

/**
 * API methods
 */
export const api = {
  // Session Summaries
  createSummary: (summaryData) => apiClient.post('/summaries', summaryData),
  getSummaries: (userId, params) => apiClient.get(`/summaries/${userId}`, { params }),

  // Practice Assignment
  assignPractice: (studentId, subject, options) =>
    apiClient.post('/practice/assign', null, {
      params: { student_id: studentId, subject, ...options },
    }),
  completePractice: (assignmentId, itemId, completionData) =>
    apiClient.post('/practice/complete', null, {
      params: { assignment_id: assignmentId, item_id: itemId, ...completionData },
    }),

  // Q&A
  submitQuery: (queryData) => apiClient.post('/qa/query', queryData),

  // Progress Dashboard
  getProgress: (userId, includeSuggestions = true) =>
    apiClient.get(`/progress/${userId}`, {
      params: { include_suggestions: includeSuggestions },
    }),

  // Nudges
  checkNudges: (studentId) => apiClient.get('/nudges/check', { params: { student_id: studentId } }),
  engageNudge: (nudgeId) => apiClient.post(`/nudges/${nudgeId}/engage`),

  // Overrides
  createOverride: (overrideData) => apiClient.post('/overrides', overrideData),
  getOverrides: (studentId) => apiClient.get(`/overrides/${studentId}`),
};

export default api;

