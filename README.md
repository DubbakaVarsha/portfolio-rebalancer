# Nivesh India Portfolio Rebalancer

A local, explainable Indian-market portfolio-rebalancing website. It uses INR, Indian number/date formatting, and Indian equity, global equity, government securities, gold, and cash allocation categories. It compares holdings with effective target allocations, applies policy checks, estimates fees, records proposal/trade outcomes, and exposes exceptions through overview, portfolio, proposal, data, and methodology pages. It does not connect to a broker or place orders. All data is synthetic; there are no live NSE/BSE prices or real securities. This is educational software, not financial advice.

## Run locally

Requires Python 3.10 or newer; no package installation or network service is needed.

```powershell
python generate_data.py --out data --portfolios 30 --holdings-per-portfolio 5 --days 30
python validate_data.py data/portfolio.db
python app.py
```

Open <http://127.0.0.1:8010>. The server binds to localhost and defaults to port 8010; choose another free port with `python app.py --port 8020` if needed. To generate the requested full baseline (1,000 portfolios, 5,000 instruments and holdings, 250 trading days of prices), run:

```powershell
python generate_data.py --out data/full --portfolios 1000 --holdings-per-portfolio 5 --days 250 --seed 20261022
python validate_data.py data/full/portfolio.db
$env:PORTFOLIO_DB = "data/full/portfolio.db"
python app.py
```

The site includes an India-localized overview, searchable and filterable account/suggestion lists, holding-level target drift, proposed changes with policy reasons and projected allocations, data validation and example cases, one-click CSV exports, and a fresher-friendly presentation guide with a short script and demo steps. Navigation is client-side; JSON endpoints are served by the local Python server.

Full-scale CSV and JSON exports are large; the generator streams exports to disk. The sample command uses the same generator and seed logic at smaller scale. SQLite is the canonical generated store, with a `schema.sql` SQL seed/schema file, per-entity CSV and JSON exports, `ground_truth.json`, `edge_cases.json`, `validation_summary.json`, and `manifest.json` including source provenance and checksums.

## How it works

1. The fixed-seed generator creates master entities before dependent records and uses stable, zero-padded identifiers.
2. Proposal generation values each holding at the latest available price, compares its current weight to the target for that asset class, then applies drift, minimum trade, excluded-instrument, missing-price and available-quantity rules.
3. Trade records keep an explicit status and reason. A proposal carries its lifecycle status and exception codes; prior proposal records are not overwritten by the dashboard.
4. Fees use the account fee rate and minimum fee. Output totals are calculated from source holdings/prices and persisted proposal/trade records.
5. `ground_truth.json` labels deterministic generated conditions. `edge_cases.json` keeps the five deliberately invalid negative scenarios separate from normal input records.

## Model and rules

See [docs/data_dictionary.md](docs/data_dictionary.md) for fields, types, key rules, cardinality, and lifecycle notes. `schema.sql` defines eleven normalized tables with primary/foreign keys, checks, and indexes. The principal cardinalities are one investor to many portfolios; one portfolio to many holdings, targets, fees, constraints, and proposals; one instrument to many holdings and dated prices; and one proposal to many trades and projected-allocation rows. Portfolio/instrument is a many-to-many relationship through `Holding`. Proposal/trade state is stored as records rather than updated in place. `MarketPrice` and policy records are dated/effective-dated.

Constraints are educational policy examples: 5 percentage-point drift threshold, ₹500 minimum trade, per-account maximum turnover of 2%, 15%, or 40%, and exclusion of ineligible instruments. The simulator enforces minimum trade, drift, missing price, exclusion, sell-quantity, and turnover checks. The dashboard shows the first 250 portfolios and supports text search; use the API/exports for complete analysis. Allocation-negative and omitted-fee cases are documented fixtures, not corrupt baseline rows. The turnover cap limits proposed trade value; it is a simplified policy proxy and does not model exchange order-book liquidity.

The synthetic target mixes are: Conservative 20/5/45/10/20, Balanced 35/15/25/15/10, and Growth 55/20/10/10/5 across Indian equity, global equity, government securities, gold, and cash. They are illustrative allocations, not a prescribed Indian investment strategy. Amounts use INR and UI dates use Indian locale/Asia-Kolkata. The synthetic calendar uses weekdays and does not exclude Indian exchange holidays.

Each portfolio's synthetic `account_value` sets its initial funding scale; `cash_balance` starts at ₹0 because the cash allocation is represented by its own synthetic holding, preventing cash from being counted twice.

## Validation and reproducibility

`validate_data.py [path/to/portfolio.db]` checks primary-key uniqueness, foreign keys, allowed states, effective-date order, target and projected allocation totals, proposal fee reconciliation, blocked-instrument rules, sell quantities, turnover caps, and holding/portfolio date order. The generator also writes a validation summary, row counts, source provenance, and SHA-256 checksums in its manifest. To compare two runs, generate into two separate directories using identical arguments and compare the `manifest.json` `checksums` and `counts` objects. `generated_at` is a fixed label to preserve reproducibility.

Verification performed for this submission: JavaScript syntax check, local HTTP/API smoke check, full-dataset validation with zero reported errors, and two independent full-scale generations with seed `20261022`. The two fresh runs matched on all row counts and SHA-256 checksums (1,000 portfolios, 5,000 instruments, 5,000 holdings, and 1,249,956 price rows). The candidate FAQ does not require a hosted demo or automated test suite; these commands demonstrate local verification.

## Assumptions and limitations

- Synthetic INR prices and holdings are randomly varied from a fixed seed. The weekday-only calendar does not remove Indian exchange holidays. There is no external market-data source or personal information.
- The UI and API are read-only and bind to localhost by default. No authentication is implemented; do not expose the server to an untrusted network.
- Data is an educational simulation, not a recommendation engine for actual investments. Indian securities transaction tax, GST on fees, capital-gains taxes, lot-level cost basis, corporate actions, and live liquidity are not modeled.
- Target weights sum to 100% in valid baseline records. Deliberate violations live in isolated edge-case fixtures and the corresponding expected decision is documented.

## AI-use disclosure / prompt history

AI-assisted implementation was used in this project. The full user prompt available in this work session is recorded in [`AI_PROMPTS.md`](AI_PROMPTS.md); no other AI tools were used in this workspace. The user should review the generated code, understand the rules and limitations above, and make any final changes before submitting under their name. AI responses are not required by the candidate FAQ.

## Submission checklist

- [x] Source code and local run instructions
- [x] Synthetic data generator, fixed seed, parameterized scale, exports, schema, data dictionary, manifest and separate labels
- [x] Negative scenario coverage and validation command
- [x] AI assistance and prompt record
- [ ] Publish this prepared project to a dedicated public GitHub repository and send its link from the recruiting email address (requires the candidate's GitHub account and their own submission action)
