# 🎯 Implementation Priority & Best Practices

**Created:** Based on architectural dependencies and MVP delivery requirements  
**Purpose:** Guide development order and establish best practices for key algorithms

---

## Priority Framework

Prioritization follows **dependency-first** and **foundation-first** principles:
1. **Foundation Layer** → Must exist before anything else can be built
2. **Core Data Models** → Required for all feature development
3. **Business Logic** → Algorithms and rules that power features
4. **Integration Services** → Connect to external systems
5. **Testing & Validation** → Ensure quality before demo

---

## Phase 1: Foundation Layer (Weeks 1-2)

### 🔴 **PRIORITY 1: Database Architecture & Choice**
**Question #1: AWS Database Selection**

**Decision:** Use **PostgreSQL on AWS RDS** (not DynamoDB)

**Reasoning:**
- **Rails Integration:** PostgreSQL is the standard for Rails apps, ensuring seamless integration
- **Relational Data:** Many-to-many relationships (tutors↔students), complex queries (progress tracking, analytics), and joins are better suited to SQL
- **Future-Proof:** Easier to add complex analytics, reporting, and admin dashboards
- **Transaction Support:** Critical for tutor overrides and immediate dashboard updates
- **Cost:** RDS PostgreSQL is cost-effective for MVP scale

**Implementation:**
- AWS RDS PostgreSQL (multi-AZ for production)
- Use connection pooling (PgBouncer) for Lambda/ECS
- Design schema with Rails migration compatibility in mind

---

### 🔴 **PRIORITY 2: Authentication System**
**Question #4: Build Auth Using AWS**

**Decision:** AWS Cognito for user authentication

**Reasoning:**
- **Managed Service:** Reduces security burden, handles password resets, MFA
- **JWT Tokens:** Standard for API Gateway + Lambda/ECS integration
- **Multi-User Types:** Supports students, tutors, parents, admins with different attributes
- **Integration:** Cognito tokens work seamlessly with API Gateway authorizers
- **Cost:** Free tier covers MVP needs

**Implementation:**
- AWS Cognito User Pools (separate pools or groups for roles)
- API Gateway Lambda Authorizer for token validation
- Store user metadata in PostgreSQL (link Cognito `sub` to `User.id`)

---

### 🟠 **PRIORITY 3: User Model & Relationships**
**Question #6: Many-to-Many Tutor-Student Relationships**

**Decision:** Junction table with additional metadata

**Reasoning:**
- **Flexibility:** Students can have multiple tutors, tutors can have multiple students
- **Metadata:** Store relationship-specific data (start_date, status, subject_focus)
- **Analytics:** Track which tutor-student pairs have most overrides/engagement

**Schema Design:**
```sql
-- Junction table
tutor_student_assignments (
  tutor_id UUID,
  student_id UUID,
  subject_id UUID,
  assigned_at TIMESTAMP,
  status VARCHAR, -- 'active', 'paused', 'completed'
  PRIMARY KEY (tutor_id, student_id, subject_id)
)
```

---

### 🟠 **PRIORITY 4: Goal Management System**
**Question #7: Both Students and Tutors Can Create/Manage Goals**

**Decision:** Shared ownership with permission model

**Reasoning:**
- **Collaboration:** Tutors set initial goals, students can add personal goals
- **Audit Trail:** Track who created/modified each goal
- **Override Logic:** Tutors can modify student-created goals (needed for Step 5)

**Schema Design:**
```sql
goals (
  id UUID PRIMARY KEY,
  student_id UUID,
  created_by UUID, -- user_id (tutor or student)
  subject VARCHAR,
  target_completion_date DATE,
  status VARCHAR, -- 'active', 'completed', 'paused'
  created_at TIMESTAMP,
  updated_at TIMESTAMP
)
```

---

## Phase 2: Core Business Logic (Weeks 2-4)

### 🟡 **PRIORITY 5: Practice Bank Curation System**
**Question #5: Build Curation System**

**Decision:** Admin-managed bank with tagging and versioning

**Reasoning:**
- **Quality Control:** Human-curated items ensure accuracy before AI generation
- **Tagging:** Tag by subject, difficulty, goal_type (SAT, AP, etc.)
- **Versioning:** Track changes, allow rollback if AI flags issues
- **Analytics:** Compare bank vs AI-generated item performance

