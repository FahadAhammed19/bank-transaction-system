# Northbank — Bank Account Transaction Management

Django Batch 10, Module 19 assignment by Fahad Ahammed. An educational banking demo with fictional accounts and simulated BDT balances. No real banking integration or real money movement.

**Submission status:** Source, README, sample database, and 13 automated tests are prepared. The required five UI screenshots remain pending because the preparation environment's browser preview relay was unavailable. See [screenshot checklist](screenshots/README.md). Do not submit until the screenshots are added.

## Features
- Registration with Django password validation; login; POST-only logout.
- Login required for dashboard, account, transactions, and exports.
- One account per user, with holder name, unique generated demo account number, and zero opening balance.
- Positive two-decimal deposits and withdrawals; overdrafts rejected.
- Balance update and transaction creation in one database transaction.
- Form request IDs prevent a successful form replay from applying twice.
- Transaction history with type, amount, date/time, and balance after; newest first.
- Combined transaction-type and date filters.
- Dashboard balance, total deposits, total withdrawals, and transaction count.
- **Two bonuses:** pagination (10 per page) and CSV export honoring current filters.
- Responsive custom CSS interface, clear success/error messages, empty states, and keyboard focus styles.

## Setup
Use Python 3.12 or newer.

```sh
python -m venv .venv
# macOS / Linux:
source .venv/bin/activate
# Windows PowerShell instead:
# .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Choose ONE database setup:

**A. Restore included sample database (recommended for evaluation):**
```sh
python restore_sample.py
python manage.py migrate
```
This creates `db.sqlite3` from `sample_data/demo.sql`. It refuses to overwrite an existing database. The ZIP also includes `sample_data/demo.sqlite3`, an equivalent ready-made SQLite copy; you can copy it to the project root as `db.sqlite3` instead. Both contain only invented users/accounts. The SQL representation is suitable for version control and can be restored without installing the SQLite CLI.

**B. Fresh database with generated demo data:**
```sh
python manage.py migrate
python manage.py seed_demo
```
`seed_demo` refuses to overwrite existing demo users. To start empty, omit the seed command and register a new user.

Start the application:
```sh
python manage.py runserver
```
Open http://127.0.0.1:8000/ in your browser.

## Demo credentials

| Username | Password | Holder |
| --- | --- | --- |
| `demo` | `DemoPass!2026` | Alex Morgan |
| `demo_other` | `DemoPass!2026` | Jamie Taylor |

These are intentionally public, fictional, non-staff demo accounts. The sample has 14 transactions for Alex and one for Jamie, so pagination and account isolation can be checked. Alex's starting sample balance is BDT 45,200.00; Jamie's is BDT 1,500.00. Seeded record dates are relative to generation time. For a date filter, choose a date visible in the table. Do not reuse demo passwords for real accounts.

## Pages

| URL | Purpose |
| --- | --- |
| `/register/` | Create a user profile |
| `/login/` | Sign in |
| `/logout/` | POST to log out |
| `/account/create/` | Create your own demo account |
| `/` | Account dashboard |
| `/deposit/` | Deposit simulated money |
| `/withdraw/` | Withdraw simulated money |
| `/transactions/` | History, filters, pagination |
| `/transactions/export/` | Filtered CSV download |

Example filter: `/transactions/?kind=deposit&date=2026-11-22`. Date filtering uses Asia/Dhaka. Export includes all matched rows, not just the current page.

## Tests
```sh
python manage.py check
python manage.py test banking
python manage.py makemigrations --check --dry-run
```
13 tests cover registration/account creation, login/logout, protected pages, decimal totals, invalid amounts, overdrafts, duplicate form submissions, rollback, ownership, filtering/CSV, pagination, balance limits, CSRF, and missing-account setup.

## Manual check and screenshot capture
1. Register a new profile and create an account; verify balance is zero.
2. Deposit 100.25, then withdraw 20.10; verify balance is 80.15.
3. Try withdrawing 1000; verify balance/history do not change.
4. Check dashboard totals, filter transaction type/date, and export CSV.
5. Sign in as the second demo user and confirm the first user's records are not visible.
6. Capture Registration, Login, Dashboard, Deposit/Withdraw, and Transaction History. Add the actual PNG files to `screenshots/` and commit them.

The environment completed automated tests but could not complete visual/browser QA. Screenshots are mandatory in the assignment and remain outstanding.

## Project structure
```text
manage.py
requirements.txt
restore_sample.py
banking/              settings, routing, models, forms, services, views, tests
banking/migrations/   database schema
banking/management/commands/seed_demo.py
templates/            server-rendered Django pages
static/style.css      responsive interface
sample_data/          fictional SQLite SQL dump and database copy
screenshots/          required capture checklist (images pending)
```

## Data integrity and scope
Ownership is resolved from the logged-in user, never from posted account IDs. Money operations accept POST only and use CSRF protection. Decimal arithmetic, positive-amount validation, database constraints, conditional balance updates, and atomic ledger insertion protect balances. Historical balances are stored with each transaction. Django hashes passwords. The admin provides read-only financial fields; it cannot create/delete accounts or transactions.

This is a local assignment demo, not production banking software. SQLite can encounter lock contention with concurrent writers; the UI asks the user to retry and request IDs avoid reapplying a completed transaction. Production would require a suitable database, concurrency testing, audit/security review, operational controls, HTTPS, and more. No transfers, loans, payments, or external account connections are implemented.

## Configuration
`DJANGO_DEBUG` defaults to `1`; `DJANGO_ALLOWED_HOSTS` defaults to localhost. Environment variables are read directly (no automatic `.env` loading). For a hosted deployment, disable debug, set a random `DJANGO_SECRET_KEY`, configure hosts/CSRF origins, and use a production server. `DJANGO_DB_PATH` optionally chooses a database file. The assignment does not require hosting.

## Submission
Submit a public GitHub repository containing source, README, sample database, and at least five genuine UI screenshots. Complete the screenshot checklist before submitting.
