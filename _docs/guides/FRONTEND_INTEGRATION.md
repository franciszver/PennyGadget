# Frontend Integration Guide

## Overview

This guide helps frontend developers integrate the AI Study Companion API into React applications.

---

## 📦 **Installation**

### **Option 1: Using Fetch (Native)**
No additional dependencies needed - uses native `fetch` API.

### **Option 2: Using Axios**
```bash
npm install axios
```

---

## 🔐 **Authentication**

### **AWS Cognito Integration**

The API uses JWT tokens from AWS Cognito for user authentication.

```javascript
// Get token from Cognito
import { Auth } from 'aws-amplify';

async function getAuthToken() {
  try {
    const session = await Auth.currentSession();
    return session.getIdToken().getJwtToken();
  } catch (error) {
    console.error('Error getting token:', error);
    return null;
  }
}

// Store token
localStorage.setItem('authToken', token);
```

### **Service-to-Service Authentication**

For service-to-service requests (e.g., from Rails backend), use API key:

```javascript
const headers = {
  'X-API-Key': process.env.REACT_APP_API_KEY,
};
```

---

## 📡 **API Client Setup**

### **Using Fetch (examples/api-client/apiClient.js)**

```javascript
import apiClient from './api-client/apiClient';

// All methods return promises
const result = await apiClient.getProgress(userId);
```

### **Using Axios (examples/api-client/apiClientAxios.js)**

```javascript
import api from './api-client/apiClientAxios';

// All methods return promises
const result = await api.getProgress(userId);
```

---

## 🎨 **React Component Examples**

### **1. Q&A Component**

Submit queries and display AI responses with confidence levels.

**File**: `examples/react/QAComponent.jsx`

**Features**:
- Query submission
- Confidence display
- Clarification requests
- Escalation suggestions

**Usage**:
```jsx
import QAComponent from './examples/react/QAComponent';

<QAComponent studentId="student-uuid" />
```

---

### **2. Progress Dashboard**

Display student goals, progress, and suggestions.

**File**: `examples/react/ProgressDashboard.jsx`

**Features**:
- Goal tracking
- Progress visualization
- Empty state handling
- Related subject suggestions
- Insights display

**Usage**:
```jsx
import ProgressDashboard from './examples/react/ProgressDashboard';

<ProgressDashboard userId="user-uuid" />
```

---

### **3. Practice Assignment**

Request and complete practice items.

**File**: `examples/react/PracticeAssignment.jsx`

**Features**:
- Practice item requests
- Adaptive difficulty
- Completion tracking
- Performance feedback

**Usage**:
```jsx
import PracticeAssignment from './examples/react/PracticeAssignment';

<PracticeAssignment studentId="student-uuid" />
```

---

## 🔄 **Error Handling**

### **Error Response Format**

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input parameters",
    "details": {
      "field": "student_id",
      "reason": "Student ID is required"
    }
  }
}
```

### **Error Handling Example**

```javascript
try {
  const result = await apiClient.submitQuery(queryData);
  // Handle success
} catch (error) {
  // Handle different error types
  if (error.status === 401) {
    // Unauthorized - redirect to login
    window.location.href = '/login';
  } else if (error.status === 404) {
    // Not found
    console.error('Resource not found:', error.message);
  } else if (error.status === 400) {
    // Validation error
    console.error('Validation error:', error.details);
  } else {
    // Other errors
    console.error('Error:', error.message);
  }
}
```

### **Error Codes**

- `VALIDATION_ERROR` (400) - Invalid input
- `UNAUTHORIZED` (401) - Missing or invalid authentication
- `FORBIDDEN` (403) - Insufficient permissions
- `NOT_FOUND` (404) - Resource not found
- `INTERNAL_ERROR` (500) - Server error
- `SERVICE_UNAVAILABLE` (503) - External service unavailable

---

## 📋 **API Endpoints**

### **Session Summaries**

```javascript
// Create summary (from Rails backend)
await apiClient.createSummary({
  session_id: 'session-uuid',
  student_id: 'student-uuid',
  tutor_id: 'tutor-uuid',
  transcript: 'Session transcript...',
  session_duration_minutes: 45,
  subject: 'Algebra',
  topics_covered: ['quadratic_equations']
});

// Get summaries
await apiClient.getSummaries(userId, {
  role: 'student',
  limit: 20,
  offset: 0
});
```

### **Practice Assignment**

```javascript
// Assign practice
await apiClient.assignPractice(studentId, 'Algebra', {
  num_items: 5,
  topic: 'quadratic_equations',
  goal_tags: ['SAT']
});

