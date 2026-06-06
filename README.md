# VendorBridge

VendorBridge is a FastAPI + PostgreSQL + Redis + React procurement ERP for the Odoo hackathon. This implementation covers milestones 0-3: project setup, relational database foundation, auth/RBAC, immutable activity ledger foundation, and vendor management with India procurement validation.

## Quick Start

```powershell
Copy-Item .env.example .env
docker compose up -d

cd apps/api
python -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
pip install -e ".[dev]"
alembic upgrade head
python -m app.seed
uvicorn app.main:app --reload --port 8000
```

In a second terminal:

```powershell
cd apps/web
npm install
npm run dev
```

Open `http://localhost:5173`.

## Demo Credentials

All demo users use the password `VendorBridge@123`.

| Role | Email |
| --- | --- |
| Admin | `admin@vendorbridge.test` |
| Procurement Officer | `officer@vendorbridge.test` |
| Manager | `rahul.mehta@vendorbridge.test` |
| Finance Manager | `priya.shah@vendorbridge.test` |
| Vendor | `vendor@infrasupplies.test` |

## Milestone Coverage

- Milestone 0: monorepo scaffold, Docker Compose, backend/frontend commands, README, `.env.example`, health endpoint.
- Milestone 1: SQLAlchemy model foundation and Alembic migration for users, vendors, RFQ/quote/procurement workflow tables, budgets, notifications, email outbox, activity hash-chain tables, indexes, constraints, and PostgreSQL append-only triggers for ledger tables.
- Milestone 2: registration, login, password hashing, JWT sessions, current-user endpoint, RBAC dependency, frontend auth screens, role-aware app shell.
- Milestone 3: vendor category seed data, GSTIN/PAN validation, vendor CRUD, pagination/search/filtering, block/unblock actions, lifecycle/compliance badges, and vendor list/form UI.

## Git Workflow

Feature branches should follow the plan in `TASK.md`, for example `feature/auth`, `feature/vendors`, `feature/rfq`, and `feature/approvals`. Do not commit `.env`, local DB files, virtualenvs, `node_modules`, generated builds, or `clones-odoo/`.

## Useful Commands

```powershell
# Backend tests
cd apps/api
pytest

# Backend formatting/linting
ruff check app tests
ruff format app tests

# Frontend checks
cd apps/web
npm run build
```

