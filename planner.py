"""Deterministic scheduling logic. No LLM here — dates and hours must add up."""
from datetime import date, timedelta
from typing import Optional


def build_schedule(
    topics: list[dict],
    exam_date: date,
    start_date: Optional[date] = None,
    max_hours_per_day: float = 3.0,
    break_minutes: int = 10,
) -> list[dict]:
    """
    Turn a list of topics into a day-by-day plan.
    Each day gets a list of sessions. Sessions are 25–50 minute blocks.
    Weak spots and higher difficulty get earlier placement.
    Returns list of {date, sessions: [{topic, minutes, type}]}.
    """
    if start_date is None:
        start_date = date.today()

    days_available = (exam_date - start_date).days
    if days_available <= 0:
        raise ValueError("Exam date must be in the future.")

    # Sort: weak spots first, then difficulty descending, then longer topics
    ordered = sorted(
        topics,
        key=lambda t: (not t["weak_spot"], -t["difficulty"], -t["estimated_hours"]),
    )

    # Flatten into small sessions (25-min pomodoro-style, max 50 min for hard topics)
    sessions = []
    for topic in ordered:
        remaining = topic["estimated_hours"] * 60  # minutes
        block = 50 if topic["difficulty"] >= 4 else 25
        while remaining > 5:
            chunk = min(block, remaining)
            sessions.append({
                "topic": topic["name"],
                "minutes": int(chunk),
                "difficulty": topic["difficulty"],
                "weak_spot": topic["weak_spot"],
            })
            remaining -= chunk
            if remaining > 10:
                sessions.append({"topic": "Break", "minutes": break_minutes, "type": "break"})

    # Distribute sessions across days, respecting max_hours_per_day
    schedule = []
    day_index = 0
    day_session_minutes = 0
    current_day_sessions = []

    for sess in sessions:
        if sess.get("type") == "break":
            current_day_sessions.append(sess)
            continue

        if day_session_minutes + sess["minutes"] > max_hours_per_day * 60:
            # Close current day
            if current_day_sessions:
                schedule.append({
                    "date": start_date + timedelta(days=day_index),
                    "sessions": current_day_sessions,
                })
            day_index += 1
            current_day_sessions = []
            day_session_minutes = 0

        current_day_sessions.append(sess)
        day_session_minutes += sess["minutes"]

    # Final day
    if current_day_sessions:
        schedule.append({
            "date": start_date + timedelta(days=day_index),
            "sessions": current_day_sessions,
        })

    # If we ran out of days, compress: allow overflow on last day
    if day_index >= days_available and schedule:
        # Merge overflow into last available day
        while len(schedule) > days_available:
            overflow = schedule.pop()
            schedule[-1]["sessions"].extend(overflow["sessions"])

    return schedule


def total_study_minutes(schedule: list[dict]) -> int:
    return sum(
        s["minutes"] for day in schedule for s in day["sessions"]
        if s.get("type") != "break"
    )