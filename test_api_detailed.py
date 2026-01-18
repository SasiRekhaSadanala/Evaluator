import requests
import json
import sys

url = "http://127.0.0.1:8000/api/evaluate"

# Create a simple test file
test_content = """This is a test document about RAG systems.
The document discusses offline processing and embeddings.
It covers document indexing and retrieval pipelines."""

with open("test_simple.txt", "w") as f:
    f.write(test_content)

# Test the evaluation
with open("test_simple.txt", "rb") as f:
    files = {"files": ("test_simple.txt", f, "text/plain")}
    
    data = {
        "assignment_type": "content",
        "problem_statement": "Create a report on RAG systems and offline processing"
    }
    
    print("=" * 60)
    print("Testing Evaluation Endpoint")
    print("=" * 60)
    print(f"URL: {url}")
    print(f"Assignment Type: {data['assignment_type']}")
    print(f"Problem Statement: {data['problem_statement']}")
    print("=" * 60)
    
    try:
        response = requests.post(url, files=files, data=data, timeout=30)
        
        print(f"\nStatus Code: {response.status_code}")
        print(f"\nResponse Headers:")
        for key, value in response.headers.items():
            print(f"  {key}: {value}")
        
        print(f"\nResponse Body:")
        try:
            json_response = response.json()
            print(json.dumps(json_response, indent=2))
        except:
            print(response.text)
            
        sys.exit(0 if response.status_code == 200 else 1)
        
    except requests.exceptions.Timeout:
        print("\n❌ Request timed out after 30 seconds")
        sys.exit(1)
    except requests.exceptions.ConnectionError as e:
        print(f"\n❌ Connection error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
