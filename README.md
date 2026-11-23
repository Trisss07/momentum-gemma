# Momentum — Anti-Procrastination Study Companion

Built for the GDG Build with Gemma Hackathon (University of Aberdeen, July 2026).

Momentum turns a syllabus into a realistic, day-by-day study plan and gives you a 2-minute "momentum starter" for any topic you're avoiding.

## Stack
- **Gemma 4** (via Google AI Studio free tier) for syllabus decomposition and micro-action generation
- **Plain Python** for all scheduling maths (no hallucinated dates)
- **Streamlit** for the interface

## Run locally
1. `pip install -r requirements.txt`
2. Copy `.env.example` to `.env` and add your `GEMINI_API_KEY`
3. `streamlit run app.py`

## Design decisions
- Weak spots and high-difficulty topics are front-loaded in the schedule.
- Sessions are 25–50 min pomodoro-style blocks with breaks.
- If the plan exceeds available days, sessions are compressed rather than dropped.
- Gemma output is clamped to sane ranges (hours 0.5–4, difficulty 1–5).
- The model is swappable via one constant in `gemma_client.py`.

## What we learned
- Small models sometimes return malformed JSON; a robust extractor is essential.
- Separating deterministic logic from generative logic made the demo reliable under time pressure.
- Prompt engineering for structured extraction (temperature 0.2, explicit schema) improved consistency noticeably over a naive "list the topics" prompt.