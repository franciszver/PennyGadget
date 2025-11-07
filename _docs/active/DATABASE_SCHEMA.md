# 🗄️ Database Schema Design
**Product:** AI Study Companion MVP  
**Database:** PostgreSQL on AWS RDS  
**Version:** 1.0.0

---

## Schema Overview

This schema supports:
- Multi-role users (students, tutors, parents, admins)
- Many-to-many tutor-student relationships
- Session transcripts and AI-generated summaries
- Practice bank with AI-generated items
- Q&A interactions with confidence tracking
- Nudges and engagement tracking
- Tutor overrides with immediate updates
- Multi-goal progress tracking
- Analytics and reporting

---

## Core Tables

### `users`
Primary user table storing all user types with role-based access.

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cognito_sub VARCHAR(255) UNIQUE NOT NULL,  -- AWS Cognito user ID
    email VARCHAR(255) UNIQUE NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('student', 'tutor', 'parent', 'admin')),
    
    -- Profile data (JSONB for flexibility)
    profile JSONB DEFAULT '{}',
    -- Structure:
    -- {
    --   "goals": [...],
    --   "subjects": [...],
    --   "preferences": {
    --     "learning_style": "visual" | "textual" | "mixed",
    --     "nudge_frequency_cap": 1
    --   },
    --   "progress": {
    --     "multi_goal_tracking": [
    --       {
    --         "subject": "string",
    --         "completion": "%",
    --         "streak": int,
    --         "xp": int
    --       }
    --     ]
    --   }
    -- }
    
    -- Gamification (MVP: basic, POST-MVP: expanded)
    gamification JSONB DEFAULT '{}',
    -- Structure:
    -- {
    --   "xp": int,
    --   "level": int,
    --   "badges": [...],
    --   "streaks": int,
    --   "meta_rewards": [...]
    -- }
    
    -- Analytics (aggregated)
    analytics JSONB DEFAULT '{}',
    -- Structure:
    -- {
    --   "override_count": int,
    --   "confidence_distribution": {
    --     "High": "%",
    --     "Medium": "%",
    --     "Low": "%"
    --   },
    --   "nudge_engagement": {
    --     "opened": "%",
    --     "clicked": "%"
    --   }
    -- }
    
    disclaimer_shown BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_cognito_sub ON users(cognito_sub);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_email ON users(email);
```

---

### `tutor_student_assignments`
Junction table for many-to-many tutor-student relationships.

```sql
CREATE TABLE tutor_student_assignments (
    tutor_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    subject_id UUID REFERENCES subjects(id),  -- Optional: subject-specific assignment
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'paused', 'completed')),
    
    -- Relationship metadata
    notes TEXT,
    start_date DATE,
    end_date DATE,
    
    PRIMARY KEY (tutor_id, student_id, subject_id),
    CONSTRAINT check_tutor_role CHECK (
        EXISTS (SELECT 1 FROM users WHERE id = tutor_id AND role = 'tutor')
    ),
    CONSTRAINT check_student_role CHECK (
        EXISTS (SELECT 1 FROM users WHERE id = student_id AND role = 'student')
    )
);

CREATE INDEX idx_tsa_tutor ON tutor_student_assignments(tutor_id);
CREATE INDEX idx_tsa_student ON tutor_student_assignments(student_id);
CREATE INDEX idx_tsa_status ON tutor_student_assignments(status);
```

---

### `subjects`
Subject catalog (e.g., Algebra, Chemistry, SAT Math).

```sql
CREATE TABLE subjects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    category VARCHAR(50),  -- e.g., "Math", "Science", "Test Prep"
    description TEXT,
    related_subjects UUID[],  -- Array of related subject IDs for cross-subject suggestions
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_subjects_category ON subjects(category);
```

---

### `goals`
Student goals (can be created by students or tutors).

```sql
CREATE TABLE goals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_by UUID NOT NULL REFERENCES users(id),  -- Who created it (tutor or student)
    
    subject_id UUID REFERENCES subjects(id),
    goal_type VARCHAR(50),  -- e.g., "SAT", "AP", "General"
    title VARCHAR(255) NOT NULL,
    description TEXT,
    
    target_completion_date DATE,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'completed', 'paused', 'cancelled')),
    
    -- Progress tracking
    completion_percentage DECIMAL(5,2) DEFAULT 0.00 CHECK (completion_percentage >= 0 AND completion_percentage <= 100),
    current_streak INTEGER DEFAULT 0,
    xp_earned INTEGER DEFAULT 0,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_goals_student ON goals(student_id);
