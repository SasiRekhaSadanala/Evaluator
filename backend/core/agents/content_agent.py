import re
from typing import Any, Dict, List
import difflib

from .base_agent import EvaluationAgent
from utils.llm_service import LLMService
from backend.core.services import embedding_service as _embedding_mod


class _EmbeddingBridge:
    """Thin wrapper so content agent can call embedding_service functions as methods."""
    @staticmethod
    def compute_similarity(text_a: str, text_b: str) -> float:
        return _embedding_mod.compute_similarity(text_a, text_b)

    @staticmethod
    def is_available() -> bool:
        return _embedding_mod.is_available()


class ContentEvaluationAgent(EvaluationAgent):
    """Evaluates student content (PPT text, summaries) through structural analysis."""

    def __init__(self):
        super().__init__()
        self.llm_service = LLMService()
        self.embedding_service = _EmbeddingBridge()

    def evaluate(self, input_data: Any) -> Dict[str, Any]:
        """
        Evaluate student content through structural and keyword analysis.

        Args:
            input_data: Dictionary containing:
                - student_content (str): The student's text content
                - rubric (dict): Evaluation criteria with key concepts, OR
                - ideal_reference (str): Reference content for comparison
                - problem_statement (str): Task description for auto-extraction

        Returns:
            Dictionary with:
                - score: Total evaluation score
                - max_score: Maximum possible score
                - feedback: List of learning-oriented feedback strings
        """
        student_content = input_data.get("student_content", "")
        rubric = input_data.get("rubric", {})
        ideal_reference = input_data.get("ideal_reference", "")
        problem_statement = input_data.get("problem_statement", "")

        feedback = []
        scores = {}

        # Extract key concepts from rubric, reference, or problem statement
        key_concepts = self._extract_key_concepts(rubric, ideal_reference, problem_statement)

        # Step 0: LLM-based Relevance Check (Primary Gate)
        if self.llm_service.enabled:
            verdict = self.llm_service.check_relevance(problem_statement, student_content, "content")
            self._last_relevance_verdict = verdict
            
            # Handle verdicts strictly
            if verdict == "IRRELEVANT":
                feedback.append("⚠️ LLM determined content is irrelevant to the prompt. Score: 0.")
                llm_feedback = self.llm_service.generate_semantic_feedback(
                    context_type="content",
                    submission_content=student_content,
                    rubric_context=str(rubric),
                    deterministic_findings=feedback,
                    missing_concepts=[],
                    relevance_status="IRRELEVANT"
                )
                if llm_feedback:
                    feedback = ["LLM Explanation:"] + llm_feedback
                return {
                    "score": 0,
                    "max_score": 100,
                    "feedback": feedback
                }
            elif verdict == "UNCERTAIN":
                # feedback.append("⚠️ LLM could not determine relevance. Treating as irrelevant for safety. Score: 0.")
                pass
                # Continue with evaluation using keyword fallback
            elif verdict == "PARTIAL":
                feedback.append("⚠️ LLM found partial relevance. Proceeding with reduced scoring.")
                # Continue with evaluation but note the partial status
            elif verdict == "RELEVANT":
                feedback.append("✓ LLM verified content is relevant to the prompt.")
                # Continue with full evaluation


        # Heuristic: Check for prompt copying (plagiarism of question)
        # If strict LLM relevance failed (UNCERTAIN) or is disabled, we must ensure 
        # the student didn't just copy the prompt to cheat keyword detection.
        if problem_statement and len(student_content) > 0:
            similarity = difflib.SequenceMatcher(None, problem_statement, student_content).ratio()
            # If > 60% similarity, likely just the prompt
            if similarity > 0.6:
                feedback.append(f"⚠️ Content is too similar to the problem statement ({int(similarity*100)}% match). Score penalized.")
                is_plagiarism = True
                self._last_relevance_verdict = "IRRELEVANT"
            else:
                is_plagiarism = False
        else:
            is_plagiarism = False
        
        # Analyze concept coverage
        coverage_score = self._evaluate_concept_coverage(
            student_content, key_concepts, feedback,
            ideal_reference=ideal_reference,
            rubric_id=input_data.get("rubric_id", "default"),
        )
        
        # Fallback Gate: If LLM is disabled or uncertain, and coverage is zero, fail
        if coverage_score == 0:
            feedback.append("⚠️ Irrelevant submission: No key concepts from the prompt were found.")
            if self.llm_service.enabled:
                llm_feedback = self.llm_service.generate_semantic_feedback(
                    context_type="content",
                    submission_content=student_content,
                    rubric_context=str(rubric),
                    deterministic_findings=feedback,
                    missing_concepts=getattr(self, "_last_missing_concepts", []),
                    relevance_status="IRRELEVANT"
                )
                if llm_feedback:
                    feedback = ["LLM Explanation:"] + llm_feedback
            return {
                "score": 0,
                "max_score": 100,
                "feedback": feedback
            }

        scores["coverage"] = coverage_score

        # Analyze factual accuracy using semantic embeddings
        factual_score = self._evaluate_factual_accuracy(
            student_content, problem_statement, ideal_reference, feedback
        )
        scores["factual_accuracy"] = factual_score

        # Analyze alignment with requirements
        alignment_score = self._evaluate_alignment(
            student_content, rubric, feedback
        )
        scores["alignment"] = alignment_score

        # Analyze logical flow
        flow_score = self._evaluate_logical_flow(student_content, feedback)
        scores["flow"] = flow_score

        # Analyze completeness
        completeness_score = self._evaluate_completeness(student_content, feedback)
        scores["completeness"] = completeness_score

        # Calculate total score — factual accuracy is the heaviest weight
        weights = {
            "factual_accuracy": 0.40,  # PRIMARY: Is the answer factually correct?
            "coverage": 0.30,          # Does it cover key concepts?
            "alignment": 0.15,         # Alignment with requirements
            "flow": 0.08,              # Writing style/flow
            "completeness": 0.07,      # Depth and detail
        }

        total_score = sum(scores.get(k, 0) * v for k, v in weights.items())
        
        # Cap score if plagiarism detected
        if is_plagiarism:
             total_score = min(total_score, 20)
             
        max_score = sum(weights.values()) * 100

        # Integrate LLM Feedback (Step 2, 4, 5)
        if self.llm_service.enabled:
            # Collect missing concepts for semantic explanation (Step 4)
            missing_concepts = getattr(self, "_last_missing_concepts", [])
            
            # Collect deterministic findings for context
            findings = [f for f in feedback if f.startswith("✓") or f.startswith("→") or f.startswith("❌")]
            
            llm_feedback = self.llm_service.generate_semantic_feedback(
                context_type="content",
                submission_content=student_content,
                rubric_context=str(rubric),
                deterministic_findings=findings,
                missing_concepts=missing_concepts,
                relevance_status=getattr(self, "_last_relevance_verdict", "UNCERTAIN")
            )
            
            if llm_feedback:
                feedback = ["LLM Explanation:"] + llm_feedback
        
        return {
            "score": round(total_score, 2),
            "max_score": max_score,
            "feedback": feedback,
        }

    def _extract_key_concepts(self, rubric: dict, ideal_reference: str, problem_statement: str = "") -> List[str]:
        """Extract key concepts from rubric, reference, or problem statement.
        
        Priority order:
        1. Explicit rubric concepts (highest priority)
        2. Reference content keywords
        3. Auto-extracted from problem statement (fallback)
        """
        concepts = []

        # Priority 1: Explicit rubric concepts
        if rubric:
            if "concepts" in rubric:
                concepts.extend(rubric["concepts"])
            if "criteria" in rubric:
                criteria = rubric["criteria"]
                if isinstance(criteria, list):
                    concepts.extend(criteria)
                elif isinstance(criteria, dict):
                    concepts.extend(criteria.keys())

        # Priority 2: Reference content
        if ideal_reference:
            words = re.findall(r"\b\w{4,}\b", ideal_reference.lower())
            concepts.extend(list(set(words))[:10])

        # Priority 3: Auto-extract from problem statement (fallback)
        if not concepts and problem_statement:
            task_concepts = self._extract_task_concepts(problem_statement)
            concepts.extend(task_concepts)

        return list(set(concepts))  # Remove duplicates
    
    def _extract_task_concepts(self, problem_statement: str) -> List[str]:
        """Auto-extract task-specific concepts from problem statement.
        
        Extracts domain-specific terms by:
        - Filtering out common stopwords AND question words
        - Extracting multi-word technical phrases (e.g., 'TF-IDF', 'machine learning')
        - Keeping words 4+ characters
        - Filtering generic verbs and adjectives
        """
        # Common stopwords + question words to filter out
        stopwords = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
            "of", "with", "from", "by", "as", "is", "was", "are", "were", "be",
            "been", "being", "have", "has", "had", "do", "does", "did", "will",
            "would", "should", "could", "may", "might", "must", "can", "this",
            "that", "these", "those", "your", "their", "our", "its", "his", "her",
            # Question words — never useful as required answer concepts
            "what", "which", "where", "when", "who", "whom", "whose", "how",
            "why", "explain", "describe", "define", "discuss", "compare",
            "stand", "stands", "mean", "means", "meant",
            "primary", "purpose", "main", "brief", "briefly",
            # Additional generic words to filter
            "make", "create", "provide", "include", "ensure", "allow", "enable",
            "support", "help", "need", "want", "give", "take", "show", "tell",
            "huge", "large", "small", "good", "bad", "best", "better", "more",
            "less", "most", "least", "very", "much", "many", "some", "all",
            "each", "every", "both", "either", "neither", "other", "another",
            "such", "same", "different", "new", "old", "first", "last", "next",
            "previous", "following", "above", "below", "between", "among",
            "expert", "hours", "challenge", "statement", "detailed", "report",
            "proposed", "solution", "plan", "problem",
            "write", "answer", "question", "assignment", "submit",
        }
        
        # Step 1: Extract acronyms and hyphenated terms (e.g., TF-IDF, NLP)
        acronyms = re.findall(r'\b[A-Z][A-Z0-9-]{1,}\b', problem_statement)
        # Also match lowercase versions of acronyms
        acronyms_lower = [a.lower() for a in acronyms]
        
        # Step 2: Extract multi-word phrases in quotes or with special formatting
        quoted_phrases = re.findall(r'["\']([^"\']+)["\']', problem_statement)
        
        # Step 3: Extract words 4+ characters
        words = re.findall(r"\b\w{4,}\b", problem_statement.lower())
        
        # Filter stopwords and generic terms
        task_concepts = [w for w in set(words) if w not in stopwords]
        
        # Prioritize technical/domain terms
        domain_terms = []
        for concept in task_concepts:
            # Skip common verbs/adjectives UNLESS they're technical
            if concept.endswith(('ing', 'ed', 'ly', 'ment', 'ness')):
                technical_suffixed = [
                    'indexing', 'embedding', 'processing', 'generation', 'retrieval',
                    'learning', 'clustering', 'classification', 'tokenized',
                    'frequency', 'weighting',
                ]
                if concept in technical_suffixed:
                    domain_terms.append(concept)
            elif concept.endswith('tion'):
                # Keep technical -tion words
                domain_terms.append(concept)
            else:
                domain_terms.append(concept)
        
        # Add acronyms (high-value concepts)
        domain_terms = acronyms_lower + quoted_phrases + domain_terms
        
        # Deduplicate while preserving order
        seen = set()
        unique_terms = []
        for t in domain_terms:
            tl = t.lower()
            if tl not in seen:
                seen.add(tl)
                unique_terms.append(tl)
        
        return unique_terms[:15]

    def _evaluate_factual_accuracy(
        self, student_content: str, problem_statement: str,
        ideal_reference: str, feedback: List[str]
    ) -> float:
        """Evaluate factual accuracy of the answer using semantic embeddings.
        
        This method detects whether the answer provides a factually correct
        response to the question. It works WITHOUT the LLM by using:
        
        1. Semantic similarity between the question+ideal vs question+answer
        2. Sentence-level coherence scoring (real vs made-up definitions)
        3. Technical term density analysis
        4. Cross-sentence consistency checking
        
        Returns:
            Score 0-100 representing factual accuracy.
        """
        score = 50  # Start with a neutral baseline
        
        # ── Strategy 1: Semantic similarity with ideal reference ──
        if ideal_reference and ideal_reference.strip():
            try:
                sim = self.embedding_service.compute_similarity(
                    student_content, ideal_reference
                )
                # Scale: 0.0-1.0 similarity → 0-100
                # High similarity to ideal = high factual accuracy
                ref_score = sim * 100
                feedback.append(f"✓ Semantic similarity to reference: {sim:.2f}")
                # If ideal is provided, this is the strongest signal
                return min(100, max(0, ref_score))
            except Exception:
                pass
        
        # ── Strategy 2: Question-Answer semantic coherence ──
        # Compare the full answer against the problem statement
        # A correct answer should be more semantically coherent with the question
        try:
            # Break the student answer into sentences
            sentences = [s.strip() for s in re.split(r'[.!?]+', student_content) if len(s.strip()) > 20]
            
            if problem_statement and sentences:
                # Compute per-sentence similarity to the problem statement
                sentence_scores = []
                for sent in sentences[:10]:  # Max 10 sentences
                    sim = self.embedding_service.compute_similarity(
                        sent, problem_statement
                    )
                    sentence_scores.append(sim)
                
                if sentence_scores:
                    avg_sim = sum(sentence_scores) / len(sentence_scores)
                    max_sim = max(sentence_scores)
                    min_sim = min(sentence_scores)
                    
                    # Variance in sentence similarity indicates mixed quality
                    variance = max_sim - min_sim
                    
                    # Higher average similarity = more on-topic
                    coherence_score = avg_sim * 100
                    score = coherence_score
        except Exception:
            pass
        
        # ── Strategy 3: Technical term density ──
        # Correct answers use real technical terms; wrong answers use made-up terms
        # Real terms: "numerical statistic", "information retrieval", "corpus",
        #             "text mining", "feature extraction"
        # Fake terms: "Term Function", "Indexed Data Framework"
        try:
            # Known high-value NLP/CS/data science terminology
            known_technical_terms = {
                # NLP terms
                "term frequency", "inverse document frequency", "bag of words",
                "word embedding", "tokenization", "lemmatization", "stemming",
                "named entity", "part of speech", "sentiment analysis",
                "text classification", "information retrieval", "corpus",
                "vector space", "cosine similarity", "word2vec", "glove",
                "attention mechanism", "transformer", "bert", "gpt",
                "recurrent neural", "convolutional neural", "sequence to sequence",
                # General ML/Stats terms
                "numerical statistic", "feature extraction", "text mining",
                "search engine", "machine learning", "deep learning",
                "supervised learning", "unsupervised learning", "neural network",
                "classification", "regression", "clustering", "dimensionality",
                "cross validation", "precision", "recall", "f1 score",
                "overfitting", "underfitting", "regularization",
                "gradient descent", "backpropagation", "activation function",
                # Data terms
                "data preprocessing", "feature engineering", "data pipeline",
                "training data", "test data", "validation", "normalization",
            }
            
            content_lower = student_content.lower()
            matches = 0
            matched_terms = []
            for term in known_technical_terms:
                if term in content_lower:
                    matches += 1
                    matched_terms.append(term)
            
            if matches >= 5:
                tech_bonus = min(30, matches * 5)
                score += tech_bonus
                feedback.append(f"✓ Uses {matches} verified technical terms: {', '.join(matched_terms[:5])}")
            elif matches >= 2:
                tech_bonus = matches * 3
                score += tech_bonus
                feedback.append(f"✓ Uses {matches} verified technical terms.")
            elif matches == 0:
                score -= 15
                feedback.append("→ No recognized technical terminology found in the answer.")
            
        except Exception:
            pass
        
        # ── Strategy 4: Answer length and depth bonus ──
        word_count = len(student_content.split())
        if word_count > 100:
            score += 10
        elif word_count > 60:
            score += 5
        elif word_count < 30:
            score -= 10
        
        # ── Strategy 5: Self-consistency check ──
        # Answers that define the same acronym differently within the text
        # are likely confused or making things up
        try:
            # Check if the answer redefines the same term multiple ways
            sentences = [s.strip() for s in student_content.split('.') if len(s.strip()) > 10]
            if len(sentences) >= 2:
                # Compare first definition sentence to last sentences
                first_sim = self.embedding_service.compute_similarity(
                    sentences[0], sentences[-1]
                )
                if first_sim < 0.2:
                    score -= 10
                    feedback.append("→ Answer shows low internal coherence.")
                elif first_sim > 0.6:
                    score += 5
        except Exception:
            pass
        
        final_score = min(100, max(0, score))
        feedback.append(f"✓ Factual accuracy score: {final_score:.0f}/100")
        return final_score

    def _evaluate_concept_coverage(
        self, content: str, key_concepts: List[str], feedback: List[str],
        ideal_reference: str = "", rubric_id: str = "",
    ) -> float:
        """
        Evaluate coverage of key concepts using semantic similarity + keyword fallback.

        Strategy:
        1. Try embedding-based semantic scoring (if sentence-transformers available)
        2. Run keyword matching in parallel
        3. Final score = max(keyword_score * 0.5, semantic_score)
           This prevents keyword gaming while rewarding paraphrasing.
        """
        if not key_concepts:
            feedback.append("ℹ No key concepts specified for comparison.")
            return 60

        # ── Keyword scoring (always runs — it's the floor) ──
        keyword_score = self._keyword_coverage(content, key_concepts, feedback)

        # ── Semantic scoring (optional — requires sentence-transformers) ──
        semantic_score = None
        try:
            from backend.core.services.embedding_service import (
                is_available,
                semantic_coverage_score,
                concept_hit_rate,
            )
            if is_available():
                # Overall semantic similarity
                if ideal_reference or rubric_id:
                    sem = semantic_coverage_score(
                        content,
                        rubric_id=rubric_id or "default",
                        ideal_answer=ideal_reference,
                    )
                    if sem is not None:
                        semantic_score = sem

                # Per-concept hit rate
                hit_rate = concept_hit_rate(content, key_concepts)
                if hit_rate is not None:
                    concept_pct = hit_rate * 100
                    # Blend: 60% semantic similarity + 40% concept hit rate
                    if semantic_score is not None:
                        semantic_score = 0.6 * semantic_score + 0.4 * concept_pct
                    else:
                        semantic_score = concept_pct

                    if concept_pct >= 70:
                        feedback.append(
                            f"✓ Semantic analysis: {concept_pct:.0f}% of concepts "
                            f"are semantically covered (paraphrasing OK)."
                        )

        except Exception as e:
            # Graceful fallback — semantic scoring is optional
            semantic_score = None

        # ── Combine: semantic wins if it's higher, keyword stays as floor ──
        if semantic_score is not None:
            final_score = max(keyword_score * 0.5, semantic_score)
            if semantic_score > keyword_score:
                feedback.append(
                    f"✓ Semantic scoring improved coverage: "
                    f"{keyword_score:.0f} → {final_score:.0f} "
                    "(paraphrased content detected)."
                )
        else:
            final_score = keyword_score

        return min(round(final_score), 100)

    def _keyword_coverage(
        self, content: str, key_concepts: List[str], feedback: List[str]
    ) -> float:
        """Pure keyword-based coverage scoring (original logic, now a sub-method)."""
        content_lower = content.lower()
        covered_concepts = [
            c for c in key_concepts
            if isinstance(c, str) and c.lower() in content_lower
        ]
        missing_concepts = [
            c for c in key_concepts
            if isinstance(c, str) and c.lower() not in content_lower
        ]

        self._last_missing_concepts = missing_concepts

        coverage_percent = (len(covered_concepts) / len(key_concepts)) * 100

        if coverage_percent >= 80:
            score = 90
            feedback.append(
                f"✓ Excellent keyword coverage ({len(covered_concepts)}/{len(key_concepts)} concepts)."
            )
            if missing_concepts and not self.llm_service.enabled:
                feedback.append(f"→ Missing: {', '.join(missing_concepts[:5])}")
        elif coverage_percent >= 60:
            score = 70
            feedback.append(
                f"→ Good keyword coverage ({len(covered_concepts)}/{len(key_concepts)} concepts)."
            )
            if not self.llm_service.enabled:
                feedback.append(f"→ Missing: {', '.join(missing_concepts[:5])}")
        elif coverage_percent >= 40:
            score = 50
            feedback.append(
                f"→ Partial keyword coverage ({len(covered_concepts)}/{len(key_concepts)} concepts)."
            )
            if not self.llm_service.enabled:
                feedback.append(f"→ Missing key concepts: {', '.join(missing_concepts[:7])}")
        elif coverage_percent >= 20:
            score = 20
            feedback.append(
                f"→ Low keyword coverage ({len(covered_concepts)}/{len(key_concepts)} concepts)."
            )
        else:
            score = 0
            feedback.append(
                f"❌ Very low keyword coverage ({len(covered_concepts)}/{len(key_concepts)} concepts)."
            )
            if not self.llm_service.enabled:
                feedback.append(f"❌ Missing critical concepts: {', '.join(missing_concepts[:10])}")

        return min(score, 100)


    def _evaluate_alignment(
        self, content: str, rubric: dict, feedback: List[str]
    ) -> float:
        """Evaluate alignment with rubric requirements."""
        score = 50

        if not rubric:
            return score

        # Check for learning objectives match
        if "learning_objectives" in rubric:
            objectives = rubric["learning_objectives"]
            if isinstance(objectives, list):
                matched = sum(
                    1 for obj in objectives
                    if isinstance(obj, str) and obj.lower() in content.lower()
                )
                if matched > 0:
                    score += 30
                    feedback.append(
                        f"✓ Addresses {matched} learning objectives."
                    )
                else:
                    feedback.append("→ Content should align with stated learning objectives.")

        # Check for required sections
        if "required_sections" in rubric:
            sections = rubric["required_sections"]
            if isinstance(sections, list):
                matched_sections = sum(
                    1 for sec in sections
                    if isinstance(sec, str) and sec.lower() in content.lower()
                )
                if matched_sections >= len(sections) * 0.7:
                    score += 20
                    feedback.append(
                        f"✓ Includes most required sections ({matched_sections}/{len(sections)})."
                    )
                else:
                    feedback.append(
                        f"→ Missing some required sections. "
                        f"Found {matched_sections}/{len(sections)}."
                    )

        return min(score, 100)

    def _evaluate_logical_flow(self, content: str, feedback: List[str]) -> float:
        """Evaluate logical flow and organization."""
        score = 50

        lines = content.split("\n")
        paragraphs = [p.strip() for p in lines if p.strip()]
        sentences = re.split(r"[.!?]+", content)
        sentences = [s.strip() for s in sentences if s.strip()]

        # Check paragraph structure
        if len(paragraphs) > 3:
            score += 25
            feedback.append(f"✓ Well-organized ({len(paragraphs)} distinct sections).")
        elif len(paragraphs) > 1:
            score += 15
            feedback.append("→ Consider organizing content into more distinct sections.")
        else:
            feedback.append("→ Break content into multiple paragraphs for clarity.")

        # Check sentence complexity and variety
        avg_sentence_length = (
            sum(len(s.split()) for s in sentences) / len(sentences)
            if sentences else 0
        )

        if 10 < avg_sentence_length < 25:
            score += 15
            feedback.append("✓ Sentence structure is clear and varied.")
        elif avg_sentence_length > 30:
            feedback.append(
                "→ Some sentences are too long. Break them for clarity."
            )
        elif avg_sentence_length < 5:
            feedback.append(
                "→ Sentences are too short. Expand with more detail."
            )

        # Check for transitions (simple keyword check)
        transition_words = [
            "therefore", "however", "additionally", "moreover", "furthermore",
            "in conclusion", "as a result", "for example", "similarly",
            "in contrast", "meanwhile", "next", "finally"
        ]
        transitions = sum(
            1 for word in transition_words if word in content.lower()
        )

        if transitions >= 3:
            score += 10
            feedback.append("✓ Good use of transitions for logical flow.")
        elif transitions > 0:
            feedback.append("→ Add more transition words to improve flow between ideas.")

        return min(score, 100)

    def _evaluate_completeness(self, content: str, feedback: List[str]) -> float:
        """Evaluate content completeness and detail."""
        score = 50

        lines = content.split("\n")
        non_empty_lines = [l for l in lines if l.strip()]
        word_count = len(content.split())

        # Check content length
        if word_count > 300:
            score += 30
            feedback.append(f"✓ Substantial content ({word_count} words).")
        elif word_count > 150:
            score += 15
            feedback.append(f"→ Content is moderate ({word_count} words). Add more detail.")
        else:
            feedback.append(
                f"→ Content is brief ({word_count} words). Expand with examples and explanations."
            )

        # Check for examples or details
        example_indicators = [
            "example", "for instance", "such as", "specifically",
            "in particular", "illustration", "case study"
        ]
        has_examples = any(
            indicator in content.lower() for indicator in example_indicators
        )

        if has_examples:
            score += 10
            feedback.append("✓ Includes examples or specific details.")
        else:
            feedback.append("→ Add concrete examples to support your concepts.")

        # Check for evidence or reasoning
        reasoning_indicators = [
            "because", "reason", "evidence", "research", "study",
            "proven", "demonstrated", "support", "justify"
        ]
        has_reasoning = any(
            indicator in content.lower() for indicator in reasoning_indicators
        )

        if has_reasoning:
            score += 10
            feedback.append("✓ Includes reasoning or evidence.")
        else:
            feedback.append("→ Add reasoning or evidence to strengthen claims.")

        return min(score, 100)
