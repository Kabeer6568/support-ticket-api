# Support Ticket API

A customer support ticket application built with **Python, FastAPI, SQLAlchemy,
PostgreSQL, and a plain HTML/CSS/JavaScript frontend**. It supports customer,
support-agent, and administrator roles, with AI-assisted ticket triage.

## What This Project Does

The system allows customers/users to create and manage support tickets, while administrators can manage and respond to those tickets.

### User Features

* User registration
* User login
* Authentication
* Create support tickets
* View personal tickets
* View individual ticket details
* Reply to tickets
* View ticket status and conversation history

### Admin Features

* Admin authentication
* View all tickets
* Filter tickets
* Change ticket status
* Reply to users
* Assign/manage tickets
* Browse and filter a paginated directory of customers, support agents, and admins

## Technology Stack

### Backend

* Python
* FastAPI
* Pydantic
* SQLAlchemy

### Database

* PostgreSQL

### Authentication

* JWT authentication
* Password hashing
* Role-based access control

### AI

Gemini reviews each new ticket. It resolves only sufficiently confident, low-risk
requests; urgent, sensitive, uncertain, or failed AI requests are escalated for
human support.

## How the Application Works

A user or frontend application sends an HTTP request to the FastAPI backend.

For example, ticket creation uses:

```text
POST /ticket
```

The backend receives the request and processes it.

```text
Client
   ↓
FastAPI Route
   ↓
Validation
   ↓
Business Logic
   ↓
Database
   ↓
JSON Response
```

For example, when a user creates a ticket:

```text
User
 ↓
POST /ticket
 ↓
Validate request and authenticate user
 ↓
Save ticket and run AI triage
 ↓
Resolve or escalate/assign to an agent
 ↓
Return the ticket and triage result
```

## Example API

Ticket routes include:

```text
GET /ticket?page=1&limit=10
```

and return:

```json
{"items": [], "page": 1, "limit": 10, "total": 0}
```

Another endpoint:

```text
GET /ticket/1
```

could return:

```json
{"id": 1, "title": "Unable to login", "desc": "…", "status": "open", "user_id": 1, "assigned_to": 2}
```

## Frontend

The plain HTML/CSS/JavaScript frontend lives in `frontend/` and covers the API's
current user-facing features:

* Account registration, login, profile display, and sign out
* Role-aware ticket listing, status filtering, pagination, creation, and status updates
* Ticket conversations, replies, and automatic AI triage when a ticket is created
* Automatic ticket resolution for confident, non-urgent requests; serious, sensitive,
  uncertain, or AI-unavailable cases are assigned to a randomly selected support agent
* Admin ticket assignment, deletion, user-role changes, and a paginated directory of customers, support agents, and admins
* Configurable API URL, database health check, and admin-access check

## Setup

Use Python 3.10 or newer and a PostgreSQL database. Create a `.env` file in the
repository root with `DATABASE_URL` and a strong `SECRET_KEY`. Set
`GEMINI_API_KEY` to enable AI triage; without it, tickets safely fall back to
human escalation. Set `ACCESS_TOKEN_EXPIRE_MINUTES` to change the access-token
lifetime; it defaults to 60 minutes. Keep `.env` private and do not commit it.

Create a virtual environment and install the application dependencies from the
repository root:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

For an existing database created by an earlier version of this application,
record the existing schema baseline before running the role cleanup migration:

```powershell
.\.venv\Scripts\alembic.exe stamp 0001_initial_schema
.\.venv\Scripts\alembic.exe upgrade head
```

Only stamp the baseline if the existing database already has the current
application tables (`users`, `tickets`, `comments`, and `ticket_triage_results`).
The upgrade backfills empty/missing user roles to `user` and enforces valid,
non-null roles. For a new database, run migrations without stamping:

```powershell
.\.venv\Scripts\alembic.exe upgrade head
```

The application no longer creates or alters tables at startup; apply migrations
before starting the API. Tokens issued before expiration was introduced do not
contain an expiry and must be replaced by signing in again.

Start the API from the repository root:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

If you use Git Bash, activate the virtual environment with
`source .venv/Scripts/activate` and run:

```bash
python -m uvicorn app.main:app --reload
```

In another terminal, serve the static frontend:

```powershell
.\.venv\Scripts\python.exe -m http.server 5500 --directory frontend
```

In Git Bash, with the virtual environment activated, use:

```bash
python -m http.server 5500 --directory frontend
```