CREATE INDEX idx_goals_status ON goals(status);
CREATE INDEX idx_goals_subject ON goals(subject_id);
```

---

### `sessions`
Tutoring session records.

```sql
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tutor_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    session_date TIMESTAMP WITH TIME ZONE NOT NULL,
    duration_minutes INTEGER,
    subject_id UUID REFERENCES subjects(id),
    
    -- Transcript (stored as text, may reference external storage)
    transcript_text TEXT,
    transcript_storage_url VARCHAR(500),  -- S3 URL if stored externally
    transcript_available BOOLEAN DEFAULT TRUE,
    
    -- Session metadata
    topics_covered TEXT[],
    notes TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_sessions_student ON sessions(student_id);
CREATE INDEX idx_sessions_tutor ON sessions(tutor_id);
CREATE INDEX idx_sessions_date ON sessions(session_date);
```

---

### `summaries`
AI-generated session summaries (permanently stored).

```sql
CREATE TABLE summaries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tutor_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- AI-generated content
    narrative TEXT NOT NULL,  -- The summary narrative
    next_steps TEXT[] NOT NULL,  -- Array of actionable next steps
    
    -- Metadata
    subjects_covered TEXT[],
    summary_type VARCHAR(50),  -- e.g., "normal", "brief", "missing_transcript"
    
    -- Override tracking
    overridden BOOLEAN DEFAULT FALSE,
    override_id UUID REFERENCES overrides(id),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_summaries_session ON summaries(session_id);
CREATE INDEX idx_summaries_student ON summaries(student_id);
CREATE INDEX idx_summaries_tutor ON summaries(tutor_id);
```

---

### `practice_bank_items`
Curated practice questions from the bank.

```sql
CREATE TABLE practice_bank_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Question content
    question_text TEXT NOT NULL,
    answer_text TEXT NOT NULL,
    explanation TEXT,
    
    -- Classification
    subject_id UUID NOT NULL REFERENCES subjects(id),
    difficulty_level INTEGER NOT NULL CHECK (difficulty_level >= 1 AND difficulty_level <= 10),
    goal_tags TEXT[],  -- e.g., ["SAT", "AP_Calculus"]
    topic_tags TEXT[],  -- e.g., ["quadratic_equations", "factoring"]
    
    -- Metadata
    created_by UUID REFERENCES users(id),  -- Admin/tutor who created it
    version INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT TRUE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_pbi_subject ON practice_bank_items(subject_id);
CREATE INDEX idx_pbi_difficulty ON practice_bank_items(difficulty_level);
CREATE INDEX idx_pbi_goal_tags ON practice_bank_items USING GIN(goal_tags);
CREATE INDEX idx_pbi_active ON practice_bank_items(is_active);
```

---

### `practice_assignments`
Assigned practice items (from bank or AI-generated).

```sql
CREATE TABLE practice_assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Source tracking
    source VARCHAR(20) NOT NULL CHECK (source IN ('bank', 'ai_generated')),
    bank_item_id UUID REFERENCES practice_bank_items(id),
    
    -- AI-generated items (if source = 'ai_generated')
    ai_question_text TEXT,
    ai_answer_text TEXT,
    ai_explanation TEXT,
    flagged BOOLEAN DEFAULT FALSE,  -- AI items are flagged for tutor review
    
    -- Assignment metadata
    subject_id UUID REFERENCES subjects(id),
    difficulty_level INTEGER CHECK (difficulty_level >= 1 AND difficulty_level <= 10),
    goal_tags TEXT[],
    
    -- Student performance
    student_rating_before INTEGER,  -- Elo rating before this assignment
    student_rating_after INTEGER,   -- Elo rating after completion
    performance_score DECIMAL(3,2), -- 0.00 to 1.00
    completed BOOLEAN DEFAULT FALSE,
    completed_at TIMESTAMP WITH TIME ZONE,
    
    -- Override tracking
    overridden BOOLEAN DEFAULT FALSE,
    override_id UUID REFERENCES overrides(id),
    
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_pa_student ON practice_assignments(student_id);
CREATE INDEX idx_pa_source ON practice_assignments(source);
CREATE INDEX idx_pa_flagged ON practice_assignments(flagged);
CREATE INDEX idx_pa_completed ON practice_assignments(completed);
```

---

### `student_ratings`
Elo-style ratings per student per subject (for adaptive difficulty).

```sql
CREATE TABLE student_ratings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    subject_id UUID NOT NULL REFERENCES subjects(id),
    
    rating INTEGER DEFAULT 1000,  -- Elo rating (default 1000 = intermediate)
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(student_id, subject_id)
);

