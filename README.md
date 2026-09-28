# Case Diary — AI Memory Agent for Indian Litigation Lawyers

**Case Diary** is an AI-powered assistant designed for Indian litigation lawyers. Indian court cases can continue for years with numerous hearings, adjournments, arguments, court directions, requested documents, and action items. Case Diary maintains persistent memory across the entire history of a case using **Hindsight**, enabling lawyers to instantly prepare structured hearing briefs and track legal history.

---

## 🏛️ Architecture Overview

```
[ React Frontend ] (Port 3000 / Vite)
        │
        ▼
[ FastAPI Backend ] (Port 8000)
   ├── SQLite (Source of Truth for Cases, Hearings, & Evidence)
   └── Agent Service (Claude 3.5 Sonnet via Anthropic API)
        │
        ▼
[ Hindsight Vector Memory ] (Port 8888 API / Port 9999 UI)
   └── Persistent Vector Bank (Retain, Recall, Reflect via Gemini LLM)
```

### Core Flow
`Case History → Hindsight Memory → Recall Relevant History → Claude Reasoning → Hearing Preparation Brief → Store New Memory`

---

## 🚀 Phase 2 Setup Instructions

### Prerequisites
* **Python 3.10+** (Python 3.14 recommended)
* **Docker Desktop** (Running Linux containers)
* **API Keys**: Google Gemini API key (for Hindsight LLM) and Anthropic API key (for Claude Agent)

### 1. Environment Setup
Create a Python virtual environment and install dependencies:
```bash
python -m venv .venv
.\.venv\Scripts\activate   # Windows
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env` and fill in your API credentials:
```bash
cp .env.example .env
```
Ensure your `.env` contains:
```env
HINDSIGHT_BASE_URL=http://localhost:8888
HINDSIGHT_BANK_ID=case-diary-demo
HINDSIGHT_API_LLM_PROVIDER=gemini
HINDSIGHT_API_LLM_API_KEY=your_gemini_api_key_here
HINDSIGHT_API_LLM_MODEL=gemini-2.0-flash
ANTHROPIC_API_KEY=your_anthropic_api_key_here
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
```

### 3. Launch Hindsight via Docker Compose
Ensure Docker Desktop is running, then execute:
```bash
docker compose up -d
```
* **Hindsight API**: `http://localhost:8888`
* **Hindsight Control Plane (UI)**: `http://localhost:9999`

### 4. Run Setup Verification Script
Verify that Hindsight connectivity, retain/recall operations, and Claude API configuration are functioning:
```bash
python scripts/check_setup.py
```

---

## ⚖️ Safety & Design Rules
* **Synthetic Data Only**: All demo case data is synthetic and clearly labeled.
* **Strict Grounding**: Never invent evidence or citations.
* **No Predictor Claims**: Do not predict court outcomes or provide definitive legal advice.
* **Human-in-the-loop**: The lawyer remains the ultimate decision-maker.
