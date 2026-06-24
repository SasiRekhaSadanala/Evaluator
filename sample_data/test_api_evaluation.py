import requests
import json
import os

url = "http://localhost:8000/api/evaluate"

# Prepare files
files = [
    ("files", ("submission.py", open("test_evaluation/submission.py", "rb")))
]

# Prepare data
data = {
    "assignment_type": "code",
    "problem_statement": open("problem.txt", "r").read(),
    "rubric_content": open("rubric.json", "r").read()
}

print("Starting evaluation via API...")
response = requests.post(url, data=data, files=files)

if response.status_code == 200:
    result = response.json()
    print("\n--- Evaluation Result ---")
    print(f"Status: {result.get('status')}")
    print(f"Message: {result.get('message')}")
    
    if "results" in result:
        for r in result["results"]:
            print(f"\nSubmission ID: {r['submission_id']}")
            print(f"Final Score: {r['final_score']}/{r['max_score']} ({r['percentage']}%)")
            print("\nFeedback:")
            for f in r["feedback"]:
                print(f"- {f}")
            
            if "detailed_critique" in r:
                print("\nDetailed Critique (Dimension level):")
                critique = r["detailed_critique"]
                if isinstance(critique, str):
                    try:
                        critique = json.loads(critique)
                    except:
                        pass
                print(json.dumps(critique, indent=2))
    else:
        print("No results found in response.")
else:
    print(f"Error: {response.status_code}")
    print(response.text)