CREATE INDEX idx_sr_student ON student_ratings(student_id);
CREATE INDEX idx_sr_subject ON student_ratings(subject_id);
CREATE INDEX idx_sr_rating ON student_ratings(rating);
```

---

### `qa_interactions`
Q&A conversations with confidence tracking.

```sql
CREATE TABLE qa_interactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    query TEXT NOT NULL,
    answer TEXT NOT NULL,
    confidence VARCHAR(10) NOT NULL CHECK (confidence IN ('High', 'Medium', 'Low')),
    confidence_score DECIMAL(3,2),  -- 0.00 to 1.00 (for analytics)
    
    -- Context
    context_subjects TEXT[],
    clarification_requested BOOLEAN DEFAULT FALSE,
    out_of_scope BOOLEAN DEFAULT FALSE,
    
    -- Escalation
    tutor_escalation_suggested BOOLEAN DEFAULT FALSE,
    escalated_to_tutor_id UUID REFERENCES users(id),
    
    -- Disclaimer
    disclaimer_shown BOOLEAN DEFAULT TRUE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_qa_student ON qa_interactions(student_id);
CREATE INDEX idx_qa_confidence ON qa_interactions(confidence);
CREATE INDEX idx_qa_created ON qa_interactions(created_at);
```

---

### `nudges`
Nudge tracking (in-app and email).

```sql
CREATE TABLE nudges (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    type VARCHAR(50) NOT NULL,  -- 'login', 'inactivity', 'cross_subject'
    channel VARCHAR(20) NOT NULL CHECK (channel IN ('in_app', 'email', 'both')),
    
    message TEXT NOT NULL,
    personalized BOOLEAN DEFAULT TRUE,
    
    -- Engagement tracking
    sent_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    opened_at TIMESTAMP WITH TIME ZONE,
    clicked_at TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    trigger_reason TEXT,
    suggestions_made TEXT[],  -- For cross-subject nudges
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_nudges_user ON nudges(user_id);
CREATE INDEX idx_nudges_type ON nudges(type);
CREATE INDEX idx_nudges_sent ON nudges(sent_at);
CREATE INDEX idx_nudges_opened ON nudges(opened_at);
```

---

### `overrides`
Tutor overrides of AI suggestions.

```sql
CREATE TABLE overrides (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tutor_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    override_type VARCHAR(50) NOT NULL,  -- 'summary', 'practice', 'qa_answer'
    action TEXT NOT NULL,  -- Description of override action
    
    -- References to overridden content
    summary_id UUID REFERENCES summaries(id),
    practice_assignment_id UUID REFERENCES practice_assignments(id),
    qa_interaction_id UUID REFERENCES qa_interactions(id),
    
    -- Override details
    original_content JSONB,  -- Snapshot of original
    new_content JSONB,       -- New content
    reason TEXT,              -- Why override was made
    
    -- Analytics
    subject_id UUID REFERENCES subjects(id),
    difficulty_level INTEGER,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_overrides_tutor ON overrides(tutor_id);
CREATE INDEX idx_overrides_student ON overrides(student_id);
CREATE INDEX idx_overrides_type ON overrides(override_type);
CREATE INDEX idx_overrides_created ON overrides(created_at);
```

---

## Views (for Analytics & Reporting)

### `v_student_progress`
Aggregated progress view for dashboards.

```sql
CREATE VIEW v_student_progress AS
SELECT 
    g.student_id,
    g.id AS goal_id,
    s.name AS subject_name,
    g.completion_percentage,
    g.current_streak,
    g.xp_earned,
    g.status,
    g.target_completion_date,
    COUNT(DISTINCT sess.id) AS sessions_count,
    COUNT(DISTINCT pa.id) AS practice_items_completed,
    AVG(sr.rating) AS average_rating
FROM goals g
LEFT JOIN subjects s ON g.subject_id = s.id
LEFT JOIN sessions sess ON sess.student_id = g.student_id AND sess.subject_id = g.subject_id
LEFT JOIN practice_assignments pa ON pa.student_id = g.student_id AND pa.completed = TRUE
LEFT JOIN student_ratings sr ON sr.student_id = g.student_id AND sr.subject_id = g.subject_id
WHERE g.status = 'active'
GROUP BY g.id, g.student_id, s.name, g.completion_percentage, g.current_streak, 
         g.xp_earned, g.status, g.target_completion_date;
```

---

### `v_override_analytics`
Analytics view for tutor override patterns.

```sql
CREATE VIEW v_override_analytics AS
SELECT 
    o.override_type,
    s.name AS subject_name,
    o.difficulty_level,
    COUNT(*) AS override_count,
    COUNT(DISTINCT o.tutor_id) AS unique_tutors,
    COUNT(DISTINCT o.student_id) AS unique_students,
    DATE_TRUNC('day', o.created_at) AS override_date
FROM overrides o
LEFT JOIN subjects s ON o.subject_id = s.id
GROUP BY o.override_type, s.name, o.difficulty_level, DATE_TRUNC('day', o.created_at);
```

---

### `v_confidence_distribution`
Q&A confidence distribution analytics.

```sql
CREATE VIEW v_confidence_distribution AS
SELECT 
    student_id,
    confidence,
    COUNT(*) AS count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY student_id), 2) AS percentage
