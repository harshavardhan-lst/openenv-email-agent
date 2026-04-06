"""Gemini-powered quiz generation and answer evaluation with structured fallbacks."""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Any, Dict, List, Tuple

logger = logging.getLogger(__name__)

_gemini_client = None


def get_gemini_client():
    global _gemini_client
    if _gemini_client is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return None
        try:
            from google import genai as genai_client

            _gemini_client = genai_client.Client(api_key=api_key)
            logger.info("Gemini client initialized")
        except Exception as e:
            logger.exception("Gemini init failed: %s", e)
            return None
    return _gemini_client


def _strip_code_fence(text: str) -> str:
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()


def _heuristic_quiz_from_summary(summary: str) -> List[Dict[str, Any]]:
    snippet = summary.strip()[:400]
    words = [w for w in re.findall(r"[A-Za-z0-9]{4,}", summary)[:8]]
    keyword = words[0] if words else "the task"
    return [
        {
            "id": 0,
            "type": "theory",
            "question": f"In your own words, what concrete steps did you take related to: {keyword}?",
            "expected_answer": snippet[:200] or summary[:200],
        },
        {
            "id": 1,
            "type": "mcq",
            "question": "Which best describes how specific your summary is?",
            "options": [
                "It names actions, context, and outcomes",
                "It is one vague sentence",
                "It copies a generic template",
                "It does not describe the task",
            ],
            "expected_answer": "It names actions, context, and outcomes",
        },
        {
            "id": 2,
            "type": "mcq",
            "question": "Does your summary reference what you actually did (not only how you felt)?",
            "options": [
                "Yes — it states what was done",
                "Mostly feelings only",
                "Only goals, no actions",
                "Unrelated text",
            ],
            "expected_answer": "Yes — it states what was done",
        },
    ]


def generate_quiz_questions(summary: str) -> List[Dict[str, Any]]:
    """Return three verification questions; uses Gemini when configured."""
    fallback = _heuristic_quiz_from_summary(summary)
    if not os.getenv("GEMINI_API_KEY"):
        logger.warning("GEMINI_API_KEY missing; using heuristic quiz")
        return fallback

    prompt = f"""
The user completed a habit/task with this summary: "{summary}"

Generate exactly 3 specific questions about this task to verify they actually did it.
Question 1 MUST be a "theory" question requiring a text answer.
Questions 2 and 3 MUST be "mcq" (Multiple Choice) with exactly 4 "options".

Return ONLY a JSON object in this exact format, with no markdown formatting or extra text:
{{
  "questions": [
    {{
      "id": 0,
      "type": "theory",
      "question": "What algorithm did you use?",
      "expected_answer": "Explanation of algorithm..."
    }},
    {{
      "id": 1,
      "type": "mcq",
      "question": "Which of these is the correct logic?",
      "options": ["A", "B", "C", "D"],
      "expected_answer": "B"
    }}
  ]
}}
"""
    try:
        client = get_gemini_client()
        if not client:
            return fallback
        response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        text = _strip_code_fence(response.text or "")
        result = json.loads(text)
        qs = result.get("questions") or []
        if len(qs) == 3:
            return qs
        logger.warning("Gemini returned %s questions; using heuristic quiz", len(qs))
        return fallback
    except Exception as e:
        logger.exception("Gemini quiz generation error: %s", e)
        return fallback


def _local_score_answers(
    task_summary: str, questions: List[Any], answers: List[str]
) -> Tuple[int, str]:
    per = 10
    total = 0
    details: List[str] = []
    for i, q in enumerate(questions):
        ans = (answers[i] if i < len(answers) else "").strip()
        qobj = q if isinstance(q, dict) else {"type": "theory", "question": str(q)}
        qtype = (qobj.get("type") or "theory").lower()
        exp = str(qobj.get("expected_answer") or "").strip()
        if qtype == "mcq":
            ok = exp.lower() == ans.lower() if exp else len(ans) > 0
            pts = per if ok else max(0, per - 7)
        else:
            if len(ans) < 12:
                pts = 0
            elif exp and exp.lower() in ans.lower():
                pts = per
            elif len(ans) > 40 and any(
                w in ans.lower() for w in task_summary.lower().split() if len(w) > 4
            ):
                pts = 7
            else:
                pts = 4
        total += pts
        details.append(f"Q{i+1}: {pts}/{per}")
    explanation = "Rule-based scoring (Gemini unavailable): " + "; ".join(details)
    return min(30, total), explanation


def evaluate_quiz_with_gemini(
    task_summary: str, questions: List[Any], answers: List[str]
) -> Tuple[int, str]:
    """Score 0–30 plus short explanation; falls back to local rules if Gemini fails."""
    payload_q = json.dumps(questions, default=str)
    payload_a = json.dumps(answers, default=str)
    prompt = f"""
The user completed this task summary: "{task_summary}"

They were asked the following verification questions:
{payload_q}

They provided the following answers respectively:
{payload_a}

Act as a strict teacher. Evaluate the answers for correctness.
If the answers do not make sense in response to the question, score them 0.
Provide a score between 0 and 30 (30 is perfect, 10 points per question).
Provide a short, educational explanation describing what they got right or wrong.

Return ONLY a JSON object exactly like this:
{{
  "score": 25,
  "explanation": "Great job, but your first answer was too short..."
}}
"""
    if not os.getenv("GEMINI_API_KEY"):
        return _local_score_answers(task_summary, questions, answers)

    try:
        client = get_gemini_client()
        if not client:
            return _local_score_answers(task_summary, questions, answers)
        response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        text = _strip_code_fence(response.text or "")
        result = json.loads(text)
        score = int(result.get("score", 0))
        score = max(0, min(30, score))
        explanation = str(result.get("explanation") or "Verification complete.")
        return score, explanation
    except Exception as e:
        logger.exception("Gemini evaluation error: %s", e)
        return _local_score_answers(task_summary, questions, answers)
