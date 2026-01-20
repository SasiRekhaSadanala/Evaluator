# Assignment Evaluator v2.0

An artificially intelligent submission evaluation system for student assignments, featuring conditional scoring, strict relevance checking, and semantic feedback.

## Overview

A full-stack application (FastAPI + Next.js) that evaluates student code and content submissions using a multi-agent approach. Version 2.0 introduces **Conditional Scoring** to prevent grading inflation and **Strict Relevance Checks** to detect irrelevant or plagiarized submissions.

## Key Features

### 🧠 Intelligent Evaluation
- **Code Analysis**:
  - **Python & C++ Support**: AST-based (Python) and Regex-based (C++) static analysis.
  - **Conditional Scoring**: "Approach-First" logic. If the code logic is irrelevant, structure/effort points are withheld.
  - **Strict Fallback**: Robust keyword matching when LLM is uncertain, ensuring valid code isn't unfairly penalized.
- **Content Analysis**:
  - **Report Evaluation**: Checks concept coverage, alignment, and flow.
  - **Plagiarism Detection**: Flags submissions that are mere copies of the problem statement (>60% similarity).
  - **Keyword Fallback**: Allows valid reports to pass even if LLM feedback is unavailable.

### 🤖 AI-Powered Feedback
- **Google Gemini 1.5 Flash**: Fast, efficient semantic analysis.
- **Structured Output**: Feedback is strictly organized into:
  1.  **Summary**: Brief overview.
  2.  **Corrections Needed**: Detailed gap analysis.
  3.  **Strengths**: Positive highlights.
- **Fail-Safe**: System degrades gracefully to keyword analysis if AI is offline.

### 💻 Modern Interface
- **Next.js 14 Frontend**: Responsive, dark-mode UI with Tailwind CSS.
- **Real-time Results**: Instant feedback with visual score bars.
- **CSV Export**: One-click download of summary reports via secure API endpoints.

## Architecture

```
Evaluator_v2/
├── backend/ (FastAPI)
│   ├── core/agents/         # Code, Content, Aggregator Agents
│   ├── routes/              # /evaluate, /download endpoints
│   └── services/            # EvaluatorService & LLM Integration
├── frontend/ (Next.js)
│   ├── app/results/         # Results dashboard
│   └── components/          # FileUpload & UI elements
└── utils/
    └── llm_service.py       # Gemini Integration Layer
```

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Google Gemini API Key

### Installation

1.  **Clone the repository**
    ```bash
    git clone https://github.com/SasiRekhaSadanala/Evaluator_v2.git
    cd Evaluator_v2
    ```

2.  **Backend Setup**
    ```bash
    python -m venv .venv
    # Windows:
    .venv\Scripts\activate
    # Linux/Mac:
    source .venv/bin/activate
    
    pip install -r requirements.txt
    ```

3.  **Frontend Setup**
    ```bash
    cd frontend
    npm install
    cd ..
    ```

4.  **Environment Configuration**
    Create `.env` in root:
    ```env
    LLM_ENABLED=true
    LLM_PROVIDER=gemini
    LLM_MODEL=gemini-1.5-flash
    GEMINI_API_KEY=your_api_key_here
    ```

### Running the App

1.  **Start Backend** (Port 8000)
    ```bash
    python run_backend.py
    ```

2.  **Start Frontend** (Port 3000)
    ```bash
    cd frontend
    npm run dev
    ```

3.  Open `http://localhost:3000` to start evaluating.

## Version History

- **v2.0 (Jan 2026)**:
    - Implemented Conditional Scoring (Anti-Inflation).
    - Added Content Plagiarism Check (Prompt Copy Prevention).
    - Fixed CSV Download API.
    - Polished AI Feedback Text.
- **v1.0**: Initial Release with basic agents.

## License
MIT License
