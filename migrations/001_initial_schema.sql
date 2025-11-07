-- Initial Schema Migration
-- AI Study Companion MVP
-- Version: 1.0.0

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- Core Tables
-- ============================================================================

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cognito_sub VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('student', 'tutor', 'parent', 'admin')),
    
    profile JSONB DEFAULT '{}',
    gamification JSONB DEFAULT '{}',
    analytics JSONB DEFAULT '{}',
    
    disclaimer_shown BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_users_cognito_sub ON users(cognito_sub);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- Subjects table
CREATE TABLE IF NOT EXISTS subjects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    category VARCHAR(50),
    description TEXT,
    related_subjects UUID[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_subjects_category ON subjects(category);

-- Tutor-Student Assignments (many-to-many)
CREATE TABLE IF NOT EXISTS tutor_student_assignments (
    tutor_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    subject_id UUID REFERENCES subjects(id),
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'paused', 'completed')),
    
    notes TEXT,
    start_date DATE,
    end_date DATE,
    
    PRIMARY KEY (tutor_id, student_id, subject_id)
);

CREATE INDEX IF NOT EXISTS idx_tsa_tutor ON tutor_student_assignments(tutor_id);
CREATE INDEX IF NOT EXISTS idx_tsa_student ON tutor_student_assignments(student_id);
CREATE INDEX IF NOT EXISTS idx_tsa_status ON tutor_student_assignments(status);

-- Goals table
CREATE TABLE IF NOT EXISTS goals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_by UUID NOT NULL REFERENCES users(id),
    
    subject_id UUID REFERENCES subjects(id),
    goal_type VARCHAR(50),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    
    target_completion_date DATE,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'completed', 'paused', 'cancelled')),
    
    completion_percentage DECIMAL(5,2) DEFAULT 0.00 CHECK (completion_percentage >= 0 AND completion_percentage <= 100),
    current_streak INTEGER DEFAULT 0,
    xp_earned INTEGER DEFAULT 0,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_goals_student ON goals(student_id);
CREATE INDEX IF NOT EXISTS idx_goals_status ON goals(status);
CREATE INDEX IF NOT EXISTS idx_goals_subject ON goals(subject_id);

-- Sessions table
CREATE TABLE IF NOT EXISTS sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tutor_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    session_date TIMESTAMP WITH TIME ZONE NOT NULL,
    duration_minutes INTEGER,
    subject_id UUID REFERENCES subjects(id),
    
    transcript_text TEXT,
    transcript_storage_url VARCHAR(500),
    transcript_available BOOLEAN DEFAULT TRUE,
    
    topics_covered TEXT[],
    notes TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_sessions_student ON sessions(student_id);
CREATE INDEX IF NOT EXISTS idx_sessions_tutor ON sessions(tutor_id);
CREATE INDEX IF NOT EXISTS idx_sessions_date ON sessions(session_date);

-- Summaries table
CREATE TABLE IF NOT EXISTS summaries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tutor_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    narrative TEXT NOT NULL,
    next_steps TEXT[] NOT NULL,
    
    subjects_covered TEXT[],
    summary_type VARCHAR(50),
    
    overridden BOOLEAN DEFAULT FALSE,
    override_id UUID,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_summaries_session ON summaries(session_id);
CREATE INDEX IF NOT EXISTS idx_summaries_student ON summaries(student_id);
CREATE INDEX IF NOT EXISTS idx_summaries_tutor ON summaries(tutor_id);

-- Practice Bank Items
CREATE TABLE IF NOT EXISTS practice_bank_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    question_text TEXT NOT NULL,
    answer_text TEXT NOT NULL,
    explanation TEXT,
    
    subject_id UUID NOT NULL REFERENCES subjects(id),
    difficulty_level INTEGER NOT NULL CHECK (difficulty_level >= 1 AND difficulty_level <= 10),
    goal_tags TEXT[],
    topic_tags TEXT[],
    
    created_by UUID REFERENCES users(id),
    version INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT TRUE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_pbi_subject ON practice_bank_items(subject_id);
CREATE INDEX IF NOT EXISTS idx_pbi_difficulty ON practice_bank_items(difficulty_level);
CREATE INDEX IF NOT EXISTS idx_pbi_goal_tags ON practice_bank_items USING GIN(goal_tags);
CREATE INDEX IF NOT EXISTS idx_pbi_active ON practice_bank_items(is_active);