Open `http://127.0.0.1:5500`. The frontend defaults to the API at
`http://127.0.0.1:8000`; change the API server field on the sign-in page if
your API uses a different address. The API permits these local frontend origins
by default. To use another origin, set `FRONTEND_ORIGINS` in `.env` to a
comma-separated list of exact origins, for example:

```text
FRONTEND_ORIGINS=http://localhost:5500,http://127.0.0.1:5500
```

Admin-only tools require signing in as an admin. Assignment and role-management
forms use numeric IDs. Administrators can browse and filter the paginated user
directory in Admin tools; it never exposes password hashes. The directory API is
`GET /users` and supports `role`, `page`, and `limit` query parameters.

New tickets are reviewed by Gemini before the create request completes. When the
model returns a valid, high-confidence safe resolution, the ticket is marked
`resolved` and the response is shown in the ticket details. Urgent or sensitive
issues, low-confidence results, invalid AI output, and provider failures are
escalated. Escalated tickets are marked `open` and randomly assigned to a
registered `support_agent`. If no support agents exist, the ticket remains open
and an administrator is told to assign it. AI triage results are stored in the
`ticket_triage_results` table.

## Deploying publicly on Vercel

The FastAPI application serves the static frontend from the same origin, so the
frontend can call the API without a separate CORS origin. Vercel's Python
runtime detects `app/main.py` as the FastAPI entry point and serves the mounted
frontend alongside the API.

1. Push this repository to GitHub and import it into Vercel with the repository
   root as the project root.
2. Add a PostgreSQL database through the Vercel Marketplace (Neon has a
   permanent free plan). Use its pooled PostgreSQL connection URL for serverless
   access and configure that URL as `DATABASE_URL` in Vercel's project
   environment variables.
3. Add `SECRET_KEY` and `GEMINI_API_KEY` as Vercel environment variables.
   Generate a long, random secret key; do not reuse the example or commit any
   real secret. `GEMINI_API_KEY` is optional; without it, ticket creation falls
   back to human escalation. Optionally set `ACCESS_TOKEN_EXPIRE_MINUTES`.
4. Apply migrations to the Neon database before deploying the application:

   ```powershell
   $env:DATABASE_URL = "your Neon pooled PostgreSQL connection URL"
   .\.venv\Scripts\python.exe -m alembic upgrade head
   ```

   Run this only for a new, empty database. If migrating an existing database,
   follow the existing-database baseline instructions above instead.
5. Deploy from Vercel. Visit the deployment URL and use **Check API + DB** to
   verify connectivity.

Set `FRONTEND_ORIGINS` in Vercel only if another, separate website origin will
call the API; same-origin requests from the Vercel-hosted frontend do not need
CORS. Never paste database URLs or API keys into chat, source control, or
public build logs.

## Tests

Install development dependencies and run the API and migration tests:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest
```

The tests use an isolated in-memory SQLite database and do not contact the
configured PostgreSQL database or Gemini.

## Project Architecture

The current project structure is:

```text
support-ticket-api/
│
├── app/
│   ├── main.py
│   ├── auth.py
│   ├── database.py
│   ├── ai/
│   ├── models/
│   ├── routes/
│   └── schemas/
├── frontend/
├── migrations/
├── tests/
├── alembic.ini
├── .env
├── .gitignore
├── requirements.txt
├── requirements-dev.txt
└── README.md
```

## Main Concepts We Will Learn

While building this project, we will learn:

* Python
* FastAPI
* REST APIs
* HTTP methods
* Request/response handling
* JSON
* URL parameters
* Query parameters
* Pydantic schemas
* Dependency injection
* Authentication
* Authorization
* JWT
* Password hashing
* PostgreSQL
* SQL
* SQLAlchemy
* Database relationships
* Migrations
* Error handling
* Environment variables
* Testing
* Redis
* Background tasks
* Docker
* Linux
* API documentation
* Deployment

## Current Status

Implemented:

* Registration, password hashing, expiring JWT authentication, and role-based access
* Customer and support-agent ticket workflows, comments, assignment, and status updates
* Admin ticket management and user directory
* Gemini ticket triage with human escalation and provider-failure fallback
* Alembic schema migrations and focused automated API/migration tests

Redis, background processing, knowledge-base search/RAG, and deployment setup
are not currently implemented.

## Goal

The goal is not simply to say:

> "I know Python."

The goal is to build and maintain a backend application using Python, FastAPI,
PostgreSQL, authentication, migrations, automated tests, and an external AI API.
