# OVERALL_PROGRESS.md — Master Project Roadmap

## 1. Project Identity & Architecture Overview

* **Project Name**: FinMan (Generalized Household Finance Manager)
* **Target Domain**: Multi-member Indian households (cash + UPI + bank accounts) and generalized personal/group finance.
* **Architecture**: Decoupled Client-Server Architecture.
  * **Backend**: Python 3.10+ with **FastAPI**, **SQLAlchemy 2.0**, and **Pydantic v2**.
  * **Database**: **Single-file SQLite (`finance.db`)** — Zero external server dependencies (no Postgres daemon, no Docker required).
  * **Security**: Stateless **JWT** Bearer tokens + **bcrypt** password hashing + strict **Role-Based Access Control (RBAC)** (`ADMIN` vs. `MEMBER`).
  * **Testing & Docs**: Automated `pytest` suite + Native interactive Swagger UI (`/docs`).
  * **Execution Strategy**: Iterative, strictly isolated phases built by autonomous worker agents (`ling 3.0 flash`, `glm 5.3 flash`, etc.).

---

## 2. Master Phase Status Dashboard

| Phase | Description | Status | Completion % | Gate Sign-off |
| :--- | :--- | :---: | :---: | :---: |
| **Phase 1** | **Core Backend & Ledger Engine** (DB, Auth, RBAC, Accounts, Atomic Balances) | `COMPLETED` | 100% | [x] Gate passed |
| **Phase 2** | **Ingestion Pipeline & Financial Analytics** (Dynamic SMS Parser, Transactions, Reports) | `NOT STARTED` | 0% | [ ] Pending |
| **Phase 3** | **Client Interface (UI / Frontend)** (Mobile/Web Client, SMS Paste Dock, Dashboards) | `NOT STARTED` | 0% | [ ] Pending |
| **Phase 4** | **Lab Packaging, Seeding & Release** (Indian Household Seeder, Test Suite, Docs) | `NOT STARTED` | 0% | [ ] Pending |

---

## 3. High-Level Phase Specifications & Exit Gates

### Phase 1: Core Backend & Ledger Engine
* **Objective**: Build a self-contained, zero-dependency FastAPI backend with atomic financial integrity and role-based household controls.
* **Core Deliverables**:
  * SQLite configured with `PRAGMA foreign_keys = ON;` and Write-Ahead Logging (`WAL` mode).
  * 4 Relational Models: `Household`, `User`, `Account`, `Transaction`.
  * JWT Auth & RBAC: `ADMIN` (Parents) can manage members and see family totals; `MEMBER` (Kids) can only see personal accounts.
  * Atomic Balance Engine: Creating/modifying transactions atomically adjusts account balances with ACID safety.
  * Personal (`/balances/me`) and Household (`/household/total-balance`) balance queries.
* **Phase 1 Exit Gate**:
  - [ ] All Phase 1 test suites pass cleanly (`pytest tests/test_phase1_*.py`).
  - [ ] `uvicorn app.main:app` runs without warnings and `/docs` is accessible.
  - [ ] Non-admin attempting to access `/api/v1/household/*` receives strict `403 Forbidden`.
  - [ ] Account balance mathematically updates on transaction insert/rollback.

---

### Phase 2: Ingestion Pipeline & Financial Analytics
* **Objective**: Implement smart ingestion for Indian bank/UPI messages and aggregate financial data.
* **Core Deliverables**:
  * Dynamic, extensible rule-based regex parser supporting SBI, HDFC, and generic Indian UPI messages.
  * Ingest endpoint: `POST /api/v1/transactions/parse-sms` (extracts amount, type, merchant, remaining balance).
  * Transaction Query Engine with filters (`date_range`, `category`, `account_id`, `user_id`).
  * Monthly category spend analytics (Aggregations for pie/donut charts).
* **Phase 2 Exit Gate**:
  - [ ] Parser tests pass on 10+ real-world Indian bank SMS samples without crashing.
  - [ ] Unmatched SMS messages gracefully return `confidence: "LOW"` without HTTP 500 errors.
  - [ ] Monthly category aggregation returns accurate sums matching database records.

