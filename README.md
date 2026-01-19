# Assignment Evaluator

An intelligent submission evaluation system for student assignments with a modern web interface and AI-powered feedback.

## Overview

A full-stack application that evaluates student code and content submissions using multi-agent analysis. Features a **FastAPI** backend with **Next.js** frontend, optional **Google Gemini LLM** integration for semantic feedback, and comprehensive evaluation metrics. Supports **Python** and **C++** code evaluation.

## Architecture

### Backend (FastAPI)
- **Multi-Agent System**: Specialized agents for code, content, and aggregation
- **RESTful API**: `/api/evaluate` endpoint for submission processing
- **LLM Integration**: Optional Google Gemini for enhanced feedback (configurable via `.env`)
- **Static Analysis**: AST-based code analysis, keyword-based content evaluation

### Frontend (Next.js 14)
- **Modern UI**: React-based interface with Tailwind CSS
- **File Upload**: Support for `.py`, `.cpp`, `.cc`, `.cxx`, `.h`, `.hpp`, `.txt`, and `.pdf` files
- **Real-time Results**: Instant evaluation feedback display
- **Responsive Design**: Mobile-friendly interface

### Evaluation Agents
1. **CodeEvaluationAgent** - Multi-language code analysis (Python AST, C++ regex)
2. **ContentEvaluationAgent** - Keyword and structure analysis for text
3. **AggregatorAgent** - Score normalization and feedback consolidation
4. **LLM Service** (Optional) - Semantic feedback enhancement via Google Gemini

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- npm or yarn

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/SasiRekhaSadanala/Evaluator.git
cd Evaluator
```

2. **Set up Python virtual environment**
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac
```

3. **Install Python dependencies**
```bash
pip install -r requirements.txt
```

4. **Install frontend dependencies**
```bash
cd frontend
npm install
cd ..
```

5. **Configure environment (optional)**
Create a `.env` file in the root directory:
```env
LLM_ENABLED=true  # Set to false to disable LLM features
GEMINI_API_KEY=your_api_key_here  # Required if LLM_ENABLED=true
```

### Running the Application

#### Start Backend
```bash
python run_backend.py
```
Backend runs on `http://localhost:8000`

#### Start Frontend (in a new terminal)
```bash
cd frontend
npm run dev
```
Frontend runs on `http://localhost:3000`

### API Endpoints
- **Health Check**: `GET http://localhost:8000/health`
- **Evaluate**: `POST http://localhost:8000/api/evaluate`
- **API Docs**: `http://localhost:8000/docs` (Swagger UI)

## Project Structure

```
Evaluator/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application
│   │   ├── routes/
│   │   │   └── evaluate.py      # Evaluation endpoint
│   │   ├── services/
│   │   │   └── evaluator.py     # Evaluation service
│   │   └── schemas/
│   │       └── __init__.py      # Pydantic models
│   └── core/
│       ├── agents/              # Evaluation agents
│       │   ├── code_agent.py
│       │   ├── content_agent.py
│       │   └── aggregator_agent.py
│       ├── controller/
│       │   └── orchestrator.py  # Workflow coordinator
│       └── utils/               # Utilities
├── frontend/
│   ├── app/                     # Next.js app directory
│   │   ├── page.tsx            # Landing page
│   │   └── upload/
│   │       └── page.tsx        # Upload interface
│   ├── components/             # React components
│   └── public/                 # Static assets
├── utils/
│   └── llm_service.py          # Google Gemini integration
├── sample_data/                # Example submissions
├── outputs/                    # Evaluation results (CSV)
├── run_backend.py             # Backend startup script
├── nuke_ports.py              # Port cleanup utility
└── README.md                  # This file
```

## Features

### Code Evaluation
- **Multi-Language Support**: Python (AST-based) and C++ (regex-based) analysis
- **Approach Relevance**: Function and keyword matching
- **Readability**: Line length, comments (# for Python, // and /* */ for C++), naming conventions
- **Structure**: Modularization, variable usage, namespaces (C++), header guards (C++)
- **Effort Metrics**: Code volume, control flow complexity

### Content Evaluation
- **Concept Coverage**: Keyword matching against learning objectives
- **Alignment**: Section structure and topic relevance
- **Logical Flow**: Paragraph organization and transitions
- **Completeness**: Word count, examples, reasoning depth

### LLM-Enhanced Feedback (Optional)
- **Semantic Analysis**: Context-aware feedback via Google Gemini
- **Strict Constraints**: No score modification, no hallucinations
- **Fallback**: Graceful degradation to keyword-based feedback

### Score Normalization
- **Learning-Oriented**: Gentle curve for lower scores (growth mindset)
- **0-100 Scale**: Normalized output for consistency
- **Weighted Aggregation**: Configurable rubric weights

## Usage Example

### Via Web Interface
1. Navigate to `http://localhost:3000`
2. Select assignment type (Code, Content, or Mixed)
3. Upload student submissions
4. Optionally provide problem statement or reference
5. Click "Evaluate" and view results

### Via API (Python)
```python
import requests

files = [('files', open('submission.py', 'rb'))]
data = {
    'assignment_type': 'code',
    'problem_statement': 'Write a function to calculate factorial'
}

response = requests.post(
    'http://localhost:8000/api/evaluate',
    files=files,
    data=data
)

results = response.json()
print(f"Score: {results['score']}/{results['max_score']}")
```

## Output Format

### JSON Response
```json
{
  "score": 95.0,
  "max_score": 100,
  "combined_feedback": [
    "✓ Code is well-structured with clear functions",
    "✓ Addresses all problem requirements",
    "→ Consider adding more edge case handling"
  ],
  "llm_feedback": "The solution demonstrates...",
  "student_name": "Student1",
  "file_name": "submission.py"
}
```

### CSV Export
Results are also exported to `outputs/` directory:
- `results.csv` - Summary view
- `results_detailed.csv` - Detailed feedback breakdown

## Design Decisions

1. **No Code Execution**: Safe, fast, no security risks
2. **Static Analysis**: AST parsing for code, regex for content
3. **Optional LLM**: Configurable AI enhancement without dependency
4. **Clean Architecture**: Independent agents, clear separation of concerns
5. **Learning-Oriented**: Encouraging feedback and gentle score normalization
6. **Modern Stack**: FastAPI + Next.js for performance and developer experience

## Utilities

### Port Cleanup
If ports 8000 or 3000 are blocked:
```bash
python nuke_ports.py
```

### Environment Variables
- `LLM_ENABLED`: Enable/disable Google Gemini integration (default: `true`)
- `GEMINI_API_KEY`: Your Google AI API key (required if LLM enabled)

## Known Limitations
- Keyword matching is heuristic-based (no deep NLP)
- Code analysis limited to structure (no logic verification)
- No plagiarism detection
- No test case execution
- LLM feedback requires API key and internet connection

## Contributing
This is an educational project. Feel free to fork and extend!

## License
MIT License

---

**Status**: Production Ready ✅  
**Version**: 1.0  
**Last Updated**: January 2026
