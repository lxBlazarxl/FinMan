# ARCHITECTURE.md

This file highlights FinMan's backend architecture.

It lets you:
- Create a household and users (admin + members)
- Create accounts for each user
- Parse a text SMS into money info
- Create transactions that change account balances
- List transactions with filters (date, category, etc.)
- Delete transactions (which puts money back)
- See balances and simple analytics (category breakdown, monthly summary)

## Big picture flow

1. A user calls the server API (HTTP endpoints).
2. The server checks who the user is (JWT token).
3. If the request needs database access, it opens a database session.
4. The server reads or writes the database using models.
5. If the request is about money movement, it also updates balances.
6. The server returns JSON.

## How authentication works (simple)

- Client sends an `Authorization: Bearer <token>` header.
- The server decodes the token to find the user id.
- Then it loads that user from the database.
- Some endpoints also require the user to be an admin.

## Folder map

- `app/main.py` starts the FastAPI app and connects all routers.
- `app/api/...` has the API endpoints (HTTP routes).
- `app/models/...` describes database tables.
- `app/schemas/...` describes the JSON shapes for requests/responses.
- `app/services/...` has the “business logic” (balance rules, SMS parsing, analytics).
- `app/core/...` has shared core pieces (config, database, security).
- `tests/...` has automated tests.

## File-by-file (what each file does)

### `app/main.py`
- Creates the FastAPI app.
- Adds CORS settings.
- Registers routers:
  - `/api/v1/auth`
  - `/api/v1/household`
  - `/api/v1/accounts`
  - `/api/v1/balances`
  - `/api/v1/transactions`
  - `/api/v1/analytics`
- Has a `/health` endpoint.
- On startup, it creates database tables (`Base.metadata.create_all(...)`).

### `app/api/deps.py`
- `get_current_user`: reads JWT token, finds the user in the database.
- `require_admin`: uses `get_current_user` and blocks non-admin users.

### `app/api/v1/auth.py`
- `POST /auth/register-household`
  - Creates a household.
  - Creates the admin user.
  - Creates a “Cash Wallet” account for the admin.
  - Returns an access token.
- `POST /auth/login`
  - Checks phone + password.
  - Returns an access token.

### `app/api/v1/household.py`
- `POST /household/members`
  - Admin-only endpoint.
  - Creates a new member user.
  - Creates a default “Pocket Cash” cash account for that member (or uses the provided name).
- `GET /household/members`
  - Admin-only endpoint.
  - Lists all users in the household.

### `app/api/v1/accounts.py`
- `POST /accounts/`
  - Creates a new account for the logged-in user.
- `GET /accounts/`
  - Lists accounts owned by the logged-in user.
- `GET /accounts/{account_id}`
  - Returns one account if it belongs to the current user.

### `app/api/v1/balances.py`
- `GET /balances/me`
  - Returns total balance for the current user.
  - Also returns the accounts list.
- `GET /balances/household`
  - Admin-only endpoint.
  - Returns total balance for the whole household and member breakdown.

### `app/api/v1/transactions.py`
This is the money movement part.

- `POST /transactions/parse-sms`
  - Takes `sms_text` and calls the SMS parser.
  - Returns parsed amount/type/merchant/category/confidence.

- `POST /transactions/` and `POST /transactions`
  - Creates a transaction on an account.
  - Checks permissions:
    - Admin can create if they target an account in the household.
    - Members can only create on their own accounts.
  - Calls `apply_transaction_balance(...)` to change the account balance.
  - Saves the transaction to the database.

- `GET /transactions` and `GET /transactions?....`
  - Returns transactions list.
  - Filtering options include:
    - `start_date`, `end_date`
    - `category`
    - `account_id`, `type`
    - pagination: `limit`, `offset`
  - Filtering rules depend on role:
    - Members only see their own transactions.
    - Admin can see household transactions, and can also filter by `target_user_id`.

- `DELETE /transactions/{id}`
  - Deletes a transaction if the user has permissions.
  - Calls `revert_transaction_balance(...)` to put money back.
  - Removes the transaction record.

### `app/api/v1/analytics.py`
- `GET /analytics/category-breakdown`
  - Returns spending by category.
  - Uses `scope`:
    - `personal` => current user only
    - `household` => admin only

- `GET /analytics/monthly-summary`
  - Returns monthly totals:
    - total income
    - total expense
    - net savings
    - savings rate percentage

