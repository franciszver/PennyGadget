# 🔌 API Contracts
**Product:** AI Study Companion MVP  
**Integration:** Rails/React Application  
**Version:** 1.0.0

---

## Overview

This document defines the REST API contracts for integrating the AI Study Companion service with the existing Rails/React platform. All endpoints use JSON for request/response bodies.

**Base URL:** `https://api.pennygadget.ai/v1` (or configured environment variable)

**Authentication:**
- **Service-to-Service:** API Key in `X-API-Key` header
- **User Requests:** JWT token from AWS Cognito in `Authorization: Bearer <token>` header

---

## Common Response Formats

### Success Response
```json
{
  "success": true,
  "data": { ... },
  "metadata": {
    "timestamp": "2024-01-15T10:30:00Z",
    "request_id": "req-abc123"
  }
}
```

### Error Response
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input parameters",
    "details": {
      "field": "session_id",
      "reason": "Session ID is required"
    }
  },
  "metadata": {
    "timestamp": "2024-01-15T10:30:00Z",
    "request_id": "req-abc123"
  }
}
```

### Error Codes
- `VALIDATION_ERROR` (400) - Invalid input
- `UNAUTHORIZED` (401) - Missing or invalid authentication
- `FORBIDDEN` (403) - Insufficient permissions
- `NOT_FOUND` (404) - Resource not found
- `INTERNAL_ERROR` (500) - Server error
- `SERVICE_UNAVAILABLE` (503) - External service unavailable

---

## Endpoints

### 1. Session Summaries

#### `POST /summaries`
Generate AI summary from a completed tutoring session.

**Request (from Rails app):**
```json
{
  "session_id": "session-uuid",
  "student_id": "student-uuid",
  "tutor_id": "tutor-uuid",
  "transcript": "Full transcript text...",
  "session_duration_minutes": 45,
  "subject": "Algebra",
  "topics_covered": ["quadratic_equations", "factoring"]
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "summary_id": "summary-uuid",
    "session_id": "session-uuid",
    "narrative": "We reviewed factoring polynomials, then pivoted to balancing chemical equations...",
    "next_steps": [
      "Practice factoring polynomials: x² - 9, x² + 7x + 12",
      "Review balancing equations: CH₄ + O₂ → CO₂ + H₂O"
    ],
    "subjects_covered": ["Algebra", "Chemistry"],
    "summary_type": "normal",
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

**Edge Cases:**
- Missing transcript → Returns summary with `summary_type: "missing_transcript"`
- Short session → Returns summary with `summary_type: "brief"`

---

#### `GET /summaries/:user_id`
Retrieve all summaries for a user (student or tutor view).

**Query Parameters:**
- `role` (optional): `"student"` or `"tutor"` - determines view format
- `limit` (optional): Number of results (default: 20, max: 100)
- `offset` (optional): Pagination offset

**Response:**
```json
{
  "success": true,
  "data": {
    "summaries": [
      {
        "summary_id": "summary-uuid",
        "session_id": "session-uuid",
        "session_date": "2024-01-10T14:00:00Z",
        "narrative": "...",
        "next_steps": [...],
        "subjects_covered": ["Algebra"],
        "tutor_name": "Dr. Sarah Mitchell"
      }
    ],
    "pagination": {
      "total": 15,
      "limit": 20,
      "offset": 0,
      "has_more": false
    }
  }
}
```

---

### 2. Practice Assignment

#### `POST /practice/assign`
Assign adaptive practice items to a student.

**Request:**
```json
{
  "student_id": "student-uuid",
  "subject": "Algebra",
  "topic": "quadratic_equations",
  "num_items": 5,
  "goal_tags": ["SAT", "AP_Calculus"]
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "assignment_id": "assignment-uuid",
    "items": [
      {
        "item_id": "item-uuid",
        "source": "bank",
        "question": "Factor the quadratic: x² + 7x + 12",
        "difficulty": 5,
        "subject": "Algebra",
        "goal_tags": ["SAT"]
      },
      {
        "item_id": "item-ai-uuid",
        "source": "ai_generated",
        "flagged": true,
        "question": "Explain the concept of orbital hybridization...",
        "difficulty": 6,
        "subject": "Chemistry",
        "requires_tutor_review": true
      }
    ],
    "adaptive_metadata": {
      "student_rating_before": 1200,
      "selected_difficulty_range": "5-7"
    }
  }
}
```

**Edge Cases:**
- No bank items available → Returns AI-generated items with `flagged: true`
- Conflicting difficulty → Returns items with different difficulties per subject

---

#### `POST /practice/complete`
Record completion of a practice item.

**Request:**
```json
{
  "assignment_id": "assignment-uuid",
  "item_id": "item-uuid",
  "student_answer": "(x + 3)(x + 4)",
  "correct": true,
  "time_taken_seconds": 45,
  "hints_used": 0
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "performance_score": 0.95,
    "student_rating_before": 1200,
    "student_rating_after": 1250,
    "next_difficulty_suggestion": 6
  }
}
```

---

### 3. Conversational Q&A

#### `POST /qa/query`
Submit a student query and get AI-generated answer.

**Request:**
```json
{
  "student_id": "student-uuid",
  "query": "I don't understand factoring quadratics",
  "context": {
    "recent_sessions": ["Algebra"],
    "current_practice": "quadratic_equations",
    "last_summary": "We worked on factoring polynomials"
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "interaction_id": "qa-uuid",
    "query": "I don't understand factoring quadratics",
    "answer": "Factoring quadratics means breaking down expressions like x² + 5x + 6 into (x + 2)(x + 3)...",
    "confidence": "High",
    "confidence_score": 0.85,
    "disclaimer_shown": true,
    "escalation": null,
    "metadata": {
      "clarification_requested": false,
      "out_of_scope": false
    }
  }
}
```

**Low Confidence Response:**
```json
{
  "success": true,
  "data": {
    "interaction_id": "qa-uuid",
    "query": "Can you explain the Schrödinger equation in detail?",
    "answer": "The Schrödinger equation is a fundamental equation in quantum mechanics...",
    "confidence": "Low",
    "confidence_score": 0.35,
    "disclaimer_shown": true,
    "escalation": {
      "suggested": true,
      "reason": "Advanced topic requiring expert guidance",
      "message": "I recommend discussing this with your tutor for a more detailed explanation."
    }
  }
}
```

**Edge Cases:**
- Ambiguous query → Returns answer with `clarification_requested: true`
- Out-of-scope → Returns answer with `out_of_scope: true` and redirect message

---

### 4. Nudges

#### `POST /nudges/check`
Check if a student should receive a nudge (called by scheduled job).

**Request:**
```json
{
  "student_id": "student-uuid",
  "check_type": "inactivity" | "goal_completion" | "login"
}
```

**Response (if nudge should be sent):**
```json
{
  "success": true,
  "data": {
    "should_send": true,
    "nudge": {
      "nudge_id": "nudge-uuid",
      "type": "inactivity",
      "channel": "both",
      "message": "Hi! We noticed you've only completed 2 sessions so far...",
      "personalized": true,
      "suggestions": ["Physics", "Biology"]
    }
  }
}
```

**Response (if nudge should NOT be sent):**
```json
{
  "success": true,
  "data": {
    "should_send": false,
    "reason": "frequency_cap_reached",
    "next_available": "2024-01-16T00:00:00Z"
  }
}
```

---

#### `POST /nudges/:nudge_id/engage`
Track nudge engagement (opened/clicked).

**Request:**
```json
{
  "engagement_type": "opened" | "clicked"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "nudge_id": "nudge-uuid",
    "engagement_logged": true,
    "engagement_type": "opened"
  }
}
```

---

### 5. Tutor Overrides

#### `POST /overrides`
Create a tutor override of an AI suggestion.

**Request:**
```json
{
  "tutor_id": "tutor-uuid",
  "student_id": "student-uuid",
  "override_type": "summary" | "practice" | "qa_answer",
  "target_id": "summary-uuid",  // ID of summary/practice/qa being overridden
  "action": "Replace next steps",
  "new_content": {
    "next_steps": [
      "Focus on chapter 5 exercises only",
      "Skip practice problems, review theory instead"
    ]
  },
  "reason": "AI suggestions too advanced for current level"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "override_id": "override-uuid",
    "tutor_id": "tutor-uuid",
    "student_id": "student-uuid",
    "override_type": "summary",
    "action": "Replace next steps",
    "dashboard_updated": true,
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

---

#### `GET /overrides/:student_id`
Get all overrides for a student (tutor view).

**Response:**
```json
{
  "success": true,
  "data": {
    "overrides": [
      {
        "override_id": "override-uuid",
        "tutor_name": "Dr. Sarah Mitchell",
        "override_type": "summary",
        "action": "Modified next steps",
        "reason": "AI suggestions too advanced",
        "created_at": "2024-01-10T14:00:00Z"
      }
    ]
  }
}
```

---

### 6. Progress Dashboard

#### `GET /progress/:user_id`
Get multi-goal progress dashboard data.

**Query Parameters:**
- `include_suggestions` (optional): Include related subject suggestions (default: true)

**Response:**
```json
{
  "success": true,
  "data": {
    "user_id": "student-uuid",
    "goals": [
      {
        "goal_id": "goal-uuid",
        "subject": "SAT Math",
        "goal_type": "SAT",
        "completion_percentage": 70,
        "current_streak": 5,
        "xp_earned": 700,
        "status": "active",
        "target_date": "2024-06-01"
      },
      {
        "goal_id": "goal-uuid-2",
        "subject": "Chemistry",
        "goal_type": "AP",
        "completion_percentage": 40,
        "current_streak": 2,
        "xp_earned": 400,
        "status": "active",
        "target_date": "2024-05-15"
      }
    ],
    "insights": [
      "You're making great progress in SAT Math!",
      "Chemistry could use more attention - consider scheduling extra practice"
    ],
    "suggestions": [
      {
        "type": "related_subject",
        "subjects": ["AP English", "AP Math"],
        "message": "Based on your SAT success, you might enjoy:"
      }
    ],
    "disclaimer_required": false
  }
}
```

**First Login Response:**
```json
{
  "success": true,
  "data": {
    "user_id": "student-uuid",
    "goals": [],
    "insights": [],
    "suggestions": [],
    "disclaimer_required": true,
    "disclaimer": {
      "message": "Important Notice: This AI Study Companion is designed to support your learning...",
      "acknowledgment_required": true
    }
  }
}
```

---

## Rails Integration Examples

### Ruby Client Class

```ruby
class AIServiceClient
  BASE_URL = ENV['AI_SERVICE_URL'] || 'https://api.pennygadget.ai/v1'
  API_KEY = ENV['AI_SERVICE_API_KEY']
  
  def self.create_summary(session_id, student_id, tutor_id, transcript, metadata)
    response = HTTParty.post(
      "#{BASE_URL}/summaries",
      headers: {
        'Content-Type' => 'application/json',
        'X-API-Key' => API_KEY
      },
      body: {
        session_id: session_id,
        student_id: student_id,
        tutor_id: tutor_id,
        transcript: transcript,
        session_duration_minutes: metadata[:duration],
        subject: metadata[:subject],
        topics_covered: metadata[:topics]
      }.to_json
    )
    
    handle_response(response)
  end
  
  def self.assign_practice(student_id, subject, options = {})
    response = HTTParty.post(
      "#{BASE_URL}/practice/assign",
      headers: {
        'Content-Type' => 'application/json',
        'X-API-Key' => API_KEY
      },
      body: {
        student_id: student_id,
        subject: subject,
        topic: options[:topic],
        num_items: options[:num_items] || 5,
        goal_tags: options[:goal_tags] || []
      }.to_json
    )
    
    handle_response(response)
  end
  
  def self.submit_query(student_id, query, context = {})
    response = HTTParty.post(
      "#{BASE_URL}/qa/query",
      headers: {
        'Content-Type' => 'application/json',
        'X-API-Key' => API_KEY
      },
      body: {
        student_id: student_id,
        query: query,
        context: context
      }.to_json
    )
    
    handle_response(response)
  end
  
  def self.get_progress(user_id, include_suggestions: true)
    response = HTTParty.get(
      "#{BASE_URL}/progress/#{user_id}",
      headers: {
        'X-API-Key' => API_KEY
      },
      query: {
        include_suggestions: include_suggestions
      }
    )
    
    handle_response(response)
  end
  
  private
  
  def self.handle_response(response)
    if response.success?
      response.parsed_response['data']
    else
      error = response.parsed_response['error']
      raise AIServiceError.new(error['code'], error['message'], error['details'])
    end
  end
end

class AIServiceError < StandardError
  attr_reader :code, :details
  
  def initialize(code, message, details = nil)
    super(message)
    @code = code
    @details = details
  end
end
```

### Usage in Rails Controller

```ruby
class SessionsController < ApplicationController
  def create_summary
    session = Session.find(params[:session_id])
    
    summary_data = AIServiceClient.create_summary(
      session.id,
      session.student_id,
      session.tutor_id,
      session.transcript,
      {
        duration: session.duration_minutes,
        subject: session.subject.name,
        topics: session.topics.pluck(:name)
      }
    )
    
    # Store summary in local DB
    Summary.create!(
      ai_service_id: summary_data['summary_id'],
      session: session,
      narrative: summary_data['narrative'],
      next_steps: summary_data['next_steps']
    )
    
    render json: { summary: summary_data }
  end
end
```

---

## React Integration Examples

### React Hook for Q&A

```typescript
// hooks/useAIQuery.ts
import { useState } from 'react';
import axios from 'axios';

const AI_SERVICE_URL = process.env.REACT_APP_AI_SERVICE_URL;

export const useAIQuery = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  const submitQuery = async (studentId: string, query: string, context?: any) => {
    setLoading(true);
    setError(null);
    
    try {
      const token = await getCognitoToken(); // Get JWT from Cognito
      
      const response = await axios.post(
        `${AI_SERVICE_URL}/qa/query`,
        {
          student_id: studentId,
          query,
          context
        },
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
      );
      
      return response.data.data;
    } catch (err) {
      setError(err.response?.data?.error || { message: 'Failed to submit query' });
      throw err;
    } finally {
      setLoading(false);
    }
  };
  
  return { submitQuery, loading, error };
};
```

---

## Rate Limiting

- **Service-to-Service:** 1000 requests/minute per API key
- **User Requests:** 100 requests/minute per user
- **Headers:** `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`

---

## Webhooks (Optional - POST-MVP)

For real-time updates, the service can send webhooks to Rails app:

```
POST https://your-rails-app.com/webhooks/ai-service
Headers:
  X-Webhook-Signature: <HMAC signature>
Body:
{
  "event": "override_created",
  "data": { ... },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

---

## Versioning

API version is specified in the URL path (`/v1/`). Breaking changes will increment the version number. Non-breaking changes (new optional fields, new endpoints) will be added to the current version.

---

## Testing

Use the golden response test cases (`_docs/qa/golden_responses.yaml`) to validate API behavior. Each endpoint should match expected outputs for edge cases.