---

### Phase 3: Client Interface (Frontend / Mobile)
* **Objective**: Build a responsive client interface (Flutter, React Native, or Responsive Web) tailored for daily Indian household usage.
* **Core Deliverables**:
  * Auth screens (Login, Household Onboarding).
  * Role-Aware Dashboard:
    * *Personal View (Everyone)*: Accounts list, personal cumulative balance, recent activity.
    * *Household View (Admin Only)*: Total family liquidity pool, member contribution breakdown.
  * Rapid Ingestion Dock: 1-click SMS paste box that pre-populates the transaction form.
  * Manual transaction quick-dial buttons for cash spends (Chai, Auto, Kirana).
  * Visual category breakdown charts.
* **Phase 3 Exit Gate**:
  - [ ] Client seamlessly connects to the FastAPI backend API endpoints.
  - [ ] Kids/Members cannot see or navigate to the household cumulative balance screen.
  - [ ] Pasting an SMS parses immediately and submits a verified transaction in under 3 taps.

---

### Phase 4: Lab Packaging, Seeding & Open-Source Release
* **Objective**: Ensure the project is 100% reproducible for lab evaluators with zero manual friction.
* **Core Deliverables**:
  * `seed.py`: Automated database seeder creating a realistic "Sharma Family" with realistic transactions (Rent, BigBasket, Maid salary, Swiggy, Cash spends).
  * Comprehensive test suite with high code coverage.
  * Open-source documentation: `README.md` with system architecture diagrams, API specs, setup instructions, and `LICENSE` (MIT).
  * Single-command launch script (`run.sh` / `run.bat`).
* **Phase 4 Exit Gate**:
  - [ ] A clean clone of the repo runs in one command and presents a pre-populated, beautiful demo dashboard.
  - [ ] 100% tests pass on a fresh environment.
  - [ ] README contains complete documentation and screenshots.

---

## 4. System-Wide Architectural Invariants (Must Follow)

Every worker agent (`ling 3.0 flash`, `glm 5.3 flash`, etc.) MUST observe these immutable rules:

1. **Zero External DB Dependencies**: Never introduce PostgreSQL, MySQL, Redis, or Docker requirements into the backend. SQLite must remain the primary, self-contained database.
2. **Explicit Foreign Key Enforcement**: SQLite does NOT enforce foreign keys by default. The database setup MUST run `PRAGMA foreign_keys = ON;` upon establishing every connection.
3. **Write-Ahead Logging (WAL)**: SQLite must run in WAL mode (`PRAGMA journal_mode = WAL;`) to prevent database locked errors when reading dashboards while writing transactions.
4. **Never Store Redundant Balances**: Cumulative user balance and cumulative household balance must NEVER be stored as static columns. They MUST be queried dynamically via `SUM(current_balance)` to avoid math drift.
5. **No Blind 500s on Parser Failures**: The SMS parser must NEVER throw an unhandled exception on weird text strings. It must return a structured fallback response.
6. **Strict RBAC Enforcement**: Any endpoint exposing multi-user household data or member management MUST depend on `require_admin`.
7. **Python Runtime (Python 3.11)**: The system default `python3` is 3.14 (pre-release), where binary wheels for Rust/C-extensions like `pydantic-core` fail to build. All virtual environments must be created using `python3.11` (located at `/home/aariz/.local/bin/python3.11`).

---

## 5. Phase Transition Protocol

Before an agent or developer advances to the next Phase:
1. All checkboxes in `SUB_PHASE_PROGRESS.md` for the current phase must be marked `[x]`.
2. All automated tests for the phase must execute and pass with exit code `0`.
3. The Phase status in Section 2 above must be updated to `COMPLETED` and Gate Sign-off marked `[x]`.
4. A summary of additions and any technical notes must be logged in the Progress Log below.

---

## 6. Progress Audit Log

| Timestamp | Phase | Worker / Agent | Summary of Changes | Test Result |
| :--- | :---: | :--- | :--- | :---: |
| *Now* | Phase 1 | — | Phase 1 exit gate: `pytest tests/test_phase1.py -v` PASS | PASS |
