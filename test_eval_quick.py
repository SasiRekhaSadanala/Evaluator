import requests

url = "http://127.0.0.1:8000/api/evaluate"

# Test with a simple text file first
with open("test_submissions/rag_report.txt", "rb") as f:
    files = [("files", ("rag_report.txt", f, "text/plain"))]
    
    data = {
        "assignment_type": "content",
        "problem_statement": "Create a detailed report on the Offline AI-Powered RAG Knowledge Portal"
    }
    
    print("Testing evaluation endpoint...")
    try:
        response = requests.post(url, files=files, data=data, timeout=30)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text[:500]}")
    except Exception as e:
        print(f"Error: {e}")
