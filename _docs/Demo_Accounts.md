<!-- 15b5cb04-295d-41d6-a382-40f85fd87fac b48de7cb-0a60-4821-97e2-03c7f4f0c496 -->
# Demo User Accounts for Boss Presentation

## Overview

Create 5 specific demo-ready test user accounts that can be immediately used to demo each requirement to your boss. Each account will have clear credentials and be pre-configured with the exact data needed to trigger the demo scenario.

## Demo Accounts

All accounts use password: `demo123`

1. **demo_goal_complete@demo.com** - Shows goal completion → related subject suggestions (addresses 52% churn)
2. **demo_sat_complete@demo.com** - Shows SAT completion → College Essays, Study Skills, AP Prep
3. **demo_chemistry@demo.com** - Shows Chemistry completion → Physics, STEM suggestions
4. **demo_low_sessions@demo.com** - Shows inactivity nudge (<3 sessions by Day 7) → prompts to book session
5. **demo_multi_goal@demo.com** - Shows multi-goal progress tracking (3+ active goals)

## Tasks

### 1. Create Demo User Accounts Script

**File**: `scripts/create_demo_users.py`

- Create script that uses SQLAlchemy to insert 5 demo accounts directly into database
- Use `get_db()` from `src.config.database` for database connection
- Create subjects first: "College Essays", "Study Skills", "AP Prep", "Physics", "Biology", "AP Chemistry", "STEM Prep" (if not exist)
- For each demo account:
- Create User with specific email and cognito_sub
- Set created_at to appropriate date (7 days ago for demo_low_sessions, 30 days ago for others)
- Create appropriate goals (completed/active) with proper subjects
- Create appropriate sessions (count and dates)
- Link goals to subjects properly
- Handle all foreign key relationships
- Use transactions for data integrity

### 2. Demo Account Data Setup

**demo_goal_complete@demo.com**:

- Created 30 days ago
- 1 recently completed goal: "Improve Algebra Skills" (completed 2 days ago, subject: Algebra)
- 2 active goals in related subjects (Geometry, Pre-Calculus)
- 5+ sessions completed
- Should show related subject suggestions when viewing progress

**demo_sat_complete@demo.com**:

- Created 30 days ago
- 1 recently completed SAT Math goal (completed 1 day ago, goal_type: "SAT", subject: "SAT Math")
- 5+ sessions completed
- Should trigger suggestions: "College Essays", "Study Skills", "AP Prep" when viewing progress

**demo_chemistry@demo.com**:

- Created 30 days ago
- 1 recently completed Chemistry goal (completed 3 days ago, subject: "Chemistry")
- 5+ sessions completed
- Should trigger suggestions: "Physics", "Biology", "AP Chemistry", "STEM Prep" when viewing progress

**demo_low_sessions@demo.com**:

- Created exactly 7 days ago (created_at = today - 7 days)
- Only 2 sessions completed (below threshold of 3)
- 1 active goal
- Should trigger inactivity nudge when checking nudges endpoint
- Nudge should suggest "book next session"

**demo_multi_goal@demo.com**:

- Created 30 days ago
- 3+ active goals across different subjects:
- Goal 1: "Master Algebra" (Math, 75% complete)
- Goal 2: "Chemistry Fundamentals" (Science, 50% complete)
- Goal 3: "SAT Prep" (Test Prep, 20% complete)
- 5+ sessions completed
- Progress endpoint should show all 3 goals with different completion percentages

### 3. Enhance Related Subject Suggestions

**File**: `src/api/handlers/progress.py`

- Update `_get_related_subjects()` function:
- When goal_type is "SAT" and goal is completed → return ["College Essays", "Study Skills", "AP Prep"]
- When subject is "Chemistry" and goal is completed → return ["Physics", "Biology", "AP Chemistry", "STEM Prep"]
- Ensure these suggestions appear in progress endpoint response

### 4. Verify Inactivity Nudge Logic

**File**: `src/services/nudges/engine.py`

- Verify `_check_inactivity_nudge()` correctly checks:
- Days since signup >= 7
- Session count < 3
- Ensure nudge message includes "book next session" in suggestions
- If needed, update to explicitly include "Schedule your next tutoring session" in suggestions

### 5. Create Demo Verification Script

**File**: `scripts/verify_demo_users.py`

- Verify all 5 demo accounts exist in database
- Check each account has correct:
- Goals (completed/active with proper dates)
- Sessions (count and dates)
- Subjects linked properly
- Test API endpoints return expected data:
- GET /api/v1/progress/{user_id} - Check suggestions appear
- POST /api/v1/nudges/check - Check inactivity nudge triggers for demo_low_sessions
- Print verification results with clear pass/fail

### 6. Create Demo Guide Document

**File**: `DEMO_USER_GUIDE.md`

- Document each demo account:
- Email and password
- What scenario it demonstrates
- Expected behavior when logging in
- Which API endpoints to test
- Which frontend pages to show
- Step-by-step demo script for boss presentation
- Troubleshooting tips

## Files to Create/Modify

**New Files:**

- `scripts/create_demo_users.py` - Creates 5 demo accounts with all required data
- `scripts/verify_demo_users.py` - Verifies demo accounts are set up correctly
- `DEMO_USER_GUIDE.md` - Guide for demoing each account

**Modified Files:**

- `src/api/handlers/progress.py` - Enhance `_get_related_subjects()` for SAT and Chemistry suggestions
- `src/services/nudges/engine.py` - Verify/update inactivity nudge to include "book next session" suggestion

## Implementation Details

### Database Seeding Order

1. Create subjects (if not exist): College Essays, Study Skills, AP Prep, Physics, Biology, AP Chemistry, STEM Prep
2. Create users (5 demo accounts)
3. Create goals (link to users and subjects)
4. Create sessions (link to users, set proper dates)
5. Commit transaction

### SAT Suggestions Logic

- Check if goal_type == "SAT" and status == "completed"
- Return: ["College Essays", "Study Skills", "AP Prep"]
- These should be subject names that can be used to create new goals

### Chemistry Suggestions Logic

- Check if subject name contains "Chemistry" and goal is completed
- Return: ["Physics", "Biology", "AP Chemistry", "STEM Prep"]

### Inactivity Nudge

- Current logic checks: days_since_signup >= 7 AND session_count < 3
- Ensure suggestions include: "Schedule your next tutoring session" or "Book your next session"

## Testing & Demo Steps

1. Run `python scripts/create_demo_users.py` to create all demo accounts
2. Run `python scripts/verify_demo_users.py` to verify setup
3. For each account:

- Login with email/password
- Navigate to Progress page
- Verify expected suggestions appear
- For demo_low_sessions: Check nudges endpoint triggers inactivity nudge

4. Use `DEMO_USER_GUIDE.md` for step-by-step demo script

## Demo Account Credentials Summary

| Account | Email | Password | Demo Scenario |
|---------|-------|----------|---------------|
| Goal Complete | demo_goal_complete@demo.com | demo123 | Goal completion → related subjects |
| SAT Complete | demo_sat_complete@demo.com | demo123 | SAT → College Essays, Study Skills, AP Prep |
| Chemistry | demo_chemistry@demo.com | demo123 | Chemistry → Physics, STEM |
| Low Sessions | demo_low_sessions@demo.com | demo123 | <3 sessions by Day 7 → inactivity nudge |
| Multi-Goal | demo_multi_goal@demo.com | demo123 | Multiple goals progress tracking |