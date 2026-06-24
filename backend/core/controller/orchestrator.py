"""
Orchestrator v2.0 — coordinates evaluation, integrity, and tracking.

Wires together:
- Code/Content evaluation agents
- Aggregator agent
- Integrity check (plagiarism detection)
- Student profile tracking (score history + percentile)
- Review queue (flags uncertain/suspicious submissions)
"""

import hashlib
from typing import Any, Dict, List, Optional

from ..agents.aggregator_agent import AggregatorAgent
from ..agents.code_agent import CodeEvaluationAgent
from ..agents.content_agent import ContentEvaluationAgent
from ..utils.file_parser import (
    get_student_name_from_filename,
    read_folder,
    read_submissions_by_type,
)
from ..utils.rubric import Rubric
from ..utils.vtt_parser import (
    parse_vtt,
    extract_concepts,
    extract_concept_dict,
    llm_extract_concepts,
    score_summary_against_concepts,
    strip_html,
)


class Orchestrator:
    """Orchestrates evaluation workflow across student submissions."""

    ASSIGNMENT_TYPES = {"code", "content", "mixed", "transcript"}

    def __init__(self, rubric: Optional[Rubric] = None):
        self.rubric = rubric or Rubric()
        self.code_agent = CodeEvaluationAgent()
        self.content_agent = ContentEvaluationAgent()
        self.aggregator_agent = AggregatorAgent()

    def evaluate_submissions(
        self,
        assignment_type: str,
        folder_path: str,
        problem_statement: Optional[str] = None,
        ideal_reference: Optional[str] = None,
        assignment_id: Optional[str] = None,
        topic_tag: Optional[str] = None,
        transcript_text: Optional[str] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """
        Evaluate all submissions in a folder.

        Args:
            assignment_type: 'code', 'content', 'mixed', or 'transcript'
            folder_path: Path to folder containing student submissions
            problem_statement: For code assignments
            ideal_reference: For content assignments
            assignment_id: Unique assignment ID (for integrity + tracking)
            topic_tag: Topic tag for student progress tracking
            transcript_text: Raw VTT transcript (for transcript assignments)

        Returns:
            Dictionary mapping student names to final evaluation results
        """
        if assignment_type not in self.ASSIGNMENT_TYPES:
            raise ValueError(
                f"Invalid assignment type. Must be one of: {self.ASSIGNMENT_TYPES}"
            )

        # Generate assignment_id if not provided
        if not assignment_id:
            seed = f"{assignment_type}:{problem_statement or ''}:{ideal_reference or ''}"
            assignment_id = hashlib.md5(seed.encode()).hexdigest()[:16]

        # Read submissions
        if assignment_type == "mixed":
            submissions = read_submissions_by_type(folder_path)
        else:
            submissions = read_folder(folder_path)

        # Get test cases from rubric
        test_cases = self.rubric.get_test_cases() if hasattr(self.rubric, 'get_test_cases') else []

        # Evaluate each submission
        results = {}

        if assignment_type == "code":
            results = self._evaluate_code_submissions(
                submissions, problem_statement, assignment_id, test_cases
            )
        elif assignment_type == "content":
            results = self._evaluate_content_submissions(
                submissions, ideal_reference, problem_statement, assignment_id
            )
        elif assignment_type == "mixed":
            results = self._evaluate_mixed_submissions(
                submissions, problem_statement, ideal_reference, assignment_id, test_cases
            )
        elif assignment_type == "transcript":
            results = self._evaluate_transcript_submissions(
                submissions, transcript_text or "", assignment_id
            )

        # ── Post-evaluation: student tracking + percentiles ──
        self._run_student_tracking(results, assignment_id, topic_tag or "")

        return results

    # ======================================================================
    # CODE SUBMISSIONS
    # ======================================================================

    def _evaluate_code_submissions(
        self,
        submissions: Dict[str, str],
        problem_statement: Optional[str] = None,
        assignment_id: str = "",
        test_cases: List[dict] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """Evaluate code-only submissions with integrity checks."""
        results = {}
        test_cases = test_cases or []
        total = len(submissions)

        for idx, (filename, code) in enumerate(submissions.items(), 1):
            student_name = get_student_name_from_filename(filename)
            print(f"[{idx}/{total}] Evaluating {student_name}...")

            # Prepare input for code agent
            code_criteria = self.rubric.get_criteria("code")
            code_weights = {k: v.get("weight", 0.25) for k, v in code_criteria.items()}
            agent_input = {
                "problem_statement": problem_statement or "",
                "rubric": {"weights": code_weights},
                "student_code": code,
                "filename": filename,
                "test_cases": test_cases,
            }

            # Evaluate with code agent
            code_output = self.code_agent.evaluate(agent_input)

            # Aggregate
            aggregator_input = {
                "agent_outputs": [code_output],
                "rubric": {"weights": [1.0]},
            }
            final_result = self.aggregator_agent.evaluate(aggregator_input)

            result_entry = {
                "file": filename,
                "assignment_type": "code",
                **final_result,
            }

            # ── Integrity check ──
            integrity = self._run_integrity_check(
                code, assignment_id, student_name, text_content=""
            )
            if integrity:
                result_entry["flag_score"] = integrity["flag_score"]
                result_entry["flag_reasons"] = integrity["reasons"]

            # ── Review queue ──
            self._maybe_queue(student_name, assignment_id, result_entry)

            results[student_name] = result_entry

        return results

    # ======================================================================
    # CONTENT SUBMISSIONS
    # ======================================================================

    def _evaluate_content_submissions(
        self,
        submissions: Dict[str, str],
        ideal_reference: Optional[str] = None,
        problem_statement: Optional[str] = None,
        assignment_id: str = "",
    ) -> Dict[str, Dict[str, Any]]:
        """Evaluate content-only submissions."""

        # Precompute ideal reference embedding (once, not per student)
        self._precompute_embedding(ideal_reference, assignment_id)

        results = {}
        total = len(submissions)

        for idx, (filename, content) in enumerate(submissions.items(), 1):
            student_name = get_student_name_from_filename(filename)
            print(f"[{idx}/{total}] Evaluating {student_name}...")

            content_criteria = self.rubric.get_criteria("content")
            content_weights = {k: v.get("weight", 0.25) for k, v in content_criteria.items()}
            agent_input = {
                "student_content": content,
                "rubric": {"weights": content_weights},
                "ideal_reference": ideal_reference or "",
                "problem_statement": problem_statement or "",
                "rubric_id": assignment_id,
            }

            content_output = self.content_agent.evaluate(agent_input)

            aggregator_input = {
                "agent_outputs": [content_output],
                "rubric": {"weights": [1.0]},
            }
            final_result = self.aggregator_agent.evaluate(aggregator_input)

            result_entry = {
                "file": filename,
                "assignment_type": "content",
                **final_result,
            }

            # ── Integrity check ──
            integrity = self._run_integrity_check(
                "", assignment_id, student_name, text_content=content
            )
            if integrity:
                result_entry["flag_score"] = integrity["flag_score"]
                result_entry["flag_reasons"] = integrity["reasons"]

            # ── Review queue ──
            self._maybe_queue(student_name, assignment_id, result_entry)

            results[student_name] = result_entry

        return results

    # ======================================================================
    # MIXED SUBMISSIONS
    # ======================================================================

    def _evaluate_mixed_submissions(
        self,
        submissions: Dict[str, Dict[str, str]],
        problem_statement: Optional[str] = None,
        ideal_reference: Optional[str] = None,
        assignment_id: str = "",
        test_cases: List[dict] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """Evaluate mixed submissions (both code and content)."""
        test_cases = test_cases or []

        # Precompute embedding
        self._precompute_embedding(ideal_reference, assignment_id)

        results = {}
        code_submissions = submissions.get("code", {})
        content_submissions = submissions.get("text", {})

        all_students = set(
            get_student_name_from_filename(f)
            for f in list(code_submissions.keys()) + list(content_submissions.keys())
        )

        for student_name in all_students:
            agent_outputs = []

            # Evaluate code if available
            student_code = None
            for filename, code in code_submissions.items():
                if get_student_name_from_filename(filename) == student_name:
                    student_code = code
                    code_criteria = self.rubric.get_criteria("code")
                    code_weights = {k: v.get("weight", 0.25) for k, v in code_criteria.items()}
                    agent_input = {
                        "problem_statement": problem_statement or "",
                        "rubric": {"weights": code_weights},
                        "student_code": code,
                        "filename": filename,
                        "test_cases": test_cases,
                    }
                    code_output = self.code_agent.evaluate(agent_input)
                    agent_outputs.append(code_output)
                    break

            # Evaluate content if available
            for filename, content in content_submissions.items():
                if get_student_name_from_filename(filename) == student_name:
                    content_criteria = self.rubric.get_criteria("content")
                    content_weights = {k: v.get("weight", 0.25) for k, v in content_criteria.items()}
                    agent_input = {
                        "student_content": content,
                        "rubric": {"weights": content_weights},
                        "ideal_reference": ideal_reference or "",
                        "problem_statement": problem_statement or "",
                        "rubric_id": assignment_id,
                    }
                    content_output = self.content_agent.evaluate(agent_input)
                    agent_outputs.append(content_output)
                    break

            # Aggregate results
            if agent_outputs:
                weights = self.rubric.get_weights()
                aggregator_input = {
                    "agent_outputs": agent_outputs,
                    "rubric": {"weights": list(weights.values())},
                }
                final_result = self.aggregator_agent.evaluate(aggregator_input)

                result_entry = {
                    "assignment_type": "mixed",
                    "agent_count": len(agent_outputs),
                    **final_result,
                }

                # Integrity check on code + content
                integrity = self._run_integrity_check(
                    student_code or "", assignment_id, student_name, 
                    text_content=submissions.get("text", {}).get(student_name, "")
                )
                if integrity:
                    result_entry["flag_score"] = integrity["flag_score"]
                    result_entry["flag_reasons"] = integrity["reasons"]

                # Review queue
                self._maybe_queue(student_name, assignment_id, result_entry)

                results[student_name] = result_entry

        return results

    # ======================================================================
    # TRANSCRIPT SUMMARY SUBMISSIONS
    # ======================================================================

    def _evaluate_transcript_submissions(
        self,
        submissions: Dict[str, str],
        transcript_text: str,
        assignment_id: str = "",
    ) -> Dict[str, Dict[str, Any]]:
        """
        Evaluate student summaries against a lecture transcript.

        OPTIMIZED: Uses batch encoding to score all students at once.
        - Concepts encoded ONCE
        - All student sentences encoded in ONE batch call
        - 10-20x faster than one-by-one scoring

        Args:
            submissions: Dict of filename → content.
            transcript_text: Raw VTT transcript text.
            assignment_id: Unique assignment identifier.

        Returns:
            Dictionary mapping student names to evaluation results.
        """
        import time
        start_time = time.time()

        # Phase 1: Parse transcript and extract concepts (ONE TIME)
        clean_transcript = parse_vtt(transcript_text) if transcript_text.strip() else ""

        if not clean_transcript or len(clean_transcript) < 100:
            print("⚠ Transcript too short or empty. Cannot evaluate summaries.")
            results = {}
            for filename, content in submissions.items():
                student_name = get_student_name_from_filename(filename)
                results[student_name] = {
                    "file": filename,
                    "assignment_type": "transcript",
                    "final_score": 0,
                    "max_score": 100,
                    "combined_feedback": [
                        "⚠ Transcript was too short or empty to evaluate against."
                    ],
                }
            return results

        # Phase 1b: Extract TF-IDF candidates as fallback
        tfidf_candidates = extract_concepts(clean_transcript, top_n=20)

        # Phase 1c: LLM-FIRST concept extraction (uses 70B model)
        # The LLM reads the full transcript and extracts concepts directly.
        # TF-IDF candidates are only used as fallback if LLM is unavailable.
        concepts = llm_extract_concepts(clean_transcript, tfidf_fallback_concepts=tfidf_candidates)

        transcript_word_count = len(clean_transcript.split())
        print(f"✓ Parsed transcript: {transcript_word_count} words")
        print(f"✓ Final concepts ({len(concepts)}): {concepts}")

        # Phase 2: Pre-process ALL submissions (strip HTML, map to student names)
        cleaned_summaries = {}  # student_name -> cleaned text
        filename_map = {}       # student_name -> filename

        for filename, raw_content in submissions.items():
            student_name = get_student_name_from_filename(filename)
            content = raw_content
            if "<html" in content.lower() or "<!doctype" in content.lower() or "<p>" in content.lower():
                content = strip_html(content)
            cleaned_summaries[student_name] = content
            filename_map[student_name] = filename

        print(f"✓ Pre-processed {len(cleaned_summaries)} submissions")

        # Phase 3: BATCH score all summaries at once (FAST!)
        from backend.core.utils.vtt_parser import batch_score_summaries
        all_scores = batch_score_summaries(cleaned_summaries, concepts, clean_transcript)

        elapsed = time.time() - start_time
        print(f"✓ Scored {len(all_scores)} summaries in {elapsed:.1f}s ({elapsed/len(all_scores):.2f}s per student)")

        # Phase 4: Build feedback for each student
        results = {}
        for student_name, scoring in all_scores.items():
            filename = filename_map.get(student_name, "")
            score = scoring["total_score"]
            matched = scoring["matched_concepts"]
            missing = scoring["missing_concepts"]
            word_count = scoring["word_count"]
            coverage = scoring["concept_coverage"]
            depth = scoring["depth_score"]
            expression = scoring.get("expression_score", 60)

            feedback = []
            score_10 = round(score / 10, 1)

            # ── Score Breakdown (transparent — student sees exactly where marks went) ──
            # Formula: coverage*0.35 + depth*0.15 + expression*0.10 + attempt*0.30 + 10 base
            coverage_pts = round(coverage * 0.35, 1)
            depth_pts = round(depth * 0.15, 1)
            expression_pts = round(expression * 0.10, 1)
            attempt_pts = round(scoring.get("attempt_score", 100) * 0.30, 1)
            base_pts = 10.0

            # ── Overall Assessment ──
            if score_10 >= 8.5:
                feedback.append(f"🏆 **Excellent Work** — Score: {score_10}/10")
                feedback.append("Outstanding summary that demonstrates a thorough understanding of the lecture material. Well done!")
            elif score_10 >= 7.0:
                feedback.append(f"✅ **Good Summary** — Score: {score_10}/10")
                feedback.append("You've captured the key ideas from the lecture effectively. A few more details would make this even stronger.")
            elif score_10 >= 5.5:
                feedback.append(f"📝 **Adequate Summary** — Score: {score_10}/10")
                feedback.append("Your summary covers some important points, but misses several key topics discussed in the lecture.")
            elif score_10 >= 4.0:
                feedback.append(f"⚠️ **Needs Improvement** — Score: {score_10}/10")
                feedback.append("The summary is quite brief and doesn't reflect most of what was taught. Please revisit the lecture content.")
            else:
                feedback.append(f"❌ **Insufficient** — Score: {score_10}/10")
                feedback.append("This submission does not adequately reflect the lecture content. Please rewrite with more detail.")

            # ── Score Breakdown ──
            feedback.append(
                f"**📊 Score Breakdown**: "
                f"Topic Coverage: {coverage_pts}/35 | "
                f"Depth of Understanding: {depth_pts}/15 | "
                f"Writing Quality: {expression_pts}/10 | "
                f"Effort: {attempt_pts}/30 | "
                f"Base: {base_pts}/10"
            )

            # ── Strengths ──
            strengths = []
            if len(matched) >= len(concepts) * 0.8:
                strengths.append(f"covered {len(matched)} out of {len(concepts)} key topics — excellent coverage")
            elif len(matched) >= len(concepts) * 0.6:
                strengths.append(f"covered {len(matched)} out of {len(concepts)} key topics")
            if depth >= 70:
                strengths.append("explained concepts in depth, not just listed them")
            if 80 <= word_count <= 150:
                strengths.append("well-structured and appropriately detailed")
            if expression >= 70:
                strengths.append("clear and well-written")

            if strengths:
                feedback.append(f"**💪 Strengths**: {'; '.join(strengths).capitalize()}.")

            # ── Topics Covered ──
            if matched:
                feedback.append(f"**📋 Topics Covered** ({len(matched)}/{len(concepts)}): {', '.join(matched[:12])}")

            # ── How to Improve (highly specific per student) ──
            improvements = []

            # 1) Missing topics — only if there are any
            if missing:
                top_missing = missing[:5]
                improvements.append(f"Include these missing topics: **{', '.join(top_missing)}**")

            # 2) Depth-specific feedback — different tiers, never the same generic line
            if depth < 40:
                improvements.append(
                    f"Your depth score is low ({round(depth)}/100). You seem to be listing topics without explaining them. "
                    f"For each concept, add 1-2 sentences explaining *what* it is and *why* it's important."
                )
            elif depth < 55:
                improvements.append(
                    f"Your depth score ({round(depth)}/100) suggests you're mentioning concepts but not connecting them. "
                    f"Try explaining relationships — e.g., *why* do we standardize data before training? *What happens* if we skip it?"
                )
            elif depth < 70:
                # Only show this if it's actually costing them points AND they have good coverage
                if len(matched) >= len(concepts) * 0.5:
                    improvements.append(
                        f"Your depth score ({round(depth)}/100) is decent but could be stronger. "
                        f"Try using cause-and-effect phrases like 'because', 'which helps', 'in order to' to show deeper understanding."
                    )
            # depth >= 70 → no improvement needed, don't add anything

            # 3) Word count — specific advice
            if word_count < 30:
                improvements.append(
                    f"Your summary is very short ({word_count} words). A good summary should be 80-120 words "
                    f"and cover the main concepts taught in the lecture."
                )
            elif word_count < 50:
                improvements.append(
                    f"Your summary is too brief ({word_count} words). Aim for 80-120 words — "
                    f"enough to mention and briefly explain each key concept."
                )
            elif word_count > 200:
                improvements.append(
                    f"Your summary is quite long ({word_count} words). Focus on the {len(concepts)} most important concepts "
                    f"and keep it to 100-120 words for clarity."
                )

            # 4) Expression quality
            if expression < 40:
                improvements.append(
                    "Use complete sentences with proper capitalization and punctuation. "
                    "A well-structured summary is easier to read and shows clearer thinking."
                )
            elif expression < 55:
                improvements.append(
                    "Your writing could be more polished — use proper sentences and avoid run-on phrases."
                )

            # 5) For high-scoring students who lost a few points — explain specifically why
            if score_10 >= 8.0 and not improvements:
                # They scored well but not perfect — explain the gap
                if depth < 80:
                    improvements.append(
                        f"You covered all the topics well! The small deduction is mainly from depth of explanation ({round(depth)}/100). "
                        f"To get a perfect score, try explaining *why* each concept matters, not just mentioning it."
                    )
                elif expression < 80:
                    improvements.append(
                        f"Excellent topic coverage! The small deduction comes from writing quality ({round(expression)}/100). "
                        f"Polish your sentences and vary your vocabulary for a perfect score."
                    )
                else:
                    improvements.append(
                        "Near-perfect summary! To reach 10/10, try adding one more sentence "
                        "explaining how the concepts connect to each other."
                    )

            if improvements:
                feedback.append("**🎯 How to Improve**:")
                for imp in improvements:
                    feedback.append(f"  → {imp}")

            # ── LLM-enhanced feedback (Groq) ──
            # Pass student-specific data to Groq for unique, differentiated feedback
            try:
                from utils.llm_service import LLMService
                llm = LLMService()
                if llm.enabled:
                    student_summary_text = cleaned_summaries.get(student_name, "")
                    llm_feedback = llm.generate_semantic_feedback(
                        context_type="transcript",
                        submission_content=student_summary_text[:800],
                        rubric_context=f"Lecture transcript concepts: {', '.join(concepts)}",
                        deterministic_findings=feedback,
                        missing_concepts=missing,
                        matched_concepts=matched,
                        word_count=word_count,
                        depth_score=depth,
                    )
                    if llm_feedback and isinstance(llm_feedback, list) and len(llm_feedback) > 0:
                        llm_text = llm_feedback[0] if len(llm_feedback) == 1 else " ".join(llm_feedback)
                        if len(llm_text) > 50:
                            # Prepend LLM insight after the rule-based header
                            feedback.insert(2, f"**🤖 AI Analysis**: {llm_text[:500]}")
            except Exception as e:
                print(f"[Transcript] LLM feedback skipped for {student_name}: {e}")

            result_entry = {
                "file": filename,
                "assignment_type": "transcript",
                "final_score": round(score / 10, 1),
                "max_score": 10,
                "combined_feedback": feedback,
                "concept_coverage": coverage,
                "matched_concepts": len(matched),
                "total_concepts": len(concepts),
                "word_count": word_count,
                "summary_text": cleaned_summaries.get(student_name, ""),
            }

            # Integrity check
            integrity = self._run_integrity_check(
                "", assignment_id, student_name, text_content=cleaned_summaries.get(student_name, "")
            )
            if integrity:
                result_entry["flag_score"] = integrity["flag_score"]
                result_entry["flag_reasons"] = integrity["reasons"]

            # Review queue
            self._maybe_queue(student_name, assignment_id, result_entry)

            results[student_name] = result_entry
            print(f"  ✓ [{list(all_scores.keys()).index(student_name)+1}/{len(all_scores)}] {student_name} — {score_10}/10")

        return results

    # ======================================================================
    # HELPER METHODS
    # ======================================================================

    def _run_integrity_check(
        self, code: str, assignment_id: str, student_id: str, text_content: str = ""
    ) -> Optional[Dict]:
        """Run plagiarism + AI detection. Returns None if DB unavailable."""
        try:
            from backend.core.services.integrity_service import integrity_flag
            return integrity_flag(code, assignment_id, student_id, text_content=text_content)
        except Exception as e:
            print(f"Integrity check failed (non-fatal): {e}")
            return None

    def _maybe_queue(
        self, student_id: str, assignment_id: str, result: Dict
    ):
        """Queue submission for review if trigger conditions are met."""
        try:
            from backend.core.services.review_queue import maybe_queue_for_review
            maybe_queue_for_review(
                submission_id=f"{student_id}_{assignment_id}",
                student_id=student_id,
                assignment_id=assignment_id,
                result=result,
            )
        except Exception as e:
            print(f"Review queue insert failed (non-fatal): {e}")

    def _precompute_embedding(
        self, ideal_reference: Optional[str], rubric_id: str
    ):
        """Precompute ideal answer embedding for semantic scoring."""
        if not ideal_reference:
            return
        try:
            from backend.core.services.embedding_service import (
                is_available,
                precompute_rubric_embedding,
            )
            if is_available():
                precompute_rubric_embedding(ideal_reference, rubric_id)
        except Exception:
            pass  # Embedding is optional

    def _run_student_tracking(
        self,
        results: Dict[str, Dict],
        assignment_id: str,
        topic_tag: str,
    ):
        """Record scores, compute improvement deltas, and percentile ranks."""
        try:
            from backend.core.services.student_tracker import (
                record_score,
                get_improvement_delta,
                compute_percentiles_for_cohort,
            )

            # Record scores
            score_map = {}
            for student_name, result in results.items():
                score = result.get("final_score", 0)
                record_score(student_name, assignment_id, score, topic_tag)
                score_map[student_name] = score

            # Compute percentiles across the cohort
            percentiles = compute_percentiles_for_cohort(score_map)

            # Compute deltas and attach to results
            for student_name, result in results.items():
                delta_info = get_improvement_delta(
                    student_name, topic_tag, result.get("final_score", 0)
                )
                result["percentile"] = percentiles.get(student_name)
                result["improvement_delta"] = delta_info.get("delta")
                result["trend"] = delta_info.get("trend")

        except Exception as e:
            print(f"Student tracking failed (non-fatal): {e}")

    def get_rubric(self) -> Rubric:
        return self.rubric

    def set_rubric(self, rubric: Rubric) -> None:
        self.rubric = rubric
