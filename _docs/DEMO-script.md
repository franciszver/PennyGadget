# Demo Walkthrough Script (#48)

A narratable, screenshot-by-screenshot demo of the live app. Matches the
actual routes in `examples/frontend-starter/src/App.jsx` and the actual
page components — no invented features.

- **Frontend**: https://elevareai-frontend.onrender.com
- **API**: https://elevareai-api.onrender.com
- **Demo account**: `demo@elevare.ai` — password is the `DEMO_PASSWORD`
  value (never write the literal password anywhere; see README "Set Manual
  Secrets" / Render dashboard).

## Pre-demo warm-up (do this first, every time)

Render free-tier web services spin down after ~15 min idle; the first
request after idle takes ~50s. Wake the API before the audience is watching:

```bash
curl https://elevareai-api.onrender.com/health
# wait for {"status":"healthy","database":"connected"} - may take ~50s
curl https://elevareai-api.onrender.com/health
# second call should return near-instantly once warm
```

Then load the frontend once yourself (not screenshotted) so its own cold
start (static site, usually fast) is also out of the way before recording.

## Demo beats

Each beat = one screenshot. Capture in order; filenames are consumed
in sorted order by `scripts/build_demo_media.py`, so the numeric prefix
controls playback order.

| # | Filename | Route | Action | What to show | Narration line |
|---|----------|-------|--------|---------------|-----------------|
| 1 | `01-login.png` | `/login` | Land on the login page | ElevareAI logo, tagline "Lift your learning, gently.", email/password form | "This is ElevareAI - an AI study companion that lives between tutoring sessions." |
| 2 | `02-dashboard.png` | `/dashboard` | Log in as `demo@elevare.ai` | The goals pie chart, nudges (if any) | "After logging in, the student lands on their dashboard - goals and progress at a glance." |
| 3 | `03-qa-math.png` | `/qa` | Ask a math question, e.g. "How do I solve x squared plus 5x plus 6 equals 0?" | The rendered answer with KaTeX-formatted math (equations, not raw LaTeX text) and the Confidence badge | "Students can ask questions any time - answers render real math notation, not plain text, and each answer carries a confidence rating." |
| 4 | `04-qa-history.png` | `/qa` (reload or revisit) | Show the conversation history loading in | Prior Q&A pairs above the live one, "Showing conversation history" banner | "The AI remembers previous questions - this is persistent memory, not a one-off chatbot." |
| 5 | `05-practice.png` | `/practice` | Pick a subject (from the student's goals) and generate a practice set | The AI-generated question list for that subject | "Practice questions are generated per-subject from the student's active goals." |
| 6 | `06-practice-answer.png` | `/practice` | Answer a practice question | The "Correct!" / feedback state with explanation | "Immediate feedback with an explanation - not just right/wrong." |
| 7 | `07-goals.png` | `/goals` | View goals list | Active/completed goals, subjects, target dates | "Goals drive everything - practice subjects and suggestions all come from here." |
| 8 | `08-progress.png` | `/progress` | View progress page | Elo ratings per goal, completion dates, related-subject suggestions | "Progress tracks skill level (Elo) per subject and suggests what to learn next - this is what keeps students engaged after they finish a goal." |

Eight beats is the target; drop 4 (history) or 6 (practice-answer) if
time is short, but keep 1, 2, 3, 5, 7, 8 as the minimum spine (login,
dashboard, QA math, practice, goals, progress).

## Capture checklist

See `scripts/demo_capture_checklist.md` for the full step-by-step capture
process (manual screenshot vs. chrome-devtools MCP automation) and the
frame naming convention.

## Building the video/gif from frames

1. Save the 8 (or however many) PNGs above into a local, **gitignored**
   frames directory, e.g. `_docs/local/demo-frames/`, using exactly the
   filenames from the table so sort order matches the beat order.
2. Install the two build dependencies (not in `requirements.txt` -
   they're only needed for this one-off media build):
   ```bash
   pip install imageio-ffmpeg Pillow
   ```
3. Run the build script:
   ```bash
   python scripts/build_demo_media.py \
     --frames-dir _docs/local/demo-frames \
     --out-dir demo-media \
     --seconds-per-frame 2.5 \
     --fps 30 \
     --gif-width 800
   ```
4. Output lands in `demo-media/demo.mp4` and `demo-media/demo.gif`. Both
   `demo-media/` and `_docs/local/` are gitignored - **do not commit the
   frames or the rendered media.**

## What's owner-dependent (not done here)

- **Real screenshots**: not captured in this change - the browser profile
  used by this session is locked, so only synthetic (solid-color)
  placeholder frames were used to prove the build pipeline works. The
  owner needs to capture the real 8 frames per the checklist.
- **Whether to commit final media**: this script and this doc keep
  `demo.mp4`/`demo.gif` out of git entirely (gitignored `demo-media/`
  output dir). If the finished demo video should ship in the repo or as a
  GitHub Release asset, that's an owner decision to make later - attach
  it to a release rather than committing a binary to `main`.