### `app/schemas/*.py`
Schemas are “templates” for JSON.

- `app/schemas/auth.py`
  - Token formats and login/register request shapes.

- `app/schemas/user.py`
  - User response shape.
  - Member creation request shape.

- `app/schemas/household.py`
  - Household response shape.

- `app/schemas/account.py`
  - Account creation request shape.
  - Account response shape.
  - Personal and household balance response shapes.

- `app/schemas/sms.py`
  - SMS parse request/response shapes.
  - Confidence levels: HIGH/MEDIUM/LOW.

- `app/schemas/transaction.py`
  - Transaction create request shape.
  - Transaction response shape.

- `app/schemas/analytics.py`
  - Category breakdown and monthly summary response shapes.

- `app/schemas/__init__.py`
  - Exports schema names so other files can import them easily.

### `app/models/*.py`
Models describe database tables.

- `app/models/base.py`
  - The SQLAlchemy base class used by all models.

- `app/models/enums.py`
  - Defines enums used around the project:
    - user roles (ADMIN/MEMBER)
    - account types
    - transaction types (EXPENSE/INCOME/TRANSFER)

- `app/models/household.py`
  - `Household` table (household id, name, created time).

- `app/models/user.py`
  - `User` table (name, phone, password hash, role, household link).

- `app/models/account.py`
  - `Account` table (owner user, name, type, current balance, created time).

- `app/models/transaction.py`
  - `Transaction` table (account link, user link, amount, type, category, description, sms text, date).

### `app/services/*.py`
Services contain the “rules”.

- `app/services/sms_parser.py`
  - `parse_bank_sms(sms_text)` uses regex rules to find:
    - amount
    - whether it looks like expense or income
    - merchant name
    - a suggested category based on merchant keywords
    - a confidence level
  - If it can’t understand the SMS, it returns confidence = LOW.

- `app/services/balance_service.py`
  - `apply_transaction_balance(...)`
    - EXPENSE decreases account balance
    - INCOME increases account balance
  - `revert_transaction_balance(...)`
    - does the opposite (used when deleting a transaction)
  - `get_user_cumulative_balance(...)`
    - adds up balances for all accounts owned by a user
  - `get_household_cumulative_balance(...)`
    - adds up each member’s balances and returns a list of members

- `app/services/analytics_service.py`
  - Creates date ranges for “this month” (or a passed year/month).
  - `get_category_breakdown(...)`
    - sums expense transactions by category
    - calculates percent per category
  - `get_monthly_summary(...)`
    - sums income and expense transactions for the month
    - calculates net savings and savings rate

### `app/core/*.py`
Core shared utilities.

- `app/core/config.py`
  - Reads settings like:
    - API prefix
    - secret key
    - database URL (SQLite file `finance.db`)

- `app/core/database.py`
  - Creates the SQLAlchemy engine.
  - Turns on SQLite foreign keys (`PRAGMA foreign_keys = ON`).
  - Turns on WAL mode (`PRAGMA journal_mode = WAL`).
  - Provides `get_db()` which opens/closes a database session.

- `app/core/security.py`
  - Password hashing and checking (bcrypt).
  - JWT access token creation.

### `tests/*.py`
Automated checks.

- `tests/test_phase1.py`
  - Tests for Phase 1 (earlier core features).

- `tests/test_sms_parser.py`
  - Tests for the SMS parser.

- `tests/test_phase2.py`
  - Runs the Phase 2 integration tests:
    - parse SMS endpoint
    - create transaction and balance change
    - delete transaction and balance restoration
    - member isolation and category filtering
    - analytics and admin-vs-member permissions

## How it all comes together (end-to-end example)

Example: “Send an SMS, then create a transaction”

1. Client calls `POST /api/v1/transactions/parse-sms` with `sms_text`.
2. `transactions.py` calls `parse_bank_sms(...)`.
3. `sms_parser.py` uses regex rules and returns amount/type/category/confidence.
4. Client (or a test) then calls `POST /api/v1/transactions/` with:
   - account id
   - amount
   - type (EXPENSE/INCOME)
   - category
5. `transactions.py` checks user permissions using `get_current_user`.
6. It calls `apply_transaction_balance(...)` which updates the account balance.
7. It saves a `Transaction` row.
8. Later, `GET /api/v1/balances/me` and `GET /api/v1/transactions?...` read from the database and return results.

That’s the full flow from HTTP request -> permission check -> business logic -> database -> JSON response.
