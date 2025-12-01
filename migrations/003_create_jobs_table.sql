-- Create jobs table for async background job tracking
CREATE TABLE IF NOT EXISTS jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    student_id UUID REFERENCES users(id) ON DELETE CASCADE,
    parameters JSONB NOT NULL,
    result JSONB,
    error_message TEXT,
    progress_percent INTEGER DEFAULT 0,
    progress_message VARCHAR(255),
    webhook_url VARCHAR(500),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_jobs_job_type ON jobs(job_type);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_user_id ON jobs(user_id);
CREATE INDEX IF NOT EXISTS idx_jobs_student_id ON jobs(student_id);
CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs(created_at);

-- Add check constraint for status
ALTER TABLE jobs ADD CONSTRAINT check_job_status 
    CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'cancelled'));

-- Add check constraint for progress_percent
ALTER TABLE jobs ADD CONSTRAINT check_progress_percent 
    CHECK (progress_percent >= 0 AND progress_percent <= 100);

-- Create trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_jobs_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_jobs_updated_at
    BEFORE UPDATE ON jobs
    FOR EACH ROW
    EXECUTE FUNCTION update_jobs_updated_at();

