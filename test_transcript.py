"""Test the transcript evaluation endpoint with real data."""
import requests
import json

API = "http://127.0.0.1:8000/api/evaluate"

# Read the FULL VTT transcript (the user's real one)
# For testing, we'll use the sample lecture VTT
with open("test_submissions/transcript_test/sample_lecture.vtt") as f:
    vtt_text = f.read()

# Submit all 5 student summaries (txt + html)
files = [
    ("files", ("student_good.txt", open("test_submissions/transcript_test/student_good.txt", "rb"))),
    ("files", ("student_medium.txt", open("test_submissions/transcript_test/student_medium.txt", "rb"))),
    ("files", ("student_bad.txt", open("test_submissions/transcript_test/student_bad.txt", "rb"))),
    ("files", ("student_html_good.html", open("test_submissions/transcript_test/student_html_good.html", "rb"))),
    ("files", ("student_html_medium.html", open("test_submissions/transcript_test/student_html_medium.html", "rb"))),
]

data = {
    "assignment_type": "transcript",
    "transcript_text": vtt_text,
    "topic": "ML",
}

print("Sending evaluation request...")
resp = requests.post(API, data=data, files=files, timeout=120)
result = resp.json()

print(f"\nStatus: {result['status']}")
print(f"Message: {result['message']}")
print()

if result.get("results"):
    for r in sorted(result["results"], key=lambda x: x["final_score"], reverse=True):
        print(f"{'='*60}")
        print(f"Student: {r['submission_id']}")
        print(f"Score: {r['final_score']}/100")
        print(f"Feedback:")
        for fb in r.get("feedback", []):
            print(f"  {fb}")
        print()
    
    # Summary
    print(f"{'='*60}")
    s = result.get("summary", {})
    print(f"Summary: {s.get('total_submissions')} submissions")
    print(f"Average: {s.get('average_percentage'):.1f}%")
    print(f"Highest: {s.get('highest_score')}")
    print(f"Lowest: {s.get('lowest_score')}")
else:
    print(f"Error: {result.get('error_message', 'unknown')}")
