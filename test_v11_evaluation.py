import requests
import json

url = "http://127.0.0.1:8000/api/evaluate"

problem_statement = """create a detailed report on the proposed solution and implementation plan for the problem statement Offline AI-Powered RAG Knowledge Portal AI/ML & Natural Language Processing Challenge Expert 24 Hours Organizations generate huge amounts of internal knowledge (technical manuals, research papers, project reports, compliance docs). Searching these documents manually is inefficient, and cloud/internet-based solutions raise privacy and security concerns. Core Features 1. Document Upload & Indexing Multi-format support (PDF/DOCX/TXT) AI embeddings and preprocessing System indexing using AI embeddings 2. AI Model Integration Offline LLM implementation RAG pipeline (Retriever + Generator) Document-based response generation only 3. Interactive Chatbot Natural language queries Citation and source referencing Complete offline operation"""

print("=" * 80)
print("Testing V1.1 Refined Concept Extraction")
print("=" * 80)

try:
    with open("Report.pdf", "rb") as f:
        files = {"files": ("Report.pdf", f, "application/pdf")}
        
        data = {
            "assignment_type": "content",
            "problem_statement": problem_statement
        }
        
        print(f"\nSending request...")
        response = requests.post(url, files=files, data=data, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('status') == 'success' and result.get('results'):
                item = result['results'][0]
                print(f"\n✅ SUCCESS!")
                print(f"\nSubmission: {item['submission_id']}")
                print(f"Score: {item['final_score']}/{item['max_score']} ({item['percentage']}%)")
                print(f"\nFeedback ({len(item['feedback'])} items):")
                for fb in item['feedback']:
                    print(f"  {fb}")
                    
                # Check for improvements
                feedback_text = ' '.join(item['feedback'])
                print(f"\n{'='*80}")
                print("VERIFICATION:")
                print(f"{'='*80}")
                
                if 'huge' in feedback_text or 'expert' in feedback_text or 'statement' in feedback_text:
                    print("❌ Still showing generic tokens (huge/expert/statement)")
                else:
                    print("✅ Generic tokens filtered out successfully!")
                    
                if 'Missing:' in feedback_text or 'Missing key concepts:' in feedback_text:
                    print("✅ Missing concepts are being identified")
                else:
                    print("⚠️  No missing concepts shown")
                    
            else:
                print(f"\n❌ FAILED: {result.get('message')}")
                print(f"Error: {result.get('error_message')}")
        else:
            print(f"\n❌ HTTP Error: {response.status_code}")
            print(response.text)
            
except Exception as e:
    print(f"\n❌ Error: {type(e).__name__}: {e}")
