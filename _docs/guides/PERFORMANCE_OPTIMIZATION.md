# Performance Optimization Guide

## Overview

This document outlines performance optimizations implemented and recommended for the AI Study Companion MVP.

---

## ✅ Implemented Optimizations

### 1. **Caching System** (`src/utils/cache.py`)

**Purpose**: Reduce database queries for frequently accessed data

**Features**:
- In-memory cache with TTL (Time To Live)
- Decorator-based caching for functions
- Cache key generators for common queries

**Usage**:
```python
from src.utils.cache import cached, get_cache

# Cache function results
@cached(ttl=600, key_prefix="user")
def get_user(user_id: str):
    return db.query(User).filter(User.id == user_id).first()

# Manual caching
cache = get_cache()
cache.set("user:123", user_data, ttl=300)
user = cache.get("user:123")
```

**Cacheable Data**:
- User profiles (5 min TTL)
- Subject information (10 min TTL)
- Student goals (2 min TTL)
- Student ratings (1 min TTL)
- Practice bank items (5 min TTL)

**Production Recommendation**: Use Redis or Memcached for distributed caching

---

### 2. **Metrics Collection** (`src/utils/metrics.py`)

**Purpose**: Track application performance and errors

**Features**:
- Counter metrics (request counts, error counts)
- Timing metrics (response times, query durations)
- Gauge metrics (current values)
- Error tracking

**Usage**:
```python
from src.utils.metrics import increment_counter, record_timing, record_error

# Increment counter
increment_counter("api.requests", tags={"endpoint": "/api/v1/qa/query"})

# Record timing
with TimingContext("db.query.duration", tags={"table": "users"}):
    result = db.query(User).all()

# Record error
record_error("DatabaseError", "Connection failed", context={"host": "db.example.com"})
```

**Metrics Tracked**:
- HTTP request/response counts
- Response times (p50, p95, p99)
- Error rates by type
- Slow requests (>1 second)
- Database query durations

**Production Recommendation**: Integrate with CloudWatch, Prometheus, or Datadog

---

### 3. **Request Metrics Middleware** (`src/api/middleware/metrics.py`)

**Purpose**: Automatically track all HTTP requests

**Features**:
- Automatic request/response tracking
- Status code classification (2xx, 3xx, 4xx, 5xx)
- Slow request detection (>1 second)
- Error tracking

**Metrics Collected**:
- `http.requests` - Total requests by method/path
- `http.responses` - Responses by status code
- `http.request.duration` - Request duration
- `http.slow_requests` - Requests >1 second
- `http.errors` - Errors by type

**Access Metrics**: `GET /metrics` (protect in production)

---

## 🔧 Query Optimization Recommendations

### 1. **Database Indexes**

**Current Indexes** (from models):
- ✅ `users.cognito_sub` (unique)
- ✅ `users.email` (unique)
- ✅ `sessions.student_id`
- ✅ `sessions.tutor_id`
- ✅ `summaries.student_id`
- ✅ `qa_interactions.student_id`
- ✅ `qa_interactions.confidence`
- ✅ `practice_assignments.student_id`
- ✅ `goals.student_id`
- ✅ `goals.status`

**Recommended Additional Indexes**:
```sql
-- Composite index for common queries
CREATE INDEX idx_goals_student_status ON goals(student_id, status);
CREATE INDEX idx_summaries_student_created ON summaries(student_id, created_at DESC);
CREATE INDEX idx_practice_assignments_student_completed ON practice_assignments(student_id, completed);
CREATE INDEX idx_qa_interactions_student_created ON qa_interactions(student_id, created_at DESC);

-- For practice bank item queries
CREATE INDEX idx_practice_bank_items_subject_difficulty ON practice_bank_items(subject_id, difficulty_level, is_active);
CREATE INDEX idx_student_ratings_student_subject ON student_ratings(student_id, subject_id);
```

---

### 2. **Eager Loading**

**Current Issues**:
- N+1 queries in `get_summaries` (loading session and tutor separately)
- N+1 queries in `get_progress` (loading subject for each goal)

**Optimized Queries**:
```python
from sqlalchemy.orm import joinedload

# Before (N+1 queries)
summaries = db.query(Summary).filter(Summary.student_id == user_id).all()
# Each summary.session and summary.tutor triggers a separate query

# After (1 query with joins)
summaries = db.query(Summary)\
    .options(
        joinedload(Summary.session),
        joinedload(Summary.tutor)
    )\
    .filter(Summary.student_id == user_id)\
    .all()
```

**Recommended Optimizations**:

**File**: `src/api/handlers/summaries.py`
```python
from sqlalchemy.orm import joinedload

# In get_summaries
summaries = db.query(Summary)\
    .options(
        joinedload(Summary.session),
        joinedload(Summary.tutor)
    )\
    .filter(Summary.student_id == user_id)\
    .order_by(Summary.created_at.desc())\
    .offset(offset)\
    .limit(limit)\
    .all()
```