// Complete practice item
await apiClient.completePractice(assignmentId, itemId, {
  student_answer: 'x = 3',
  correct: true,
  time_taken_seconds: 60,
  hints_used: 0
});
```

### **Q&A**

```javascript
// Submit query
await apiClient.submitQuery({
  student_id: 'student-uuid',
  query: 'Explain photosynthesis',
  context: {
    recent_sessions: ['Biology'],
    subjects: ['Biology']
  }
});
```

### **Progress Dashboard**

```javascript
// Get progress
await apiClient.getProgress(userId, true); // include suggestions
```

### **Nudges**

```javascript
// Check for nudges
await apiClient.checkNudges(studentId);

// Engage with nudge
await apiClient.engageNudge(nudgeId);
```

### **Overrides**

```javascript
// Create override (tutor only)
await apiClient.createOverride({
  student_id: 'student-uuid',
  override_type: 'summary',
  target_id: 'summary-uuid',
  override_data: {
    narrative: 'Updated narrative...'
  }
});

// Get overrides
await apiClient.getOverrides(studentId);
```

---

## 🎯 **Best Practices**

### **1. Loading States**

Always show loading indicators during API calls:

```jsx
const [loading, setLoading] = useState(false);

const handleSubmit = async () => {
  setLoading(true);
  try {
    await apiClient.submitQuery(data);
  } finally {
    setLoading(false);
  }
};
```

### **2. Error Boundaries**

Use React Error Boundaries to catch errors:

```jsx
class ErrorBoundary extends React.Component {
  componentDidCatch(error, errorInfo) {
    console.error('API Error:', error);
    // Log to error tracking service
  }
  
  render() {
    if (this.state.hasError) {
      return <div>Something went wrong</div>;
    }
    return this.props.children;
  }
}
```

### **3. Caching**

Cache frequently accessed data:

```javascript
// Use React Query or SWR for caching
import useSWR from 'swr';

function useProgress(userId) {
  const { data, error } = useSWR(
    userId ? `/progress/${userId}` : null,
    () => apiClient.getProgress(userId)
  );
  return { data, error, loading: !data && !error };
}
```

### **4. Retry Logic**

Implement retry logic for failed requests:

```javascript
async function apiRequestWithRetry(endpoint, options, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await apiRequest(endpoint, options);
    } catch (error) {
      if (i === maxRetries - 1) throw error;
      await new Promise(resolve => setTimeout(resolve, 1000 * (i + 1)));
    }
  }
}
```

### **5. TypeScript Support**

Add TypeScript types for better type safety:

```typescript
interface QueryResponse {
  success: boolean;
  data: {
    answer: string;
    confidence: 'High' | 'Medium' | 'Low';
    confidence_score: number;
    clarification_requested: boolean;
    tutor_escalation_suggested: boolean;
  };
  };
}
```

---

## 🔧 **Environment Variables**

Create `.env` file:

```env
REACT_APP_API_URL=http://localhost:8000/api/v1
REACT_APP_API_KEY=your-api-key-here
```

---

## 📱 **Mobile Integration**

The API works with React Native as well. Use the same API client:

```javascript
// React Native
import apiClient from './api-client/apiClient';

// Works the same way
const result = await apiClient.getProgress(userId);
```

---

## 🧪 **Testing**

### **Mock API Client for Testing**

```javascript
// __mocks__/apiClient.js
export const apiClient = {
  getProgress: jest.fn(() => Promise.resolve({ success: true, data: {} })),
  submitQuery: jest.fn(() => Promise.resolve({ success: true, data: {} })),
};
```

### **Testing Components**

```javascript
import { render, screen, waitFor } from '@testing-library/react';
import QAComponent from './QAComponent';

test('submits query', async () => {
  render(<QAComponent studentId="test-id" />);
  
  const input = screen.getByPlaceholderText('What would you like help with?');
  fireEvent.change(input, { target: { value: 'Test query' } });
  
  const button = screen.getByText('Ask Question');
  fireEvent.click(button);
  
  await waitFor(() => {
    expect(screen.getByText(/confidence/i)).toBeInTheDocument();
  });
});
```

---

## 📚 **Additional Resources**

- **API Contracts**: See `_docs/active/API_CONTRACTS.md`
- **Demo Examples**: See `scripts/demo_examples.http`
- **Error Handling**: See error handling section above

---

## 🆘 **Troubleshooting**

### **CORS Issues**

If you encounter CORS errors, ensure:
1. Backend CORS is configured correctly
2. You're using the correct API URL
3. Authentication headers are set correctly

### **Authentication Errors**

If you get 401 errors:
1. Verify token is valid and not expired
2. Check token format: `Bearer <token>`
3. Ensure token is being sent in Authorization header

### **Network Errors**

If you get network errors:
1. Check API URL is correct
2. Verify server is running
3. Check firewall/proxy settings

---

**Last Updated**: November 2024

