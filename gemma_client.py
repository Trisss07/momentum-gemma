"""Gemma client via Google AI Studio (supports AQ. and AIza keys)."""
import os
import json
import re
from typing import Optional
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise RuntimeError("GEMINI_API_KEY not set. Get one at https://aistudio.google.com/apikey")

client = genai.Client(api_key=API_KEY)

# Switch back to Gemma 4; minimal disables thinking for faster responses
DEFAULT_MODEL = "gemma-4-26b-a4b-it"


def _extract_json(text: str) -> dict:
    """Robustly pull a JSON object from model output that may contain prose."""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fence:
        try:
            return json.loads(fence.group(1))
        except json.JSONDecodeError:
            pass
    start = text.find("{")
    if start != -1:
        depth = 0
        for i in range(start, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    candidate = text[start:i + 1]
                    try:
                        return json.loads(candidate)
                    except json.JSONDecodeError:
                        break
    raise ValueError(f"Could not extract JSON from model output: {text[:300]}")


def parse_syllabus(syllabus_text: str, exam_date: str) -> list[dict]:
    """
    Use Gemma to decompose a syllabus into structured topics.
    Returns list of {name, estimated_hours, difficulty (1-5), weak_spot (bool)}.
    """
    system = (
        "You are a study planner assistant. Your ONLY job is to decompose a syllabus "
        "into a JSON array of topics. Each topic must have: name (string), "
        "estimated_hours (number between 0.5 and 4), difficulty (integer 1-5), "
        "weak_spot (boolean). Output ONLY valid JSON, no prose."
    )
    user = f"""Syllabus:
{syllabus_text}

Exam date: {exam_date}

Return a JSON array of topics. Split broad headings into 2-4 sub-topics if large.
"""
    try:
        response = client.models.generate_content(
            model=DEFAULT_MODEL,
            config=types.GenerateContentConfig(
                system_instruction=system,
                max_output_tokens=4096,
                thinking_config=types.ThinkingConfig(thinking_level="minimal"),
            ),
            contents=user,
        )
        raw = response.text
    except Exception as e:
        raise RuntimeError(f"Gemma API call failed: {e}") from e

    data = _extract_json(raw)
    if isinstance(data, dict) and "topics" in data:
        data = data["topics"]

    cleaned = []
    for item in data:
        if not isinstance(item, dict) or "name" not in item:
            continue
        cleaned.append({
            "name": str(item.get("name", "Untitled"))[:120],
            "estimated_hours": min(4.0, max(0.5, float(item.get("estimated_hours", 1.0)))),
            "difficulty": min(5, max(1, int(item.get("difficulty", 3)))),
            "weak_spot": bool(item.get("weak_spot", False)),
        })
    if not cleaned:
        raise ValueError("Gemma returned no valid topics. Try a shorter syllabus excerpt.")
    return cleaned


def generate_momentum_starter(topic_name: str, difficulty: int) -> str:
    """Generate a single low-friction 'first action' for a topic."""
    system = (
        "You write extremely short, concrete 'first actions' for students who are "
        "procrastinating. Each action must take 2–5 minutes and require zero setup. "
        "No motivation speeches. No long explanations. One sentence only."
    )
    user = f"Topic: {topic_name}\nDifficulty (1-5): {difficulty}\n\nGive me ONE first action."
    try:
        response = client.models.generate_content(
            model=DEFAULT_MODEL,
            config=types.GenerateContentConfig(
                system_instruction=system,
                max_output_tokens=512,
                thinking_config=types.ThinkingConfig(thinking_level="minimal"),
            ),
            contents=user,
        )
        text = response.text.strip().strip('"')
        if len(text) > 200:
            text = text.split(".")[0] + "."
        return text
    except Exception as e:
        print(f"[STARTER ERROR] {e}")
        return f"Open your notes to the '{topic_name}' section and read the first worked example aloud."