**File**: `src/api/handlers/progress.py`
```python
from sqlalchemy.orm import joinedload

# In get_progress
active_goals = db.query(Goal)\
    .options(joinedload(Goal.subject))\
    .filter(
        Goal.student_id == user_id,
        Goal.status == "active"
    )\
    .all()
```

---

### 3. **Query Result Caching**

**Cache Frequently Accessed Data**:

```python
from src.utils.cache import cached, student_goals_cache_key, get_cache

# Cache student goals
@cached(ttl=120, key_prefix="goals")
def get_student_goals(db: DBSession, student_id: str):
    return db.query(Goal)\
        .options(joinedload(Goal.subject))\
        .filter(Goal.student_id == student_id, Goal.status == "active")\
        .all()

# Cache student ratings
@cached(ttl=60, key_prefix="rating")
def get_student_rating_cached(db: DBSession, student_id: str, subject_id: str):
    return adaptive_service.get_student_rating(student_id, subject_id)
```

---

### 4. **Pagination Optimization**

**Current**: Using `offset` and `limit` (can be slow for large offsets)

**Recommended**: Use cursor-based pagination for large datasets

```python
# Cursor-based pagination (faster for large datasets)
def get_summaries_cursor(db: DBSession, student_id: str, cursor: Optional[str] = None, limit: int = 20):
    query = db.query(Summary).filter(Summary.student_id == student_id)
    
    if cursor:
        # Decode cursor (e.g., timestamp + ID)
        cursor_time, cursor_id = decode_cursor(cursor)
        query = query.filter(
            (Summary.created_at < cursor_time) |
            ((Summary.created_at == cursor_time) & (Summary.id < cursor_id))
        )
    
    summaries = query.order_by(Summary.created_at.desc()).limit(limit + 1).all()
    
    has_more = len(summaries) > limit
    if has_more:
        summaries = summaries[:-1]
    
    next_cursor = encode_cursor(summaries[-1]) if summaries else None
    
    return summaries, next_cursor, has_more
```

---

## 📊 Performance Monitoring

### **Key Metrics to Monitor**

1. **Response Times**
   - P50 (median): < 200ms
   - P95: < 500ms
   - P99: < 1000ms

2. **Error Rates**
   - 4xx errors: < 1%
   - 5xx errors: < 0.1%

3. **Database Performance**
   - Query duration: < 100ms (p95)
   - Connection pool usage: < 80%
   - Slow queries: Alert on > 1s

4. **Cache Performance**
   - Hit rate: > 70%
   - Cache size: Monitor memory usage

---

## 🚀 Production Recommendations

### **1. Use Redis for Caching**
```python
# Replace SimpleCache with Redis
import redis
from redis import Redis

redis_client = Redis(host='redis.example.com', port=6379, db=0)

def get_cache():
    return redis_client
```

### **2. Use CloudWatch/Prometheus for Metrics**
```python
# CloudWatch integration
import boto3
cloudwatch = boto3.client('cloudwatch')

def record_metric(metric_name, value, unit='Count'):
    cloudwatch.put_metric_data(
        Namespace='AIStudyCompanion',
        MetricData=[{
            'MetricName': metric_name,
            'Value': value,
            'Unit': unit
        }]
    )
```

### **3. Database Connection Pooling**
```python
# Optimize connection pool
engine = create_engine(
    DATABASE_URL,
    pool_size=20,  # Number of connections
    max_overflow=10,  # Additional connections
    pool_pre_ping=True,  # Verify connections
    pool_recycle=3600  # Recycle connections after 1 hour
)
```

### **4. Enable Query Logging for Slow Queries**
```python
# Log slow queries
import logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)

# In production, use query logging service
```

### **5. Use CDN for Static Assets**
- Serve static files (docs, images) via CDN
- Reduce server load

---

## 📈 Expected Performance Improvements

### **With Caching**
- User profile queries: **90% faster** (cache hit)
- Subject lookups: **95% faster** (cache hit)
- Goals queries: **80% faster** (cache hit)

### **With Eager Loading**
- Summary list queries: **70% fewer queries**
- Progress dashboard: **60% fewer queries**

### **With Indexes**
- Filtered queries: **50-80% faster**
- Sorted queries: **60-90% faster**

---

## 🔍 Monitoring Dashboard

Access metrics at: `GET /metrics`

**Example Response**:
```json
{
  "success": true,
  "data": {
    "counters": {
      "http.requests:method=GET:path=/api/v1/progress/123": 150,
      "http.responses:method=GET:path=/api/v1/progress/123:status=200": 148
    },
    "timings": {
      "http.request.duration": {
        "count": 150,
        "avg": 0.234,
        "p95": 0.456,
        "p99": 0.789
      }
    },
    "recent_errors": [...]
  }
}
```

---

## ✅ Next Steps

1. ✅ Implement caching utilities
2. ✅ Implement metrics collection
3. ✅ Add request metrics middleware
4. ⏳ Add database indexes (migration)
5. ⏳ Implement eager loading in handlers
6. ⏳ Add Redis integration (production)
7. ⏳ Set up CloudWatch/Prometheus (production)

---

**Last Updated**: November 2024

