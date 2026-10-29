# Data dictionary and relational model

All IDs are immutable text primary keys. Dates use ISO 8601 calendar dates; timestamps are omitted because the deterministic simulation is date-based. Currency is ISO 4217. Percent values are percentage points (0–100) except `drift_threshold` and turnover, stored as proportions (0–1 and 0–100 respectively as noted). `schema.sql` is authoritative for SQLite types, nullability, uniqueness, checks, and foreign keys.

The generated baseline uses INR and the asset classes Indian equity, global equity, government securities, gold, and cash. All tickers begin with `SIM` to identify simulated instruments; the dataset does not contain live NSE/BSE securities or prices.

| Entity / field | Type; required | Allowed values / unit | Key and validation |
|---|---|---|---|
| InvestorProfile.investor_id | TEXT; yes | `INV-` + six digits | PK, unique, immutable |
| InvestorProfile.display_name | TEXT; yes | Synthetic label | Required; no real personal data |
| InvestorProfile.risk_tolerance | TEXT; yes | Conservative, Balanced, Growth | Enum check |
| InvestorProfile.created_at | DATE; yes | ISO date | Required |
| Portfolio.portfolio_id | TEXT; yes | `PORT-<investor-id>-01` | PK |
| Portfolio.investor_id | TEXT; yes | Existing investor | FK to InvestorProfile; many portfolios per investor |
| Portfolio.base_currency | TEXT; yes | INR only in generated baseline | Required |
| Portfolio.account_value | REAL; yes | INR | > 0; synthetic initial funding used to size positions |
| Portfolio.cash_balance | REAL; yes | INR | >= 0; baseline is 0 because cash exposure is represented by the synthetic CASH instrument holding |
| Portfolio.lifecycle_state | TEXT; yes | ACTIVE, CLOSED | Enum |
| Portfolio.created_at | DATE; yes | ISO date | Required |
| Instrument.instrument_id | TEXT; yes | `INS-` + six digits | PK |
| Instrument.ticker | TEXT; yes | Synthetic unique symbol | UNIQUE |
| Instrument.name | TEXT; yes | Synthetic description | Required |
| Instrument.asset_class | TEXT; yes | INDIAN_EQUITY, GLOBAL_EQUITY, GOVT_BONDS, GOLD, CASH | Enum; joins to target asset class |
| Instrument.currency | TEXT; yes | ISO 4217 | Required |
| Instrument.eligible | INTEGER; yes | 0 or 1 | Boolean; 0 means excluded from new trades |
| Instrument.lifecycle_state | TEXT; yes | ACTIVE baseline | Required |
| Holding.holding_id | TEXT; yes | `HOLD-<portfolio-id>-<instrument-id>` | PK |
| Holding.portfolio_id | TEXT; yes | Existing portfolio | FK |
| Holding.instrument_id | TEXT; yes | Existing instrument | FK; portfolio/instrument pair UNIQUE |
| Holding.quantity | REAL; yes | Instrument units | >= 0 |
| Holding.as_of | DATE; yes | ISO date | Must not predate portfolio |
| Holding.lifecycle_state | TEXT; yes | ACTIVE baseline | Required |
| MarketPrice.price_id | TEXT; yes | `PX-<instrument-id>-<date>` | PK |
| MarketPrice.instrument_id | TEXT; yes | Existing instrument | FK |
| MarketPrice.price_date | DATE; yes | ISO date, trading days | Unique instrument/date |
| MarketPrice.close | REAL; yes | Currency per unit | > 0 |
| MarketPrice.currency | TEXT; yes | ISO 4217 | Required |
| MarketPrice.stale_flag | INTEGER; yes | 0 or 1 | Boolean; stale-price invalid fixture is in edge_cases.json |
| TargetAllocation.target_id | TEXT; yes | `TGT-<portfolio>-<asset-class>` | PK |
| TargetAllocation.portfolio_id | TEXT; yes | Existing portfolio | FK |
| TargetAllocation.asset_class | TEXT; yes | Instrument asset-class enum | Required |
| TargetAllocation.target_pct | REAL; yes | Percentage points | 0–100; active rows per portfolio sum to 100 |
| TargetAllocation.effective_from | DATE; yes | ISO date | Required; starts validity window |
| TargetAllocation.effective_to | DATE; no | ISO date or null | Null means currently effective; if present, >= start |
| FeeSchedule.fee_id | TEXT; yes | `FEE-` + six digits | PK |
| FeeSchedule.portfolio_id | TEXT; yes | Existing portfolio | FK |
| FeeSchedule.fee_rate | REAL; yes | Proportion of notional | >= 0 |
| FeeSchedule.minimum_fee | REAL; yes | INR | >= 0; baseline ₹10 |
| FeeSchedule.maximum_fee | REAL; yes | Currency | >= 0 INR; zero means no cap in current generator |
| FeeSchedule.effective_from | DATE; yes | ISO date | Required |
| FeeSchedule.effective_to | DATE; no | ISO date or null | Null means current |
| Constraint.constraint_id | TEXT; yes | `CON-` + six digits | PK |
| Constraint.portfolio_id | TEXT; yes | Existing portfolio | FK |
| Constraint.minimum_trade | REAL; yes | INR | >= 0; baseline ₹500 |
| Constraint.drift_threshold | REAL; yes | Proportion (0.05 = 5 percentage points) | >= 0 |
| Constraint.exclude_ineligible | INTEGER; yes | 0 or 1 | Boolean |
| Constraint.max_turnover_pct | REAL; yes | Percentage points | >= 0; enforced as a per-proposal cap on proposed trade notional |
| Constraint.effective_from | DATE; yes | ISO date | Required |
| Constraint.effective_to | DATE; no | ISO date or null | Null means current |
| RebalanceProposal.proposal_id | TEXT; yes | `RB-2026-` + six digits | PK |
| RebalanceProposal.portfolio_id | TEXT; yes | Existing portfolio | FK |
| RebalanceProposal.created_at | DATE; yes | ISO date | Required |
| RebalanceProposal.status | TEXT; yes | READY, REVIEW, ON_TARGET | Lifecycle outcome |
| RebalanceProposal.exception_codes | TEXT; yes | JSON array of codes | Derived from rule outcomes |
| RebalanceProposal.total_value | REAL; yes | Currency | >= 0; derived from holding quantities x latest prices available |
| RebalanceProposal.estimated_fees | REAL; yes | Currency | >= 0; equals trade fee sum |
| Trade.trade_id | TEXT; yes | `TRD-<portfolio-counter>-<sequence>` | PK |
| Trade.proposal_id | TEXT; yes | Existing proposal | FK; one proposal to many trades |
| Trade.portfolio_id | TEXT; yes | Existing portfolio | FK |
| Trade.instrument_id | TEXT; yes | Existing instrument | FK |
| Trade.side | TEXT; yes | BUY, SELL | Enum |
| Trade.quantity | REAL; yes | Instrument units | >= 0; sell quantity must not exceed holding |
| Trade.notional | REAL; yes | Currency | >= 0 |
| Trade.estimated_fee | REAL; yes | Currency | >= 0; max(minimum fee, rate x notional) for proposed trades |
| Trade.status | TEXT; yes | PROPOSED, BLOCKED, NO_ACTION | Lifecycle decision |
| Trade.reason_code | TEXT; yes | Rule code | Required and auditable |
| PostTradeAllocation.allocation_id | TEXT; yes | `PTA-<portfolio-counter>-<asset-class>` | PK |
| PostTradeAllocation.proposal_id | TEXT; yes | Existing proposal | FK; proposal to one row per asset class |
| PostTradeAllocation.asset_class | TEXT; yes | Instrument asset-class enum | Unique within proposal |
| PostTradeAllocation.current_pct | REAL; yes | Percentage points | Derived from current valued holdings |
| PostTradeAllocation.target_pct | REAL; yes | Percentage points | Copied from effective target allocation |
| PostTradeAllocation.projected_pct | REAL; yes | Percentage points | Derived after applying proposed, non-blocked trades |
| PostTradeAllocation.drift_pct | REAL; yes | Percentage points | Projected less target; must reconcile to projected and target values |

