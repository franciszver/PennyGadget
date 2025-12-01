# Async Practice Generation Guide

## Overview

The practice assignment endpoint can take 30-45 seconds when generating AI questions, which exceeds CloudFront's 30-second timeout. This guide explains how to use the new async endpoints to avoid 504 Gateway Timeout errors.

## Problem

- **Synchronous endpoint** (`POST /api/v1/practice/assign`) takes 44+ seconds
- **CloudFront timeout** is 30 seconds → results in 504 Gateway Timeout
- **User experience** is poor with long waits

## Solution: Async Endpoints

We've added three ways to handle async practice generation:

1. **Async Endpoint** - Returns immediately with job ID
2. **Job Status Endpoint** - Poll for completion
3. **WebSocket** - Real-time updates
4. **Webhooks** - Get notified when complete

## Usage

### Option 1: Async Endpoint with Polling

```javascript
// 1. Start async job
const response = await fetch('https://api.example.com/api/v1/practice/assign/async', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    student_id: 'student-uuid',
    subject: 'Algebra',
    num_items: 5,
    topic: 'Linear Equations'
  })
});

const { job_id, status_url } = await response.json();

// 2. Poll for status
const checkStatus = async () => {
  const statusResponse = await fetch(`https://api.example.com/api/v1/jobs/${job_id}`);
  const status = await statusResponse.json();
  
  if (status.data.status === 'completed') {
    // Use status.data.result
    return status.data.result;
  } else if (status.data.status === 'failed') {
    throw new Error(status.data.error);
  } else {
    // Still processing, poll again
    setTimeout(checkStatus, 2000);
  }
};

await checkStatus();
```

### Option 2: WebSocket (Real-time)

```javascript
// 1. Start async job
const response = await fetch('https://api.example.com/api/v1/practice/assign/async', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    student_id: 'student-uuid',
    subject: 'Algebra',
    num_items: 5
  })
});

const { job_id, websocket_url } = await response.json();

// 2. Connect via WebSocket
const ws = new WebSocket(`wss://api.example.com/api/v1/jobs/${job_id}/ws`);

ws.onmessage = (event) => {
  const update = JSON.parse(event.data);
  
  switch (update.type) {
    case 'status':
      console.log(`Progress: ${update.progress_percent}% - ${update.progress_message}`);
      break;
    case 'completed':
      // Use update.result
      console.log('Practice assignment ready!', update.result);
      ws.close();
      break;
    case 'failed':
      console.error('Job failed:', update.error);
      ws.close();
      break;
  }
};
```

### Option 3: Webhook Callback

```javascript
// Start async job with webhook URL
const response = await fetch('https://api.example.com/api/v1/practice/assign/async', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    student_id: 'student-uuid',
    subject: 'Algebra',
    num_items: 5,
    webhook_url: 'https://your-app.com/webhooks/practice-complete'
  })
});

const { job_id } = await response.json();

// Your webhook endpoint will receive:
// POST https://your-app.com/webhooks/practice-complete
// {
//   "event": "practice.assignment.completed",
//   "timestamp": "2025-12-01T...",
//   "data": {
//     "job_id": "...",
//     "student_id": "...",
//     "result": { ... }
//   }
// }
```

## API Endpoints

### POST /api/v1/practice/assign/async

Create an async practice generation job.

**Request:**
```json
{
  "student_id": "uuid",
  "subject": "Algebra",
  "topic": "Linear Equations",
  "num_items": 5,
  "goal_tags": ["goal-uuid"],
  "webhook_url": "https://your-app.com/webhook" // optional
}
```

**Response:**
```json
{
  "success": true,
  "job_id": "uuid",
  "status": "pending",
  "message": "Practice generation started. Use the job_id to check status.",
  "status_url": "/api/v1/jobs/{job_id}",
  "websocket_url": "/api/v1/jobs/{job_id}/ws"
}
```

### GET /api/v1/jobs/{job_id}

Get job status.

**Response:**
```json
{
  "success": true,
  "data": {
    "job_id": "uuid",
    "job_type": "practice_generation",
    "status": "processing", // pending, processing, completed, failed
    "progress_percent": 45,
    "progress_message": "Generating AI question 2 of 3...",
    "created_at": "2025-12-01T...",
    "updated_at": "2025-12-01T...",
    "result": { ... } // only if completed
  }
}
```

### WebSocket /api/v1/jobs/{job_id}/ws

Real-time job updates.

**Messages received:**
```json
// Status update
{
  "type": "status",
  "status": "processing",
  "progress_percent": 45,
  "progress_message": "Generating AI question 2 of 3..."
}

// Completion
{
  "type": "completed",
  "result": { ... }
}

// Failure
{
  "type": "failed",
  "error": "Error message"
}
```

## Migration

Run the migration to create the jobs table:

```bash
psql -h your-db-host -U your-user -d your-database -f migrations/003_create_jobs_table.sql
```

Or use your migration tool:

```python
# In your migration runner
from src.config.database import engine
with open('migrations/003_create_jobs_table.sql') as f:
    engine.execute(f.read())
```

## Backwards Compatibility

The original synchronous endpoint (`POST /api/v1/practice/assign`) still works for:
- Quick assignments (bank items only, no AI generation)
- Backwards compatibility
- Testing

For production use with AI generation, use the async endpoint.

## Best Practices

1. **Use async endpoint** when generating AI questions (takes 30+ seconds)
2. **Use WebSocket** for real-time UI updates
3. **Use webhooks** for server-to-server notifications
4. **Poll job status** as fallback if WebSocket unavailable
5. **Handle errors** - check for `failed` status and display error message

## Example: React Hook

```javascript
import { useState, useEffect } from 'react';

function useAsyncPractice(studentId, subject, numItems) {
  const [jobId, setJobId] = useState(null);
  const [status, setStatus] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!jobId) return;

    // Connect via WebSocket
    const ws = new WebSocket(`wss://api.example.com/api/v1/jobs/${jobId}/ws`);
    
    ws.onmessage = (event) => {
      const update = JSON.parse(event.data);
      setStatus(update);
      
      if (update.type === 'completed') {
        setResult(update.result);
        ws.close();
      } else if (update.type === 'failed') {
        setError(update.error);
        ws.close();
      }
    };

    return () => ws.close();
  }, [jobId]);

  const startJob = async () => {
    const response = await fetch('/api/v1/practice/assign/async', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ student_id: studentId, subject, num_items: numItems })
    });
    const data = await response.json();
    setJobId(data.job_id);
  };

  return { startJob, status, result, error };
}
```

## Troubleshooting

### Job stuck in "processing"
- Check backend logs for errors
- Job may have failed but status not updated
- Restart the job if needed

### WebSocket connection fails
- Fall back to polling (`GET /api/v1/jobs/{job_id}`)
- Check CORS settings
- Verify WebSocket support in your environment

### Webhook not received
- Verify webhook URL is accessible
- Check webhook endpoint logs
- Verify timeout settings (webhooks have 10s timeout)

