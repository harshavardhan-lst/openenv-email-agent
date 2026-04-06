"""Tasks, AI quiz retrieval, submission scoring, and history."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from pymongo.database import Database
from pymongo.errors import DuplicateKeyError

from backend.database.mongodb_connection import get_database
from backend.database import repository as repo
from backend.schemas import QuizResultResponse, QuizSubmit, TaskCreate, TaskSubmitResponse
from backend.services import ai_quiz_service, fraud_detection_service, similarity_service
from backend.utils.helper_functions import start_of_local_day_utc, user_account_age_days

logger = logging.getLogger(__name__)

router = APIRouter()

PASS_SCORE = 15
FRAUD_THRESHOLD = 0.6


def get_db() -> Database:
    return get_database()


@router.post("/tasks", response_model=TaskSubmitResponse)
def submit_task(task: TaskCreate, db: Database = Depends(get_db)):
    u = repo.get_user_by_id(db, task.user_id)
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    try:
        doc = repo.create_task(db, task.user_id, task.summary)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user id")
    logger.info("Task created %s for user %s", doc["_id"], task.user_id)
    return TaskSubmitResponse(message="Task submitted successfully", task_id=str(doc["_id"]))


@router.get("/quiz/{task_id}")
def get_quiz(task_id: str, db: Database = Depends(get_db)):
    task = repo.get_task_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    cached = task.get("quiz_questions")
    if cached and len(cached) == 3:
        return {"quiz_questions": cached}

    questions = ai_quiz_service.generate_quiz_questions(task.get("summary") or "")
    try:
        repo.set_task_quiz_questions(db, task_id, questions)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid task id")
    return {"quiz_questions": questions}


@router.post("/quiz/submit", response_model=QuizResultResponse)
def submit_quiz(data: QuizSubmit, db: Database = Depends(get_db)):
    task = repo.get_task_by_id(db, data.task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if repo.get_quiz_for_task(db, data.task_id):
        raise HTTPException(status_code=400, detail="Quiz already submitted for this task")

    summary = task.get("summary") or ""
    questions = task.get("quiz_questions") or data.questions
    if not questions or len(questions) != 3:
        questions = ai_quiz_service.generate_quiz_questions(summary)
        try:
            repo.set_task_quiz_questions(db, data.task_id, questions)
        except ValueError:
            pass

    answers = [str(a) if a is not None else "" for a in data.answers]
    if len(answers) != len(questions):
        raise HTTPException(status_code=400, detail="Answers must match number of questions")

    score, explanation = ai_quiz_service.evaluate_quiz_with_gemini(summary, questions, answers)
    task_similarity = similarity_service.task_answer_similarity(summary, questions, answers)

    user_id_str = str(task["user_id"])
    user = repo.get_user_by_id(db, user_id_str)
    if not user:
        raise HTTPException(status_code=404, detail="User not found for task")

    start_day = start_of_local_day_utc()
    tasks_today = repo.count_user_tasks_since(db, user_id_str, start_day)
    avg_score = repo.average_quiz_score_for_user(db, user_id_str)
    avg_user_score = min(30, max(0, int(round(avg_score)))) if avg_score > 0 else min(30, data.avg_user_score)
    account_age = user_account_age_days(user.get("created_at"))
    if account_age == 0:
        account_age = max(0, data.account_age_days)
    previous_rewards = int(user.get("total_rewards") or 0)

    feature_row = [
        float(score),
        float(data.time_taken),
        float(data.attempts),
        float(avg_user_score),
        float(tasks_today),
        float(account_age),
        float(previous_rewards),
        float(datetime.now(timezone.utc).hour),
    ]

    ml_fraud = fraud_detection_service.predict_fraud_probability(feature_row)
    fraud_probability = fraud_detection_service.blend_with_similarity(ml_fraud, task_similarity)

    passed = score >= PASS_SCORE
    reward_granted = passed and fraud_probability < FRAUD_THRESHOLD

    try:
        repo.insert_quiz(
            db,
            data.task_id,
            score,
            fraud_probability,
            reward_granted,
            explanation,
            task_similarity,
        )
    except DuplicateKeyError:
        raise HTTPException(status_code=400, detail="Quiz already submitted for this task") from None
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    if reward_granted:
        repo.update_task_status(db, data.task_id, "rewarded")
        repo.insert_reward_history(db, user_id_str, "Skill Badge Earned")
        repo.increment_user_rewards(db, user_id_str, 1)
    elif not passed:
        repo.update_task_status(db, data.task_id, "failed")
    else:
        repo.update_task_status(db, data.task_id, "suspicious")

    logger.info(
        "Quiz submitted task=%s score=%s fraud=%.3f similarity=%.3f reward=%s",
        data.task_id,
        score,
        fraud_probability,
        task_similarity,
        reward_granted,
    )

    return QuizResultResponse(
        score=score,
        fraud_probability=fraud_probability,
        passed=passed,
        reward_granted=reward_granted,
        explanation=explanation,
        task_similarity=task_similarity,
    )


@router.get("/history/{user_id}")
def get_history(user_id: str, db: Database = Depends(get_db)) -> List[Dict[str, Any]]:
    tasks = repo.list_tasks_for_user(db, user_id)
    history: List[Dict[str, Any]] = []
    for task in tasks:
        tid = str(task["_id"])
        quiz = repo.get_quiz_for_task(db, tid)
        if quiz:
            fp = float(quiz.get("fraud_probability") or 0)
            if fp < 0.3:
                risk = "Low"
            elif fp < 0.7:
                risk = "Medium"
            else:
                risk = "High"
            history.append(
                {
                    "task_summary": task.get("summary"),
                    "score": quiz.get("score"),
                    "fraud_risk": risk,
                    "reward_granted": quiz.get("reward_granted"),
                    "status": task.get("status"),
                    "task_similarity": quiz.get("task_similarity"),
                }
            )
        else:
            history.append(
                {
                    "task_summary": task.get("summary"),
                    "score": None,
                    "fraud_risk": None,
                    "reward_granted": False,
                    "status": task.get("status"),
                    "task_similarity": None,
                }
            )
    return history
