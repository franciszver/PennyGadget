-- Add Parent-Student Assignments Table
-- Migration 004: parent<->student linkage for scoped parent dashboard access (#68)
-- Links are admin/seed-provisioned; there is no self-service linking endpoint.

CREATE TABLE IF NOT EXISTS parent_student_assignments (
    parent_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'paused', 'completed')),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (parent_id, student_id)
);

CREATE INDEX IF NOT EXISTS idx_psa_parent ON parent_student_assignments(parent_id);
CREATE INDEX IF NOT EXISTS idx_psa_student ON parent_student_assignments(student_id);
CREATE INDEX IF NOT EXISTS idx_psa_status ON parent_student_assignments(status);

CREATE TRIGGER update_parent_student_assignments_updated_at BEFORE UPDATE ON parent_student_assignments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
