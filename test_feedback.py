import asyncio
from backend.core.agents.code_agent import CodeEvaluationAgent
from backend.core.agents.content_agent import ContentEvaluationAgent

def test_code():
    agent = CodeEvaluationAgent()
    input_data = {
        "problem_statement": "Write a Python function to calculate the Greatest Common Divisor (GCD) of two numbers.",
        "student_code": "def hello():\n    # This is missing a loop\n    print('world')\n",
        "filename": "hello.py",
        "rubric": {
            "weights": {"approach": 0.4, "readability": 0.2, "structure": 0.2, "effort": 0.2}
        }
    }
    res = agent.evaluate(input_data)
    print("\n--- CODE EVALUATION (IRRELEVANT) ---")
    print("Score:", res["score"])
    feedback_str = "\n".join(res["feedback"])
    print("Feedback:\n" + feedback_str.encode('ascii', errors='replace').decode('ascii'))

def test_content():
    agent = ContentEvaluationAgent()
    input_data = {
        "problem_statement": "Explain the process of photosynthesis in plants.",
        "student_content": "The stock market went up today because of tech earnings.",
        "rubric": {}
    }
    res = agent.evaluate(input_data)
    print("\n--- CONTENT EVALUATION (IRRELEVANT) ---")
    print("Score:", res["score"])
    feedback_str = "\n".join(res["feedback"])
    print("Feedback:\n" + feedback_str.encode('ascii', errors='replace').decode('ascii'))

if __name__ == "__main__":
    test_code()
    test_content()
