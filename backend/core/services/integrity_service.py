"""
Integrity checking service — plagiarism detection.

Produces a flag_score (0–1) and flag_reasons list for each submission.
This is a parallel track: it never auto-zeros a score. High flag_score
submissions are routed to the human review queue.

AI-generation detection (GPT-2 perplexity) is deferred to a future version.
"""

from difflib import SequenceMatcher
from typing import Dict, List, Optional

from backend.core.services.submission_index import (
    normalize_code,
    submission_fingerprint,
    check_exact_match,
    get_prior_submissions,
    add_submission,
)


# ---------------------------------------------------------------------------
# Plagiarism analysis
# ---------------------------------------------------------------------------

def similarity_ratio(code_a: str, code_b: str) -> float:
    """
    Compute similarity between two code submissions (0.0–1.0).

    Uses normalized code so renamed variables, changed comments,
    and whitespace differences don't affect the score.
    """
    norm_a = normalize_code(code_a)
    norm_b = normalize_code(code_b)
    return SequenceMatcher(None, norm_a, norm_b).ratio()


def check_plagiarism(new_code: str, prior_submissions: List[str]) -> float:
    """
    Check a submission against all prior submissions for the same assignment.

    Args:
        new_code: The student's raw code.
        prior_submissions: List of normalized code from other students.

    Returns:
        Maximum similarity ratio (0.0–1.0).
        > 0.85 is suspicious, > 0.95 is very likely copied.
    """
    if not prior_submissions:
        return 0.0

    norm_new = normalize_code(new_code)
    max_sim = max(
        SequenceMatcher(None, norm_new, prior).ratio()
        for prior in prior_submissions
    )
    return max_sim


# ---------------------------------------------------------------------------
# AI-generation detection (Perplexity)
# ---------------------------------------------------------------------------

def compute_perplexity(text: str) -> float:
    """
    Compute text perplexity using a local GPT-2 model.

    Human writing typically has perplexity > 50.
    AI-generated text often falls below 20–30.
    """
    try:
        import torch
        from transformers import GPT2LMHeadModel, GPT2TokenizerFast

        tokenizer = GPT2TokenizerFast.from_pretrained("gpt2")
        model = GPT2LMHeadModel.from_pretrained("gpt2")

        inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
        with torch.no_grad():
            outputs = model(**inputs, labels=inputs["input_ids"])
            loss = outputs.loss
            
        return float(torch.exp(loss).item())
    except Exception as e:
        print(f"Perplexity calculation failed: {e}")
        return 100.0  # Fallback: assume human-like


# ---------------------------------------------------------------------------
# Combined integrity flag
# ---------------------------------------------------------------------------

def integrity_flag(
    code: str,
    assignment_id: str,
    student_id: str,
    text_content: str = "",
) -> Dict:
    """
    Run all integrity checks and produce a combined flag.

    Args:
        code: Student's raw code submission.
        assignment_id: Assignment identifier.
        student_id: Student identifier.
        text_content: Student's text explanation/content.

    Returns:
        {
            "flag_score": float (0–1),
            "reasons": [str, ...]
        }
    """
    reasons = []
    plagiarism_score = 0.0

    # ── Step 1: Plagiarism (Exact + Fuzzy) ──
    exact = check_exact_match(assignment_id, student_id, code)
    if exact:
        plagiarism_score = 1.0
        reasons.append(f"High-confidence plagiarism: Exact code match with {exact}.")
    else:
        prior = get_prior_submissions(assignment_id, student_id)
        if prior:
            plagiarism_score = check_plagiarism(code, prior)
            if plagiarism_score > 0.85:
                reasons.append(f"Suspicious similarity to peer submission ({plagiarism_score:.0%}).")

    # ── Step 2: AI Detection (Perplexity) ──
    ai_flag = 0.0
    if text_content or code:
        # Use simple heuristic: if code is very long and has low perplexity, it's suspect
        content_to_check = text_content if text_content else code
        perplexity = compute_perplexity(content_to_check)
        
        if perplexity < 25:
            ai_flag = 1.0
            reasons.append(f"High AI likelihood: low perplexity score ({perplexity:.1f}).")
        elif perplexity < 40:
            ai_flag = 0.7
            reasons.append(f"Moderate AI likelihood: perplexity score ({perplexity:.1f}).")

    # ── Step 3: Combine Scores ──
    # Plagiarism is the primary driver, AI is a supporting signal (weighted at 70%)
    flag_score = max(plagiarism_score, ai_flag * 0.7)

    # ── Step 4: Record for future ──
    add_submission(assignment_id, student_id, code)

    return {
        "flag_score": round(flag_score, 2),
        "reasons": reasons,
    }
