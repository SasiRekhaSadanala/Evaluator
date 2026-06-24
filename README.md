<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/FastAPI-0.100+-009688?style=for-the-badge&logo=fastapi&logoColor=white" />
  <img src="https://img.shields.io/badge/Next.js-14-black?style=for-the-badge&logo=next.js&logoColor=white" />
  <img src="https://img.shields.io/badge/PostgreSQL-15-336791?style=for-the-badge&logo=postgresql&logoColor=white" />
  <img src="https://img.shields.io/badge/Groq-LLaMA_3.1-F55036?style=for-the-badge&logo=meta&logoColor=white" />
  <img src="https://img.shields.io/badge/OpenRouter-Nemotron-76B900?style=for-the-badge&logo=nvidia&logoColor=white" />
  <img src="https://img.shields.io/badge/JWT-Auth-FB015B?style=for-the-badge&logo=jsonwebtokens&logoColor=white" />
  <img src="https://img.shields.io/badge/Transcript_Eval-VTT_Parser-E91E63?style=for-the-badge&logo=audioboom&logoColor=white" />
</p>

<h1 align="center">🎓 Evaluator 2.0</h1>
<h3 align="center">Intelligent AI-Powered Academic Assessment Platform</h3>

<p align="center">
  <em>An end-to-end system for evaluating student code, content, and lecture transcript summaries using AST analysis, LLM reasoning, semantic embeddings, automated test execution, plagiarism detection, and real-time student performance tracking — with a multi-agent scoring pipeline (CodeAgent, ContentAgent, AggregatorAgent), LLM-powered dynamic concept extraction, and an AI Study Coach, all managed through role-based teacher and student dashboards with JWT authentication.</em>
</p>

<p align="center">
  <strong>Built by</strong>: B Harsha Vardhan (23BDS015) · L Akash (23BDS031) · S Sasi Rekha (23BDS049) · SK Izhaar Ahmed (23BDS053)
</p>

---

## 📖 Table of Contents

