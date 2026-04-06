"""Sentence-transformer cosine similarity between task summary and user answers."""

from __future__ import annotations

import logging
from typing import Any, List

import numpy as np

logger = logging.getLogger(__name__)

_model = None


def _get_model():
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer

            _model = SentenceTransformer("all-MiniLM-L6-v2")
            logger.info("SentenceTransformer loaded (all-MiniLM-L6-v2)")
        except Exception as e:
            logger.exception("Embedding model load failed: %s", e)
            return None
    return _model


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    denom = (np.linalg.norm(a) * np.linalg.norm(b)) or 1.0
    return float(np.dot(a, b) / denom)


def task_answer_similarity(task_summary: str, questions: List[Any], answers: List[str]) -> float:
    """
    Cosine similarity between the task summary embedding and the combined embedding
    of non-empty user answers (especially theory answers).
    Returns 0.0 if embeddings are unavailable.
    """
    model = _get_model()
    if model is None:
        return 0.0

    parts: List[str] = []
    for i, q in enumerate(questions):
        if i >= len(answers):
            break
        ans = (answers[i] or "").strip()
        if not ans:
            continue
        qobj = q if isinstance(q, dict) else {}
        qtype = str(qobj.get("type") or "theory").lower()
        if qtype == "theory":
            parts.append(ans)
        else:
            parts.append(ans)

    combined = " ".join(parts).strip()
    if not combined:
        return 0.0

    try:
        t_emb = model.encode(task_summary, normalize_embeddings=True)
        a_emb = model.encode(combined, normalize_embeddings=True)
        return max(0.0, min(1.0, _cosine(np.array(t_emb), np.array(a_emb))))
    except Exception as e:
        logger.warning("Similarity computation failed: %s", e)
        return 0.0
