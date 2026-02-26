import os
import json
import google.generativeai as genai
from typing import List, Optional, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class LLMService:
    """
    Service wrapper for Google's Gemini LLM.
    Role: Semantic Assistant ONLY. Does not assign scores.
    """

    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.enabled = os.getenv("LLM_ENABLED", "false").lower() == "true"
        self.model_name = os.getenv("LLM_MODEL", "gemini-2.0-flash")
        self._client = None
        self._setup_done = False

    def _ensure_setup(self):
        """Lazy initialization of the Gemini client."""
        if self._setup_done or not self.enabled:
            return

        if not self.api_key:
            print("WARNING: LLM_ENABLED is true but GEMINI_API_KEY is missing. Disabling LLM.")
            self.enabled = False
            return

        try:
            genai.configure(api_key=self.api_key)
            # Use a default model first, can be overridden during generation
            self._client = genai.GenerativeModel(self.model_name)
            self._setup_done = True
        except Exception as e:
            print(f"WARNING: Failed to initialize Gemini: {e}. Disabling LLM.")
            self.enabled = False
            self._setup_done = True

    def generate_semantic_feedback(
        self, 
        context_type: str, 
        submission_content: str, 
        rubric_context: str, 
        deterministic_findings: List[str],
        missing_concepts: List[str] = None,
        relevance_status: str = "UNCERTAIN"
    ) -> List[str]:
        """
        Generate qualitative feedback based on deterministic findings.
        
        Args:
            context_type: "code" or "content"
            submission_content: The student's code or text.
            rubric_context: Relevant parts of the rubric.
            deterministic_findings: List of strings like "Found 3 functions".
            missing_concepts: List of missing keywords to be explained semantically.

        Returns:
            List of feedback strings. Returns empty list on failure or if disabled.
        """
        if not self.enabled:
            return []

        self._ensure_setup()
        
        # Try a few common model identifiers to avoid 404s/Quotas
        models_to_try = [self.model_name, "gemini-2.0-flash", "gemini-flash-latest", "gemini-2.5-flash", "gemini-pro-latest"]
        # Remove duplicates while preserving order
        models_to_try = list(dict.fromkeys(m for m in models_to_try if m))
        
        last_error = ""
        for model in models_to_try:
            try:
                client = genai.GenerativeModel(model)
                prompt = self._build_prompt(context_type, submission_content, rubric_context, deterministic_findings, missing_concepts, relevance_status)
                response = client.generate_content(prompt)
                
                if response.text:
                    # Parse bullet points from response
                    lines = [line.strip() for line in response.text.split("\n") if line.strip()]
                    return lines if lines else [response.text.strip()]
                
                continue

            except Exception as e:
                last_error = str(e)
                continue
                
        print(f"WARNING: All LLM models failed. Last error: {last_error}. Falling back to rule-based feedback.")
        return []

    def _build_prompt(
        self, 
        context_type: str, 
        submission: str, 
        rubric: str, 
        findings: List[str],
        missing: List[str] = None,
        relevance_status: str = "UNCERTAIN"
    ) -> str:
        findings_str = "\n".join(f"- {f}" for f in findings)
        missing_str = ", ".join(missing) if missing else "None"

        if relevance_status == "IRRELEVANT":
            relevance_instructions = """
1. Format your response into these exact sections:
    **Summary**: State clearly that the submission is irrelevant to the assigned problem. Briefly mention what their code/text actually does (as context).
    
    **Corrections Needed**: 
    - DO NOT critique the student's code for style, comments, or naming. It is irrelevant.
    - INSTEAD, provide a comprehensive "How to Solve the Assigned Problem" guide.
    - Include high-level Pseudo-code and logical steps for the ACTUAL assigned task.
    - Be a mentor: help them understand the problem they missed.
    
    **Strengths**: Mention 1 minor technical strength of their code (syntax/structure) ONLY if it exists, otherwise omit this section.
"""
        else:
            relevance_instructions = """
1. Format your response into these exact sections:
    **Summary**: [Brief 1-sentence explanation of what the code/content is trying to do]
    
    **Corrections Needed**: [A detailed paragraph explaining conceptual gaps. Behave like a patient, cool teacher. When pointing out issues like missing comments or structure, give precise examples of where and how they should write them. e.g., "you need to write comments right before your loops explaining X like this..."]
    
    **Strengths**: [1-3 concise lines highlighting what was done well]
"""
        
        base_prompt = f"""
You are a helpful Teaching Assistant explaining evaluation results.
Your goal is to explain the following evaluation results and findings to a student.
DO NOT assign a score. The score has already been determined by the system.
DO NOT change weights or grading criteria.
DO NOT invent new criteria. Focus ONLY on the provided context.
Only explain based on provided facts and findings.

Context: {context_type.upper()} Assignment
Rubric/Criteria used:
{rubric}

Automated Findings (Facts that determine the score):
{findings_str}

Missing Concepts (Keywords to explain):
{missing_str}

Student Submission (for context):
{submission[:4000]}

MANDATORY INSTRUCTIONS:
{relevance_instructions}

2. Explain logically WHY the findings lead to the evaluation result.
3. Rewrite missing concepts as a semantic explanation.
4. Keep feedback encouraging but technical.
5. Start directly with the output content (no "Here is...").
6. Do NOT use markdown headers like "##". Use bold keys exactly as provided (e.g., "**Summary**:").

"""
        return base_prompt

    def check_relevance(
        self,
        problem_statement: str,
        submission_content: str,
        context_type: str = "code"
    ) -> str:
        """
        Ask LLM if the submission is relevant to the problem.

        Args:
            problem_statement: The task description.
            submission_content: Student's code or text.
            context_type: "code" or "content".

        Returns:
            "RELEVANT" if submission genuinely attempts to solve the problem.
            "PARTIAL" if submission shows some understanding but incomplete/off-track.
            "IRRELEVANT" if completely unrelated or wrong problem.
            "UNCERTAIN" if LLM failed or disabled (fail-closed for safety).
        """
        if not self.enabled:
            return "UNCERTAIN"

        self._ensure_setup()
        
        prompt = f"""
You are an expert evaluator for an automated grading system.
Your task is to determine if the {context_type} submission GENUINELY ATTEMPTS to solve the specific problem described.

Problem Statement:
{problem_statement[:1500]}

Submission:
{submission_content[:3000]}

CRITICAL EVALUATION RULES:
1. **Identify the Core Logic Requirement**: What is the unique algorithmic or conceptual task? (e.g., "Implement a Trie", "Calculate GCD", "Summarize Photosynthesis").
2. **Identify the Submission's Actual Logic**: What does this code/text actually do?
3. **Ignore Superficial Similarities**: DO NOT be fooled by:
    - Common programming terms (`int`, `vector`, `List`, `return`).
    - Standard boilerplate templates.
    - Matching words that are used in a different context.
4. **Verdicts**:
    - **IRRELEVANT**: If the submission is for a different problem, is just boilerplate, or contains no logic related to the core task.
    - **PARTIAL**: If the submission shows some understanding of the problem domain but is incomplete, significantly off-track, or only addresses a small part.
    - **RELEVANT**: If the submission shows a clear attempt to solve the specific problem, even if it has bugs or is unfinished.
    - **UNCERTAIN**: Only if you genuinely cannot determine relevance from the provided information.

Response Format:
Reasoning: [1-2 sentences explaining the core logic mismatch or match]
Verdict: [RELEVANT/PARTIAL/IRRELEVANT/UNCERTAIN]
"""
        max_retries = 2
        for attempt in range(max_retries):
            try:
                # Use the configured model
                client = genai.GenerativeModel(self.model_name or "gemini-2.0-flash")
                response = client.generate_content(prompt)
                
                if not response.text:
                    continue
                    
                text = response.text.strip().upper()
                
                # Parse verdict with priority on the "Verdict: " prefix
                if "VERDICT: RELEVANT" in text or "VERDICT:RELEVANT" in text:
                    return "RELEVANT"
                if "VERDICT: PARTIAL" in text or "VERDICT:PARTIAL" in text:
                    return "PARTIAL"
                if "VERDICT: IRRELEVANT" in text or "VERDICT:IRRELEVANT" in text:
                    return "IRRELEVANT"
                if "VERDICT: UNCERTAIN" in text or "VERDICT:UNCERTAIN" in text:
                    return "UNCERTAIN"
                
                # Loose fallback - look for standalone verdict words
                if "RELEVANT" in text and "IRRELEVANT" not in text and "PARTIAL" not in text:
                    return "RELEVANT"
                if "IRRELEVANT" in text:
                    return "IRRELEVANT"
                if "PARTIAL" in text:
                    return "PARTIAL"
                    
            except Exception as e:
                print(f"LLM Relevance Check failed: {e}")
                continue
        
        # Fail-closed: If LLM fails, treat as uncertain (which will be handled conservatively)
        return "UNCERTAIN"

    def parse_rubric_text(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Uses LLM to convert a plain text rubric description into the structured 
        RubricConfig JSON dictionary format expected by the system.
        """
        if not self.enabled:
            return None
            
        self._ensure_setup()
        
        rubric_schema = """
        {
            "name": "Custom Extracted Rubric",
            "version": "1.0",
            "dimensions": {
                "code": {
                    "weight": [float between 0 and 1],
                    "max_score": 100,
                    "criteria": {
                        "criterion1": {"weight": [float], "max_score": 100}
                    }
                },
                "content": {
                    "weight": [float between 0 and 1],
                    "max_score": 100,
                    "criteria": {
                        "criterion1": {"weight": [float], "max_score": 100}
                    }
                }
            }
        }
        """
        
        prompt = f"""
        You are an AI tasked with converting a plain text grading rubric into a strict JSON configuration.
        
        The output must strictly be a VALID JSON object matching this general structure:
        {rubric_schema}
        
        Rules:
        1. Analyze the text to find evaluation dimensions and their respective weights.
        2. Sum of weights for all dimensions at the top level should ideally equal 1.0 (e.g. code: 0.6, content: 0.4).
        3. Within each dimension, create a 'criteria' dictionary based on the text. The sum of criteria weights within a dimension should equal 1.0.
        4. If a dimension is completely omitted from the text, omit it from the JSON. If the user only provides criteria without weights, assign equal weights.
        5. Return ONLY the raw JSON string. Do not use Markdown formatting like ```json. Do not include any explanations.
        
        User Text to Parse:
        {text}
        """
        
        max_retries = 2
        for attempt in range(max_retries):
            try:
                client = genai.GenerativeModel(self.model_name or "gemini-2.0-flash")
                response = client.generate_content(prompt)
                
                if not response.text:
                    continue
                    
                # Clean up any potential markdown formatting
                json_str = response.text.strip()
                if json_str.startswith("```json"):
                    json_str = json_str[7:]
                if json_str.startswith("```"):
                    json_str = json_str[3:]
                if json_str.endswith("```"):
                    json_str = json_str[:-3]
                    
                json_str = json_str.strip()
                parsed = json.loads(json_str)
                return parsed
            except Exception as e:
                print(f"LLM Rubric Parsing failed: {e}")
                continue
                
        return None