1.  [What is Evaluator 2.0?](#-what-is-evaluator-20)
2.  [Key Features at a Glance](#-key-features-at-a-glance)
3.  [System Architecture](#-system-architecture)
4.  [How the Scoring Pipeline Works](#-how-the-scoring-pipeline-works)
    - [Step 1: File Upload & Parsing](#step-1-file-upload--parsing)
    - [Step 1a: Single-File Mixed Evaluation (Auto-Split)](#step-1a-single-file-mixed-evaluation-auto-split)
    - [Step 2: LLM Relevance Check](#step-2-llm-relevance-check)
    - [Step 3: Code Evaluation (Code Agent)](#step-3-code-evaluation-code-agent)
    - [Step 4: Content Evaluation (Content Agent)](#step-4-content-evaluation-content-agent)
    - [Step 5: Test Case Execution (Judge0 / Local)](#step-5-test-case-execution-judge0--local)
    - [Step 6: Score Aggregation](#step-6-score-aggregation)
    - [Step 7: Integrity Check (Plagiarism + AI Detection)](#step-7-integrity-check-plagiarism--ai-detection)
    - [Step 8: Student Tracking & Percentiles](#step-8-student-tracking--percentiles)
    - [Step 9: Review Queue](#step-9-review-queue)
5.  [Transcript Evaluation: Scoring Lecture Summaries](#-transcript-evaluation-scoring-lecture-summaries)
6.  [Tree-Sitter: How Code is Structurally Analyzed](#-tree-sitter-how-code-is-structurally-analyzed)
7.  [Semantic Embeddings: Understanding Meaning, Not Just Keywords](#-semantic-embeddings-understanding-meaning-not-just-keywords)
8.  [LLM Integration: Groq + OpenRouter](#-llm-integration-groq--openrouter)
9.  [Test Case Execution: Verifying Code Correctness](#-test-case-execution-verifying-code-correctness)
10. [Integrity System: Plagiarism & AI Detection](#-integrity-system-plagiarism--ai-detection)
11. [Review Queue: Human-in-the-Loop](#-review-queue-human-in-the-loop)
12. [Student Profile Tracking](#-student-profile-tracking)
13. [Frontend: The Teacher Dashboard](#-frontend-the-teacher-dashboard)
14. [Frontend: The Student Portal](#-frontend-the-student-portal)
15. [AI Study Coach](#-ai-study-coach)
16. [Authentication & Role-Based Access](#-authentication--role-based-access)
17. [CSV Export System](#-csv-export-system)
18. [API Reference](#-api-reference)
19. [Project Structure](#-project-structure)
20. [How to Run (Local Development)](#-how-to-run-local-development)
21. [Deployment (Render + Vercel)](#-deployment-render--vercel)
22. [Environment Variables](#-environment-variables)
23. [Tech Stack](#-tech-stack)
24. [Common Questions](#-common-questions)

---

## 🎯 What is Evaluator 2.0?

**Evaluator 2.0** is an intelligent academic assessment platform designed for **teachers and professors** who need to evaluate student submissions at scale. Instead of manually reading and grading dozens (or hundreds) of code files and written reports, the teacher uploads all submissions through a web interface, and the system automatically:

1. **Parses** each submission using AST (Abstract Syntax Tree) analysis
2. **Runs test cases** against code submissions to check correctness
3. **Checks relevance** — does the submission actually answer the question?
4. **Scores** based on approach, readability, structure, and effort
5. **Detects plagiarism** between students and flags AI-generated content
6. **Generates detailed, personalized feedback** for each student using Groq LLaMA 3.1
7. **Tracks student progress** over time with percentiles and trends
8. **Routes uncertain submissions** to a manual review queue for the teacher
9. **Evaluates lecture transcript summaries** — students summarize a VTT lecture, and the system scores coverage, depth, and expression using batch semantic embeddings
10. **Provides an AI Study Coach** — students can chat with an AI tutor that knows their weak areas

The system combines multiple AI techniques:
- **Tree-sitter** for understanding code structure at the syntax level
- **Sentence-transformers** (all-MiniLM-L6-v2) for understanding meaning through embeddings
- **Groq LLaMA 3.1 8B** for fast feedback generation and concept refinement
- **OpenRouter NVIDIA Nemotron** for code relevance checks
- **GPT-2 perplexity** for detecting AI-generated submissions
- **Judge0 / Local execution** for actually running code against test cases
- **Auto-split parser** for single-file mixed submissions (code + explanation in one file)
- **VTT transcript parser** with LLM-refined dynamic concept extraction

---

## ✨ Key Features at a Glance

| Feature | What It Does | Technology Used |
|---|---|---|
| 🧠 **AST-Aware Scoring** | Understands code structure (loops, functions, nesting) | Tree-sitter |
| 🧪 **Test Case Execution** | Runs student code against test inputs/outputs | Judge0 API + Local Python/C++ fallback |
| 💬 **AI Feedback** | Generates personalized, learning-oriented comments | Groq LLaMA 3.1 8B Instant |
| 🔍 **Relevance Checking** | Verifies submission actually answers the question | OpenRouter NVIDIA Nemotron |
| 🕵️ **Plagiarism Detection** | Compares submissions using fingerprinting + similarity | SequenceMatcher + Fingerprinting |
| 🤖 **AI Content Detection** | Flags likely AI-generated submissions | GPT-2 Perplexity Analysis |
| 📊 **Semantic Scoring** | Understands paraphrased content, not just keywords | all-MiniLM-L6-v2 Embeddings |
| 📈 **Student Tracking** | Performance history, trends, percentile ranking | PostgreSQL + NumPy |
| 👨‍🏫 **Review Queue** | Teacher reviews flagged/uncertain submissions | DB + in-memory queue |
| 🌙 **Dark-Mode Dashboard** | Beautiful, enterprise-grade teacher UI | Next.js 14 + Tailwind CSS |
| 🎓 **Student Portal** | Personal dashboard, submissions, progress, leaderboard | JWT Auth + Role-based routing |
| 🤝 **AI Study Coach** | Streaming chat tutor aware of student's weak areas | Groq LLaMA 3.1 + streaming responses |
| 🔐 **JWT Authentication** | Role-based access control (teacher/student) | PyJWT + SHA-256 |
| 📄 **Single-File Mixed Eval** | One file with code + explanation → auto-split | Language-aware parser |
| 🎙 **Transcript Evaluation** | Score summaries against VTT lecture transcripts | Batch embeddings + LLM-refined concepts |
| 📊 **Batch Processing** | Evaluate 120+ students using batch-encoded embeddings | all-MiniLM-L6-v2 + NumPy |
| 📥 **CSV Export** | Export results with /10 scores, rich LLM feedback | Custom CSV with real AI feedback |
| 🚀 **Cloud Deployment** | Production-ready on Render + Vercel + Neon | Environment-based configuration |

---

## 🏗 System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        FRONTEND (Next.js 14)                        │
│                                                                     │
│  ┌─────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────────┐ │
│  │  Login  │  │  Upload  │  │ Results  │  │    Review Queue      │ │
│  │  Page   │  │   Page   │  │Dashboard │  │                      │ │
│  └────┬────┘  └────┬─────┘  └────┬─────┘  └────────┬─────────────┘ │
│       │            │             │                  │               │
│  ┌────▼────────────────────────────────────────────────────────────┐│
│  │  STUDENT PORTAL                                                 ││
│  │  ┌──────────┐ ┌────────────┐ ┌──────────┐ ┌────────┐ ┌──────┐ ││
│  │  │Dashboard │ │Submissions │ │ Progress │ │Leader  │ │Coach │ ││
│  │  │          │ │            │ │          │ │board   │ │(Chat)│ ││
│  │  └──────────┘ └────────────┘ └──────────┘ └────────┘ └──────┘ ││
│  └────────────────────────────────────────────────────────────────┘│
└───────┼──────────────┼─────────────┼──────────────────┼────────────┘
        │              │             │                  │
        ▼              ▼             ▼                  ▼
┌─────────────────────── REST API (FastAPI) ──────────────────────────┐
│  POST /api/auth/login      POST /api/evaluate                       │
│  GET  /api/portal/*        GET  /api/evaluations/history            │
│  GET  /api/reviews         POST /api/reviews/:id/override           │
│  GET  /api/students/:id    POST /api/portal/chat (streaming)        │
└───────┬─────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────── ORCHESTRATOR ────────────────────────────────┐
│                                                                     │
│   ┌────────────┐    ┌─────────────┐    ┌────────────────────┐      │
│   │ Code Agent │    │Content Agent│    │ Aggregator Agent   │      │
│   │            │    │             │    │                    │      │
│   │ • AST      │    │ • Keywords  │    │ • Weighted average │      │
│   │ • Approach │    │ • Embeddings│    │ • Normalization    │      │
│   │ • Readabi. │    │ • Factual   │    │ • Score curving    │      │
│   │ • Structur.│    │ • Coverage  │    │                    │      │
│   │ • Effort   │    │ • Alignment │    └────────────────────┘      │
│   └──────┬─────┘    └──────┬──────┘                                │
│          │                 │                                        │
│   ┌──────▼─────────────────▼──────┐                                │
│   │        SHARED SERVICES        │                                │
│   │ • LLM Service                 │    ┌─────────────────────────┐ │
│   │   ├─ Groq (LLaMA 3.1 8B)     │    │   INTEGRITY SERVICE     │ │
│   │   └─ OpenRouter (Nemotron)    │    │ • Plagiarism detection  │ │
│   │ • Tree-sitter Parser          │    │ • AI content detection  │ │
│   │ • Embedding Service           │    │ • Perplexity scoring    │ │
│   │ • Judge0 / Local Runner       │    └────────────┬────────────┘ │
│   │ • Rubric Manager              │                                │
│   │ • File Parser (auto-split)    │                                │
│   └───────────────────────────────┘                                │
│                                                      │              │
│   ┌──────────────────────────────────────────────────▼────────────┐ │
│   │                    STUDENT TRACKER                            │ │
│   │  • Score history  • Percentile ranking  • Trend analysis     │ │
│   └──────────────────────────────────────────────────────────────┘ │
│                                                                     │
│   ┌──────────────────────────────────────────────────────────────┐  │
│   │                     REVIEW QUEUE                              │ │
│   │  • Flags uncertain verdicts  • Routes to teacher dashboard   │ │
│   └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────── DATA LAYER ──────────────────────────────────┐
│  PostgreSQL (Neon)     In-Memory Fallback        File System        │
│  • evaluation_results  • review queue           • CSV exports       │
│  • review_queue        • submission index       • embedding cache   │
│  • student_scores      • users (auth)                               │
│  • submission_index                                                  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🔄 How the Scoring Pipeline Works

When a teacher uploads student submissions, the system processes them through a **9-step pipeline**. Here's exactly what happens at each step:

### Step 1: File Upload & Parsing

**Where**: `backend/app/routes/evaluate.py` → `backend/core/controller/orchestrator.py`

The teacher uploads one or more files (`.py`, `.cpp`, `.txt`, etc.) through the web interface along with:
- **Assignment type**: `code`, `content`, `mixed`, or `transcript`
- **Problem statement**: The question that was asked
- **Test cases** (optional): JSON array like `[{"input": "1 2 3", "output": "6"}]`
- **Lecture transcript** (for transcript mode): A `.vtt` file
- **Topic tag** (optional): For tracking student progress by subject

The system:
1. Saves uploaded files to a temporary folder
2. Reads each file's content using `file_parser.py`
3. Extracts the student name from the filename (e.g., `student_alice.py` → `student_alice`)
4. Routes to the appropriate evaluation agent based on assignment type

### Step 1a: Single-File Mixed Evaluation (Auto-Split)

**Where**: `backend/core/utils/file_parser.py` → `split_mixed_content()`

In traditional mixed mode, students submit two files — one for code, one for explanation. But many students prefer to put everything in **one file**. Evaluator 2.0 handles this automatically:

| Input File Type | Code Extracted From | Content Extracted From |
|---|---|---|
| `.py` (Python) | Full file → Code Agent | Docstrings + standalone comments → Content Agent |
| `.cpp` (C++) | Full file → Code Agent | Block comments (`/* */`) + consecutive `//` lines → Content Agent |
| `.txt` / `.md` | Fenced code blocks (` ``` `) + indented blocks → Code Agent | Everything else (prose) → Content Agent |
| `.pdf` | Fenced code blocks from extracted text → Code Agent | Prose sections → Content Agent |

> **No student action required**: Students don't need to format their files in any special way. The parser handles Python docstrings, C++ block comments, and markdown code fences automatically.

### Step 2: LLM Relevance Check

**Where**: `utils/llm_service.py` → `check_relevance()`

Before scoring anything, the system asks **OpenRouter NVIDIA Nemotron**: *"Does this submission actually answer the question that was asked?"*

The LLM returns one of **four verdicts**:

| Verdict | Meaning | Effect on Score |
|---|---|---|
| `RELEVANT` | Yes, this answers the question | Full scoring (no penalty) |
| `PARTIAL` | Somewhat related but incomplete | Reduced scoring (0.6x multiplier) |
| `UNCERTAIN` | AI isn't confident | Score as normal (no penalty) |
| `IRRELEVANT` | Completely off-topic | Approach score = 0, other scores × 0.1 |

> **Why UNCERTAIN ≠ IRRELEVANT**: When the LLM can't decide (e.g., API is rate-limited), it would be unfair to penalize the student. The system gives the benefit of the doubt and scores normally. Only a confident `IRRELEVANT` verdict triggers penalties.

### Step 3: Code Evaluation (Code Agent)

**Where**: `backend/core/agents/code_agent.py`

This is the core scoring engine for code submissions. It evaluates **four dimensions**:

#### 3a. Approach Score (40% weight)

Measures how well the student's code solves the problem using three strategies:

1. **Function Name Matching**: Tree-sitter extracts function names from the code. If a function name matches a keyword from the problem statement (e.g., `threeSum` matches "threeSum" in the problem), it scores 90-100.
2. **Keyword Overlap**: Extracts meaningful keywords from the problem statement (5+ characters, excluding stopwords) and checks how many appear in the code.
3. **LLM Verdict**: If the LLM confirmed `RELEVANT`, the approach score is boosted.

**If test cases are provided:**
```
approach = 0.4 × relevance_score + 0.6 × test_pass_rate
```

**Score floor from tests:**
```
If student passes 80% of tests but has messy code:
  test_floor = test_pass_rate × 90 (max 90)
  total_score = max(total_score, test_floor)
```
Working code > pretty code. If the code WORKS, it shouldn't get a low score just because variable names aren't perfect.

**Wrong-problem cap:**
```
If LLM says IRRELEVANT: total_score = min(total_score, 25)
```

#### 3b. Readability Score (20% weight)
- Line length (are lines under 80 characters?)
- Comments and docstrings present?
- Naming conventions (camelCase, snake_case consistency)
- Type hints (Python), const usage (C++)

#### 3c. Structure Score (20% weight)
- Number of functions/classes (modularity)
- Variable assignments (structured logic)
- Nesting depth (deep nesting shows algorithmic complexity)
- Control flow (loops, conditions, error handling)

#### 3d. Effort Score (20% weight)
- Lines of code (minimum viable effort)
- Unique identifiers (diverse variable names)
- Nesting complexity (takes more effort to write)
- Tree-sitter composite complexity score (0-100)

```
Final Code Score = approach × 0.40 + readability × 0.20 + structure × 0.20 + effort × 0.20
```

### Step 4: Content Evaluation (Content Agent)

**Where**: `backend/core/agents/content_agent.py`

For written submissions, the system evaluates **five dimensions**:

| Dimension | Weight | What It Measures |
|---|---|---|
| **Factual Accuracy** | 40% | Semantic similarity to ideal reference answer (embedding cosine similarity) |
| **Coverage** | 30% | Does it mention key concepts from the reference? (keyword + semantic) |
| **Alignment** | 15% | Does it meet the problem statement requirements? |
| **Flow** | 8% | Is the writing logically organized with transitions? |
| **Completeness** | 7% | Is it detailed enough? Does it include examples? |

**Coverage scoring uses two methods in parallel:**
1. **Keyword matching** (always available): Checks if key terms appear in the text
2. **Semantic embeddings** (if sentence-transformers is installed): Uses all-MiniLM-L6-v2 to understand that "binary search tree" and "BST" mean the same thing

**Special rules:**
- If coverage = 0 AND LLM says irrelevant → **score = 0** (off-topic submission)
- If plagiarism detected → **capped at 20/100**

### Step 5: Test Case Execution (Judge0 / Local)

**Where**: `backend/core/services/judge0_service.py`

If the teacher provides test cases, the system **actually runs the student's code** against them.

```
Test cases provided?
├── NO  → Skip test execution (static analysis only)
└── YES → Is it a "class Solution" pattern?
          ├── YES (Python) → Auto-wrap with stdin parser + method caller
          ├── YES (C++)    → Auto-wrap with #include headers + main() generator
          └── NO           → Run code as-is
          ↓
          Is Judge0 reachable? (HTTP ping to /about endpoint)
          ├── YES → Submit to Judge0 API (sandboxed, supports all languages)
          └── NO  → Is the language Python?
                    ├── YES → Run locally via Python subprocess
                    └── NO  → Is the language C++?
                              ├── YES → Compile with g++ -std=c++17 and run locally
                              └── NO  → Skip test execution
```

**LeetCode-style auto-wrapping** works for both Python and C++. The system detects `class Solution` patterns and automatically generates test harness code.

### Step 6: Score Aggregation

**Where**: `backend/core/agents/aggregator_agent.py`

The Aggregator Agent combines all individual agent outputs into a final score:

1. **Normalize** each agent's score to 0-100 scale
2. **Apply weights** from the rubric (default: code = 60%, content = 40% for mixed)
3. **Apply learning-oriented normalization**: A gentle curve that pushes scores toward the mid-range

```python
if raw_score > 85:
    final = 85 + (raw_score - 85) * 0.3    # Compress excellence
elif raw_score < 30:
    final = 30 + (raw_score - 30) * 0.5    # Lift failing scores slightly
else:
    final = raw_score                       # Middle range: keep as-is
```

### Step 7: Integrity Check (Plagiarism + AI Detection)

**Where**: `backend/core/services/integrity_service.py`

1. **Exact match detection**: Code fingerprinting (hash after normalizing whitespace/comments)
2. **Fuzzy similarity**: `SequenceMatcher` — similarity > 85% is suspicious; > 95% is near-certain copying
3. **AI-generation detection**: GPT-2 perplexity scoring. Human writing typically has perplexity > 50; AI-generated text often falls below 20-30.

> **Important**: Integrity checks **never auto-zero a score**. They only produce a `flag_score` and `flag_reasons`. High-flag submissions are routed to the teacher's review queue.

### Step 8: Student Tracking & Percentiles

**Where**: `backend/core/services/student_tracker.py`

After each evaluation:
1. **Record the score** in the database with topic tag
2. **Compute improvement delta** against the student's last 5 submissions on the same topic
3. **Determine trend**: `improving` (>5 point gain), `declining` (>5 point drop), or `stable`
4. **Compute percentile**: Where does this student rank in the class?

### Step 9: Review Queue

**Where**: `backend/core/services/review_queue.py`

Submissions are automatically flagged for teacher review when:

| Trigger | Condition | Why |
|---|---|---|
| `UNCERTAIN` | LLM couldn't determine relevance | Teacher should verify |
| `FLAG` | Integrity flag_score > 0.7 | Possible plagiarism or AI-generated |
| `BOUNDARY` | Score within 5 points of 25, 50, or 75 | Grade boundary — teacher should confirm |
| `LOW_SCORE` | Final score < 10 | Likely an evaluation error |

The teacher can review and **override the score** with their own assessment.

---

## 🎙 Transcript Evaluation: Scoring Lecture Summaries

**Where**: `backend/core/utils/vtt_parser.py` → `backend/core/controller/orchestrator.py`

A dedicated evaluation mode for **lecture transcript summaries**. Teachers upload a `.vtt` lecture transcript and student HTML/text files containing their summaries. The system scores each summary against the lecture content using semantic embeddings.

### How It Works

```
┌────────────────────────────────────────────────────────────────┐
│  TEACHER UPLOADS                                                │
│  1. Lecture transcript (.vtt file)                              │
│  2. Student summaries (120+ .html/.txt files)                   │
└──────────┬─────────────────────────────────────────────────────┘
           ▼
┌────────────────────────────────────────────────────────────────┐
│  STEP 1: Parse VTT Transcript                                   │
│  • Strip timestamps, speaker labels, [Music] tags               │
│  • Merge cue text into clean paragraph form                     │
│  • Output: single clean transcript string                       │
└──────────┬─────────────────────────────────────────────────────┘
           ▼
┌────────────────────────────────────────────────────────────────┐
│  STEP 2: Two-Phase Concept Extraction                           │
│                                                                  │
│  Phase 1 — TF-IDF Candidate Extraction (20 terms):              │
│  • Mine 2-3 word technical phrases from transcript               │
│  • Score single words with TF × IDF × tech_boost                │
│  • 250+ filler words filtered out                                │
│  • Stem-aware deduplication                                      │
│                                                                  │
│  Phase 2 — LLM Concept Refinement (Groq):                       │
│  • Send 20 candidates + transcript snippet to Groq              │
│  • LLM filters to genuinely teachable concepts (5-12)           │
│  • Anti-hallucination: only keeps terms from original candidates │
│  • Fallback: TF-IDF top 10 if LLM fails                        │
└──────────┬─────────────────────────────────────────────────────┘
           ▼
┌────────────────────────────────────────────────────────────────┐
│  STEP 3: Batch Score All Students (ONE encode call)             │
│  • Encode all concepts → 384-dim vectors (one batch)            │
│  • Split each summary into sentences                            │
│  • Encode ALL sentences from ALL students → one batch call      │
│  • Cosine similarity: each sentence × each concept              │
│  • Threshold: 0.30 (phrases) / 0.35 (single words)             │
│  • Union: semantic + keyword matching for robustness            │
│  • Output: matched/missing concepts per student                 │
└──────────┬─────────────────────────────────────────────────────┘
           ▼
┌────────────────────────────────────────────────────────────────┐
│  STEP 4: Multi-Criteria Scoring                                 │
│                                                                 │
│  Score/10 = Coverage(35%) + Depth(15%) + Expression(10%)        │
│           + Attempt(30%) + Base(10%)                            │
│                                                                 │
│  • Coverage: % of key concepts found (dynamic count, not 10)   │
│  • Depth: explains WHY, not just WHAT (causal language)         │
│  • Expression: sentence structure, punctuation, readability     │
│  • Attempt: submit 10+ words → full 30% (rewards effort)       │
│  • Base: 1/10 guaranteed for any submission                     │
│  • Floor: minimum 3.5/10 for genuine attempts                   │
└──────────┬─────────────────────────────────────────────────────┘
           ▼
┌────────────────────────────────────────────────────────────────┐
│  STEP 5: Rich Feedback Generation (Groq LLaMA 3.1)             │
│  • Overall assessment (Excellent/Good/Adequate/Needs Work)      │
│  • 🤖 AI Analysis: personalized paragraph per student           │
│  • Specific strengths identified                                │
│  • Topics covered and missing (dynamic count)                   │
│  • Actionable improvement suggestions                           │
└──────────┬─────────────────────────────────────────────────────┘
           ▼
┌────────────────────────────────────────────────────────────────┐
│  STEP 6: Integrity + Export                                     │
│  • Cross-student plagiarism check                               │
│  • CSV export with real LLM feedback (not templates)            │
│  • Dashboard display with percentile ranking                    │
└────────────────────────────────────────────────────────────────┘
```

### Why Two-Phase Concept Extraction?

**The problem**: Pure TF-IDF often selects generic words like "data set", "precision", "classified" — students get penalized for not mentioning terms that aren't real concepts.

**The fix**: TF-IDF oversamples 20 candidates (fast, deterministic), then Groq filters to only genuinely teachable concepts (smart, contextual). The LLM acts as a quality gate, not a generator.

**Impact**: A student covering 5 real concepts scores 5/6 (83%) instead of 5/10 (50%).

### Performance: Batch Processing 120+ Students

The key optimization is **batch encoding**:
1. Collect ALL sentences from ALL 120 students into one list
2. Encode them in a **single `model.encode()` call** with `batch_size=128`
3. Use NumPy matrix operations for similarity computation

| Approach | Time for 120 students |
|---|---|
| One-by-one encoding | ~6+ minutes |
| Batch encoding | **~30-60 seconds** |

---

## 🌳 Tree-Sitter: How Code is Structurally Analyzed

**Where**: `backend/core/services/treesitter_parser.py`

Tree-sitter is a **parser generator tool** that builds real syntax trees from source code. Unlike regex or keyword matching, tree-sitter understands code the same way a compiler does.

### What metrics does tree-sitter extract?

| Metric | What It Measures | How It's Used |
|---|---|---|
| `line_count` | Total lines of code | Effort scoring |
| `function_count` | Number of function definitions | Structure scoring |
| `class_count` | Number of class definitions | Structure scoring |
| `comment_count` | Number of comment lines | Readability scoring |
| `loop_count` | Number of for/while loops | Approach scoring |
| `condition_count` | Number of if/elif/else | Approach scoring |
| `try_except_count` | Number of error-handling blocks | Structure scoring |
| `import_count` | Number of import statements | Structure scoring |
| `variable_count` | Number of variable assignments | Structure scoring |
| `max_nesting_depth` | Deepest level of nested blocks | Complexity scoring |
| `unique_identifiers` | Count of unique variable/function names | Effort scoring |
| `function_names` | List of all function/method names | Approach scoring (name matching) |
| `complexity_score` | Composite 0-100 metric | Final scoring |

### The Complexity Score Formula

```python
complexity_score = min(100, (
    nesting_depth × 10 +           # Deep nesting = complex algorithm
    unique_identifiers × 2.5 +     # Diverse names = thoughtful code
    (conditions + loops) × 5       # Control flow = algorithmic thinking
))
```

**Supported Languages**: Python (`.py`) and C++ (`.cpp`)

---

## 🧮 Semantic Embeddings: Understanding Meaning, Not Just Keywords

**Where**: `backend/core/services/embedding_service.py`

The system uses **all-MiniLM-L6-v2** (a sentence-transformer model) to convert text into 384-dimensional vectors. Texts with similar meanings end up close together in this vector space.

```
"Binary Search Tree" → [0.23, -0.11, 0.87, ...]  (384 numbers)
"BST"                → [0.21, -0.09, 0.85, ...]  (very similar vector!)
"Hash Table"         → [0.67, 0.45, -0.12, ...]  (very different vector)
```

### Two scoring methods:

1. **Semantic Coverage Score**: Cosine similarity between student text and ideal answer. Score range: 0-100.
2. **Concept Hit Rate**: For each key concept, finds the best-matching sentence in the student's text. If similarity > threshold, it's a "hit".

### Embedding cache

Ideal answer embeddings are computed once and cached to disk (as `.npy` files) so subsequent evaluations of the same assignment are faster.

> **Lazy loading**: The embedding model is only loaded when needed, with `ImportError` guards so servers without `sentence-transformers` installed don't crash — they just skip semantic scoring.

---

## 🤖 LLM Integration: Groq + OpenRouter

**Where**: `utils/llm_service.py`

### What the LLMs Do

| LLM | Model | Purpose | Rate Limit |
|---|---|---|---|
| **Groq** | LLaMA 3.1 8B Instant | Feedback generation, concept refinement, AI Study Coach | 25 req/min |
| **OpenRouter** | NVIDIA Nemotron 30B (free) | Code relevance checking (RELEVANT/PARTIAL/IRRELEVANT) | 20 req/min |

### Groq Configuration
```python
API: https://api.groq.com/openai/v1/chat/completions
Model: llama-3.1-8b-instant
Temperature: 0.3 (deterministic-ish)
Max tokens: 500
Retry: On 429, wait 15 seconds and retry once
```

### OpenRouter Configuration
```python
API: https://openrouter.ai/api/v1/chat/completions
Model: nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free
Temperature: 0.2 (more deterministic for yes/no judgments)
Max tokens: 200
```

### Rate Limiting Architecture

```python
class _RateLimiter:
    # Groq: 60/25 = 2.4 seconds minimum between calls
    # OpenRouter: 60/20 = 3.0 seconds minimum between calls
    # Prevents 429 errors that would crash batch evaluation
```

### Fallback Strategy

Every LLM call is wrapped in try/except with deterministic fallbacks:
- Concept refinement → falls back to TF-IDF top 10
- Relevance check → falls back to keyword-based heuristic  
- Feedback generation → falls back to rule-based template feedback
- The system **never crashes** due to LLM failures

---

## 🧪 Test Case Execution: Verifying Code Correctness

**Where**: `backend/core/services/judge0_service.py`

### How Teachers Provide Test Cases

```json
[
  {"input": "-1 0 1 2 -1 -4", "output": "[[-1, -1, 2], [-1, 0, 1]]"},
  {"input": "0 1 1", "output": "[]"},
  {"input": "0 0 0", "output": "[[0, 0, 0]]"}
]
```

Both `{"input", "output"}` and `{"stdin", "expected_output"}` formats are accepted.

### C++ LeetCode Auto-Wrapping

The system detects `class Solution` patterns and automatically wraps with:
1. Required `#include` headers
2. `using namespace std;`
3. Parsed method signature (parameter types via regex)
4. Generated `main()` function with stdin parsing
5. Output formatting matching expected format

### Local Fallback

When Judge0 is unavailable:
- **Python**: `subprocess` execution with sandboxing
- **C++**: Compile with `g++ -std=c++17 -O2`, execute as subprocess
- All temporary files cleaned up afterward

---

## 🕵️ Integrity System: Plagiarism & AI Detection

**Where**: `backend/core/services/integrity_service.py`

### Plagiarism Detection
```
Student Code → Normalize (strip whitespace, comments) → Fingerprint (MD5 hash)
                                                              │
                                           ┌──────────────────┤
                                           ▼                  ▼
                                     Exact Match?      Fuzzy Similarity
                                     (hash lookup)    (SequenceMatcher)
```

### AI-Generated Content Detection

Uses **GPT-2 perplexity** as a signal:

| Perplexity Score | Interpretation | Flag Action |
|---|---|---|
| > 50 | Likely human-written | No flag |
| 25 - 40 | Moderate AI likelihood | `flag_score += 0.7` |
| < 25 | High AI likelihood | `flag_score += 1.0` |

> GPT-2 perplexity is lazy-loaded with ImportError guards — servers without PyTorch skip this check gracefully.

---

## 👨‍🏫 Review Queue: Human-in-the-Loop

**Where**: `backend/core/services/review_queue.py` + `frontend/app/review/page.tsx`

The system uses a **"flag, don't punish"** philosophy:
1. Suspicious submissions are **flagged** and queued for review
2. The teacher sees **why** it was flagged
3. The teacher can **override the score** with their own assessment
4. The original AI score is preserved for tracking

**Dual storage**: PostgreSQL (persistent) + in-memory dictionary (fallback).

---

## 📈 Student Profile Tracking

**Where**: `backend/core/services/student_tracker.py`

| Metric | Description |
|---|---|
| **Score History** | Every score with timestamp and topic tag |
| **Improvement Delta** | Change vs. average of last 5 submissions |
| **Trend** | `improving`, `declining`, or `stable` |
| **Percentile** | Class ranking (0-100) |
| **Skill Breakdown** | Average score per topic tag |
| **Cumulative GPA** | Letter grade + GPA on 4.0 scale |

### Grade Scale

| Score | Grade | GPA |
|---|---|---|
| 93-100 | A | 4.0 |
| 90-92 | A- | 3.7 |
| 87-89 | B+ | 3.3 |
| 83-86 | B | 3.0 |
| 80-82 | B- | 2.7 |
| 77-79 | C+ | 2.3 |
| 73-76 | C | 2.0 |
| 70-72 | C- | 1.7 |
| 60-69 | D-D+ | 0.7-1.3 |
| < 60 | F | 0.0 |

---

## 🖥 Frontend: The Teacher Dashboard

Built with **Next.js 14**, **TailwindCSS**, and the **"Obsidian Scholar"** design system — a dark-mode, data-dense interface.

### Pages

| Page | Path | Purpose |
|---|---|---|
| **Landing** | `/` | Marketing page with features, workflow demo, CTA |
| **Login** | `/login` | Role-based login (Student/Teacher toggle) |
| **Upload** | `/upload` | Upload files, set problem statement, paste test cases |
| **Results** | `/results` | Dashboard with all evaluation results, scores, feedback |
| **Review Queue** | `/review` | Review flagged submissions, override scores |
| **Student Profile** | `/student/[id]` | Individual student dashboard with history and trends |

### Design System
- **Background**: Deep obsidian (#0A0A12)
- **Surface layers**: Four tonal levels for depth
- **Primary accent**: Violet (#A78BFA) for interactive elements
- **Semantic colors**: Emerald (success), Coral (warning), Amber (caution)
- **Typography**: JetBrains Mono for code, Inter/system fonts for UI

---

## 🎓 Frontend: The Student Portal

Students access their portal at `/portal` after logging in.

### Student Pages

| Page | Path | Purpose |
|---|---|---|
| **Dashboard** | `/portal` | GPA, percentile, recent submissions, skill breakdown, achievements |
| **My Submissions** | `/portal/submissions` | Full history with expandable AI feedback |
| **Progress** | `/portal/progress` | Score trend chart, cumulative grade, topic-wise development |
| **Leaderboard** | `/portal/leaderboard` | Anonymized class ranking — student sees own position highlighted |
| **AI Coach** | `/portal/coach` | Streaming AI study coach + improvement plan generator |

### Privacy Controls

| Data | Student Access | How |
|---|---|---|
| Own scores & feedback | ✅ | Scoped by `student_id` in JWT |
| Own history & trends | ✅ | Filtered via ID resolver |
| Other students' names | ❌ | Shown as "Student #N" |
| Other students' scores | ❌ | Only anonymized averages |
| Integrity flag details | ❌ | Shows "Under Review" only |
| Teacher features | ❌ | `require_student` dependency → 403 |

### Dynamic Achievements
- **Top 10%** / **Top 25%** — class percentile ranking
- **On the Rise** — improving trend detected
- **Dedicated Submitter** — 10+ submissions completed
- **Near Perfect Score** — scored 95+ on any submission

---

## 🤝 AI Study Coach

**Where**: `backend/app/routes/chat_routes.py` + `frontend/app/portal/coach/page.tsx`

A streaming AI chatbot that knows each student's performance history.

### How It Works

```
Student: "How can I improve my ML assignment?"

System Context (auto-injected):
- Student's past scores, weak areas, submission history
- Missing concepts from recent evaluations
- Lecture transcript concepts

Groq LLaMA 3.1 Response (streamed):
"Based on your last submission (6.5/10), you missed key concepts 
like cross-validation and feature scaling. Here's a focused study plan:
1. Review StandardScaler — it normalizes features before training...
2. Practice k-fold cross validation — it prevents overfitting..."
```

### Features
- **Streaming responses** — tokens appear as they're generated
- **Context-aware** — knows student's weak areas from evaluation history
- **Improvement plan generator** — one-click personalized study plan
- **Chat status indicator** — shows if Groq backend is available

---

## 🔐 Authentication & Role-Based Access

**Where**: `backend/app/middleware/auth.py` + `backend/app/routes/auth_routes.py`

```
Login Request (POST /api/auth/login)
├── Role: Teacher? → Validates against seeded teacher account
└── Role: Student? → Auto-creates account on first login
    ↓
JWT Token Issued (24-hour expiry)
├── Contains: username, role, student_id, display_name
└── Stored in browser localStorage
    ↓
Subsequent API Requests
├── Authorization: Bearer <token>
├── Teacher routes → require_teacher dependency
└── Student routes → require_student dependency (403 for teachers)
```

### Default Credentials

| Role | Username | Password | Notes |
|---|---|---|---|
| Teacher | `teacher` | `teacher` | Auto-seeded on startup |
| Student | any | same as username | Auto-created on first login |

---

## 📥 CSV Export System

**Where**: `backend/core/utils/csv_export.py`

### Two export formats:

**Summary CSV (`results.csv`):**
```
student_name, score, concept_coverage, concepts_matched, feedback, summary_text
```

**Detailed CSV (`results_detailed.csv`):**
```
student_name, score, concept_coverage, concepts_matched, 
topics_covered, topics_missing, feedback, summary_text
```

The feedback column includes the **actual LLM-generated feedback** (stripped of emojis/markdown for CSV cleanliness), not generic templates. Students get the same rich, personalized AI analysis in the CSV that they see on the web dashboard.

---

## 📡 API Reference

### Authentication Endpoints

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/api/auth/login` | None | Login with username/password, returns JWT |
| `GET` | `/api/auth/me` | Bearer | Get current user info from token |

### Core Endpoints (Teacher)

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/api/evaluate` | None* | Upload and evaluate submissions |
| `GET` | `/api/evaluations/history` | None* | Retrieve all past evaluation results |
| `DELETE` | `/api/evaluations/clear-all?confirm=true` | None* | Clear ALL evaluation data |
| `GET` | `/api/download/{filename}` | None | Download CSV report |
| `GET` | `/api/reviews` | None* | Get pending review queue items |
| `POST` | `/api/reviews/{id}/override` | None* | Teacher overrides a score |
| `GET` | `/api/students/{id}/profile` | None* | Get student's complete profile |
| `GET` | `/health` | None | Health check with DB and LLM status |

### Student Portal Endpoints

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/api/portal/dashboard` | Student | Student's personal dashboard |
| `GET` | `/api/portal/submissions` | Student | All evaluated submissions |
| `GET` | `/api/portal/progress` | Student | Score trends and skill breakdown |
| `GET` | `/api/portal/leaderboard` | Student | Anonymized class ranking |
| `POST` | `/api/portal/chat` | Student | AI Study Coach (streaming) |
| `POST` | `/api/portal/improvement-plan` | Student | Personalized improvement plan |
| `GET` | `/api/portal/chat/status` | Student | Chat backend availability |

### POST /api/evaluate — Request Format

```
Content-Type: multipart/form-data

Fields:
  files[]            - Student submission files (required)
  assignment_type    - "code" | "content" | "mixed" | "transcript" (required)
  problem_statement  - The question asked (recommended)
  test_cases         - JSON array (optional)
  rubric_content     - Custom rubric JSON (optional)
  topic              - Topic tag for tracking (optional)
  transcript_file    - VTT lecture file (for transcript mode)
```

---

## 📁 Project Structure

```
Evaluator/
├── backend/
│   ├── app/
│   │   ├── main.py                    # FastAPI application entry point + CORS config
│   │   ├── config.py                  # Application configuration
│   │   ├── middleware/
│   │   │   └── auth.py                # JWT auth middleware + role-based dependencies
│   │   ├── routes/
│   │   │   ├── evaluate.py            # POST /api/evaluate (main endpoint)
│   │   │   ├── evaluations.py         # GET /api/evaluations/history, DELETE clear-all
│   │   │   ├── auth_routes.py         # POST /api/auth/login, GET /api/auth/me
│   │   │   ├── student_portal_routes.py # GET /api/portal/* (student-scoped endpoints)
│   │   │   ├── chat_routes.py         # POST /api/portal/chat (AI Study Coach)
│   │   │   ├── review_routes.py       # GET/POST /api/reviews
│   │   │   ├── student_routes.py      # GET /api/students/:id/profile
│   │   │   └── submissions.py         # Submission management routes
│   │   ├── schemas/
│   │   │   ├── request.py             # Pydantic models (TestCase, RubricConfig, etc.)
│   │   │   ├── evaluation.py          # Evaluation response schemas
│   │   │   └── submission.py          # Submission schemas
│   │   └── services/
│   │       ├── evaluator.py           # Service layer (request → orchestrator adapter)
│   │       ├── evaluation_service.py  # Evaluation business logic
│   │       └── submission_service.py  # Submission management service
│   │
│   └── core/
│       ├── agents/
│       │   ├── base_agent.py          # Abstract base class for all agents
│       │   ├── code_agent.py          # Code evaluation (AST + approach + readability)
│       │   ├── content_agent.py       # Content evaluation (factual + coverage + alignment)
│       │   └── aggregator_agent.py    # Combines agent outputs into final score
│       │
│       ├── controller/
│       │   └── orchestrator.py        # Main pipeline coordinator (all 4 eval types)
│       │
│       ├── services/
│       │   ├── database.py            # PostgreSQL connection + schema (SSL for Neon)
│       │   ├── treesitter_parser.py   # AST parsing (Python, C++)
│       │   ├── judge0_service.py      # Test execution (Judge0 + local g++/python fallback)
│       │   ├── embedding_service.py   # Semantic embeddings (all-MiniLM-L6-v2, lazy-loaded)
│       │   ├── integrity_service.py   # Plagiarism + AI detection (GPT-2, lazy-loaded)
│       │   ├── review_queue.py        # Manual review queue (DB + in-memory fallback)
│       │   ├── student_tracker.py     # Score history + percentiles + trends + GPA
│       │   ├── evaluation_store.py    # Persistent result storage
│       │   └── submission_index.py    # Code fingerprinting for plagiarism
│       │
│       └── utils/
│           ├── file_parser.py         # File reading + student name extraction + auto-split
│           ├── rubric.py              # Rubric management + validation + default weights
│           ├── csv_export.py          # CSV export (real LLM feedback, /10 scores)
│           └── vtt_parser.py          # VTT parser + TF-IDF + LLM concept refinement + batch scoring
│
├── frontend/
│   ├── app/
│   │   ├── layout.tsx                 # Root layout with Obsidian theme
│   │   ├── page.tsx                   # Landing page
│   │   ├── login/page.tsx             # Role-based login page (Student/Teacher)
│   │   ├── upload/page.tsx            # File upload interface (4 assignment types)
│   │   ├── results/page.tsx           # Results dashboard with score cards
│   │   ├── review/page.tsx            # Review queue page with override
│   │   ├── student/[id]/page.tsx      # Student profile page (teacher view)
│   │   └── portal/                    # Student portal (auth-protected)
│   │       ├── page.tsx               # Student dashboard (GPA, achievements)
│   │       ├── submissions/page.tsx   # Submission history with AI feedback
│   │       ├── progress/page.tsx      # Score trends and skill development
│   │       ├── leaderboard/page.tsx   # Anonymized class rankings
│   │       └── coach/page.tsx         # AI Study Coach (streaming chat)
│   │
│   ├── components/
│   │   ├── AppNavbar.tsx              # Teacher navigation bar with auth
│   │   ├── StudentNavbar.tsx          # Student portal navigation bar
│   │   ├── FileUpload.tsx             # Drag-and-drop file upload component
│   │   ├── index.ts                   # Component barrel exports
│   │   ├── landing/                   # Landing page components
│   │   │   ├── HeroSection.tsx        # Hero with animated gradient
│   │   │   ├── FeaturesGrid.tsx       # Feature cards grid
│   │   │   ├── WorkflowSection.tsx    # How-it-works workflow
│   │   │   ├── CTASection.tsx         # Call-to-action section
│   │   │   ├── TrustedBy.tsx          # Trust indicators
│   │   │   ├── Navbar.tsx             # Landing page navbar
│   │   │   └── Footer.tsx             # Landing page footer
│   │   ├── results/
│   │   │   ├── ResultCard.tsx         # Individual result score card
│   │   │   └── ResultsDashboard.tsx   # Results overview dashboard
│   │   └── upload/
│   │       ├── AssignmentTypeToggle.tsx # Code/Content/Mixed/Transcript toggle
│   │       ├── ContextInputs.tsx      # Problem statement + test cases inputs
│   │       ├── FileItem.tsx           # Individual file item with preview
│   │       └── UploadCard.tsx         # File drop zone card
│   │
│   └── lib/
│       ├── api.ts                     # Centralized API base URL (supports deployment)
│       ├── auth-store.ts              # JWT token management + role detection
│       └── results-store.ts           # Client-side results persistence
│
├── utils/
│   └── llm_service.py                 # LLM service (Groq + OpenRouter + rate limiting)
│
├── test_submissions/                   # Sample test submissions
│   ├── live_test/                     # Code evaluation test files
│   ├── mixed_single/                  # Single-file mixed eval samples
│   ├── mixed_test/                    # Two-file mixed eval samples
│   ├── mixed_txt_test/                # Text-based mixed eval samples
│   ├── nlp_test/                      # NLP content evaluation samples
│   └── transcript_test/              # Transcript evaluation test files
│
├── sample_data/                       # Sample rubrics, problems, and test scripts
├── outputs/                           # Generated CSV exports
├── docker-compose.judge0.yml          # Self-hosted Judge0 setup
├── requirements.txt                   # Python dependencies (full, with ML libs)
├── requirements-deploy.txt            # Slim dependencies (for Render free tier, no torch)
├── run_backend.py                     # Backend startup script (reads PORT env var)
└── .env                               # Environment variables (gitignored)
```

---

## 🚀 How to Run (Local Development)

### Prerequisites

- **Python 3.10+**
- **Node.js 18+**
- **PostgreSQL 14+** (optional — system works without it)
- **Docker Desktop** (optional — for self-hosted Judge0)

### 1. Clone the Repository

```bash
git clone https://github.com/Izhaar-ahmed/Evaluator.git
cd Evaluator
```

### 2. Set Up the Backend

```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate     # macOS/Linux
# .venv\Scripts\activate      # Windows

# Install dependencies (full — includes ML libraries)
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file in the project root:

```env
# --- LLM ---
LLM_ENABLED=true
GROQ_API_KEY=your_groq_api_key_here           # Get from https://console.groq.com
OPENROUTER_API_KEY=your_openrouter_key_here   # Get from https://openrouter.ai/keys

# --- Database (optional for local) ---
DB_NAME=evaluator
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=postgres

# --- Judge0 (optional — for code test execution) ---
JUDGE0_API_URL=http://localhost:2358
JUDGE0_API_KEY=
```

### 4. Set Up PostgreSQL (Optional)

```bash
createdb evaluator
# The schema is auto-created on first startup — no manual migration needed
```

> **Without PostgreSQL**: The system still works! Results are stored in session, and the review queue uses an in-memory fallback.

### 5. Start the Backend

```bash
python run_backend.py
# Server starts at http://localhost:8000
# API docs at http://localhost:8000/docs
```

### 6. Set Up and Start the Frontend

```bash
cd frontend
npm install
npm run dev
# Frontend starts at http://localhost:3000
```

### 7. (Optional) Start Self-Hosted Judge0

```bash
docker-compose -f docker-compose.judge0.yml up -d
# Judge0 API available at http://localhost:2358
```

### 8. Use the Application

**As a Teacher:**
1. Open `http://localhost:3000` → click **Try Now**
2. Log in with `teacher` / `teacher`
3. Navigate to **Upload** → select assignment type → upload files
4. Enter the problem statement and optionally paste test cases
5. Click **Evaluate** → view results on the **Results** page
6. Check flagged submissions in the **Review Queue**

**As a Student:**
1. Open `http://localhost:3000/login` → select **Student** role
2. Log in (username = your student ID, password = same)
3. View your **Dashboard** with GPA, percentile, and achievements
4. Check **My Submissions** for detailed AI feedback
5. Track **Progress** over time
6. Chat with the **AI Study Coach** for personalized help

---

## 🚀 Deployment (Render + Vercel)

### Architecture

```
┌─────────────────┐         ┌──────────────────┐
│   Vercel         │  HTTPS  │   Render          │
│   (Frontend)     │ ──────→ │   (Backend)       │
│   Next.js 14     │         │   FastAPI/Uvicorn  │
│                  │         │                    │
│ NEXT_PUBLIC_     │         │ GROQ_API_KEY       │
│ API_URL          │         │ OPENROUTER_API_KEY │
└─────────────────┘         │ FRONTEND_URL       │
                             │ DB_HOST (Neon)     │
                             └────────┬───────────┘
                                      │ SSL
                                      ▼
                             ┌──────────────────┐
                             │  Neon PostgreSQL  │
                             │  (Cloud DB)       │
                             └──────────────────┘
```

### Render (Backend)

Environment variables:
```
GROQ_API_KEY, OPENROUTER_API_KEY, LLM_ENABLED=true
DB_HOST, DB_NAME, DB_USER, DB_PASSWORD, DB_SSLMODE=require
FRONTEND_URL=https://your-app.vercel.app
```

Use `requirements-deploy.txt` (excludes torch/transformers to stay under 512MB RAM limit).

### Vercel (Frontend)

Environment variable:
```
NEXT_PUBLIC_API_URL=https://your-app.onrender.com
```

### Key deployment decisions:
- `run_backend.py` reads `$PORT` from environment (Render assigns dynamically)
- CORS configured via `FRONTEND_URL` env var
- Database uses `sslmode=require` for Neon PostgreSQL
- All frontend API URLs centralized in `lib/api.ts` — zero hardcoded localhost
- Heavy ML libs (torch, transformers) excluded from deploy requirements — only LLM APIs used in cloud

---

## ⚙️ Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `LLM_ENABLED` | No | `false` | Enable LLM for feedback and concept refinement |
| `GROQ_API_KEY` | If LLM enabled | — | Groq API key for LLaMA 3.1 |
| `OPENROUTER_API_KEY` | If LLM enabled | — | OpenRouter API key for Nemotron |
| `DB_NAME` | No | `evaluator` | PostgreSQL database name |
| `DB_HOST` | No | `localhost` | PostgreSQL host |
| `DB_PORT` | No | `5432` | PostgreSQL port |
| `DB_USER` | No | `postgres` | PostgreSQL username |
| `DB_PASSWORD` | No | `postgres` | PostgreSQL password |
| `DB_SSLMODE` | No | — | Set to `require` for Neon cloud DB |
| `JUDGE0_API_URL` | No | `http://localhost:2358` | Judge0 API URL |
| `JUDGE0_API_KEY` | No | — | Judge0 API key (for RapidAPI hosted) |
| `JWT_SECRET` | No | `evaluator-secret-key-change-in-production` | Secret for JWT signing |
| `FRONTEND_URL` | For deployment | — | Frontend URL for CORS (e.g., `https://app.vercel.app`) |
| `PORT` | For deployment | `8000` | Port for backend (Render sets this dynamically) |
| `NEXT_PUBLIC_API_URL` | For deployment | `http://localhost:8000` | Backend URL for frontend API calls |

---

## 🛠 Tech Stack

### Backend
| Technology | Purpose |
|---|---|
| **FastAPI** | REST API framework with automatic OpenAPI docs |
| **Pydantic v2** | Request/response validation and serialization |
| **Uvicorn** | ASGI server for running FastAPI |
| **Tree-sitter** | Production-grade incremental parser for AST analysis |
| **Groq (LLaMA 3.1 8B)** | Fast LLM for feedback generation and concept refinement |
| **OpenRouter (Nemotron)** | Free reasoning model for code relevance checks |
| **Sentence-Transformers** | Neural text embeddings (all-MiniLM-L6-v2) for semantic similarity |
| **GPT-2** | Perplexity-based AI-generation detection |
| **PostgreSQL** | Persistent storage for results, reviews, and student data |
| **Neon** | Serverless PostgreSQL for cloud deployment |
| **psycopg2** | PostgreSQL adapter for Python |
| **NumPy** | Numerical operations for embeddings and percentiles |
| **PyJWT** | JSON Web Token authentication |
| **Judge0 CE** | Sandboxed code execution engine |
| **httpx** | Async HTTP client for LLM API calls |
| **nest_asyncio** | Nested event loop support for production stability |

### Frontend
| Technology | Purpose |
|---|---|
| **Next.js 14** | React framework with App Router and file-based routing |
| **TypeScript** | Type-safe frontend development |
| **TailwindCSS 3** | Utility-first CSS framework with custom Obsidian theme |
| **React 18** | UI component library |

### Deployment
| Technology | Purpose |
|---|---|
| **Render** | Backend hosting (FastAPI + Uvicorn) |
| **Vercel** | Frontend hosting (Next.js) |
| **Neon** | Serverless PostgreSQL (free tier) |

---

## ❓ Common Questions

### Q: How does the system differentiate between two similar code submissions?

**A:** Through the **complexity_score** computed by tree-sitter. Even if two submissions implement similar algorithms, they'll have different nesting depths, unique identifier counts, function names, and control flow counts. These produce different complexity scores, leading to different final scores.

### Q: What happens when the LLM API is rate-limited?

**A:** The system has built-in rate limiters (25 req/min for Groq, 20 req/min for OpenRouter) that space requests to avoid 429 errors. If a 429 still occurs, it waits 15 seconds and retries once. If that also fails, it falls back to deterministic rule-based scoring. `check_relevance()` returns `UNCERTAIN` on failure (not `IRRELEVANT` — students are never penalized).

### Q: What makes the transcript evaluation unique?

**A:** The two-phase concept extraction. TF-IDF alone picks garbage terms like "data set" and "precision". By sending 20 TF-IDF candidates through Groq for filtering, only genuinely teachable concepts survive. The LLM can only select from candidates, never hallucinate new ones — this gives accuracy with reliability.

### Q: Do I need Judge0 for the system to work?

**A:** No. Judge0 is **optional**. Without it, Python runs locally via subprocess and C++ compiles locally with `g++ -std=c++17`. Only other languages (Java/JS) would skip test execution.

### Q: What file types are supported?

**A:**
- **Code**: `.py` (Python), `.cpp` / `.cc` / `.h` (C++) for full AST analysis
- **Content**: `.txt`, `.md`, `.pdf`, `.html` or any text file
- **Transcript**: `.vtt` (WebVTT subtitle format)
- **Student summaries**: `.html`, `.txt`, `.pdf`

### Q: Can I use this without PostgreSQL?

**A:** Yes. Without PostgreSQL, evaluation results are stored in browser sessionStorage, and the review queue uses an in-memory fallback. All scoring features work normally — you just lose persistence across restarts.

### Q: How accurate is the AI-generation detection?

**A:** GPT-2 perplexity is a **heuristic signal**, not a definitive detector. It routes submissions for human review — the teacher makes the final decision. On servers without PyTorch, this check is gracefully skipped.

### Q: What is the default rubric?

**A:** If you don't provide a custom rubric, the defaults are:
- **Code**: approach (40%), readability (20%), structure (20%), effort (20%)
- **Content**: factual accuracy (40%), coverage (30%), alignment (15%), flow (8%), completeness (7%)
- **Mixed**: code dimension (60%) + content dimension (40%)
- **Transcript**: concept coverage (35%), attempt bonus (30%), depth (15%), expression (10%), base (10%)

---

## 👥 Contributors

| Name | Roll No. | Role | Key Contributions |
|------|----------|------|-------------------|
| **B Harsha Vardhan** | 23BDS015 | Frontend Development | Designed and built the entire Next.js 14 teacher dashboard — landing page, upload interface with drag-and-drop, results dashboard with expandable score cards, review queue with override functionality, and student profile pages with trend visualization. Implemented the Obsidian Dark design system with TailwindCSS. |
| **L Akash** | 23BDS031 | Integration & Testing | Integrated the FastAPI backend with the Next.js frontend via REST API. Configured CORS middleware, implemented multipart file upload handling, and built the `FormData` → backend pipeline. Conducted extensive end-to-end testing, identified and resolved critical bugs including test case format parsing, C++ execution failures, and error propagation across the API boundary. |
| **S Sasi Rekha** | 23BDS049 | Content & Mixed Evaluation | Developed the Content Evaluation Agent with five scoring dimensions (factual accuracy, coverage, alignment, flow, completeness). Implemented the semantic embedding pipeline using all-MiniLM-L6-v2, built the dual keyword/semantic concept hit-rate scoring system, and developed the mixed-mode agent that combines code and content evaluation for hybrid assignments. |
| **SK Izhaar Ahmed** | 23BDS053 | Code Evaluation & Integrity | Built the Code Evaluation Agent with four scoring dimensions (approach, readability, structure, effort). Integrated Tree-sitter for AST analysis, developed the Judge0 execution service with C++ auto-wrapping and local g++ fallback, implemented the integrity service with MD5 plagiarism fingerprinting, fuzzy SequenceMatcher similarity, and GPT-2 perplexity-based AI content detection. |

---

## 📚 References

1. Ala-Mutka, K. M. (2005). A survey of automated assessment approaches for programming assignments. *Computer Science Education*, 15(2), 83–102.
2. Reimers, N., & Gurevych, I. (2019). Sentence-BERT: Sentence embeddings using Siamese BERT-networks. *EMNLP 2019*.
3. Tree-sitter. (2024). Tree-sitter documentation. https://tree-sitter.github.io/tree-sitter/
4. Judge0. (2024). Judge0 CE — open-source online code execution system. https://judge0.com/
5. Radford, A., et al. (2019). Language models are unsupervised multitask learners. *OpenAI Technical Report*.
6. Wang, W., et al. (2020). MiniLM: Deep self-attention distillation for task-agnostic compression. *NeurIPS 2020*.
7. Touvron, H., et al. (2023). LLaMA: Open and efficient foundation language models. *arXiv preprint*.

---

<p align="center">
  <strong>Built with ❤️ for educators who want fair, intelligent, and transparent assessment.</strong>
</p>