-- Practice Assignments
CREATE TABLE IF NOT EXISTS practice_assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    source VARCHAR(20) NOT NULL CHECK (source IN ('bank', 'ai_generated')),
    bank_item_id UUID REFERENCES practice_bank_items(id),
    
    ai_question_text TEXT,
    ai_answer_text TEXT,
    ai_explanation TEXT,
    flagged BOOLEAN DEFAULT FALSE,
    
    subject_id UUID REFERENCES subjects(id),
    difficulty_level INTEGER CHECK (difficulty_level >= 1 AND difficulty_level <= 10),
    goal_tags TEXT[],
    
    student_rating_before INTEGER,
    student_rating_after INTEGER,
    performance_score DECIMAL(3,2),
    completed BOOLEAN DEFAULT FALSE,
    completed_at TIMESTAMP WITH TIME ZONE,
    
    overridden BOOLEAN DEFAULT FALSE,
    override_id UUID,
    
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_pa_student ON practice_assignments(student_id);
CREATE INDEX IF NOT EXISTS idx_pa_source ON practice_assignments(source);
CREATE INDEX IF NOT EXISTS idx_pa_flagged ON practice_assignments(flagged);
CREATE INDEX IF NOT EXISTS idx_pa_completed ON practice_assignments(completed);

-- Student Ratings (Elo system)
CREATE TABLE IF NOT EXISTS student_ratings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    subject_id UUID NOT NULL REFERENCES subjects(id),
    
    rating INTEGER DEFAULT 1000,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(student_id, subject_id)
);

CREATE INDEX IF NOT EXISTS idx_sr_student ON student_ratings(student_id);
CREATE INDEX IF NOT EXISTS idx_sr_subject ON student_ratings(subject_id);
CREATE INDEX IF NOT EXISTS idx_sr_rating ON student_ratings(rating);

-- Q&A Interactions
CREATE TABLE IF NOT EXISTS qa_interactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    query TEXT NOT NULL,
    answer TEXT NOT NULL,
    confidence VARCHAR(10) NOT NULL CHECK (confidence IN ('High', 'Medium', 'Low')),
    confidence_score DECIMAL(3,2),
    
    context_subjects TEXT[],
    clarification_requested BOOLEAN DEFAULT FALSE,
    out_of_scope BOOLEAN DEFAULT FALSE,
    
    tutor_escalation_suggested BOOLEAN DEFAULT FALSE,
    escalated_to_tutor_id UUID REFERENCES users(id),
    
    disclaimer_shown BOOLEAN DEFAULT TRUE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_qa_student ON qa_interactions(student_id);
CREATE INDEX IF NOT EXISTS idx_qa_confidence ON qa_interactions(confidence);
CREATE INDEX IF NOT EXISTS idx_qa_created ON qa_interactions(created_at);

-- Nudges
CREATE TABLE IF NOT EXISTS nudges (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    type VARCHAR(50) NOT NULL,
    channel VARCHAR(20) NOT NULL CHECK (channel IN ('in_app', 'email', 'both')),
    
    message TEXT NOT NULL,
    personalized BOOLEAN DEFAULT TRUE,
    
    sent_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    opened_at TIMESTAMP WITH TIME ZONE,
    clicked_at TIMESTAMP WITH TIME ZONE,
    
    trigger_reason TEXT,
    suggestions_made TEXT[],
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_nudges_user ON nudges(user_id);
CREATE INDEX IF NOT EXISTS idx_nudges_type ON nudges(type);
CREATE INDEX IF NOT EXISTS idx_nudges_sent ON nudges(sent_at);
CREATE INDEX IF NOT EXISTS idx_nudges_opened ON nudges(opened_at);

-- Overrides
CREATE TABLE IF NOT EXISTS overrides (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tutor_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    override_type VARCHAR(50) NOT NULL,
    action TEXT NOT NULL,
    
    summary_id UUID REFERENCES summaries(id),
    practice_assignment_id UUID REFERENCES practice_assignments(id),
    qa_interaction_id UUID REFERENCES qa_interactions(id),
    
    original_content JSONB,
    new_content JSONB,
    reason TEXT,
    
    subject_id UUID REFERENCES subjects(id),
    difficulty_level INTEGER,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_overrides_tutor ON overrides(tutor_id);
CREATE INDEX IF NOT EXISTS idx_overrides_student ON overrides(student_id);
CREATE INDEX IF NOT EXISTS idx_overrides_type ON overrides(override_type);
CREATE INDEX IF NOT EXISTS idx_overrides_created ON overrides(created_at);

-- ============================================================================
-- Functions
-- ============================================================================

-- Update updated_at timestamp function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_goals_updated_at BEFORE UPDATE ON goals
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_summaries_updated_at BEFORE UPDATE ON summaries
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_practice_bank_items_updated_at BEFORE UPDATE ON practice_bank_items
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Elo rating update function
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

-- ============================================================================
-- Views (for Analytics)
-- ============================================================================

-- Student Progress View
CREATE OR REPLACE VIEW v_student_progress AS
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

-- Override Analytics View
CREATE OR REPLACE VIEW v_override_analytics AS
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

-- Confidence Distribution View
CREATE OR REPLACE VIEW v_confidence_distribution AS
SELECT 
    student_id,
    confidence,
    COUNT(*) AS count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY student_id), 2) AS percentage
FROM qa_interactions
GROUP BY student_id, confidence;

