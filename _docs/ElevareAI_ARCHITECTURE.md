# 🏗️ System Architecture

**Product:** ElevareAI - AI-Powered Study Companion  
**Version:** 1.0.0  
**Last Updated:** November 2025

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Technology Stack](#technology-stack)
3. [Architecture Patterns](#architecture-patterns)
4. [User Experience & Flows](#user-experience--flows)
5. [Key Design Decisions](#key-design-decisions)
6. [Scalability & Performance](#scalability--performance)
7. [Security Architecture](#security-architecture)
8. [Deployment Architecture](#deployment-architecture)

---

## System Overview

ElevareAI is a comprehensive AI-powered tutoring platform that bridges the gap between in-person tutoring sessions. The system provides adaptive practice, conversational Q&A, personalized nudges, and progress tracking to support students' continuous learning journey.

### Core Value Proposition

- **Adaptive Learning:** Elo-based difficulty adjustment ensures students are always challenged at the right level
- **AI-Powered Support:** GPT-4 integration provides instant answers with transparent confidence labeling
- **Tutor Oversight:** Human-in-the-loop design allows tutors to override AI recommendations
- **Data-Driven Insights:** Comprehensive analytics for students, tutors, parents, and administrators

### System Components

```
┌─────────────┐
│   Frontend  │  React 18 + Vite + TanStack Query
│  (React)    │
└──────┬──────┘
       │ HTTPS/REST API
       │
┌──────▼──────────────────────────────────────┐
│         API Gateway / Load Balancer          │
│         (AWS ALB / CloudFront)               │
└──────┬──────────────────────────────────────┘
       │
┌──────▼──────────────────────────────────────┐
│         Backend API (FastAPI)                │
│         ECS Fargate Container                │
│  ┌──────────────────────────────────────┐   │
│  │  Handlers (API Endpoints)            │   │
│  │  Services (Business Logic)           │   │
│  │  Models (SQLAlchemy ORM)             │   │
│  └──────────────────────────────────────┘   │
└──────┬──────────────────────────────────────┘
       │
       ├─────────────────┬─────────────────┐
       │                 │                 │
┌──────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐
│  PostgreSQL │  │  AWS Cognito│  │   OpenAI    │
│  (RDS)      │  │  (Auth)      │  │   GPT-4     │
└─────────────┘  └──────────────┘  └─────────────┘
       │
       │
┌──────▼──────────────────────────────────────┐
│  AWS Services                                │
│  - SES (Email)                               │
│  - S3 (Storage)                              │
│  - CloudWatch (Logging)                      │
└──────────────────────────────────────────────┘
```

---

## Technology Stack

### Backend Framework: FastAPI (Python 3.11+)

**Why FastAPI?**

1. **Performance:** Built on Starlette and Pydantic, FastAPI is one of the fastest Python frameworks, comparable to Node.js and Go
2. **Type Safety:** Native Python type hints with Pydantic validation catch errors at development time
3. **Auto Documentation:** OpenAPI/Swagger docs generated automatically from code
4. **Async Support:** Native async/await support for concurrent request handling
5. **Developer Experience:** Excellent IDE support, clear error messages, and intuitive API design

**Trade-offs Considered:**
- **Django:** Too heavy for API-only service, ORM overhead
- **Flask:** Lacks built-in validation, async support requires extensions
- **Node.js/Express:** Python ecosystem better for AI/ML integrations

### Database: PostgreSQL 15+ on AWS RDS

**Why PostgreSQL over DynamoDB?**

1. **Relational Data:** Complex many-to-many relationships (tutors↔students, goals↔subjects) require joins
2. **Rails Integration:** Existing Rails application uses PostgreSQL, enabling seamless integration
3. **Complex Queries:** Analytics dashboards require aggregations, window functions, and subqueries
4. **ACID Transactions:** Critical for tutor overrides and immediate dashboard updates
5. **JSONB Support:** Flexible schema for user profiles, gamification, and analytics while maintaining relational integrity
6. **Cost-Effective:** RDS PostgreSQL is cost-effective for MVP scale (vs. DynamoDB read/write units)

**Schema Design Principles:**
- UUID primary keys for distributed system compatibility
- JSONB columns for flexible, schema-less data (profiles, gamification)
- Indexed foreign keys for performance
- GIN indexes on array columns (goal_tags, topic_tags)
- Materialized views for analytics queries

### ORM: SQLAlchemy 2.0

**Why SQLAlchemy?**

1. **Type Safety:** SQLAlchemy 2.0 provides excellent type hints and IDE support
2. **Connection Pooling:** Built-in connection pooling for ECS/Lambda deployments
3. **Migration Support:** Alembic integration for schema versioning
4. **Flexibility:** Can write raw SQL when needed for complex queries
5. **Maturity:** Battle-tested, widely used, excellent documentation

### AI/LLM: OpenAI GPT-4 via LangChain

**Why GPT-4?**

1. **Quality:** Superior reasoning and educational content generation vs. GPT-3.5
2. **Context Window:** Large context window (8K tokens) for session summaries and conversation history
3. **Structured Output:** Reliable JSON generation for practice items and summaries
4. **Educational Focus:** Better at following educational guidelines and avoiding misinformation

**Why LangChain?**

1. **Abstraction:** Provides consistent interface if we need to switch LLM providers
2. **Prompt Management:** Centralized prompt templates with versioning
3. **Chain Composition:** Enables complex multi-step AI workflows (e.g., query analysis → answer generation → confidence assessment)

**Cost Optimization:**
- GPT-4 for critical features (summaries, Q&A)
- GPT-3.5-turbo for lower-stakes tasks (nudge personalization)
- Temperature tuning (0.3 for consistency, 0.7 for creativity)

### Authentication: AWS Cognito

**Why Cognito?**

1. **Managed Service:** Reduces security burden (password hashing, MFA, token refresh)
2. **JWT Tokens:** Standard JWT tokens work seamlessly with API Gateway and FastAPI
3. **Multi-User Types:** Supports students, tutors, parents, admins with different attributes
4. **Integration:** Native AWS service integration (IAM roles, Lambda triggers)
5. **Cost:** Free tier covers MVP scale

**Implementation:**
- JWT token validation in FastAPI middleware
- Role-based access control (RBAC) at API endpoint level
- Token refresh handled client-side

### Frontend: React 18 + Vite + TanStack Query

**Why React 18?**

1. **Ecosystem:** Largest component library ecosystem
2. **Concurrent Features:** React 18's concurrent rendering improves perceived performance
3. **Server Components Ready:** Future-proof for Next.js migration if needed
4. **Developer Experience:** Excellent tooling, debugging, and community support

**Why Vite?**

1. **Performance:** 10-100x faster dev server than Create React App
2. **Modern Build:** ES modules, optimized production builds
3. **Developer Experience:** Instant HMR, better error messages

**Why TanStack Query (React Query)?**

1. **Server State Management:** Handles caching, refetching, and synchronization automatically
2. **Optimistic Updates:** Better UX for mutations (practice completion, goal updates)
3. **Background Refetching:** Keeps data fresh without user intervention
4. **Error Handling:** Built-in retry logic and error states

### Infrastructure: AWS ECS Fargate

**Why ECS Fargate over Lambda?**

1. **Long-Running Processes:** AI generation can take 5-10 seconds, exceeding Lambda timeout
2. **Connection Pooling:** Persistent database connections reduce latency
3. **State Management:** In-memory caching and session state
4. **Cost:** More cost-effective for consistent traffic vs. Lambda cold starts
5. **Container Reuse:** Docker containers can handle multiple requests efficiently

**Why Fargate over EC2?**

1. **Serverless:** No EC2 instance management, auto-scaling
2. **Security:** Isolated containers, no SSH access needed
3. **Cost:** Pay only for running containers, no idle instance costs

---

## Architecture Patterns

### 1. Layered Architecture

```
┌─────────────────────────────────────┐
│   API Layer (Handlers)              │  FastAPI route handlers
│   - Request validation              │  - Input/output schemas
│   - Authentication                  │  - Error handling
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│   Service Layer (Business Logic)     │  Domain services
│   - AdaptivePracticeService          │  - GoalProgressService
│   - ConversationHistory             │  - NudgeEngine
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│   Data Layer (Models)                │  SQLAlchemy ORM
│   - Database models                 │  - Relationships
│   - Query builders                  │  - Migrations
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│   Infrastructure Layer               │  External services
│   - OpenAI client                    │  - AWS services
│   - Email service                    │  - Cache
└─────────────────────────────────────┘
```

**Benefits:**
- Separation of concerns
- Testability (mock services, test handlers independently)
- Maintainability (clear boundaries)

### 2. Repository Pattern (via SQLAlchemy)

Models encapsulate data access logic:

```python
# Service layer doesn't know about SQL
adaptive_service = AdaptivePracticeService(db)
rating = adaptive_service.get_student_rating(student_id, subject_id)

# Model layer handles SQL complexity
class StudentRating(Base):
    @classmethod
    def get_or_create(cls, db, student_id, subject_id):
        # Handles create-if-not-exists logic
```

### 3. Strategy Pattern for AI Services

Different strategies for different use cases:

```python
# Math problems: SymPy (deterministic, fast, free)
if subject == "Math":
    generator = MathGenerator()  # Uses SymPy
    
# Other subjects: OpenAI (flexible, contextual)
else:
    generator = AIGenerator()  # Uses GPT-4
```

### 4. Factory Pattern for Practice Generation

```python
class PracticeGeneratorFactory:
    @staticmethod
    def create_generator(subject, context):
        if subject.supports_sympy:
            return MathGenerator()
        elif context.has_bank_items:
            return BankItemGenerator()
        else:
            return AIGenerator()
```

### 5. Observer Pattern for Nudges

Nudge engine observes student activity and triggers nudges:

```python
# Student completes practice → Nudge engine checks conditions
# Student inactive 7 days → Nudge engine sends inactivity nudge
# Goal completed → Nudge engine suggests related subjects
```

---

## User Experience & Flows

### Flow 1: Student Practice Session

```
1. Student logs in → Dashboard shows active goals
2. Student clicks "Start Practice" → API: GET /practice/assign
   ├─ AdaptivePracticeService calculates difficulty (based on Elo rating)
   ├─ Selects question from bank or generates AI question
   └─ Returns practice assignment
3. Student answers question → API: POST /practice/complete
   ├─ Validates answer
   ├─ Calculates performance score (accuracy + speed + hints)
   ├─ Updates Elo rating (adaptive difficulty)
   ├─ Updates goal progress
   └─ Returns next difficulty suggestion
4. Dashboard updates in real-time (TanStack Query refetch)
```

**Key UX Decisions:**
- **Immediate Feedback:** Answer validation happens instantly
- **Progressive Difficulty:** Elo system ensures questions are always appropriately challenging
- **Visual Progress:** Progress bars, streaks, and XP provide motivation
- **Retry Logic:** Incorrect answers can be retried (not marked complete)

### Flow 2: Q&A with Confidence Labeling

```
1. Student asks question → API: POST /qa/query
   ├─ QueryAnalyzer analyzes query (ambiguous? out-of-scope?)
   ├─ ConversationHistory retrieves recent context
   ├─ OpenAI generates answer (with context)
   ├─ ConfidenceCalculator computes multi-factor confidence
   │  ├─ LLM self-assessment (40%)
   │  ├─ Context relevance (30%)
   │  ├─ Query clarity (20%)
   │  └─ Answer length/completeness (10%)
   └─ Returns answer + confidence label
2. Frontend displays:
   ├─ High confidence: Answer + optional tutor suggestion
   ├─ Medium confidence: Answer + disclaimer + tutor suggestion
   └─ Low confidence: High-level overview + mandatory tutor escalation
3. Student can escalate to tutor → Creates message thread
```

**Key UX Decisions:**
- **Transparency:** Confidence labels build trust
- **Progressive Disclosure:** Low confidence answers show overview first
- **Tutor Escalation:** Seamless handoff to human tutor
- **Context Awareness:** Conversation history enables follow-up questions

### Flow 3: Session Summary Generation

```
1. Tutor session ends → Rails app sends webhook: POST /summaries
   ├─ Receives session transcript (or transcript URL)
   ├─ SummarizerService generates narrative summary
   │  ├─ Extracts key topics
   │  ├─ Identifies next steps
   │  └─ Formats as narrative (not bullet points)
   └─ Stores permanently in database
2. Student views summary → API: GET /summaries/{user_id}
   └─ Returns narrative + actionable next steps
3. Summary influences:
   ├─ Practice question selection (topics covered)
   ├─ Nudge personalization (suggested next steps)
   └─ Goal progress tracking
```

**Key UX Decisions:**
- **Narrative Format:** More engaging than bullet points
- **Actionable Next Steps:** Clear calls-to-action
- **Permanent Storage:** Summaries persist for reference
- **Context Integration:** Summaries inform practice and nudges

### Flow 4: Adaptive Nudge System

```
1. Background job runs (scheduled or event-driven)
   ├─ NudgeEngine checks conditions:
   │  ├─ Inactivity: Last login > 7 days?
   │  ├─ Goal completion: Goal just completed?
   │  ├─ Cross-subject: Related subjects available?
   │  └─ Frequency cap: Has user received nudge today?
   ├─ PersonalizationService generates personalized message
   │  ├─ Uses student insights (recent activity, goals)
   │  ├─ AI generates contextual message
   │  └─ Includes specific suggestions
   └─ Sends via in-app notification or email
2. Student receives nudge → Clicks link → Returns to app
3. Engagement tracked (opened, clicked) for analytics
```

**Key UX Decisions:**
- **Personalization:** AI-generated messages feel human
- **Frequency Capping:** Prevents notification fatigue
- **Multi-Channel:** In-app + email for reach
- **Actionable:** Nudges include direct links to relevant content

### Flow 5: Tutor Override & Dashboard Update

```
1. Tutor views student dashboard → API: GET /progress/{student_id}
   ├─ Shows AI-generated practice assignments
   ├─ Shows AI-generated summaries
   └─ Flags low-confidence Q&A interactions
2. Tutor overrides AI suggestion → API: POST /overrides
   ├─ Creates override record (for analytics)
   ├─ Updates student progress/goal immediately
   ├─ Triggers dashboard refresh (real-time update)
   └─ Optionally creates message thread
3. Override analytics tracked:
   ├─ Override patterns (which subjects, difficulty levels)
   ├─ Override frequency (per tutor, per student)
   └─ Used to improve AI recommendations
```

**Key UX Decisions:**
- **Immediate Updates:** Overrides reflect instantly (no page refresh)
- **Audit Trail:** All overrides logged for transparency
- **Analytics:** Override patterns inform AI improvements
- **Human-in-the-Loop:** Tutors maintain control over AI

---

## Key Design Decisions

### 1. Elo Rating System for Adaptive Difficulty

**Decision:** Use Elo rating system (chess-style) instead of simple right/wrong tracking.

**Rationale:**
- **Proven Algorithm:** Used by Duolingo, Khan Academy, chess platforms
- **Adaptive:** Adjusts based on performance, not just correctness
- **Fair:** Accounts for question difficulty, not just student ability
- **Multi-Factor:** Performance score includes accuracy (70%), speed (20%), hints (10%)

**Implementation:**
```python
# Elo formula
expected_score = 1 / (1 + 10^((question_rating - student_rating) / 400))
new_rating = current_rating + K * (actual_score - expected_score)

# K-factor = 32 (learning rate)
# Rating range: 400-2000 (maps to difficulty 1-10)
```

**Benefits:**
- Students always challenged at appropriate level
- Ratings decrease on poor performance (prevents overconfidence)
- Subject-specific ratings (student can be advanced in Math, beginner in Chemistry)

### 2. Multi-Factor Confidence Scoring

**Decision:** Use multi-factor confidence calculation instead of single LLM self-assessment.

**Rationale:**
- **LLM Self-Assessment (40%):** GPT-4 rates its own answer quality
- **Context Relevance (30%):** Does query relate to recent sessions/subjects?
- **Query Clarity (20%):** Is query ambiguous or out-of-scope?
- **Answer Completeness (10%):** Is answer comprehensive?

**Benefits:**
- More reliable than single-factor approach
- Reduces false high-confidence on out-of-scope queries
- Context-aware confidence (higher if related to recent learning)

**Trade-offs:**
- More complex than single-factor
- Requires multiple AI calls (query analysis + answer + confidence)
- Slightly higher latency (~200ms additional)

### 3. PostgreSQL over DynamoDB

**Decision:** Use PostgreSQL (RDS) instead of DynamoDB.

**Rationale:**
- **Relational Data:** Many-to-many relationships (tutors↔students, goals↔subjects)
- **Complex Queries:** Analytics dashboards require joins, aggregations, window functions
- **Rails Integration:** Existing Rails app uses PostgreSQL
- **ACID Transactions:** Critical for tutor overrides and immediate updates
- **JSONB Support:** Flexible schema (profiles, gamification) with relational benefits

**Trade-offs:**
- **Scaling:** DynamoDB scales better, but PostgreSQL sufficient for MVP
- **Cost:** DynamoDB read/write units can be expensive; RDS more predictable
- **Latency:** DynamoDB single-digit ms; PostgreSQL ~10-20ms (acceptable)

### 4. ECS Fargate over Lambda

**Decision:** Use ECS Fargate containers instead of AWS Lambda.

**Rationale:**
- **Long-Running Processes:** AI generation takes 5-10 seconds (exceeds Lambda timeout)
- **Connection Pooling:** Persistent database connections reduce latency
- **State Management:** In-memory caching, session state
- **Cost:** More cost-effective for consistent traffic (no cold starts)

**Trade-offs:**
- **Scaling:** Lambda auto-scales better, but ECS Fargate sufficient
- **Cold Starts:** ECS containers stay warm; Lambda has cold starts
- **Complexity:** ECS requires container management; Lambda is simpler

### 5. FastAPI over Django/Flask

**Decision:** Use FastAPI instead of Django or Flask.

**Rationale:**
- **Performance:** One of fastest Python frameworks (comparable to Node.js)
- **Type Safety:** Native type hints + Pydantic validation
- **Async Support:** Native async/await for concurrent requests
- **Auto Documentation:** OpenAPI/Swagger generated automatically
- **Developer Experience:** Excellent IDE support, clear errors

**Trade-offs:**
- **Ecosystem:** Django has larger ecosystem, but FastAPI sufficient
- **Admin Panel:** Django has built-in admin; FastAPI requires custom
- **Maturity:** Django more mature, but FastAPI production-ready

### 6. Conversation History for Context-Aware Q&A

**Decision:** Store and retrieve conversation history for Q&A context.

**Rationale:**
- **Follow-up Questions:** "What about that?" requires context
- **Topic Continuity:** Related questions build on previous answers
- **Personalization:** History informs answer style and depth

**Implementation:**
- Stores last 10 interactions per student
- Retrieves last 3 interactions for context
- Detects follow-up questions (semantic similarity)

**Benefits:**
- More natural conversation flow
- Better answers (context-aware)
- Reduced repetition (AI remembers previous answers)

### 7. SymPy for Math Problem Generation

**Decision:** Use SymPy (symbolic math library) instead of OpenAI for math problems.

**Rationale:**
- **Accuracy:** 100% accurate vs. ~85-90% for LLM-generated math
- **Speed:** <50ms vs. 1-3 seconds for OpenAI
- **Cost:** $0 vs. ~$0.01-0.03 per problem
- **Deterministic:** Same input = same output (testable)

**Fallback:**
- If SymPy fails → fallback to OpenAI
- For unsupported math topics → use OpenAI

**Benefits:**
- Higher quality math problems
- Lower latency
- Lower cost
- Better testability

---

## Scalability & Performance

### Database Optimization

1. **Connection Pooling:**
   - SQLAlchemy connection pool (5-10 connections per container)
   - Prevents connection exhaustion
   - Reuses connections for multiple requests

2. **Indexing Strategy:**
   - Indexed foreign keys (users.id, goals.student_id)
   - GIN indexes on array columns (goal_tags, topic_tags)
   - Composite indexes for common queries (student_id + subject_id)

3. **Query Optimization:**
   - Eager loading for relationships (joinedload, selectinload)
   - Pagination for large result sets
   - Materialized views for analytics queries

4. **Read Replicas (Future):**
   - Analytics queries → read replica
   - Write queries → primary database

### Caching Strategy

1. **In-Memory Caching:**
   - Student ratings (Elo) cached for 5 minutes
   - Subject catalog cached for 1 hour
   - Practice bank items cached for 30 minutes

2. **Redis (Future):**
   - Session state
   - Rate limiting counters
   - Frequently accessed data

### API Performance

1. **Async Endpoints:**
   - FastAPI async/await for concurrent request handling
   - Non-blocking I/O for database and OpenAI calls

2. **Response Time Targets:**
   - Practice assignment: <200ms
   - Q&A answer: <2s (includes OpenAI call)
   - Session summary: <5s (includes OpenAI call)
   - Dashboard: <500ms

3. **Rate Limiting:**
   - 100 requests/minute per user
   - 1000 requests/hour per user
   - Prevents abuse and cost overruns

### Horizontal Scaling

1. **ECS Service Auto-Scaling:**
   - Scale based on CPU utilization (target: 70%)
   - Scale based on request count (target: 1000 requests/minute)
   - Min: 1 container, Max: 10 containers

2. **Load Balancing:**
   - Application Load Balancer (ALB) distributes traffic
   - Health checks ensure only healthy containers receive traffic

3. **Database Scaling:**
   - RDS instance scaling (vertical)
   - Read replicas (horizontal, future)
   - Connection pooling prevents connection limits

---

## Security Architecture

### Authentication & Authorization

1. **AWS Cognito:**
   - JWT token-based authentication
   - Token validation in FastAPI middleware
   - Role-based access control (RBAC) at endpoint level

2. **API Security:**
   - HTTPS only (TLS 1.2+)
   - CORS configured for frontend domain only
   - Rate limiting prevents abuse
   - Input validation (Pydantic schemas)

3. **Database Security:**
   - Encrypted at rest (RDS encryption)
   - Encrypted in transit (SSL/TLS)
   - Connection from ECS only (security groups)
   - No public access

### Data Protection

1. **Sensitive Data:**
   - API keys stored in environment variables (ECS task definition)
   - Database passwords in AWS Secrets Manager (future)
   - PII encrypted in database (future)

2. **Audit Logging:**
   - All tutor overrides logged
   - All API requests logged (CloudWatch)
   - Error tracking and alerting

3. **Compliance:**
   - FERPA considerations (educational data)
   - GDPR-ready (data export, deletion)
   - Regular security audits

---

## Deployment Architecture

### AWS Infrastructure

```
┌─────────────────────────────────────────────────┐
│  CloudFront (CDN)                               │
│  - Frontend static assets                       │
│  - API caching (optional)                       │
└──────────────┬──────────────────────────────────┘
               │
┌──────────────▼──────────────────────────────────┐
│  Application Load Balancer (ALB)                 │
│  - HTTPS termination                             │
│  - Health checks                                 │
│  - Request routing                               │
└──────────────┬──────────────────────────────────┘
               │
┌──────────────▼──────────────────────────────────┐
│  ECS Fargate Service                             │
│  ┌──────────────────────────────────────────┐   │
│  │  Container 1: FastAPI App                │   │
│  │  Container 2: FastAPI App                │   │
│  │  Container N: FastAPI App (auto-scaled)  │   │
│  └──────────────────────────────────────────┘   │
└──────────────┬──────────────────────────────────┘
               │
       ┌───────┴────────┬──────────────┐
       │                │              │
┌──────▼──────┐  ┌──────▼──────┐  ┌───▼──────────┐
│  RDS        │  │  Cognito     │  │  S3          │
│  PostgreSQL │  │  (Auth)      │  │  (Storage)   │
└─────────────┘  └──────────────┘  └──────────────┘
```

### Container Architecture

- **Base Image:** Python 3.11-slim
- **Dependencies:** Installed via requirements.txt
- **Entry Point:** `uvicorn src.api.main:app --host 0.0.0.0 --port 8000`
- **Health Check:** `GET /health` endpoint
- **Resource Limits:** 0.25 vCPU, 512MB RAM (scalable)

### CI/CD Pipeline (Planned)

1. **GitHub Actions:**
   - Run tests on PR
   - Build Docker image
   - Push to ECR
   - Deploy to ECS (on merge to main)

2. **Deployment Strategy:**
   - Blue-green deployment (zero downtime)
   - Health checks before traffic switch
   - Automatic rollback on failure

---

## Future Enhancements

### Short-Term (Next 3 Months)

1. **Redis Caching:** Reduce database load
2. **Read Replicas:** Scale analytics queries
3. **API Gateway:** Add request throttling, API keys
4. **Monitoring:** CloudWatch dashboards, alerts

### Medium-Term (6-12 Months)

1. **Microservices:** Split into separate services (practice, Q&A, nudges)
2. **Event-Driven Architecture:** SQS/SNS for async processing
3. **GraphQL API:** More flexible frontend queries
4. **Real-Time Updates:** WebSockets for live dashboard updates

### Long-Term (12+ Months)

1. **Multi-Region:** Global deployment for low latency
2. **Edge Computing:** Lambda@Edge for static content
3. **ML Model Training:** Custom models for practice generation
4. **Advanced Analytics:** Data warehouse (Redshift) for deep insights

---

## Conclusion

This architecture balances **performance, scalability, and maintainability** while keeping **costs reasonable** for an MVP. Key strengths:

- **FastAPI** provides excellent performance and developer experience
- **PostgreSQL** handles complex relational data and analytics
- **Elo rating system** ensures adaptive, fair difficulty adjustment
- **Multi-factor confidence** provides reliable AI answer quality assessment
- **ECS Fargate** enables long-running processes with connection pooling
- **AWS managed services** reduce operational overhead

The system is designed to **scale horizontally** and can handle growth from MVP to production scale with minimal architectural changes.

---

**Document Maintained By:** Engineering Team  
**Review Cycle:** Quarterly  
**Last Reviewed:** November 2025

