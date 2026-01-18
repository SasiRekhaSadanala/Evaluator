import sys
sys.path.insert(0, 'd:/Apps/mini-proj')

from backend.core.agents.content_agent import ContentEvaluationAgent

# Test the auto-extraction directly
agent = ContentEvaluationAgent()

problem_statement = "Create a detailed report on the proposed solution and implementation plan for the Offline AI-Powered RAG Knowledge Portal"

# Test auto-extraction
concepts = agent._extract_task_concepts(problem_statement)
print("Auto-extracted concepts from problem statement:")
print(concepts)

# Test full extraction with problem statement
all_concepts = agent._extract_key_concepts({}, "", problem_statement)
print("\nFull concept extraction (no rubric, no reference):")
print(all_concepts)

# Test evaluation with auto-extraction
student_content = """
This document provides a comprehensive overview of the Offline AI-Powered RAG Knowledge Portal implementation.

The system architecture consists of several key components. First, we implement document indexing using FAISS for efficient vector storage. The embeddings are generated using a local model to ensure complete offline functionality.

The retriever-generator pipeline follows a standard RAG approach. Documents are chunked and embedded, then stored in the FAISS index.
"""

input_data = {
    "student_content": student_content,
    "rubric": {},
    "ideal_reference": "",
    "problem_statement": problem_statement
}

result = agent.evaluate(input_data)
print("\nEvaluation result:")
print(f"Score: {result['score']}/{result['max_score']}")
print("\nFeedback:")
for item in result['feedback']:
    print(f"  {item}")
