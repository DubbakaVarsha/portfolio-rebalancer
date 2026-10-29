# Portfolio Rebalance Studio

An explainable portfolio-rebalancing demo for Indian-market scenarios. It compares synthetic holdings with target allocations, applies transparent sample rules, estimates fees, and shows proposal exceptions and illustrative outcomes. The interface uses INR and Indian date and number formatting.

All investment data is synthetic. There are no live NSE/BSE prices, broker or bank connections, real orders, or personalized investment advice.

## Requirements

- Windows, macOS, or Linux
- Python 3.10 or newer
- A modern browser with JavaScript enabled
- No third-party Python packages, Node.js packages, API keys, or internet connection are required to run the app

The Python server and data tools use the standard library, including `argparse`, `csv`, `datetime`, `hashlib`, `hmac`, `http.server`, `json`, `pathlib`, `random`, and `sqlite3`. The website uses plain HTML, CSS, and JavaScript; there is no frontend build step or package manager.

## Run the project

Open PowerShell or a terminal in the project folder. Generate the sample dataset, validate it, then start the website:

```powershell
python --version
python generate_data.py --out data --portfolios 30 --holdings-per-portfolio 5 --days 30
python validate_data.py data/portfolio.db
python app.py
```

Open <http://127.0.0.1:8010> in your browser. The development server listens on localhost only. If port 8010 is already in use, run `python app.py --port 8020` and open <http://127.0.0.1:8020>.

To generate the larger candidate dataset (1,000 portfolios, 5 holdings per portfolio, and 250 weekdays of prices), run:

```powershell
python generate_data.py --out data/full --portfolios 1000 --holdings-per-portfolio 5 --days 250 --seed 20261022
python validate_data.py data/full/portfolio.db
$env:PORTFOLIO_DB = "data/full/portfolio.db"
python app.py
```

Stop the local server with `Ctrl+C`. The `data/user_store.sqlite` file is created locally when the server starts and is excluded from Git. It contains account records and saved plans; never commit it.

## What the application includes

- **Overview:** dataset metrics, proposal statuses, common exceptions, and accounts to review.
- **Accounts & suggestions:** one combined searchable and filterable view. Each row shows an account and its proposal outcome; open a row to inspect holdings, drift, suggested changes, fees, and rule results.
- **My plan:** enter a portfolio value and current asset mix; select or edit a target; compare sample targets; try a simulated price move; see explanations and download a JSON summary.
- **Sign in:** create a local demo account to save and restore a personal plan. Guests may still use the calculator without saving.
- **Data & examples, How it works, Presentation guide:** inspect sample data and edge cases, understand the rules, and follow a short demo path.

The sample rebalancing rules include a 5 percentage-point drift trigger, a ₹500 minimum trade, example turnover limits, and a fee estimate. These are simplified teaching rules, not investment guidance.

## Sign in and security limits

Create an account from **Sign in** using an email address and a passphrase of at least 12 characters. After signing in, valid planner inputs save automatically to the local `data/user_store.sqlite` database and load again on sign-in. Passwords are stored as salted PBKDF2-HMAC-SHA256 hashes. Session tokens are random, stored hashed on the server, and sent to the browser in an HttpOnly, SameSite cookie. State-changing account requests check their origin and a CSRF token.

This is a local candidate-project demo, not a production identity service. It has no email verification, password reset, account deletion, encrypted database, or backup service. Do not expose the built-in Python server to a public or untrusted network. A real public deployment requires HTTPS, a production web server, rate limiting, monitoring, protected configuration, secure backups, and a reviewed account recovery process. If HTTPS is configured in a local reverse-proxy setup, set `AUTH_COOKIE_SECURE=1` before starting the app so cookies include the Secure attribute.

## Data, rules, and validation

The generator creates parent entities before dependent records, uses deterministic identifiers, and derives proposal labels from documented rules. Deliberate negative scenarios are stored separately from the valid baseline. SQLite is the canonical dataset; CSV and JSON exports, a manifest, ground truth, edge-case fixtures, and a validation summary are generated alongside it.

See [docs/data_dictionary.md](docs/data_dictionary.md) for entity fields, relationships, and lifecycle notes, and [schema.sql](schema.sql) for table definitions and constraints. Run `python validate_data.py data/portfolio.db` after generation to check keys, foreign keys, allowed states, dates, allocation totals, fee reconciliation, turnover, and trade rules.

## Project files

- `app.py` — local HTTP server and JSON API
- `auth_store.py` — local account, session, and saved-plan storage
- `generate_data.py` — deterministic synthetic-data generator
- `validate_data.py` — dataset validation
- `schema.sql` — SQLite schema
- `web/` — browser interface, styles, and client-side logic
- `docs/data_dictionary.md` — data model documentation
- `AI_PROMPTS.md` — professional summaries of the AI-assisted project specifications

## AI-use disclosure

AI assistance was used during project development. `AI_PROMPTS.md` records the professional project specifications used to guide that work; it is not a verbatim transcript of personal conversation text. Review the generated implementation and be prepared to explain its rules, data model, and limitations before presenting it.
