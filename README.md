# Broker CRM

A lightweight CRM for mortgage and leasing brokers, built with **FastAPI**, **PostgreSQL** and **React**, with an **AI assistant** that summarises each client file and suggests next steps.

![Dashboard](docs/screenshots/dashboard.png)

## Features

- **Client management:** create, search, filter and update clients with loan type, amount, lender and pipeline stage
- **Pipeline dashboard:** active pipeline value, settled value, open and overdue tasks, and clients by stage
- **Notes and tasks:** per-client notes and follow-up tasks with due dates; overdue tasks are highlighted
- **AI assistant:** one click summarises a client and suggests next steps using Claude (Anthropic API), with a built-in rule-based fallback so the app works offline and in tests
- **REST API:** documented automatically with OpenAPI at `/docs`
- **Tested:** pytest suite that runs against PostgreSQL in GitHub Actions CI

| Clients | Client detail with AI assistant |
| --- | --- |
| ![Clients](docs/screenshots/clients.png) | ![Client detail](docs/screenshots/client-detail.png) |

## Tech stack

| Layer | Technology |
| --- | --- |
| Backend | Python 3.12, FastAPI, SQLAlchemy 2, Pydantic 2 |
| Database | PostgreSQL 16 (SQLite fallback for quick local dev) |
| Frontend | React 19, Vite |
| AI | Anthropic Claude API (optional) |
| DevOps | Docker Compose, GitHub Actions CI |

## Getting started

### Option 1: Docker (recommended)

```bash
cp .env.example .env          # optionally add your ANTHROPIC_API_KEY
docker compose up --build
```

- Web app: http://localhost:5173
- API docs: http://localhost:8000/docs

Demo data (fictional clients) is loaded automatically on first start.

### Option 2: Run locally

**Backend**

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
export DATABASE_URL=postgresql://user:password@localhost:5432/crm   # optional, defaults to SQLite
python -m app.seed
uvicorn app.main:app --reload
```

**Frontend** (in a second terminal)

```bash
cd frontend
npm install
npm run dev
```

## Running tests

```bash
cd backend
pytest -q
```

Set `DATABASE_URL` to run the same tests against PostgreSQL, as CI does.

## API overview

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/api/dashboard` | Pipeline and task summary |
| GET | `/api/clients?q=&stage=&loan_type=` | Search and filter clients |
| POST | `/api/clients` | Create a client |
| GET / PATCH / DELETE | `/api/clients/{id}` | View, update or delete a client |
| POST | `/api/clients/{id}/notes` | Add a note |
| POST | `/api/clients/{id}/tasks` | Add a task |
| PATCH | `/api/tasks/{id}` | Update or complete a task |
| POST | `/api/clients/{id}/ai-summary` | AI summary and next steps |

## Project structure

```
backend/
  app/
    main.py       # FastAPI routes
    models.py     # SQLAlchemy models (clients, notes, tasks)
    schemas.py    # Pydantic validation
    ai.py         # Claude integration with rule-based fallback
    seed.py       # Demo data
  tests/          # pytest API tests
frontend/
  src/
    App.jsx       # Dashboard, client list, client detail, forms
    api.js        # API client
docker-compose.yml
.github/workflows/ci.yml
```

## Possible next steps

- Authentication and user roles for multiple brokers
- Document uploads (payslips, IDs) to cloud storage such as AWS S3
- Email and SMS reminders for overdue tasks
- Deployment to AWS (ECS or App Runner with RDS PostgreSQL)

---

Built by [Pramisha K C](https://pramishakc3.github.io). All client data in this project is fictional.
