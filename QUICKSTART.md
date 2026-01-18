# Quick Start Guide

## 🚀 Run Demo (1 minute)

```bash
cd /path/to/mini-proj
python main.py
```

**What happens:**
- Evaluates 3 sample submissions
- Prints results to console
- Saves to `outputs/results.csv`

---

## 📝 Evaluate Your Own Submissions

### Step 1: Organize Files
Create a folder with your submissions:
```
my_submissions/
├── alice_submission.py
├── bob_submission.py
└── charlie_submission.txt
```

### Step 2: Create assignment.py
```python
from controller.orchestrator import Orchestrator
from utils.rubric import Rubric

# Load or create rubric
rubric = Rubric()

# Create orchestrator
orchestrator = Orchestrator(rubric)

# Evaluate submissions
results = orchestrator.evaluate_submissions(
    assignment_type="code",  # or "content" or "mixed"
    folder_path="./my_submissions",
    problem_statement="Your assignment description here...",
)

# Print results
for student, evaluation in results.items():
    print(f"{student}: {evaluation['final_score']}/100")
    for feedback in evaluation['combined_feedback']:
        print(f"  {feedback}")
```

### Step 3: Run
```bash
python assignment.py
```

---

## 📊 Supported Assignment Types

| Type | Input | Use Case |
|------|-------|----------|
| `"code"` | `.py` files | Programming assignments |
| `"content"` | `.txt` files | Essays, summaries, reflections |
| `"mixed"` | Both types | Hybrid assignments |

---

## 📤 Export Results

Results automatically saved to `outputs/` folder:

- **results.csv** - Summary view (1 row per student)
- **results_detailed.csv** - Detailed view (1 row per feedback item)

---

## 🎯 Output Explained

Each submission gets scored on:

### Code Assignments
- **Approach** (40%) - Does it solve the problem?
- **Readability** (20%) - Is it easy to understand?
- **Structure** (20%) - Is it well-organized?
- **Effort** (20%) - Is it complete and thought-out?

### Content Assignments
- **Coverage** (35%) - Does it address all concepts?
- **Alignment** (25%) - Does it match requirements?
- **Flow** (20%) - Is it logically organized?
- **Completeness** (20%) - Is it detailed with examples?

---

## ❓ FAQ

**Q: Can I modify the rubric?**
A: Yes! Create a custom rubric JSON and load it:
```python
rubric = Rubric.from_json("my_rubric.json")
```

**Q: Does it run student code?**
A: No, it only analyzes code statically (safe and fast).

**Q: Can I use with Python 2?**
A: No, Python 3.7+ required. Uses type hints and f-strings.

**Q: What about mixed submissions?**
A: One student can have both `student_alice.py` and `student_alice.txt`
The system matches by name and evaluates both.

**Q: How do I filter results?**
A: Open the CSV in Excel/Sheets and filter by score or keywords.

---

## 🛠️ Customize Feedback

Edit agent files to change heuristics:

- **code_agent.py** → Modify `_evaluate_*()` methods
- **content_agent.py** → Modify `_evaluate_*()` methods
- **aggregator_agent.py** → Modify `_apply_learning_oriented_normalization()`

---

## 💡 Tips

1. **Better problem statements** → Better code evaluation
2. **Include examples in problem** → Agents understand better
3. **Use detailed rubrics** → More accurate feedback
4. **Review weak scores** → Adjust heuristics if needed
5. **Keep feedback templates** → Easy to update

---

For full documentation, see `README.md`
