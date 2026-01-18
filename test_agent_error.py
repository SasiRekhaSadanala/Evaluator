import sys
sys.path.insert(0, 'd:/Apps/mini-proj')

try:
    print("Importing content agent...")
    from backend.core.agents.content_agent import ContentEvaluationAgent
    print("✓ Import successful")
    
    print("\nCreating agent instance...")
    agent = ContentEvaluationAgent()
    print("✓ Agent created")
    
    print("\nTesting evaluation...")
    input_data = {
        "student_content": "This is a test document about RAG systems and offline processing.",
        "rubric": {},
        "ideal_reference": "",
        "problem_statement": "Create a report on RAG systems"
    }
    
    result = agent.evaluate(input_data)
    print("✓ Evaluation successful")
    print(f"\nScore: {result['score']}/{result['max_score']}")
    print(f"Feedback items: {len(result['feedback'])}")
    for item in result['feedback']:
        print(f"  - {item}")
        
except Exception as e:
    print(f"\n❌ Error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