FROM qa_interactions
GROUP BY student_id, confidence;
```

---

## Functions & Triggers

### Update `updated_at` timestamp

```sql
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_goals_updated_at BEFORE UPDATE ON goals
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_summaries_updated_at BEFORE UPDATE ON summaries
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

---

### Calculate student rating update (Elo algorithm)

```sql
CREATE OR REPLACE FUNCTION update_student_rating(
    p_student_id UUID,
    p_subject_id UUID,
    p_question_rating INTEGER,
    p_performance_score DECIMAL
)
RETURNS INTEGER AS $$
DECLARE
    v_current_rating INTEGER;
    v_new_rating INTEGER;
    v_expected_score DECIMAL;
    v_k_factor INTEGER := 32;
BEGIN
    -- Get or create current rating
    SELECT COALESCE(rating, 1000) INTO v_current_rating
    FROM student_ratings
    WHERE student_id = p_student_id AND subject_id = p_subject_id;
    
    -- Calculate expected score (Elo formula)
    v_expected_score := 1.0 / (1.0 + POWER(10.0, (p_question_rating - v_current_rating) / 400.0));
    
    -- Calculate new rating
    v_new_rating := v_current_rating + v_k_factor * (p_performance_score - v_expected_score);
    
    -- Update or insert
    INSERT INTO student_ratings (student_id, subject_id, rating, last_updated)
    VALUES (p_student_id, p_subject_id, v_new_rating, CURRENT_TIMESTAMP)
    ON CONFLICT (student_id, subject_id)
    DO UPDATE SET 
        rating = v_new_rating,
        last_updated = CURRENT_TIMESTAMP;
    
    RETURN v_new_rating;
END;
$$ LANGUAGE plpgsql;
```

---

## Migration Strategy

1. **Phase 1:** Core tables (users, subjects, goals, sessions)
2. **Phase 2:** Practice and Q&A tables
3. **Phase 3:** Nudges and overrides
4. **Phase 4:** Views and functions
5. **Phase 5:** Indexes optimization

---

## Rails Integration Notes

- Use `pg` gem for PostgreSQL connection
- Use `activerecord` with custom connection pooling for Lambda/ECS
- Consider `activerecord-import` for bulk inserts
- Use `jsonb` columns for flexible schema (Rails 5+ supports JSONB natively)
- UUID primary keys work with Rails (use `uuid` gem or PostgreSQL's `gen_random_uuid()`)

---

## Security Considerations

- Row-level security (RLS) policies for multi-tenant data
- Encrypt sensitive fields (transcripts, personal notes)
- Audit logging for overrides and sensitive operations
- Connection pooling limits to prevent resource exhaustion
- Regular backups (RDS automated backups)

---

## Performance Optimization

- Indexes on all foreign keys
- GIN indexes for array columns (goal_tags, topic_tags)
- Partition large tables by date if needed (sessions, qa_interactions)
- Connection pooling (PgBouncer) for Lambda/ECS
- Read replicas for analytics queries