**Schema Design:**
```sql
practice_bank_items (
  id UUID PRIMARY KEY,
  question_text TEXT,
  answer_text TEXT,
  subject VARCHAR,
  difficulty_level INT, -- 1-10 scale
  goal_tags TEXT[], -- ['SAT', 'AP_Calculus']
  created_by UUID, -- admin/tutor
  version INT,
  is_active BOOLEAN,
  created_at TIMESTAMP
)
```

---

### 🟡 **PRIORITY 6: Confidence Threshold Algorithm**
**Question #9: Best Practice for Confidence Levels**

**Decision:** Multi-factor confidence scoring with LLM self-assessment

**Reasoning:**
- **Transparency:** Students need to trust the system
- **Safety:** Low confidence triggers tutor escalation (critical for MVP)
- **Industry Standard:** Similar to medical/legal AI systems

**Algorithm:**
```python
def calculate_confidence(query, answer, context):
    """
    Returns: "High" | "Medium" | "Low"
    """
    factors = {
        'llm_confidence': get_llm_self_assessment(query, answer),  # 0-1
        'context_relevance': check_context_match(query, context),  # 0-1
        'answer_length': normalize_length(answer),  # 0-1
        'domain_expertise': check_domain_coverage(query),  # 0-1
    }
    
    weighted_score = (
        factors['llm_confidence'] * 0.4 +
        factors['context_relevance'] * 0.3 +
        factors['answer_length'] * 0.1 +
        factors['domain_expertise'] * 0.2
    )
    
    if weighted_score >= 0.75:
        return "High"
    elif weighted_score >= 0.50:
        return "Medium"
    else:
        return "Low"
```

**Thresholds:**
- **High (≥0.75):** Direct answer, no escalation
- **Medium (0.50-0.74):** Answer with disclaimer, optional tutor suggestion
- **Low (<0.50):** High-level overview + mandatory tutor escalation prompt

**LLM Prompt for Self-Assessment:**
```
Rate your confidence in this answer (0-1) considering:
- Completeness of information
- Alignment with educational standards
- Potential for misunderstanding
- Need for human verification
```

---

### 🟡 **PRIORITY 7: Adaptive Difficulty Algorithm**
**Question #10: Best Practice for Difficulty Adjustment**

**Decision:** Elo-based rating system with subject-specific tracking

**Reasoning:**
- **Proven:** Used in chess, Duolingo, Khan Academy
- **Adaptive:** Adjusts based on performance, not just right/wrong
- **Multi-Goal:** Tracks difficulty per subject independently
- **Fair:** Accounts for question difficulty, not just student ability

**Algorithm:**
```python
def update_difficulty_rating(student_id, subject, question_difficulty, performance):
    """
    Elo-style rating update
    performance: 0.0 (completely wrong) to 1.0 (perfect)
    """
    current_rating = get_student_rating(student_id, subject)  # Default: 1000
    question_rating = question_difficulty * 100  # Scale 1-10 to 100-1000
    
    expected_score = 1 / (1 + 10 ** ((question_rating - current_rating) / 400))
    actual_score = performance
    
    k_factor = 32  # Learning rate (higher = faster adjustment)
    new_rating = current_rating + k_factor * (actual_score - expected_score)
    
    update_student_rating(student_id, subject, new_rating)
    
    # Select next question difficulty
    target_difficulty = new_rating / 100  # Convert back to 1-10 scale
    return select_question_in_range(target_difficulty - 1, target_difficulty + 1)
```

**Performance Calculation:**
```python
def calculate_performance(answer, correct_answer, time_taken, hints_used):
    """
    Multi-factor performance score
    """
    accuracy = 1.0 if answer == correct_answer else 0.0
    time_bonus = min(1.0, optimal_time / time_taken)  # Faster = better
    hint_penalty = 1.0 - (hints_used * 0.1)  # Each hint reduces score
    
    return (accuracy * 0.7 + time_bonus * 0.2 + hint_penalty * 0.1)
```

**Difficulty Selection:**
- **Beginner (Rating < 800):** Questions 1-3
- **Intermediate (800-1200):** Questions 4-7
- **Advanced (1200+):** Questions 8-10
- **Challenge Mode:** Occasionally assign +2 difficulty for growth

---

## Phase 3: Integration Services (Week 4-5)

### 🟢 **PRIORITY 8: Email Service Setup**
**Question #12: Set Up Email Service**

