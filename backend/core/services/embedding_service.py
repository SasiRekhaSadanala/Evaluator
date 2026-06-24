"""
Embedding-based semantic similarity service.

Uses sentence-transformers (all-MiniLM-L6-v2) to compute cosine similarity
between student submissions and ideal answers/key concepts.

Replaces crude keyword-counting with a model that understands paraphrasing.
All models are lazy-loaded; if sentence-transformers is not installed the
service gracefully returns None so callers fall back to keyword scoring.
"""

import os
from pathlib import Path
from typing import List, Optional

import numpy as np

# Lazy-load sentence-transformers
_model = None
_AVAILABLE = None


def _ensure_model():
    """Lazy-load the embedding model on first use."""
    global _model, _AVAILABLE
    if _AVAILABLE is not None:
        return _AVAILABLE

    try:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer("all-MiniLM-L6-v2")
        _AVAILABLE = True
    except ImportError:
        print("WARNING: sentence-transformers not installed. Semantic scoring disabled.")
        _AVAILABLE = False
    except Exception as e:
        print(f"WARNING: Failed to load embedding model: {e}")
        _AVAILABLE = False

    return _AVAILABLE


def is_available() -> bool:
    """Check if the embedding service can be used."""
    return _ensure_model()


# ---------------------------------------------------------------------------
# Rubric embedding cache
# ---------------------------------------------------------------------------

_EMBEDDING_DIR = Path(os.getenv(
    "EMBEDDING_CACHE_DIR",
    os.path.join(os.path.dirname(__file__), "..", "..", "data", "embeddings")
))


def precompute_rubric_embedding(ideal_answer: str, rubric_id: str) -> Optional[np.ndarray]:
    """
    Embed the ideal answer and cache it to disk.

    Args:
        ideal_answer: The reference answer text.
        rubric_id: Unique identifier for caching.

    Returns:
        The embedding vector, or None if service unavailable.
    """
    if not _ensure_model():
        return None

    embedding = _model.encode(ideal_answer, normalize_embeddings=True)

    # Cache to disk
    _EMBEDDING_DIR.mkdir(parents=True, exist_ok=True)
    cache_path = _EMBEDDING_DIR / f"{rubric_id}.npy"
    np.save(str(cache_path), embedding)

    return embedding


def _load_cached_embedding(rubric_id: str) -> Optional[np.ndarray]:
    """Load a cached rubric embedding from disk."""
    cache_path = _EMBEDDING_DIR / f"{rubric_id}.npy"
    if cache_path.exists():
        return np.load(str(cache_path))
    return None


# ---------------------------------------------------------------------------
# Pairwise similarity
# ---------------------------------------------------------------------------

def compute_similarity(text_a: str, text_b: str) -> float:
    """
    Compute cosine similarity between two text strings.

    Args:
        text_a: First text.
        text_b: Second text.

    Returns:
        Cosine similarity from 0.0 to 1.0. Returns 0.0 if service unavailable.
    """
    if not _ensure_model():
        return 0.0

    emb_a = _model.encode(text_a, normalize_embeddings=True)
    emb_b = _model.encode(text_b, normalize_embeddings=True)

    similarity = float(np.dot(emb_a, emb_b))
    # Clamp to [0, 1] (cosine similarity with normalized vectors is [-1, 1])
    return max(0.0, min(1.0, similarity))


# ---------------------------------------------------------------------------
# Scoring functions
# ---------------------------------------------------------------------------

def semantic_coverage_score(
    student_text: str,
    rubric_id: str,
    ideal_answer: str = "",
) -> Optional[float]:
    """
    Compute semantic similarity between student text and ideal answer.

    Args:
        student_text: The student's submission text.
        rubric_id: Identifier for the cached ideal embedding.
        ideal_answer: Ideal answer text (used to compute embedding if not cached).

    Returns:
        Score from 0 to 100, or None if service unavailable.
    """
    if not _ensure_model():
        return None

    # Try cached embedding first
    ideal_emb = _load_cached_embedding(rubric_id)
    if ideal_emb is None:
        if not ideal_answer:
            return None
        ideal_emb = precompute_rubric_embedding(ideal_answer, rubric_id)
        if ideal_emb is None:
            return None

    student_emb = _model.encode(student_text, normalize_embeddings=True)

    # Cosine similarity (both already normalized → dot product)
    similarity = float(np.dot(ideal_emb, student_emb))

    # Map from [-1, 1] to [0, 100] with 0.5 similarity → ~75 score
    score = max(0, min(100, (similarity - 0.3) / 0.7 * 100))
    return round(score)


def concept_hit_rate(
    student_text: str,
    key_concepts: List[str],
    threshold: float = 0.55,
) -> Optional[float]:
    """
    Check if student text covers each key concept semantically.

    For each concept, finds the best-matching sentence in the student's
    text and considers it a "hit" if similarity exceeds the threshold.

    Args:
        student_text: Student submission text.
        key_concepts: List of concept strings to check.
        threshold: Minimum cosine similarity to count as a hit.

    Returns:
        Hit rate from 0.0 to 1.0, or None if service unavailable.
    """
    if not _ensure_model() or not key_concepts:
        return None

    # Split student text into sentences
    import re
    sentences = re.split(r'[.!?\n]+', student_text)
    sentences = [s.strip() for s in sentences if s.strip()]

    if not sentences:
        return 0.0

    sentence_embs = _model.encode(sentences, normalize_embeddings=True)
    concept_embs = _model.encode(key_concepts, normalize_embeddings=True)

    hits = 0
    for c_emb in concept_embs:
        sims = np.dot(sentence_embs, c_emb)
        if sims.max() > threshold:
            hits += 1

    return hits / len(key_concepts)
