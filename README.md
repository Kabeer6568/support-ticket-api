# Support Ticket API

A production-style customer support ticket management backend built with **Python and FastAPI**.

This project is being built from scratch as a practical backend engineering project. The goal is to learn Python backend development by building something that resembles a real business application rather than a collection of small tutorials.

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
* View ticket status
* View ticket priority

### Admin Features

* Admin authentication
* View all tickets
* Filter tickets
* Change ticket status
* Change ticket priority
* Reply to users
* Assign/manage tickets

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

### Additional Tools

* Redis
* Docker
* Git/GitHub

### Future AI Features

After the core ticket system is completed, an AI-powered support feature will be added.

The AI functionality may include:

* Answering common support questions
* Searching a knowledge base
* RAG (Retrieval-Augmented Generation)
* Creating or escalating tickets
* Summarizing ticket conversations
* AI-assisted admin responses

## How the Application Works

A user or frontend application sends an HTTP request to the FastAPI backend.

Example:

```text
POST /tickets
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
POST /tickets
 ↓
FastAPI receives ticket data
 ↓
Validate the data
 ↓
Check authenticated user
 ↓
Save ticket in PostgreSQL
 ↓
Return ticket information as JSON
```

## Example API

A future endpoint might look like:

```text
GET /tickets
```

and return:

```json
[
    {
        "id": 1,
        "subject": "Unable to login",
        "status": "open",
        "priority": "high"
    }
]
```

Another endpoint:

```text
GET /tickets/1
```

could return:

```json
{
    "id": 1,
    "subject": "Unable to login",
    "status": "open",
    "priority": "high"
}
```

## Frontend

The plain HTML/CSS/JavaScript frontend lives in `frontend/` and covers the API's
current user-facing features:

* Account registration, login, profile display, and sign out
* Role-aware ticket listing, status filtering, pagination, creation, and status updates
* Ticket conversations, replies, and automatic AI triage when a ticket is created
* Automatic ticket resolution for confident, non-urgent requests; serious, sensitive,
  uncertain, or AI-unavailable cases are assigned to a randomly selected support agent
* Admin ticket assignment, deletion, and user-role changes
* Configurable API URL, database health check, and admin-access check

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
forms use numeric IDs because the API currently has no endpoint to list users
or support agents.

New tickets are reviewed by Gemini before the create request completes. When the
model returns a valid, high-confidence safe resolution, the ticket is marked
`resolved` and the response is shown in the ticket details. Urgent or sensitive
issues, low-confidence results, invalid AI output, and provider failures are
escalated. Escalated tickets are marked `open` and randomly assigned to a
registered `support_agent`. If no support agents exist, the ticket remains open
and an administrator is told to assign it. AI triage results are stored in the
`ticket_triage_results` table, which is created automatically at startup.

## Project Architecture

As the project grows, the code will be separated into different responsibilities.

The planned structure is:

```text
support-ticket-api/
│
├── app/
│   ├── main.py
│   │
│   ├── api/
│   │   └── routes/
│   │
│   ├── models/
│   │
│   ├── schemas/
│   │
│   ├── services/
│   │
│   ├── repositories/
│   │
│   ├── core/
│   │
│   └── db/
│
├── tests/
│
├── .env
├── .gitignore
├── requirements.txt
└── README.md
```

We will **not create all of these folders immediately**.

They will be introduced as the application becomes more complex, so each architectural decision has a purpose.

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

## Development Roadmap

### Phase 1 — Basic API

* FastAPI setup
* Project structure
* Routes
* Request/response
* Pydantic

### Phase 2 — Database

* PostgreSQL
* SQLAlchemy
* Users table
* Tickets table
* Replies table
* Relationships
* Migrations

### Phase 3 — Authentication

* Registration
* Login
* Password hashing
* JWT
* Protected routes
* User/admin roles

### Phase 4 — Ticket System

* Create tickets
* View tickets
* Update tickets
* Ticket status
* Ticket priority
* Replies
* Admin management

### Phase 5 — Production Features

* Validation
* Error handling
* Logging
* Testing
* Redis
* Background tasks

### Phase 6 — Deployment

* Docker
* Linux
* Environment configuration
* Production server
* Deployment

### Phase 7 — AI Integration

* LLM API
* Prompting
* Embeddings
* Vector search
* RAG
* AI support assistant

## Goal

The goal is not simply to say:

> "I know Python."

The goal is to be able to say:

> "I can build and maintain a backend application using Python, FastAPI, PostgreSQL, authentication, caching, Docker, and external APIs."

The project will be built incrementally so that every major component is understood rather than blindly generated by AI.
