import requests
import sys

url = "http://127.0.0.1:8000/api/evaluate"

problem_statement = """create a detailed report on the proposed solution and implementation plan for the problem statement Offline AI-Powered RAG Knowledge Portal AI/ML & Natural Language Processing Challenge Expert 24 Hours Organizations generate huge amounts of internal knowledge (technical manuals, research papers, project reports, compliance docs). Searching these documents manually is inefficient, and cloud/internet-based solutions raise privacy and security concerns. Core Features 1. Document Upload & Indexing Multi-format support (PDF/DOCX/TXT) AI embeddings and preprocessing System indexing using AI embeddings 2. AI Model Integration Offline LLM implementation RAG pipeline (Retriever + Generator) Document-based response generation only 3. Interactive Chatbot Natural language queries Citation and source referencing Complete offline operation"""

print("=" * 80)
print("Testing Evaluation with Report.pdf")
print("=" * 80)

try:
    with open("Report.pdf", "rb") as f:
        files = {"files": ("Report.pdf", f, "application/pdf")}
        
        data = {
            "assignment_type": "content",
            "problem_statement": problem_statement
        }
        
        print(f"\nSending request to: {url}")
        print(f"Assignment Type: {data['assignment_type']}")
        print(f"Problem Statement length: {len(problem_statement)} characters")
        print(f"File: Report.pdf")
        print("\nWaiting for response...\n")
        
        response = requests.post(url, files=files, data=data, timeout=60)
        
        print(f"Status Code: {response.status_code}")
        print(f"\nResponse:")
        print(response.text)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('status') == 'success':
                print("\n✅ SUCCESS!")
                print(f"Message: {result.get('message')}")
                if result.get('results'):
                    for item in result['results']:
                        print(f"\nSubmission: {item['submission_id']}")
                        print(f"Score: {item['final_score']}/{item['max_score']} ({item['percentage']}%)")
                        print("Feedback:")
                        for fb in item['feedback']:
                            print(f"  {fb}")
            else:
                print(f"\n❌ FAILED: {result.get('message')}")
                print(f"Error: {result.get('error_message')}")
        else:
            print(f"\n❌ HTTP Error: {response.status_code}")
            
except FileNotFoundError:
    print("\n❌ Report.pdf not found in current directory")
    sys.exit(1)
except Exception as e:
    print(f"\n❌ Error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