**Decision:** AWS SES (Simple Email Service)

**Reasoning:**
- **Cost:** $0.10 per 1,000 emails (very affordable)
- **Integration:** Native AWS, works with Lambda/ECS
- **Deliverability:** High inbox placement rates
- **Templates:** Support for HTML email templates for nudges

**Implementation:**
- AWS SES for transactional emails (nudges)
- Email templates stored in S3 or inline
- Track opens/clicks via SES event publishing to SNS

---

### 🟢 **PRIORITY 9: Rails/React Integration Points**
**Question #2: Separate Service Integrating with Rails App**

**Decision:** RESTful API with clear contracts

**Reasoning:**
- **Separation of Concerns:** Microservice architecture
- **Technology Flexibility:** Can use Python/Node.js for AI features
- **Scalability:** Independent scaling of AI service vs Rails app

**API Contract Design:**
```
POST /api/v1/transcripts          # Rails → AI Service (session complete)
GET  /api/v1/summaries/:user_id   # Rails → AI Service (fetch summaries)
POST /api/v1/practice/assign      # Rails → AI Service (request practice)
POST /api/v1/qa/query             # React → AI Service (student query)
GET  /api/v1/progress/:user_id    # React → AI Service (dashboard)
POST /api/v1/overrides            # Rails → AI Service (tutor override)
```

**Authentication:**
- API keys for service-to-service (Rails → AI Service)
- JWT tokens for user-facing requests (React → AI Service)

---

## Phase 4: Testing & Validation (Week 5-6)

### 🔵 **PRIORITY 10: Golden Response Creation**
**Question #13: Create Golden Responses**

**Decision:** Test suite with expected outputs for each edge case

**Reasoning:**
- **Quality Assurance:** Ensures consistent AI behavior
- **Regression Testing:** Catch issues when prompts change
- **Documentation:** Serves as specification for AI behavior

**Structure:**
```yaml
# golden_responses/session_summaries.yaml
test_cases:
  - name: "missing_transcript"
    input: { transcript: null, session_duration: 30 }
    expected_output: {
      summary: "Transcript unavailable. Limited recap generated.",
      next_steps: ["Review previous session notes", "Prepare questions for next session"]
    }
  
  - name: "mixed_subjects"
    input: { transcript: "...factoring polynomials...balancing equations..." }
    expected_output: {
      summary: "We reviewed factoring polynomials, then pivoted to balancing chemical equations.",
      next_steps: ["Practice polynomial factoring", "Review chemical equation balancing"]
    }
```

---

### 🔵 **PRIORITY 11: Demo Data Generation**
**Question #14: Generate Demo Data at End**

**Decision:** Seed script with realistic scenarios

**Reasoning:**
- **Demo Readiness:** Show all features working end-to-end
- **Testing:** Validate edge cases with known data
- **Onboarding:** Help new developers understand the system

**Data to Generate:**
- 10 students with varying progress levels
- 5 tutors with different specializations
- 20+ tutoring session transcripts (various lengths, subjects)
- 50+ practice bank items (multiple subjects, difficulties)
- Sample Q&A interactions (High/Medium/Low confidence examples)
- Nudge history (opened/clicked/ignored)
- Override examples (tutor corrections)

---

## Implementation Timeline Summary

| Week | Phase | Priorities | Deliverables |
|------|-------|------------|--------------|
| 1-2  | Foundation | #1 Database, #2 Auth, #3 Relationships, #4 Goals | Schema, Auth working |
| 2-4  | Business Logic | #5 Practice Bank, #6 Confidence, #7 Difficulty | Core algorithms implemented |
| 4-5  | Integration | #8 Email, #9 API Contracts | External services connected |
| 5-6  | Testing | #10 Golden Responses, #11 Demo Data | Validated, demo-ready |

---

## Key Architectural Decisions

1. **PostgreSQL over DynamoDB** → Better for Rails integration and complex queries
2. **AWS Cognito** → Managed auth, reduces security risk
3. **Multi-factor Confidence** → More reliable than single LLM assessment
4. **Elo Rating System** → Proven adaptive difficulty algorithm
5. **RESTful API** → Standard integration pattern for Rails/React

---

## Next Steps

1. Review and approve this priority plan
2. Set up AWS infrastructure (RDS, Cognito, SES)
3. Begin Phase 1 implementation
4. Schedule weekly reviews to adjust priorities based on blockers

