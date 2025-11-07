# Demo User Accounts Guide

**Guide for demonstrating AI Study Companion features to your boss**

---

## Demo Account Credentials

All accounts use password: `demo123`

| Account | Email | Demo Scenario |
|---------|-------|---------------|
| Goal Complete | demo_goal_complete@demo.com | Goal completion → related subject suggestions |
| SAT Complete | demo_sat_complete@demo.com | SAT → College Essays, Study Skills, AP Prep |
| Chemistry | demo_chemistry@demo.com | Chemistry → Physics, STEM suggestions |
| Low Sessions | demo_low_sessions@demo.com | <3 sessions by Day 7 → inactivity nudge |
| Multi-Goal | demo_multi_goal@demo.com | Multiple goals progress tracking |

---

## Demo Scenarios

### 1. Goal Completion → Related Subjects (Addresses 52% Churn)

**Account**: `demo_goal_complete@demo.com`  
**Password**: `demo123`

**What to Demo:**
- Student completed "Improve Algebra Skills" goal 2 days ago
- System suggests related subjects: Geometry, Pre-Calculus
- Shows how we prevent churn by suggesting next learning path

**Steps:**
1. Login with demo_goal_complete@demo.com
2. Navigate to Progress page
3. Show completed goal (100% complete)
4. Show related subject suggestions appearing below
5. Explain: "When students complete goals, we immediately suggest related subjects to keep them engaged"

**API Test:**
```bash
GET /api/v1/progress/{user_id}?include_suggestions=true
```
Should return suggestions with type "related_subject" for completed Algebra goal.

---

### 2. SAT Completion → College Essays, Study Skills, AP Prep

**Account**: `demo_sat_complete@demo.com`  
**Password**: `demo123`

**What to Demo:**
- Student completed SAT Math goal 1 day ago
- System suggests: College Essays, Study Skills, AP Prep
- Shows SAT-specific pathway suggestions

**Steps:**
1. Login with demo_sat_complete@demo.com
2. Navigate to Progress page
3. Show completed SAT Math goal
4. Show suggestions: "College Essays", "Study Skills", "AP Prep"
5. Explain: "SAT students get college prep suggestions, not just more test prep"

**API Test:**
```bash
GET /api/v1/progress/{user_id}?include_suggestions=true
```
Should return suggestions: ["College Essays", "Study Skills", "AP Prep"]

---

### 3. Chemistry → Physics, STEM Suggestions

**Account**: `demo_chemistry@demo.com`  
**Password**: `demo123`

**What to Demo:**
- Student completed Chemistry goal 3 days ago
- System suggests: Physics, Biology, AP Chemistry, STEM Prep
- Shows cross-subject learning pathways

**Steps:**
1. Login with demo_chemistry@demo.com
2. Navigate to Progress page
3. Show completed Chemistry goal
4. Show suggestions: "Physics", "Biology", "AP Chemistry", "STEM Prep"
5. Explain: "We connect related subjects to build comprehensive learning paths"

**API Test:**
```bash
GET /api/v1/progress/{user_id}?include_suggestions=true
```
Should return suggestions: ["Physics", "Biology", "AP Chemistry", "STEM Prep"]

---

### 4. Inactivity Nudge (<3 Sessions by Day 7)

**Account**: `demo_low_sessions@demo.com`  
**Password**: `demo123`

**What to Demo:**
- Student created 7 days ago
- Only 2 sessions completed (below threshold of 3)
- System triggers inactivity nudge suggesting to "book next session"
- Addresses early engagement drop-off

**Steps:**
1. Login with demo_low_sessions@demo.com
2. Navigate to Dashboard or check nudges
3. Show inactivity nudge appearing
4. Show message: "We noticed you've only completed 2 session(s) so far"
5. Show suggestion: "Schedule your next tutoring session"
6. Explain: "We proactively reach out to students at risk of churning"

**API Test:**
```bash
POST /api/v1/nudges/check
Body: {
  "student_id": "{user_id}",
  "check_type": "inactivity"
}
```
Should return `should_send: true` with nudge containing "Schedule your next tutoring session"

---

### 5. Multi-Goal Progress Tracking

**Account**: `demo_multi_goal@demo.com`  
**Password**: `demo123`

