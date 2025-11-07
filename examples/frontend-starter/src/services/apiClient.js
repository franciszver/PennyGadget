import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for adding auth token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    console.log('[API] Response error:', {
      status: error.response?.status,
      url: error.config?.url,
      message: error.message
    });
    
    if (error.response?.status === 401) {
      // Only clear auth if it's actually an auth endpoint or if we're in production
      // In development with mock auth, don't clear token on API 401s
      const isAuthEndpoint = error.config?.url?.includes('/auth') || error.config?.url?.includes('/login');
      const isDevelopment = import.meta.env.DEV || window.location.hostname === 'localhost';
      
      if (isAuthEndpoint || !isDevelopment) {
        console.log('[API] 401 on auth endpoint or production - clearing token');
        localStorage.removeItem('auth_token');
        localStorage.removeItem('user_id');
        localStorage.removeItem('user_role');
        window.location.href = '/login';
      } else {
        console.log('[API] 401 in development (mock auth) - keeping token, just logging error');
      }
    }
    return Promise.reject(error);
  }
);

// API methods
export const api = {
  // Summaries
  getSummaries: (userId) => apiClient.get(`/summaries/${userId}`),
  
  // Practice
  assignPractice: (data) => apiClient.post('/practice/assign', data),
  completePractice: (assignmentId, data) => 
    apiClient.post(`/practice/assignments/${assignmentId}/complete`, data),
  
  // Q&A
  submitQuery: (data) => apiClient.post('/qa/query', data),
  
  // Progress
  getProgress: (userId) => apiClient.get(`/progress/${userId}`),
  
  // Gamification
  getGamification: (userId) => apiClient.get(`/gamification/${userId}`),
  getLeaderboard: (params) => apiClient.get('/gamification/leaderboard', { params }),
  
  // Goals
  getGoals: (userId) => apiClient.get(`/goals?student_id=${userId}`),
  createGoal: (data) => apiClient.post('/goals', data),
  
  // Messaging
  getThreads: (userId) => apiClient.get(`/messaging/threads?user_id=${userId}`),
  sendMessage: (threadId, data) => 
    apiClient.post(`/messaging/threads/${threadId}/messages`, data),
};

export default apiClient;

