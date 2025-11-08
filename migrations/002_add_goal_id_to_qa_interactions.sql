-- Migration: Add goal_id to qa_interactions table
-- Purpose: Track which goal each QA interaction is associated with for question limit enforcement

-- Add goal_id column to qa_interactions table
ALTER TABLE qa_interactions
ADD COLUMN IF NOT EXISTS goal_id UUID REFERENCES goals(id) ON DELETE SET NULL;

-- Create index for goal_id for efficient querying
CREATE INDEX IF NOT EXISTS idx_qa_goal ON qa_interactions(goal_id);

-- Create composite index for efficient counting of questions per user per goal
CREATE INDEX IF NOT EXISTS idx_qa_student_goal ON qa_interactions(student_id, goal_id);