**What to Demo:**
- Student has 3 active goals across different subjects
- Each goal shows different completion percentage (75%, 50%, 20%)
- Progress dashboard shows all goals simultaneously
- Demonstrates multi-subject learning support

**Steps:**
1. Login with demo_multi_goal@demo.com
2. Navigate to Progress page
3. Show all 3 goals displayed:
   - "Master Algebra" (Math, 75% complete)
   - "Chemistry Fundamentals" (Science, 50% complete)
   - "SAT Prep" (Test Prep, 20% complete)
4. Show progress bars for each
5. Explain: "Students can track multiple goals simultaneously, not just single subject"

**API Test:**
```bash
GET /api/v1/progress/{user_id}
```
Should return array of 3 goals with different completion percentages.

---

## Quick Demo Script for Boss

### Opening (30 seconds)
"Let me show you how we address the key churn points you identified. I've set up 5 demo accounts that demonstrate each solution."

### Demo 1: Goal Completion (1 minute)
1. Login: demo_goal_complete@demo.com
2. "When a student completes a goal, we immediately suggest related subjects. This addresses the 52% churn rate after goal completion."
3. Show suggestions appearing

### Demo 2: SAT Pathway (1 minute)
1. Login: demo_sat_complete@demo.com
2. "For SAT students, we don't just suggest more test prep. We guide them to college essays, study skills, and AP prep - the natural next steps."
3. Show College Essays, Study Skills, AP Prep suggestions

### Demo 3: Chemistry → STEM (1 minute)
1. Login: demo_chemistry@demo.com
2. "We connect related subjects. Chemistry students see Physics, Biology, and STEM prep - building comprehensive learning paths."
3. Show Physics, Biology, AP Chemistry, STEM Prep suggestions

### Demo 4: Early Engagement (1 minute)
1. Login: demo_low_sessions@demo.com
2. "For students with less than 3 sessions by day 7, we proactively nudge them to book their next session."
3. Show inactivity nudge with "Schedule your next tutoring session" suggestion

### Demo 5: Multi-Goal Tracking (1 minute)
1. Login: demo_multi_goal@demo.com
2. "Students can track multiple goals simultaneously across different subjects. This isn't just single-subject tracking."
3. Show 3 goals with different completion percentages

### Closing (30 seconds)
"These features directly address the churn points: goal completion churn, SAT pathway guidance, cross-subject learning, early engagement, and multi-goal support."

---

## Troubleshooting

### Account Not Found
- Run: `python scripts/create_demo_users.py`
- Verify: `python scripts/verify_demo_users.py`

### Suggestions Not Appearing
- Check goal is marked as "completed" with recent `completed_at` date
- Check goal has `subject_id` linked properly
- Verify `include_suggestions=true` in API call

### Nudge Not Triggering
- Verify user was created exactly 7 days ago
- Verify session count is exactly 2 (not 3 or more)
- Check nudge endpoint: `POST /api/v1/nudges/check`

### Multi-Goal Not Showing
- Verify user has 3+ active goals
- Check all goals have different `completion_percentage`
- Verify goals are linked to different subjects

---

## API Endpoints for Testing

### Progress Endpoint
```bash
GET /api/v1/progress/{user_id}?include_suggestions=true
```

### Nudges Endpoint
```bash
POST /api/v1/nudges/check
Body: {
  "student_id": "{user_id}",
  "check_type": "inactivity"
}
```

### Health Check
```bash
GET /health
```

---

## Setup Instructions

1. **Create Demo Accounts:**
   ```bash
   python scripts/create_demo_users.py
   ```

2. **Verify Setup:**
   ```bash
   python scripts/verify_demo_users.py
   ```

3. **Start Backend:**
   ```bash
   python -m uvicorn src.api.main:app --reload
   ```

4. **Start Frontend:**
   ```bash
   cd examples/frontend-starter
   npm run dev
   ```

5. **Login and Demo:**
   - Use credentials from table above
   - Follow demo steps for each scenario

---

## Key Talking Points

- **52% Churn Prevention**: Goal completion suggestions keep students engaged
- **SAT Pathway**: Natural progression from test prep to college prep
- **Cross-Subject Learning**: Chemistry → Physics → STEM builds comprehensive skills
- **Early Engagement**: Proactive nudges for at-risk students
- **Multi-Goal Support**: Students aren't limited to single-subject tracking

---

**Ready to demo! All accounts are pre-configured and ready to go.**

