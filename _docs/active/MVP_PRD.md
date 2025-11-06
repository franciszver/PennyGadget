## Step 1: Session Completion → Summaries
Event: Student finishes a tutoring session
- Generate narrative-style summary from transcript
- Attach "next steps" recommendations
- Store permanently in `summaries[]` linked to `User.id`
- Tutor view: read-only summaries with transcript excerpts

## Step 2: Practice Assignment → Adaptive Practice
Event: Student requests or is assigned practice
- Pull items from `practice.bank_items[]`
- Generate AI-authored items → flag with `flagged: true`
- Auto-adjust difficulty based on `progress.multi_goal_tracking`
- Log source (bank vs AI) for analytics

## Step 3: Query → Conversational Q&A
Event: Student submits free-form query
- Generate answer with confidence label {High, Medium, Low}
- Show disclaimer if not yet shown (`disclaimer_shown: true`)
- If confidence = Low → suggest escalation to tutor
- Log confidence distribution in `analytics.confidence_distribution`

## Step 4: Inactivity → Nudges
Event: Student has < 3 sessions by Day 7 OR misses scheduled activity
- Send personalized nudge via `nudges[]` (in_app + email)
- Enforce `preferences.nudge_frequency_cap`
- Cross-subject suggestions (Chemistry → Physics, SAT → Essays/AP)
- Log engagement (opened/clicked) in `analytics.nudge_engagement`

## Step 5: Tutor Override → Immediate Update
Event: Tutor reviews AI suggestion
- Tutor can override → log in `overrides[]`
- Student dashboard updates immediately
- Analytics: track override frequency by subject/difficulty

## Step 6: Login → Progress Dashboard
Event: Student logs in
- Show multi-goal progress from `progress.multi_goal_tracking`
- Visual charts + textual insights
- Display universal disclaimer (if first login)
