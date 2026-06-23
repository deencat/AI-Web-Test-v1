# Agentic QA v1

Multi-agent test automation platform for AI-powered test generation, browser execution, and test management.

**Repository:** https://github.com/andrewchw/Agentic_QA_v1

---

## Overview

Agentic QA combines AI-assisted test generation with real browser automation (Stagehand + Playwright) to create, execute, and monitor web application tests.

### Key Features

- AI test generation with multiple LLM providers
- Real browser execution with screenshot capture
- Test suites with sequential and parallel execution
- Knowledge base document upload and categorization
- Execution history, queue management, and real-time monitoring
- JWT authentication with role-based access control

---

## Prerequisites

- Python 3.12.x or 3.13.x
- Node.js 18.x or 20.x LTS
- Git

---

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/andrewchw/Agentic_QA_v1.git
cd Agentic_QA_v1
```

### 2. Backend setup

```bash
cd backend

python -m venv venv
# Windows
.\venv\Scripts\activate
# macOS/Linux
# source venv/bin/activate

pip install -r requirements.txt
playwright install chromium

copy env.example .env
# Edit .env with your API keys (OpenRouter, Google AI Studio, Cerebras, etc.)

python start_server.py
```

Verify the API at http://127.0.0.1:8000/docs

Default login (change after first use): `admin@aiwebtest.com` / `admin123`

### 3. Frontend setup

```bash
cd frontend
npm install
npm run dev
```

### 4. Docker (optional)

```bash
docker-compose up -d
```

---

## Architecture Documentation

High-level architecture documents are included in the `documentation/` folder:

- MLOps Architecture
- Database Architecture
- Security Architecture
- API Documentation
- Architecture Decision Records (ADRs)

---

## Project Structure

```
Agentic_QA_v1/
├── backend/              # FastAPI backend and agents
├── frontend/             # React frontend
├── stagehand-service/    # Browser automation service
├── tests/                # Integration and E2E tests
├── documentation/        # Architecture and API docs
└── docker-compose.yml    # Optional containerized deployment
```

---

## Testing

```bash
cd backend
.\venv\Scripts\activate   # Windows
python -m pytest tests/ -v
```

Import `backend/AI-Web-Test-Postman-Collection.json` into Postman for API testing.

---

## License

See [LICENSE](LICENSE) for terms governing use of this software.
