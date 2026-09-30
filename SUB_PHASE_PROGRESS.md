# SUB_PHASE_PROGRESS.md — Granular Worker Agent Workboard

> **Notice to Worker Agents (`ling 3.0 flash`, `glm 5.3 flash`, etc.)**:
> 1. You must execute sub-tasks strictly in sequential order. Do NOT skip tasks.
> 2. Follow the **Preachings & Guardrails** for every task. Never use forbidden patterns.
> 3. After completing each task, run the specified **Verification Command**. If it fails, fix the issue before proceeding.
> 4. Mark the checkbox `- [x]` only when the verification command passes with exit code `0`.
> 5. Log your completion in the **Worker Execution Log** at the end of this document.

---

## Master Sub-Phase Index

* [PHASE 1: Core Backend & Ledger Engine](#phase-1-core-backend--ledger-engine)
  * [Sub-Phase 1.1: Environment, Configuration & SQLite Engine Setup](#sub-phase-11-environment-configuration--sqlite-engine-setup)
  * [Sub-Phase 1.2: Relational Data Models & Constraints](#sub-phase-12-relational-data-models--constraints)
  * [Sub-Phase 1.3: Pydantic Validation Schemas](#sub-phase-13-pydantic-validation-schemas)
  * [Sub-Phase 1.4: Security, Authentication & Role-Based Access Control (RBAC)](#sub-phase-14-security-authentication--role-based-access-control-rbac)
  * [Sub-Phase 1.5: Atomic Balance Engine & Account Lifecycle](#sub-phase-15-atomic-balance-engine--account-lifecycle)
  * [Sub-Phase 1.6: Main App Wiring & Automated Test Suite](#sub-phase-16-main-app-wiring--automated-test-suite)
* [PHASE 2: Ingestion Pipeline & Financial Analytics](#phase-2-ingestion-pipeline--financial-analytics)
  * [Sub-Phase 2.1: Regex Parser Rule Engine for Indian Bank SMS](#sub-phase-21-regex-parser-rule-engine-for-indian-bank-sms)
  * [Sub-Phase 2.2: Transaction Ingestion & Balance Lifecycle](#sub-phase-22-transaction-ingestion--balance-lifecycle)
  * [Sub-Phase 2.3: Transaction Query & Multi-Filter Engine](#sub-phase-23-transaction-query--multi-filter-engine)
  * [Sub-Phase 2.4: Monthly Category Spend Analytics & Cash Flow Reports](#sub-phase-24-monthly-category-spend-analytics--cash-flow-reports)
  * [Sub-Phase 2.5: Phase 2 Final Integration & Smoke Run](#sub-phase-25-phase-2-final-integration--smoke-run)
* [PHASE 3: Client Interface (Frontend / Mobile) — DEFERRED](#phase-3-client-interface-frontend--mobile--deferred)
* [PHASE 4: Lab Packaging, Seeding & Open-Source Release](#phase-4-lab-packaging-seeding--open-source-release)
  * [Sub-Phase 4.1: Realistic Indian Household Seeder Script](#sub-phase-41-realistic-indian-household-seeder-script)
  * [Sub-Phase 4.2: Pytest Fixtures & Comprehensive Test Suite](#sub-phase-42-pytest-fixtures--comprehensive-test-suite)
  * [Sub-Phase 4.3: Open-Source Documentation & Zero-Friction Runner](#sub-phase-43-open-source-documentation--zero-friction-runner)

---

# PHASE 1: Core Backend & Ledger Engine

### Sub-Phase 1.1: Environment, Configuration & SQLite Engine Setup

#### Task 1.1.1: Dependency Specification (`requirements.txt`)
* **Target File**: `/home/aariz/Projects/FinMan/requirements.txt`
* **Role**: Define pinned, battle-tested dependencies for FastAPI, SQLite, Pydantic v2, Auth, and Pytest.
* **Preachings & Rules**:
  * **Python Runtime (CRITICAL)**: The system default `python3` is Python 3.14 (pre-release), where binary wheels for `pydantic-core` fail to compile. You MUST use Python 3.11 located at `/home/aariz/.local/bin/python3.11` (or `python3.11`) to create the virtual environment `.venv`.
  * Pydantic must be version 2.x (`pydantic>=2.6.0`, `pydantic-settings>=2.2.0`).
  * SQLAlchemy must be version 2.x (`sqlalchemy>=2.0.27`).
  * Include `passlib[bcrypt]`, `bcrypt==4.0.1`.
  * Include `pyjwt>=2.8.0` for JWT handling.
  * Include `pytest>=8.0.0` and `httpx>=0.27.0` for API test clients.
* **Sub-tasks**:
  - [x] Create `requirements.txt` with required dependencies.
  - [x] Remove any broken `.venv` (`rm -rf .venv`).
  - [x] Create Python 3.11 virtual environment (`/home/aariz/.local/bin/python3.11 -m venv .venv` or `python3.11 -m venv .venv`) and install dependencies.
* **Verification Command**:
  ```bash
  cd /home/aariz/Projects/FinMan && rm -rf .venv && /home/aariz/.local/bin/python3.11 -m venv .venv && source .venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt && python -c "import fastapi, sqlalchemy, pydantic, jwt; print('Dependencies OK')"
  ```
* **Success Criteria**: Terminal outputs `Dependencies OK` with exit code `0`.

---

#### Task 1.1.2: Environment Configuration (`app/core/config.py`)
* **Target Files**:
  * `/home/aariz/Projects/FinMan/.env.example`
  * `/home/aariz/Projects/FinMan/.env`
  * `/home/aariz/Projects/FinMan/app/core/config.py`
* **Role**: Typed application configuration using `pydantic-settings`.
* **Preachings & Rules**:
  * Use `pydantic_settings.BaseSettings` with `SettingsConfigDict(env_file=".env", extra="ignore")`.
  * Define fields:
    * `PROJECT_NAME: str = "FinMan Backend"`
    * `API_V1_STR: str = "/api/v1"`
    * `SECRET_KEY: str` (default to a secure random string for dev)
    * `ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7` (7 days)
    * `DATABASE_URL: str = "sqlite:///./finance.db"`
  * Provide a singleton instance: `settings = Settings()`.
* **Sub-tasks**:
  - [x] Create `app/__init__.py` and `app/core/__init__.py`.
  - [x] Create `.env.example` and a default `.env`.
  - [x] Implement `app/core/config.py`.
* **Verification Command**:
  ```bash
  cd /home/aariz/Projects/FinMan && source .venv/bin/activate && python3 -c "from app.core.config import settings; assert settings.DATABASE_URL.startswith('sqlite'); print('Config OK:', settings.PROJECT_NAME)"
  ```
* **Success Criteria**: Terminal outputs `Config OK: FinMan Backend`.

---

#### Task 1.1.3: SQLite Engine with PRAGMAs (`app/core/database.py`)
* **Target File**: `/home/aariz/Projects/FinMan/app/core/database.py`
* **Role**: Database engine and session factory with SQLite integrity listeners.
* **Preachings & Rules (CRITICAL)**:
  * Connect args MUST include `{"check_same_thread": False}` for multi-threaded FastAPI compatibility.
  * You MUST register an SQLAlchemy event listener on `connect` to execute:
    1. `PRAGMA foreign_keys = ON;` (Forces SQLite to enforce relational integrity).
    2. `PRAGMA journal_mode = WAL;` (Enables Write-Ahead Logging for high-concurrency reads).
  * Provide a standard session dependency: `def get_db(): ...` that yields a session and ensures clean closure.
* **Sub-tasks**:
  - [x] Implement `app/core/database.py` with SQLAlchemy `create_engine`, `sessionmaker`, `event.listens_for(engine, "connect")`.
  - [x] Implement `get_db()` generator yielding `Session`.
* **Verification Command**:
  ```bash
  cd /home/aariz/Projects/FinMan && source .venv/bin/activate && python3 -c "
  from app.core.database import engine
  from sqlalchemy import text
  with engine.connect() as conn:
      fk = conn.execute(text('PRAGMA foreign_keys;')).scalar()
      wal = conn.execute(text('PRAGMA journal_mode;')).scalar()
      assert fk == 1, f'Foreign keys not enabled: {fk}'
      assert str(wal).lower() == 'wal', f'WAL mode not enabled: {wal}'
      print('SQLite Engine OK: FK=ON, WAL=ON')
  "
  ```
* **Success Criteria**: Terminal outputs `SQLite Engine OK: FK=ON, WAL=ON`.

---

### Sub-Phase 1.2: Relational Data Models & Constraints

#### Task 1.2.1: Base Model & Enums (`app/models/base.py` & `app/models/enums.py`)
* **Target Files**:
  * `/home/aariz/Projects/FinMan/app/models/__init__.py`
  * `/home/aariz/Projects/FinMan/app/models/enums.py`
  * `/home/aariz/Projects/FinMan/app/models/base.py`
* **Role**: Shared declarative base and domain enums.
* **Preachings & Rules**:
  * Use SQLAlchemy 2.0 `DeclarativeBase` and `Mapped`, `mapped_column` type annotations.
  * Define python string enums in `app/models/enums.py`:
    * `UserRole`: `ADMIN = "ADMIN"`, `MEMBER = "MEMBER"`
    * `AccountType`: `BANK = "BANK"`, `CASH = "CASH"`, `WALLET = "WALLET"`, `CREDIT_CARD = "CREDIT_CARD"`
    * `TransactionType`: `EXPENSE = "EXPENSE"`, `INCOME = "INCOME"`, `TRANSFER = "TRANSFER"`
* **Sub-tasks**:
  - [ ] Create `app/models/enums.py`.
  - [ ] Create `app/models/base.py` with `class Base(DeclarativeBase)`.
* **Verification Command**:
  ```bash
  cd /home/aariz/Projects/FinMan && source .venv/bin/activate && python3 -c "from app.models.enums import UserRole, AccountType, TransactionType; print('Enums OK')"
  ```

---

#### Task 1.2.2: The 4 Core Relational Models (`app/models/*.py`)
* **Target Files**:
  * `/home/aariz/Projects/FinMan/app/models/household.py`
  * `/home/aariz/Projects/FinMan/app/models/user.py`
  * `/home/aariz/Projects/FinMan/app/models/account.py`
  * `/home/aariz/Projects/FinMan/app/models/transaction.py`
* **Role**: Fully mapped relational entities.
* **Preachings & Rules (STRICT)**:
  * `Household`:
    * `id: Mapped[str]`: Primary key (UUID string, `default=lambda: str(uuid.uuid4())`).
    * `name: Mapped[str]`: VARCHAR(100), not nullable.
    * `created_at`: DateTime, default UTC now.
    * Relationships: `users = relationship("User", back_populates="household", cascade="all, delete-orphan")`.
  * `User`:
    * `id: Mapped[str]`: Primary key (UUID string).
    * `household_id: Mapped[str]`: ForeignKey(`households.id`, `ondelete="CASCADE"`).
    * `name: Mapped[str]`: VARCHAR(100), not nullable.
    * `phone_number: Mapped[str]`: VARCHAR(15), unique, indexed, not nullable.
    * `password_hash: Mapped[str]`: VARCHAR(255), not nullable.
    * `role: Mapped[UserRole]`: default `UserRole.MEMBER`.
    * Relationships: `household`, `accounts = relationship("Account", back_populates="user", cascade="all, delete-orphan")`.
  * `Account`:
    * `id: Mapped[str]`: Primary key (UUID string).
    * `user_id: Mapped[str]`: ForeignKey(`users.id`, `ondelete="CASCADE"`).
    * `name: Mapped[str]`: VARCHAR(100) (e.g., "SBI Salary", "Pocket Cash").
    * `type: Mapped[AccountType]`: default `AccountType.BANK`.
    * `current_balance: Mapped[float]`: Float / Numeric(12, 2), default `0.0`.
    * Relationships: `user`, `transactions = relationship("Transaction", back_populates="account")`.
  * `Transaction`:
    * `id: Mapped[str]`: Primary key (UUID string).
    * `account_id: Mapped[str]`: ForeignKey(`accounts.id`, `ondelete="RESTRICT"`). (NEVER cascade delete account with transactions).
    * `user_id: Mapped[str]`: ForeignKey(`users.id`, `ondelete="CASCADE"`).
    * `amount: Mapped[float]`: Float / Numeric(12, 2), not nullable.
    * `type: Mapped[TransactionType]`: not nullable.
    * `category: Mapped[str]`: VARCHAR(50), not nullable (e.g. "Groceries", "Rent").
    * `description: Mapped[Optional[str]]`: TEXT, nullable.
    * `date: Mapped[datetime]`: DateTime, default UTC now.
    * `raw_sms: Mapped[Optional[str]]`: TEXT, nullable (stores original SMS if parsed).
* **Sub-tasks**:
  - [ ] Implement `app/models/household.py`.
  - [ ] Implement `app/models/user.py`.
  - [ ] Implement `app/models/account.py`.
  - [ ] Implement `app/models/transaction.py`.
  - [ ] Expose all models in `app/models/__init__.py`.
* **Verification Command**:
  ```bash
  cd /home/aariz/Projects/FinMan && source .venv/bin/activate && python3 -c "
  from app.core.database import engine
  from app.models.base import Base
  import app.models
  Base.metadata.create_all(bind=engine)
  from sqlalchemy import inspect
  inspector = inspect(engine)
  tables = inspector.get_table_names()
  expected = {'households', 'users', 'accounts', 'transactions'}
  assert expected.issubset(set(tables)), f'Missing tables: {expected - set(tables)}'
  print('Models and Tables OK:', tables)
  "
  ```
* **Success Criteria**: Terminal outputs `Models and Tables OK` including all 4 tables.

---

### Sub-Phase 1.3: Pydantic Validation Schemas

#### Task 1.3.1: Pydantic Schemas (`app/schemas/*.py`)
* **Target Files**:
  * `/home/aariz/Projects/FinMan/app/schemas/__init__.py`
  * `/home/aariz/Projects/FinMan/app/schemas/auth.py`
  * `/home/aariz/Projects/FinMan/app/schemas/household.py`
  * `/home/aariz/Projects/FinMan/app/schemas/user.py`
  * `/home/aariz/Projects/FinMan/app/schemas/account.py`
  * `/home/aariz/Projects/FinMan/app/schemas/transaction.py`
* **Role**: Input validation and response serialization.
* **Preachings & Rules**:
  * All response schemas must include `model_config = ConfigDict(from_attributes=True)`.
  * `TransactionCreate`:
    * `amount` must use `Field(..., gt=0)` to strictly prevent zero or negative amounts.
    * `type` must be validated against `TransactionType`.
  * `AccountCreate`:
    * `initial_balance` optional, default `0.0`.
  * `RegisterHouseholdRequest`:
    * Validates `household_name`, `admin_name`, `phone_number` (length check: 10-15 chars), and `password` (min 6 chars).
* **Sub-tasks**:
  - [ ] Implement `app/schemas/auth.py` (`Token`, `TokenPayload`, `LoginRequest`, `RegisterHouseholdRequest`).
  - [ ] Implement `app/schemas/household.py` (`HouseholdResponse`).
  - [ ] Implement `app/schemas/user.py` (`UserResponse`, `MemberCreateRequest`).
  - [ ] Implement `app/schemas/account.py` (`AccountCreate`, `AccountResponse`, `PersonalBalanceResponse`, `HouseholdBalanceResponse`).
  - [ ] Implement `app/schemas/transaction.py` (`TransactionCreate`, `TransactionResponse`).
* **Verification Command**:
  ```bash
  cd /home/aariz/Projects/FinMan && source .venv/bin/activate && python3 -c "
  from app.schemas.transaction import TransactionCreate
  from app.models.enums import TransactionType
  import pydantic
  try:
      TransactionCreate(account_id='test', amount=-50, type=TransactionType.EXPENSE, category='Food')
      assert False, 'Should have failed on negative amount'
  except pydantic.ValidationError:
      print('Schemas Validation OK: Negative amount properly blocked')
  "
  ```
* **Success Criteria**: Terminal outputs `Schemas Validation OK: Negative amount properly blocked`.

---

### Sub-Phase 1.4: Security, Authentication & Role-Based Access Control (RBAC)

#### Task 1.4.1: Security Utility Module (`app/core/security.py`)
* **Target File**: `/home/aariz/Projects/FinMan/app/core/security.py`
* **Role**: Password hashing and JWT encoding/decoding.
* **Preachings & Rules**:
  * Use `passlib.context.CryptContext(schemes=["bcrypt"], deprecated="auto")`.
  * Implement `verify_password(plain_password: str, hashed_password: str) -> bool`.
  * Implement `get_password_hash(password: str) -> str`.
  * Implement `create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str` using `pyjwt` with algorithm `"HS256"`.
* **Sub-tasks**:
  - [ ] Implement `app/core/security.py`.
* **Verification Command**:
  ```bash
  cd /home/aariz/Projects/FinMan && source .venv/bin/activate && python3 -c "
  from app.core.security import get_password_hash, verify_password, create_access_token
  import jwt
  from app.core.config import settings
  h = get_password_hash('secret123')
  assert verify_password('secret123', h)
  assert not verify_password('wrong', h)
  token = create_access_token({'sub': 'user-123', 'role': 'ADMIN'})
  payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
  assert payload['sub'] == 'user-123' and payload['role'] == 'ADMIN'
  print('Security Module OK')
  "
  ```
* **Success Criteria**: Terminal outputs `Security Module OK`.

---

#### Task 1.4.2: FastAPI Auth Dependencies (`app/api/deps.py`)
* **Target File**: `/home/aariz/Projects/FinMan/app/api/deps.py`
* **Role**: Authenticate JWT and enforce RBAC.
* **Preachings & Rules (CRITICAL)**:
  * Use `fastapi.security.OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")`.
  * Implement `get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)) -> User`:
    * Decodes JWT token, queries user by `id`. Raises `401 Unauthorized` if invalid or user not found.
  * Implement `require_admin(current_user: User = Depends(get_current_user)) -> User`:
    * Checks `if current_user.role != UserRole.ADMIN`: raises `HTTPException(status_code=403, detail="Admin access required")`.
* **Sub-tasks**:
  - [ ] Create `app/api/__init__.py` and `app/api/deps.py`.
* **Verification Command**:
  ```bash
  cd /home/aariz/Projects/FinMan && source .venv/bin/activate && python3 -c "
  from app.api.deps import get_current_user, require_admin
  print('Auth Dependencies OK')
  "
  ```

---

#### Task 1.4.3: Auth & Member Management Routers (`app/api/v1/auth.py` & `app/api/v1/household.py`)
* **Target Files**:
  * `/home/aariz/Projects/FinMan/app/api/v1/__init__.py`
  * `/home/aariz/Projects/FinMan/app/api/v1/auth.py`
  * `/home/aariz/Projects/FinMan/app/api/v1/household.py`
* **Role**: Register household, login, add family members (Admin only).
* **Preachings & Rules**:
  * `POST /api/v1/auth/register-household`:
    * In a single DB transaction: creates `Household` $\rightarrow$ creates primary `User` with role `UserRole.ADMIN` $\rightarrow$ creates default account "Cash Wallet" (`AccountType.CASH`).
    * Returns JWT token + user summary.
  * `POST /api/v1/auth/login`:
    * Accepts form or JSON with `phone_number` and `password`. Verifies credentials, returns JWT token.
  * `POST /api/v1/household/members` (Protected by `Depends(require_admin)`):
    * Creates a new `User` under the admin's `household_id` with role `UserRole.MEMBER`.
    * Creates an initial default account (e.g. "Pocket Cash") for the member.
  * `GET /api/v1/household/members` (Protected by `Depends(require_admin)`):
    * Lists all family members under the admin's household.
* **Sub-tasks**:
  - [ ] Implement `app/api/v1/auth.py`.
  - [ ] Implement `app/api/v1/household.py`.
* **Verification Command**:
  ```bash
  cd /home/aariz/Projects/FinMan && source .venv/bin/activate && python3 -c "
  from app.api.v1.auth import router as auth_router
  from app.api.v1.household import router as household_router
  print('Auth & Household Routers OK')
  "
  ```

---

### Sub-Phase 1.5: Atomic Balance Engine & Account Lifecycle

#### Task 1.5.1: Atomic Balance Service (`app/services/balance_service.py`)
* **Target Files**:
  * `/home/aariz/Projects/FinMan/app/services/__init__.py`
  * `/home/aariz/Projects/FinMan/app/services/balance_service.py`
* **Role**: ACID balance updates and roll-up calculations.
* **Preachings & Rules (CRITICAL MATHEMATICAL INVARIANT)**:
  * Balance updates MUST happen in the same DB transaction as transaction creation/deletion.
  * Functions required:
    1. `apply_transaction_balance(db: Session, account: Account, tx_type: TransactionType, amount: float)`:
       * If `EXPENSE`: `account.current_balance -= amount`
       * If `INCOME`: `account.current_balance += amount`
    2. `revert_transaction_balance(db: Session, account: Account, tx_type: TransactionType, amount: float)`:
       * If `EXPENSE`: `account.current_balance += amount`
       * If `INCOME`: `account.current_balance -= amount`
    3. `get_user_cumulative_balance(db: Session, user_id: str) -> float`:
       * `SELECT COALESCE(SUM(current_balance), 0.0) FROM accounts WHERE user_id = :user_id`
    4. `get_household_cumulative_balance(db: Session, household_id: str) -> dict`:
       * `SELECT COALESCE(SUM(current_balance), 0.0) FROM accounts JOIN users ON accounts.user_id = users.id WHERE users.household_id = :household_id`
       * Also returns breakdown per member.
* **Sub-tasks**:
  - [ ] Implement `app/services/balance_service.py`.
* **Verification Command**:
  ```bash
  cd /home/aariz/Projects/FinMan && source .venv/bin/activate && python3 -c "
  from app.services.balance_service import apply_transaction_balance, revert_transaction_balance
  print('Balance Service OK')
  "
  ```

---

#### Task 1.5.2: Accounts & Balances Routers (`app/api/v1/accounts.py` & `app/api/v1/balances.py`)
* **Target Files**:
  * `/home/aariz/Projects/FinMan/app/api/v1/accounts.py`
  * `/home/aariz/Projects/FinMan/app/api/v1/balances.py`
* **Role**: Manage personal accounts and query cumulative totals.
* **Preachings & Rules**:
  * `POST /api/v1/accounts`: Creates account under `current_user.id`.
  * `GET /api/v1/accounts`: Returns all accounts owned by `current_user`.
  * `GET /api/v1/balances/me` (Accessible by ANY authenticated user):
    * Returns personal cumulative balance + list of user's accounts.
  * `GET /api/v1/balances/household` (STRICTLY Protected by `Depends(require_admin)`):
    * Returns total household liquid pool and breakdown per family member.
    * Regular `MEMBER` requesting this MUST receive `403 Forbidden`.
* **Sub-tasks**:
  - [ ] Implement `app/api/v1/accounts.py`.
  - [ ] Implement `app/api/v1/balances.py`.
* **Verification Command**:
  ```bash
  cd /home/aariz/Projects/FinMan && source .venv/bin/activate && python3 -c "
  from app.api.v1.accounts import router as acc_router
  from app.api.v1.balances import router as bal_router
  print('Accounts & Balances Routers OK')
  "
  ```

---

### Sub-Phase 1.6: Main App Wiring & Automated Test Suite

#### Task 1.6.1: Main App Assembly (`app/main.py`)
* **Target File**: `/home/aariz/Projects/FinMan/app/main.py`
* **Role**: FastAPI factory, router mounts, and CORS configuration.
* **Preachings & Rules**:
  * Register routers under prefix `/api/v1`:
    * `/api/v1/auth`
    * `/api/v1/household`
    * `/api/v1/accounts`
    * `/api/v1/balances`
  * Add `CORSMiddleware` with `allow_origins=["*"]`, `allow_credentials=True`, `allow_methods=["*"]`, `allow_headers=["*"]`.
  * Include a health-check endpoint: `GET /health` -> `{"status": "healthy", "service": "finman"}`.
* **Sub-tasks**:
  - [ ] Implement `app/main.py`.
* **Verification Command**:
  ```bash
  cd /home/aariz/Projects/FinMan && source .venv/bin/activate && python3 -c "
  from app.main import app
  assert app.title == 'FinMan Backend' or 'FinMan' in app.title
  print('Main App Factory OK')
  "
  ```

---

#### Task 1.6.2: Automated Integration Test Suite (`tests/test_phase1.py`)
* **Target File**: `/home/aariz/Projects/FinMan/tests/test_phase1.py`
* **Role**: Comprehensive test suite proving Phase 1 completeness.
* **Sub-tasks**:
  - [ ] Create `tests/__init__.py`.
  - [ ] Implement `tests/test_phase1.py` using `pytest` and FastAPI `TestClient`.
* **Verification Command (PHASE 1 EXIT GATE)**:
  ```bash
  cd /home/aariz/Projects/FinMan && source .venv/bin/activate && pytest tests/test_phase1.py -v
  ```
* **Success Criteria**: All tests in `test_phase1.py` pass (100% green) with exit code `0`.

---

# PHASE 2: Ingestion Pipeline & Financial Analytics

### Sub-Phase 2.1: Regex Parser Rule Engine for Indian Bank SMS

#### Task 2.1.1: Parser Schemas (`app/schemas/sms.py`)
* **Target File**: `/home/aariz/Projects/FinMan/app/schemas/sms.py`
* **Role**: Pydantic data contracts for SMS parsing requests and results.
* **Preachings & Rules**:
  * Define `ConfidenceLevel(str, Enum)`: `HIGH = "HIGH"`, `MEDIUM = "MEDIUM"`, `LOW = "LOW"`.
  * Define `SMSParseRequest`:
    * `sms_text: str = Field(..., min_length=5, max_length=1000)`
  * Define `SMSParseResult`:
    * `amount: Optional[float] = None`
    * `type: Optional[TransactionType] = None` (`EXPENSE` or `INCOME`)
    * `merchant: Optional[str] = None`
    * `detected_balance: Optional[float] = None`
    * `suggested_category: Optional[str] = "Miscellaneous"`
    * `bank_name: Optional[str] = None` (e.g. "SBI", "HDFC", "UPI")
    * `confidence: ConfidenceLevel = ConfidenceLevel.LOW`
* **Sub-tasks**:
  - [ ] Implement `app/schemas/sms.py`.
* **Verification Command**:
  ```bash
  cd /home/aariz/Projects/FinMan && source .venv/bin/activate && python3 -c "
  from app.schemas.sms import SMSParseRequest, SMSParseResult, ConfidenceLevel
  req = SMSParseRequest(sms_text='Sent Rs.50 to Chai Point')
  assert req.sms_text == 'Sent Rs.50 to Chai Point'
  print('SMS Schemas OK')
  "
  ```
* **Success Criteria**: Terminal outputs `SMS Schemas OK`.

---

#### Task 2.1.2: Dynamic Rule-Based SMS Parser Engine (`app/services/sms_parser.py`)
* **Target File**: `/home/aariz/Projects/FinMan/app/services/sms_parser.py`
* **Role**: Standalone parsing pipeline supporting SBI, HDFC, ICICI, Axis, and generic Indian UPI messages.
* **Preachings & Rules (CRITICAL RESILIENCE RULE)**:
  * The parser MUST NEVER raise an uncaught exception on malformed, spam, or random strings. It must return `confidence=ConfidenceLevel.LOW` if unmatched.
  * Extract amounts cleaned of commas (e.g. `1,450.50` -> `1450.50`).
  * Implement patterns for:
    1. **SBI Pattern**:
       * *Regex*: `(?:debited by|credited with|sent)\s*(?:Rs\.?|INR)?\s*([0-9,.]+)\s*(?:on|to)\s*([A-Za-z0-9\s/._-]+?)(?:\s+Transfer|\s+UPI|\s+Ref|\s+Avl\s*Bal|$)`
       * Detects: "Your a/c no. XX1234 is debited by Rs.450.00 on 28Sep26 transfer to Swiggy UPI Ref 429182. Avl Bal Rs.14,200.50"
    2. **HDFC Pattern**:
       * *Regex*: `(?:spent|paid|debited)\s*(?:Rs\.?|INR)?\s*([0-9,.]+)\s*(?:at|to)\s*([A-Za-z0-9\s/._-]+?)(?:\s+on|\s+via|\s+Avl\s*lmt|$)`
       * Detects: "Alert: Rs. 1,250.00 spent on HDFC Card ending 4321 at DMART MUMBAI on 29-SEP-26. Avl limit: 45,000.00"
    3. **Generic Indian UPI Pattern (GPay, PhonePe, Paytm)**:
       * *Regex*: `(?:Paid|Sent|Transfer of)\s*(?:Rs\.?|INR)?\s*([0-9,.]+)\s*(?:to)\s*([A-Za-z0-9\s/._-]+?)(?:\s+using|\s+via|\s+UPI|$)`
       * Detects: "Paid Rs. 35.00 to RAMESH TEA STALL via UPI"
    4. **Smart Category Inference Map**:
       * If merchant contains `swiggy`, `zomato`, `tea`, `chai`, `cafe` -> `Food & Dining`
       * If merchant contains `dmart`, `kirana`, `bigbasket`, `blinkit`, `zepto` -> `Groceries`
       * If merchant contains `uber`, `ola`, `auto`, `metro`, `petrol`, `fuel` -> `Transport`
       * If merchant contains `hospital`, `pharmacy`, `apollo`, `1mg` -> `Medical`
       * Default fallback category -> `Miscellaneous`
* **Sub-tasks**:
  - [ ] Implement `app/services/sms_parser.py` with multi-regex pipeline and category inference dictionary.
  - [ ] Create unit tests in `tests/test_sms_parser.py` covering 5 distinct Indian bank SMS variations.
* **Verification Command**:
  ```bash
  cd /home/aariz/Projects/FinMan && source .venv/bin/activate && python3 -c "
  from app.services.sms_parser import parse_bank_sms
  res1 = parse_bank_sms('Paid Rs. 30.00 to RAMESH CHAI STALL via UPI')
  assert res1.amount == 30.0 and 'CHAI' in res1.merchant.upper() and res1.suggested_category == 'Food & Dining'
  res2 = parse_bank_sms('Random garbage message with no numbers')
  assert res2.confidence == 'LOW' and res2.amount is None
  print('SMS Parser Engine OK')
  "
  ```
* **Success Criteria**: Terminal outputs `SMS Parser Engine OK`.

---

### Sub-Phase 2.2: Transaction Ingestion & Balance Lifecycle

#### Task 2.2.1: Transaction Router (`app/api/v1/transactions.py`)
* **Target File**: `/home/aariz/Projects/FinMan/app/api/v1/transactions.py`
* **Role**: Ingest SMS, log transactions, and maintain atomic balance synchronization.
* **Preachings & Rules**:
  * `POST /api/v1/transactions/parse-sms`:
    * Accepts `SMSParseRequest`, executes `parse_bank_sms`, returns `SMSParseResult`. (Does not save to DB, strictly a helper).
  * `POST /api/v1/transactions`:
    * Accepts `TransactionCreate`.
    * Enforces that `account_id` belongs to `current_user` (or if Admin, allowed under household).
    * Within DB transaction:
      * Calls `apply_transaction_balance(db, account, tx.type, tx.amount)`.
      * Creates `Transaction` record with `user_id = current_user.id`.
    * Returns `TransactionResponse`.
  * `DELETE /api/v1/transactions/{id}`:
    * Queries transaction. Ensures it belongs to `current_user` (or Admin).
    * Within DB transaction:
      * Calls `revert_transaction_balance(db, account, tx.type, tx.amount)`.
      * Deletes `Transaction` record.
    * Returns `{"detail": "Transaction deleted successfully"}`.
* **Sub-tasks**:
  - [ ] Implement `app/api/v1/transactions.py`.
  - [ ] Mount transaction router in `app/main.py`.
* **Verification Command**:
  ```bash
  cd /home/aariz/Projects/FinMan && source .venv/bin/activate && python3 -c "
  from app.api.v1.transactions import router
  print('Transaction Router OK')
  "
  ```

---

### Sub-Phase 2.3: Transaction Query & Multi-Filter Engine

#### Task 2.3.1: Filtered Transaction Queries (`app/api/v1/transactions.py`)
* **Target File**: `/home/aariz/Projects/FinMan/app/api/v1/transactions.py`
* **Role**: Powerful query engine with date, category, and user-scoping filters.
* **Preachings & Rules (STRICT RBAC INVARIANT)**:
  * `GET /api/v1/transactions`:
    * Query Parameters:
      * `start_date: Optional[datetime] = None`
      * `end_date: Optional[datetime] = None`
      * `category: Optional[str] = None`
      * `account_id: Optional[str] = None`
      * `type: Optional[TransactionType] = None`
      * `target_user_id: Optional[str] = None` (Admin only)
      * `limit: int = 50`, `offset: int = 0`
    * **RBAC Enforcement**:
      * If `current_user.role == UserRole.MEMBER`: Query MUST strictly filter `WHERE user_id = current_user.id`. Any `target_user_id` query param passed is ignored.
      * If `current_user.role == UserRole.ADMIN`: If `target_user_id` is supplied, filter by it (verifying that user belongs to the same household); if omitted, return transactions across all household members.
* **Sub-tasks**:
  - [ ] Add filtered `GET /api/v1/transactions` endpoint in `app/api/v1/transactions.py`.
* **Verification Command**:
  ```bash
  cd /home/aariz/Projects/FinMan && source .venv/bin/activate && python3 -c "
  from app.api.v1.transactions import get_transactions
  print('Transaction Query Engine OK')
  "
  ```

---

### Sub-Phase 2.4: Monthly Category Spend Analytics & Cash Flow Reports

#### Task 2.4.1: Analytics Schemas & Service (`app/schemas/analytics.py` & `app/services/analytics_service.py`)
* **Target Files**:
  * `/home/aariz/Projects/FinMan/app/schemas/analytics.py`
  * `/home/aariz/Projects/FinMan/app/services/analytics_service.py`
* **Role**: SQL aggregations for dashboard charts and monthly burn rate.
* **Preachings & Rules**:
  * `CategoryBreakdownItem`: `{ category: str, total_amount: float, percentage: float }`
  * `MonthlySummaryResponse`: `{ total_income: float, total_expense: float, net_savings: float, savings_rate_percentage: float }`
  * Aggregation Queries in `analytics_service.py`:
    * Use SQLAlchemy `func.sum()` and `group_by(Transaction.category)`.
    * Filter transactions within the month (default: current calendar month UTC).
* **Sub-tasks**:
  - [ ] Implement `app/schemas/analytics.py`.
  - [ ] Implement `app/services/analytics_service.py`.
* **Verification Command**:
  ```bash
  cd /home/aariz/Projects/FinMan && source .venv/bin/activate && python3 -c "
  from app.schemas.analytics import MonthlySummaryResponse, CategoryBreakdownItem
  from app.services.analytics_service import get_category_breakdown
  print('Analytics Service OK')
  "
  ```

---

#### Task 2.4.2: Analytics Router (`app/api/v1/analytics.py`)
* **Target File**: `/home/aariz/Projects/FinMan/app/api/v1/analytics.py`
* **Role**: Expose analytics endpoints.
* **Preachings & Rules**:
  * `GET /api/v1/analytics/category-breakdown`:
    * Returns category sums for pie charts.
    * If calling user is `MEMBER`: aggregates only their own expenses.
    * If calling user is `ADMIN`: query param `scope` can be `"personal"` or `"household"` (household default).
  * `GET /api/v1/analytics/monthly-summary`:
    * Returns income, expense, and net savings.
* **Sub-tasks**:
  - [ ] Implement `app/api/v1/analytics.py`.
  - [ ] Mount analytics router in `app/main.py`.
* **Verification Command**:
  ```bash
  cd /home/aariz/Projects/FinMan && source .venv/bin/activate && python3 -c "
  from app.api.v1.analytics import router as analytics_router
  print('Analytics Router OK')
  "
  ```

---

### Sub-Phase 2.5: Phase 2 Final Integration & Smoke Run

#### Task 2.5.1: Automated Phase 2 Test Suite (`tests/test_phase2.py`)
* **Target File**: `/home/aariz/Projects/FinMan/tests/test_phase2.py`
* **Role**: Complete end-to-end integration tests for Phase 2.
* **Test Cases Required**:
  1. `test_parse_sms_endpoint`: Posts SBI and UPI SMS strings to `/parse-sms`, verifies parsed fields.
  2. `test_transaction_creation_and_balance_deduction`: Creates transaction from parsed SMS, asserts account balance reduced.
  3. `test_transaction_deletion_and_balance_restoration`: Deletes transaction, asserts account balance reverted.
  4. `test_member_cannot_view_other_member_transactions`: Member attempts to query admin transactions, asserts isolation.
  5. `test_monthly_category_analytics`: Logs ₹2,000 "Groceries" and ₹500 "Transport", verifies breakdown totals and percentages.
* **Sub-tasks**:
  - [ ] Implement `tests/test_phase2.py`.
* **Verification Command (PHASE 2 EXIT GATE)**:
  ```bash
  cd /home/aariz/Projects/FinMan && source .venv/bin/activate && pytest tests/test_phase2.py -v
  ```
* **Success Criteria**: All tests in `test_phase2.py` pass (100% green) with exit code `0`.

---

# PHASE 3: Client Interface (Frontend / Mobile) — DEFERRED

> **Note**: Phase 3 (Mobile/Web Client) is deferred as per project plan. The backend remains 100% decoupled and testable via interactive Swagger UI (`/docs`).

---

# PHASE 4: Lab Packaging, Seeding & Open-Source Release

### Sub-Phase 4.1: Realistic Indian Household Seeder Script

#### Task 4.1.1: Automated Database Seeder (`seed.py`)
* **Target File**: `/home/aariz/Projects/FinMan/seed.py`
* **Role**: Idempotent python script that populates realistic Indian family demo data.
* **Preachings & Rules (IDEMPOTENCY & REALISM)**:
  * The script must be idempotent: running `python seed.py` multiple times must clean or reset cleanly without creating duplicate phone numbers.
  * **Family Composition**:
    * **Household**: "Sharma Family"
    * **Admin**: "Rajesh Sharma" (Father) | Phone: `9876543210` | Password: `password123`
    * **Member**: "Pooja Sharma" (Mother) | Phone: `9876543211` | Password: `password123`
    * **Member**: "Aarav Sharma" (Son/Student) | Phone: `9876543212` | Password: `password123`
  * **Accounts**:
    * Rajesh: "SBI Salary A/c" (Initial balance: ₹65,000), "Cash Wallet" (₹4,500)
    * Pooja: "HDFC Savings A/c" (Initial balance: ₹25,000), "Home Cash Box" (₹6,000)
    * Aarav: "Student Pocket Cash" (Initial balance: ₹1,500)
  * **Transactions (25+ realistic items across the last 30 days)**:
    * Inflow: Rajesh Salary (₹85,000 - SBI)
    * Outflow (Fixed): House Rent (₹18,000 - SBI), Maid Salary (₹3,500 - Cash), Electricity Bill (₹2,200 - HDFC)
    * Outflow (Daily/UPI): DMart Kirana (₹4,800 - HDFC), BigBasket (₹1,250 - SBI), Swiggy Dinner (₹650 - SBI), Daily Milk (₹1,400 - Cash)
    * Outflow (Student): College Books (₹750 - Cash), Canteen Chai & Samosa (₹40 - Cash), Metro Recharge (₹300 - Cash)
* **Sub-tasks**:
  - [ ] Implement `seed.py`.
* **Verification Command**:
  ```bash
  cd /home/aariz/Projects/FinMan && source .venv/bin/activate && python seed.py && python3 -c "
  from app.core.database import SessionLocal
  from app.models.user import User
  from app.models.transaction import Transaction
  db = SessionLocal()
  users_count = db.query(User).count()
  tx_count = db.query(Transaction).count()
  assert users_count == 3, f'Expected 3 users, got {users_count}'
  assert tx_count >= 20, f'Expected 20+ transactions, got {tx_count}'
  print(f'Seeder Verification OK: {users_count} users, {tx_count} transactions created')
  db.close()
  "
  ```
* **Success Criteria**: Terminal outputs `Seeder Verification OK: 3 users, 20+ transactions created`.

---

### Sub-Phase 4.2: Pytest Fixtures & Comprehensive Test Suite

#### Task 4.2.1: Shared Test Fixtures (`tests/conftest.py`)
* **Target File**: `/home/aariz/Projects/FinMan/tests/conftest.py`
* **Role**: Configures isolated in-memory/temporary SQLite testing environment.
* **Preachings & Rules**:
  * Use FastAPI `TestClient`.
  * Override `get_db` dependency to use an isolated test SQLite DB (`sqlite:///./test_finance.db`).
  * Ensure `PRAGMA foreign_keys = ON;` is enforced in test DB.
  * Auto-cleanup `test_finance.db` after test suite completes.
* **Sub-tasks**:
  - [ ] Implement `tests/conftest.py`.
* **Verification Command**:
  ```bash
  cd /home/aariz/Projects/FinMan && source .venv/bin/activate && pytest -q
  ```
* **Success Criteria**: Pytest runs across all test files and passes cleanly.

---

### Sub-Phase 4.3: Open-Source Documentation & Zero-Friction Runner

#### Task 4.3.1: Open-Source Repository Standards (`README.md`, `LICENSE`, `.gitignore`)
* **Target Files**:
  * `/home/aariz/Projects/FinMan/README.md`
  * `/home/aariz/Projects/FinMan/LICENSE`
  * `/home/aariz/Projects/FinMan/.gitignore`
* **Role**: Make repository ready for open-source evaluation and git submission.
* **Preachings & Rules**:
  * `.gitignore`: Ignore `.venv`, `__pycache__`, `*.pyc`, `finance.db`, `test_finance.db`, `.env`.
  * `LICENSE`: Standard permissive MIT License.
  * `README.md`:
    * Project overview and Indian household problem statement.
    * Architecture diagram (Decoupled, SQLite with WAL, RBAC).
    * Quickstart instructions (1 command).
    * Default credentials for Sharma Family demo evaluation.
    * API reference summary with `/docs` interactive testing guide.
* **Sub-tasks**:
  - [ ] Implement `/home/aariz/Projects/FinMan/.gitignore`.
  - [ ] Implement `/home/aariz/Projects/FinMan/LICENSE` (MIT).
  - [ ] Implement `/home/aariz/Projects/FinMan/README.md`.
* **Verification Command**:
  ```bash
  cd /home/aariz/Projects/FinMan && test -f README.md && test -f LICENSE && test -f .gitignore && echo "Repo docs OK"
  ```
* **Success Criteria**: Terminal outputs `Repo docs OK`.

---

#### Task 4.3.2: 1-Click Launch Script (`run.sh`)
* **Target File**: `/home/aariz/Projects/FinMan/run.sh`
* **Role**: Zero-configuration startup script for lab evaluators.
* **Preachings & Rules**:
  * Checks if `.venv` exists; if not, creates it and installs `requirements.txt`.
  * Checks if `finance.db` exists; if not, runs `python seed.py` automatically so the evaluator has an instant populated demo!
  * Launches `uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`.
  * Prints a clear message:  
    `"FinMan Backend is live at http://127.0.0.1:8000/docs"`
* **Sub-tasks**:
  - [ ] Create `run.sh` and make executable (`chmod +x run.sh`).
* **Verification Command**:
  ```bash
  cd /home/aariz/Projects/FinMan && test -x run.sh && echo "Runner Script OK"
  ```
* **Success Criteria**: Terminal outputs `Runner Script OK`.

---

## Worker Execution Log

| Date / Time | Sub-Task ID | Agent Model | Status | Verification Output / Notes |
| :--- | :--- | :--- | :---: | :--- |
| 2026-09-30 | Task 1.1.1 | — | `PASS` | Dependencies OK |
| 2026-09-30 | Task 1.1.2 | — | `PASS` | Config OK: FinMan Backend |
| 2026-09-30 | Task 1.1.3 | — | `PASS` | SQLite Engine OK: FK=ON, WAL=ON |