## Relationship and lifecycle summary

- InvestorProfile 1:N Portfolio. The synthetic generator creates one portfolio per investor, but the schema allows multiple.
- Portfolio 1:N Holding, TargetAllocation, FeeSchedule, Constraint, RebalanceProposal, and Trade.
- Instrument 1:N Holding and MarketPrice. Portfolio N:M Instrument through Holding.
- RebalanceProposal 1:N Trade. A trade is associated to one portfolio and instrument, and its proposal must belong to that same portfolio (cross-row equality is validated in application logic; plain FKs ensure both parent records exist).
- RebalanceProposal 1:N PostTradeAllocation (one row for each asset class) records the source-based projected weights after proposed, non-blocked trades.
- TargetAllocation, FeeSchedule, and Constraint are effective-dated. Holdings and prices are dated snapshots. Proposal and trade records are immutable generated events; regenerate to a new output directory to retain a prior run.
- Optional relationships: a price can be absent for a date/instrument; target end date, fee end date, and constraint end date are nullable for the active record. A proposal can have zero trades when on target.

## Rule-driven labels

`ground_truth.json` labels conditions created by fixed portfolio-number rules, never random labels. `edge_cases.json` contains isolated deliberately invalid examples for allocation totals, excessive sells, excluded instruments, omitted fees, and stale prices lacking a flag. These fixtures remain outside baseline features so baseline joins and reconciliations stay valid.
