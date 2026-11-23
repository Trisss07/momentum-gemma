"""Momentum — Anti-procrastination study companion powered by Gemma."""
import streamlit as st
from datetime import date, timedelta
import pandas as pd

from gemma_client import parse_syllabus, generate_momentum_starter
from planner import build_schedule, total_study_minutes

st.set_page_config(page_title="Momentum · Study Companion", page_icon="🚀", layout="wide")

# --- Header ---
st.title("🚀 Momentum")
st.caption("Turn a messy syllabus into a realistic plan — and start before you feel ready.")

with st.sidebar:
    st.header("Your inputs")
    syllabus_text = st.text_area(
        "Paste your syllabus / topic list",
        height=220,
        placeholder="e.g. Week 1: Kinematics, Week 2: Newton's Laws, Week 3: Energy...",
    )
    exam_date = st.date_input("Exam date", value=date.today() + timedelta(days=14))
    start_date = st.date_input("Start studying from", value=date.today())
    max_hours = st.slider("Max study hours per day", 1.0, 6.0, 3.0, 0.5)
    weak_areas = st.text_area(
        "Topics you're avoiding (optional)",
        placeholder="e.g. rotational dynamics, thermodynamics",
        height=80,
    )
    generate_btn = st.button("Build my plan", type="primary", use_container_width=True)

# --- Session state ---
if "topics" not in st.session_state:
    st.session_state.topics = None
if "schedule" not in st.session_state:
    st.session_state.schedule = None
if "starters" not in st.session_state:
    st.session_state.starters = {}

# --- Generate ---
if generate_btn:
    if not syllabus_text.strip():
        st.error("Paste a syllabus first.")
    elif exam_date <= start_date:
        st.error("Exam date must be after your start date.")
    else:
        with st.spinner("Gemma is decomposing your syllabus…"):
            try:
                topics = parse_syllabus(syllabus_text, str(exam_date))
                # Mark weak spots from user input
                if weak_areas.strip():
                    weak_lower = weak_areas.lower()
                    for t in topics:
                        if any(word.strip() in t["name"].lower() for word in weak_lower.split(",")):
                            t["weak_spot"] = True
                st.session_state.topics = topics
                schedule = build_schedule(
                    topics,
                    exam_date=exam_date,
                    start_date=start_date,
                    max_hours_per_day=max_hours,
                )
                st.session_state.schedule = schedule
                st.session_state.starters = {}
                st.success(f"Plan built: {len(topics)} topics, {len(schedule)} days.")
            except Exception as e:
                st.error(f"Could not build plan: {e}")

# --- Display ---
if st.session_state.schedule:
    schedule = st.session_state.schedule
    topics = st.session_state.topics
    total_min = total_study_minutes(schedule)
    total_hours = round(total_min / 60, 1)

    col1, col2, col3 = st.columns(3)
    col1.metric("Topics", len(topics))
    col2.metric("Total study time", f"{total_hours} h")
    col3.metric("Days planned", len(schedule))

    st.subheader("📅 Your day-by-day plan")

    # Global counter guarantees unique keys across all days/sessions
    session_counter = 0

    for day in schedule:
        day_label = day["date"].strftime("%a %d %b")
        day_minutes = sum(s["minutes"] for s in day["sessions"] if s.get("type") != "break")
        with st.expander(f"{day_label} — {day_minutes} min focused study", expanded=(day == schedule[0])):
            for sess in day["sessions"]:
                if sess.get("type") == "break":
                    st.caption(f"   ☕ Break — {sess['minutes']} min")
                else:
                    label = f"**{sess['topic']}** — {sess['minutes']} min"
                    if sess["weak_spot"]:
                        label += " ⚠️ *weak spot*"
                    st.markdown(label)

                    # Unique key per rendered session
                    key = f"{sess['topic']}_{session_counter}"
                    session_counter += 1

                    if key not in st.session_state.starters:
                        if st.button("Give me a 2-min starter for this", key=f"btn_{key}"):
                            with st.spinner("…"):
                                starter = generate_momentum_starter(sess["topic"], sess["difficulty"])
                            st.session_state.starters[key] = starter
                    if key in st.session_state.starters:
                        st.info(f"👉 {st.session_state.starters[key]}")

    st.divider()
    st.caption(
        "Momentum uses Gemma to parse topics and generate micro-actions. "
        "Scheduling maths is plain Python so your hours always add up."
    )
else:
    st.info("Paste your syllabus and hit **Build my plan** to get started.")