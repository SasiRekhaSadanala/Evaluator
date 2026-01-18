import requests
import json

# Test the enhanced content evaluation with concept extraction
url = "http://127.0.0.1:8000/api/evaluate"

# Prepare the test file
files = [
    ("files", ("rag_report.txt", open("test_submissions/rag_report.txt", "rb"), "text/plain"))
]

# Problem statement with clear expected concepts
data = {
    "assignment_type": "content",
    "problem_statement": "Create a detailed report on the proposed solution and implementation plan for the Offline AI-Powered RAG Knowledge Portal"
}

print("Testing concept-driven evaluation...")
print(f"Problem Statement: {data['problem_statement']}")
print("\nExpected auto-extracted concepts:")
print("- offline, knowledge, portal, implementation, plan, solution, detailed, report, proposed")
print("\nSending request...")

response = requests.post(url, files=files, data=data)

if response.status_code == 200:
    result = response.json()
    print("\n✅ Evaluation successful!")
    print(f"\nStatus: {result['status']}")
    print(f"Message: {result['message']}")
    
    if result.get('results'):
        for item in result['results']:
            print(f"\n{'='*60}")
            print(f"Submission ID: {item['submission_id']}")
            print(f"Score: {item['final_score']}/{item['max_score']} ({item['percentage']}%)")
            print(f"\nFeedback:")
            for feedback_item in item['feedback']:
                print(f"  {feedback_item}")
            print(f"{'='*60}")
else:
    print(f"\n❌ Error: {response.status_code}")
    print(response.text)
