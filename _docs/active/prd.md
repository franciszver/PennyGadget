# 📘 Product Requirements Document (PRD)
**Product Name:** AI Study Companion  
**Owner:** TBD  
**Version:** MVP + Full Product Roadmap  

---

## 1. Overview
The AI Study Companion is a persistent agent that supports students between tutoring sessions. It summarizes sessions, assigns adaptive practice, answers questions conversationally with transparent confidence labeling, nudges inactive students, recommends related subjects, and escalates to tutors when needed.

This PRD is divided into:
- **MVP Scope** → Core features to validate retention and continuity.
- **Full Product Vision** → Features layered on after MVP validation.

---

## 2. User Object Specification

```json
User {
  id: UUID,
  role: "student" | "tutor" | "parent" | "admin",

  profile: {
    goals: [Goal],
    subjects: [Subject],
    preferences: {
      learning_style: "visual" | "textual" | "mixed",
      nudge_frequency_cap: 1
    },
    progress: {
      multi_goal_tracking: [
        { subject: "string", completion: "%", streak: int, xp: int }
      ]
    }
  },

  transcripts: [Transcript],
  summaries: [Summary],   // narrative recap + next steps, permanent
  practice: {
    bank_items: [PracticeItem],
    ai_generated_items: [PracticeItem { flagged: true }]
  },

  interactions: {
    qna: {
      query: string,
      answer: string,
      confidence: "High" | "Medium" | "Low",
      disclaimer_shown: bool
    },
    nudges: [
      {
        type: "login" | "inactivity" | "cross_subject",
        channel: "in_app" | "email",
        personalized: bool,
        sent_at: timestamp
      }
    ],
    overrides: [
      {
        tutor_id: UUID,
        action: string,
        timestamp: timestamp
      }
    ],
    messaging: [MessageThread]
  },

  gamification: {
    xp: int,
    level: int,
    badges: [Badge],
    streaks: int,
    meta_rewards: [Reward]
  },

  analytics: {
    override_count: int,
    confidence_distribution: { High: "%", Medium: "%", Low: "%" },
    nudge_engagement: { opened: "%", clicked: "%" }
  }
}
3. MVP Scope
3.1 Core Features
Session Summaries

Narrative‑style recaps of tutoring sessions.

Include actionable “next steps.”

Permanently stored in summaries[].

Adaptive Practice

Pull from curated bank + AI‑generated questions.

AI‑generated items flagged for tutor review.

Auto‑adjust difficulty based on performance.

Conversational Q&A

Natural language answers to student queries.

Universal disclaimer on first login.

Confidence meter (High/Medium/Low) shown per answer.

Suggest tutor escalation when confidence is low.

Personalized Nudges

In‑app + email nudges with frequency cap.

Cross‑subject recommendations (Chemistry → Physics, SAT → Essays/AP).

Inactivity prompts for missed sessions.

Tutor Overrides & Messaging

AI flags students for tutor attention.

Tutors can override AI suggestions; overrides logged and immediately update dashboards.

Tutors can open messaging threads from flagged items.

Multi‑Goal Progress Tracking (Basic)

Dashboard showing progress across multiple subjects.

Visual + textual summaries of progress.

3.2 MVP Non‑Functional Requirements
Deployment: AWS first (API Gateway + Lambda/ECS + DynamoDB/Postgres).

LLM Integration: OpenAI with structured prompt adapters.

RBAC: Students, tutors, parents, admins with least‑privilege access.

Edge Cases: Graceful fallback when transcripts are missing or queries are ambiguous.

Analytics (Basic): Log tutor overrides, confidence tiers, and nudge engagement.

3.3 MVP Deliverables
AWS‑deployed prototype with summaries, practice, Q&A, nudges, progress, and tutor overrides.

Contributor‑friendly documentation (stepwise onboarding).

Scripted demo video showing individual features.

Source code with tests and environment configs.

4. Full Product Vision (Post‑MVP)
4.1 Expanded Features
Deep Gamification

XP, levels, streaks, badges.

Meta‑rewards (collaboration, tutor engagement).

Simplified gamification view for parents/tutors.

Parent & Admin Dashboards

Parent view: progress + simplified gamification.

Admin view: analytics dashboards, exportable reports (CSV/JSON).

Advanced Analytics

Override frequency by subject/difficulty.

Confidence telemetry vs. tutor corrections.

Retention/engagement dashboards.

Integrations

Rails/React adapters for seamless platform integration.

LMS integration, calendar sync, push notifications.

A/B testing for nudges and gamification.

5. Success Metrics
MVP Success

Reduction in churn vs. baseline.

Tutor adoption of overrides.

Student engagement with summaries, practice, and nudges.

Full Product Success

Sustained retention uplift.

Increased cross‑subject exploration.

ROI within 90 days via improved session utilization and renewals.

6. Risks & Mitigations
Transcript variability: Fallback summaries when transcripts are incomplete.

AI quality drift: Tutor overrides logged and fed into evaluation loop.

Notification fatigue: Frequency caps and opt‑outs.

Integration churn: Stable API contracts for Rails/React adapters.

7. Edge‑Case Prompt Pack (with Expected Outputs)
Session Completion → Summaries
Missing transcript → "Transcript unavailable. Limited recap generated."

Mixed subjects → "We reviewed factoring polynomials, then balancing chemical equations."

Short session → "Session was brief. Review last practice before next session."

Practice Assignment → Adaptive Practice
No bank item → AI generates flagged practice item.

Conflicting difficulty → Assign Algebra advanced, Geometry beginner.

Overlapping goals → Items tagged with both SAT + AP.

Query → Conversational Q&A
Ambiguous → Ask for clarification, suggest likely topic.

Multi‑part → Split answer into sections.

Out‑of‑scope → Redirect politely.

Low confidence → High‑level overview + tutor escalation.

Inactivity → Nudges
<3 sessions by Day 7 → Personalized nudge.

Ignored nudges → Cap enforced, engagement logged.

Goal completion → Suggest related subjects.

Tutor Override → Immediate Update
Override summary → Dashboard updated, override logged.

Replace AI practice → Bank item substituted, flagged.

Multiple overrides → All logged with timestamps.

Login → Progress Dashboard
Multiple goals → Show % complete per subject.

No goals → Prompt to add goals.

Completed goal → Suggest related subjects.

8. How to Use
Run prompts against MVP endpoints (/summaries, /practice, /qa, /nudges, /overrides, /progress).

Compare outputs to golden responses to validate disclaimers, confidence labels, escalation paths, and override behavior.

Log analytics for overrides, confidence tiers, and nudge engagement.

Iterate until outputs match golden responses; rerun edge cases after each major change to ensure regression safety.