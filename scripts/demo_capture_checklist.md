# Demo Capture Checklist (#48)

Ordered screenshots to capture for the demo video/gif. Pairs with
`_docs/DEMO-script.md` (the narration + what each beat shows) and
`scripts/build_demo_media.py` (the frames -> mp4/gif build).

## Frame naming convention

`NN-short-name.png` — two-digit zero-padded prefix controls playback
order (frames are sorted by filename). Use the exact names below so they
line up with the DEMO-script beats.

## Frames to capture

- [ ] `01-login.png` — `/login`, logged out
- [ ] `02-dashboard.png` — `/dashboard`, logged in as `demo@elevare.ai`
- [ ] `03-qa-math.png` — `/qa`, after asking a math question, answer
      visible with KaTeX-rendered equations and a Confidence badge
- [ ] `04-qa-history.png` — `/qa`, revisited/reloaded showing prior
      conversation history above the live answer
- [ ] `05-practice.png` — `/practice`, a subject selected and its
      AI-generated question list showing
- [ ] `06-practice-answer.png` — `/practice`, after answering a question,
      "Correct!" / feedback + explanation visible
- [ ] `07-goals.png` — `/goals`, goals list showing subjects/dates
- [ ] `08-progress.png` — `/progress`, Elo ratings + suggestions visible

## Before capturing

1. Run the pre-demo warm-up (two `curl .../health` calls — see
   `_docs/DEMO-script.md`) so pages don't load half-rendered while the
   API cold-starts.
2. Use a clean browser window sized consistently for every frame (e.g.
   1280x720 or 1920x1080) — the build script handles arbitrary/odd sizes,
   but consistent framing looks better in the final video.
3. Save all PNGs into one local, gitignored directory, e.g.
   `_docs/local/demo-frames/` — do not commit frames or rendered media.

## Capture options

**Option A — manual OS screenshot**
Use the OS screenshot tool (Win+Shift+S on Windows) against the live
frontend at https://elevareai-frontend.onrender.com, logged in as
`demo@elevare.ai`. Crop to the browser viewport for consistency.

**Option B — automated via chrome-devtools MCP**
When the browser automation tooling (chrome-devtools MCP `take_screenshot`)
has a free/unlocked browser profile available, drive the same 8 beats
programmatically: navigate to each route, wait for content to load
(especially the QA answer and Practice question generation, which call
the AI backend and can take up to ~20s), then screenshot. This wasn't
usable in this session because the local browser profile was locked by
another process — left for the owner to run when free.

## After capturing

Run the build:

```bash
pip install imageio-ffmpeg Pillow
python scripts/build_demo_media.py \
  --frames-dir _docs/local/demo-frames \
  --out-dir demo-media \
  --seconds-per-frame 2.5 \
  --fps 30 \
  --gif-width 800
```

Check `demo-media/demo.mp4` and `demo-media/demo.gif`. Both are
gitignored — decide separately (see `_docs/DEMO-script.md`) whether final
media ships as a repo commit or a release asset.
