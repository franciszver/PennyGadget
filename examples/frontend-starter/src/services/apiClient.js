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
  assignPractice: (data) => {
    // FastAPI endpoint expects query parameters for POST /practice/assign
    const params = new URLSearchParams();
    Object.keys(data).forEach(key => {
      if (data[key] !== null && data[key] !== undefined) {
        if (Array.isArray(data[key])) {
          // Handle arrays (like goal_tags)
          data[key].forEach(item => params.append(key, item));
        } else {
          params.append(key, data[key]);
        }
      }
    });
    return apiClient.post(`/practice/assign?${params.toString()}`);
  },
  completePractice: (assignmentId, itemId, data) => 
    apiClient.post(`/practice/complete?assignment_id=${assignmentId}&item_id=${itemId}`, data),
  
  // Q&A
  submitQuery: (data) => apiClient.post('/qa/query', data),
  getConversationHistory: (userId, limit = 10, hours = 24) => 
    apiClient.get(`/enhancements/qa/conversation-history/${userId}?limit=${limit}&hours=${hours}`),
  
  // Progress
  getProgress: (userId) => apiClient.get(`/progress/${userId}`),
  
  // Goals
  getGoals: (userId) => apiClient.get(`/goals?student_id=${userId}`),
  createGoal: (data) => apiClient.post('/goals', data),
  deleteGoal: (goalId) => apiClient.delete(`/goals/${goalId}`),
  resetGoal: (goalId) => apiClient.post(`/goals/${goalId}/reset`),
  
  // Messaging
  getThreads: (userId) => apiClient.get(`/messaging/threads?user_id=${userId}`),
  sendMessage: (threadId, data) => 
    apiClient.post(`/messaging/threads/${threadId}/messages`, data),
  
  // Nudges
  getNudges: (userId) => apiClient.get(`/nudges/users/${userId}`),
  engageNudge: (nudgeId, engagementType) => 
    apiClient.post(`/nudges/${nudgeId}/engage`, { engagement_type: engagementType }),
};

export default apiClient;

