# Portfolio Rebalance Studio: 60-minute presentation guide

This guide gives a beginner-friendly, timed explanation of the project and every page in the website. It is written so you can present in your own words. The application is a local educational simulation; it does not give personal investment advice, fetch live prices, connect to a broker, or place orders.

## Before the presentation

### Prepare the demo

1. Open PowerShell in the project folder.
2. If you need to recreate the small sample data, run:

   ```powershell
   python generate_data.py --out data --portfolios 30 --holdings-per-portfolio 5 --days 30
   python validate_data.py data/portfolio.db
   ```

3. Start the website with `python app.py` and open `http://127.0.0.1:8010`.
4. Keep the site and a terminal ready. Do not use real account, financial, or personal data in the demo.
5. In **My plan**, use an easy-to-explain example such as a ₹5,00,000 portfolio, a 50/10/20/10/10 current mix, and the Balanced target. The percentages add to 100. Try a 10% simulated Indian-equity price rise, then show the result and set the move back to zero.
6. Use the synthetic **Accounts & suggestions** list for the database walkthrough. Do not create an account live unless you have already practiced it; the local account database belongs to the machine running this application.

### Main message to remember

> Portfolio Rebalance Studio compares a portfolio's current investment mix with a target mix. It shows possible changes only after checking simple rules, and it explains the result. The website uses synthetic data so the full workflow can be demonstrated safely.

## One-hour agenda

| Time | Topic | Goal |
|---|---|---|
| 0–4 min | Welcome and project summary | Explain the problem in one minute |
| 4–9 min | Users, scope, and boundaries | Explain who benefits and what the demo does not do |
| 9–14 min | Overview page | Read the summary cards and status chart |
| 14–23 min | Accounts & suggestions page | Search, filter, and explain a sample account row |
| 23–30 min | Account and suggestion details | Show holdings, drift, proposed actions, fees, and rule reasons |
| 30–40 min | My plan page | Enter a personal mix, compare targets, and run a price scenario |
| 40–44 min | Sign in and saved plan | Explain account-specific plan persistence and local scope |
| 44–49 min | Data & examples page | Explain generated tables, validation, exports, and edge cases |
| 49–53 min | How it works page | Walk through the workflow and sample rules |
| 53–56 min | Presentation Guide page | Explain how the interface helps a new user learn and present |
| 56–60 min | Questions and closing | Answer questions and summarize limitations and next steps |

If a section runs short, ask the audience what they would like to inspect. If you are behind schedule, keep the Overview, combined Accounts & suggestions page, My plan, and Data & examples demo; summarize the other pages verbally.

## Detailed speaker notes

### 0–4 min — Welcome and project summary

**Say:**

“Hello. My project is Portfolio Rebalance Studio. It is a small portfolio-rebalancing demonstration. A portfolio is a collection of investments. An investor can have a target, for example a planned percentage in equity, bonds, gold, and cash. This project compares that target with the current holdings and shows possible changes. It also checks rules such as a minimum trade amount and a trading limit. The purpose is to make each result easy to inspect and explain.”

“All sample accounts, instruments, and prices are synthetic. The application is not connected to Indian exchanges or to a broker. It cannot submit an order. I will show both a generated sample account and a separate calculator where a user can enter their own example.”

**Explain the problem simply:**

Without a comparison tool, a person or analyst would need to calculate every holding's value, convert values to percentages, compare each percentage with a target, decide whether a difference is large enough to review, and check policy constraints. The project automates that demonstration workflow and records why a result was generated.

### 4–9 min — Users, scope, and boundaries

**Say:**

“The main actors in the business brief are an account holder, an operations analyst, a risk or compliance reviewer, and an administrator. The screens in this demo mainly help someone inspect accounts and understand proposed outcomes. The planner is a learning tool for entering a separate example portfolio.”

Clarify the important distinction:

- The **Accounts & suggestions** page displays generated sample portfolios from the synthetic dataset.
- The **Sign in** page creates a local application account so a user can save their personal planner inputs.
- These are different kinds of account. A demo account in the table is not a login account, and signing in does not reveal or connect to a real investment account.

**Describe what is included:**

- A repeatable synthetic data generator and SQLite database.
- A browser website with a JSON API served by Python.
- A rules-based rebalancing proposal and trade records.
- A personal plan calculator, with a separate local sign-in and save feature.
- Validation results, sample edge cases, CSV exports, and presentation support.

**Describe what is outside scope:**

There are no live market feeds, user brokerage integrations, real order execution, Indian tax calculations, identity verification emails, password reset emails, or public production hosting. This is a candidate-project demo, not a financial product.

### 9–14 min — Overview page

Open **Overview**. Start at the top and explain each area in order.

1. **Page heading and valuation date:** The heading identifies the Indian-market simulation. The date is the most recent synthetic price date available in the generated dataset.
2. **Accounts:** The number of sample portfolios in the database.
3. **Need a closer look:** Proposals whose generated status is `REVIEW`, generally because an exception needs attention.
4. **Trades stopped by a rule:** Count of trade records blocked by a rule. A blocked trade remains visible for traceability; it is not silently removed.
5. **Estimated fees:** Total estimated fees on sample proposals. It is a simulation and excludes actual tax and brokerage details.
6. **Suggestions at a glance:** A chart groups proposal outcomes into Ready, Review, and On target. These are generated dataset statuses, not investment recommendations.
7. **Things to check:** Common exception reasons. Explain one visible item, for example an unavailable or stale price, if present.
8. **Accounts to review:** A small preview of rows. Selecting a row opens account details.

**Say:**

“This page is a dashboard. It gives me the size and state of the sample data before I inspect an individual account. A number here is a summary; the account and suggestion views provide the reason behind it.”

Do not imply that “Ready” means it is financially suitable. It means the generated rules did not mark the proposal for review.

### 14–23 min — Accounts & suggestions page

Open **Accounts & suggestions**. The former account list and suggestion list are combined here because they describe the same generated sample portfolio and proposal.

Explain the controls:

- The search field matches a portfolio identifier or synthetic investor name.
- The risk filter narrows by Conservative, Balanced, or Growth risk tolerance.
- The status filter narrows by Ready, Review, or On target.
- The page controls move between result pages.
- The export button downloads the sample portfolio CSV, not the user's personal plan.

Read one row across, left to right:

1. **Portfolio and investor:** The stable portfolio ID identifies a synthetic sample. The name is generated and is not personal data.
2. **Risk level:** The synthetic investor's stated risk category. It describes the sample profile; it is not inferred as a suitability assessment.
3. **Current value:** The proposal's computed portfolio value using holding quantities and the latest available synthetic prices.
4. **Estimated fees:** The sum of estimated fees for eligible proposed trades.
5. **Things to check:** The proposal's exception codes rendered in plain language.
6. **Result:** Ready, Needs a look, or On target, derived from the generated proposal status.

Search for one portfolio if you have prepared an ID, or filter to **Needs a look**. Open a row. Explain that the account detail is a drill-down, not a second unrelated dataset.

### 23–30 min — Account detail and suggestion detail

#### Account detail dialog

The dialog shows the sample portfolio ID, synthetic investor, risk category, result status, current value, and estimated fee. An exception warning appears when the proposal has exception codes.

In **What it owns vs its plan**, explain:

- An instrument is a synthetic example investment.
- Asset class is the broader category, such as Indian equity or government securities.
- Value is quantity multiplied by the latest available synthetic unit price.
- **Now** is the current value as a percentage of the portfolio.
- **Plan** is the effective target percentage for that asset class.
- **Difference** is current share minus target share, in percentage points.

For example, if current Indian equity is 42% and the target is 35%, the holding is 7 percentage points above the target. This is not a 7% return and does not mean the investment gained 7%.

Click **See suggested plan**. The related proposal detail explains:

- Proposal identifier, date, status, total value, and estimated fees.
- Proposal-level exceptions or a message that there are no proposal-level exceptions.
- Each possible trade, its side (buy or sell), instrument, amount, estimated fee, status, and rule reason.
- Current and illustrative post-trade allocations by asset class.

**Say:**

“This detail is useful for review. A user can see not only a possible action but also why a rule allowed or stopped it. The projected allocation assumes allowed proposed changes happen. It is still a simulation, and fees or taxes may not be fully reflected in the projected percentage mix.”

### 30–40 min — My plan page

Close the dialog and choose **My plan**. This is the easiest page to use for a live interactive demonstration.

#### Inputs

- **Your name:** Optional display label for the result, not a financial identity field.
- **Total portfolio value:** The approximate rupee value used to convert percentages into example amounts.
- **Starting target plan:** Conservative, Balanced, or Growth. Selecting one fills the target percentages, which can then be edited.
- **Example trading limit:** A simplified maximum example turnover, shown as a percentage of portfolio value.
- **What-if asset and price move:** Applies a hypothetical price change to the selected asset class. It does not fetch actual prices.
- **Current share / Your target:** Five asset classes. Each current mix and target mix must add to 100%.

#### Live example

Enter ₹5,00,000. Use current shares 50% Indian equity, 10% global equity, 20% government securities, 10% gold, and 10% cash. These add to 100%. Select Balanced as the starting target and leave its target values as provided. Explain that the planner uses the user's entered mix, not the sample account that was previously opened.

Click **Compare target plans**. The cards show how many asset categories differ by at least five percentage points and an approximate gross difference before the calculator's limits. Choosing a preset fills the target fields; it does not guarantee that the plan is suitable.

Set a hypothetical Indian-equity price change, such as +10%. Explain that the calculator increases the selected asset-class value, recalculates the total scenario value, and then recomputes the mix. Return the scenario to zero to show the baseline again.

Click **Show my result** and explain:

- The header reports the starting amount and the changed amount after the what-if scenario.
- Summary cards show possible included changes, estimated fees, and the selected turnover limit.
- Horizontal bars compare the current scenario mix with the illustrative after mix.
- The table shows current share, target, possible change, rule result, and estimated after share.
- Each **Why?** disclosure explains the decision in plain language.
- Download saves a JSON summary of the current result to the user's computer.

#### Important technical distinction

The interactive planner calculation is implemented in browser-side JavaScript and uses entered values plus simplified sample rules. It is a separate calculation from the database proposal generator used for **Accounts & suggestions**. Explain them as two demonstrations of the same business idea, not as one shared portfolio record or as identical engines.

If the form is valid and the user is signed in, it automatically sends the plan to the local server after a short pause. A guest can calculate without signing in, but the plan is not saved to a user account. The browser also shows the save status.

### 40–44 min — Sign in and saved plan

Open **Sign in**. Explain the two options: sign in to an existing local account or create one with an email and a passphrase of at least 12 characters. There is no email verification or password reset in this demo.

After signing in, the page displays the account email and whether a saved plan exists. The sidebar changes from Guest planner to the signed-in display name. Signing out revokes the server-side session and clears the browser session cookie.

**Explain storage carefully:**

“This is local sign-in, not cloud storage. Password hashes, sessions, and personal plans are stored in a separate SQLite file on the computer running the app. Plans are isolated by the user's internal ID. This demonstrates basic account flow for the project, but it is not production identity infrastructure. The database is not encrypted at rest, and there is no account recovery process.”

For public hosting, the project would need a production server, HTTPS, rate limiting, logging and monitoring, protected backups and secrets, and account recovery. Do not claim that a local account is safe for sensitive real financial data.

### 44–49 min — Data & examples page

Open **Data & examples**. This page describes the synthetic dataset and its validation report.

- **Metrics:** Counts of investor profiles, instruments, dated prices, and trade records.
- **Dataset integrity:** The validation summary produced during data generation. The exact counts are displayed from the generated metadata, not hard-coded in the page.
- **Fixed seed:** The random seed used to make generated data repeatable.
- **Generated volume:** Generator parameters such as number of portfolios and price days.
- **Provenance:** The dataset is synthetic and does not depend on an external market feed.
- **Export records:** Download individual CSV tables for inspection.
- **Negative scenario fixtures:** Separate, deliberately constructed examples with an expected decision. They help demonstrate edge cases without corrupting the valid baseline tables.
- **Ground truth:** Deterministic labels exported separately from input features for evaluation.

Show the data dictionary and schema as supporting documents if the audience asks for detail. The entities include investor profile, portfolio, instrument, holding, market price, target allocation, fee schedule, constraint, proposal, trade, and post-trade allocation. SQLite primary and foreign keys represent the main relationships.

### 49–53 min — How it works page

Open **How it works**. The page uses a familiar analogy: compare a plan with what is already present, then check whether a possible change follows the rules.

Explain its three cards:

1. **Start with an account:** A sample portfolio links a synthetic investor profile, targets, holdings, and prices.
2. **Compare actual with target:** Value holdings, group by asset class, compute each current percentage, and measure the gap against the target.
3. **Suggest a next step:** Consider a buy or sell and calculate an estimate, while checking restrictions.

The example rule block calls out the five-percentage-point drift trigger, minimum trade, holding availability, instrument eligibility, price availability, and account trading limit. Explain that an example percentage-point trigger is not a financial regulation or universal investing recommendation.

### 53–56 min — Presentation Guide page

Open **Presentation Guide**. The on-screen page gives a short introduction, plain-language definitions, a four-step quick demo, and common question answers. It is there to help a new presenter tell the story without reading code or memorizing jargon.

This 60-minute guide adds the longer technical walkthrough. The main definitions to repeat are:

- **Portfolio:** A collection of investments.
- **Target mix:** The planned percentage in each investment category.
- **Difference / drift:** Current share minus target share, measured in percentage points.
- **Proposal:** A recorded result from the sample policy workflow.
- **Blocked trade:** A possible action retained with a reason because a rule prevented it.

### 56–60 min — Questions and closing

Invite questions. Keep the answers short and return to the page that supports the answer.

Close with:

“To summarize, this project creates reproducible synthetic investment data, compares current and target allocations, applies explainable sample rules, and provides a website to inspect the results. The main strengths are traceability, validation, repeatability, and a beginner-friendly explanation of each decision. The main limits are synthetic data, simplified financial rules, and local-only authentication. A future production version would need licensed market data, exchange calendars, tax and liquidity rules, and a professionally operated secure identity and hosting setup.”

## Page-by-page quick reference

| Page or view | What it is for | Useful thing to demonstrate |
|---|---|---|
| Overview | Summary of dataset and proposal status | Explain cards, status bars, and common exceptions |
| Accounts & suggestions | One place to browse synthetic sample portfolios and their outcomes | Search/filter and open a row |
| Account detail dialog | Current holdings compared with effective targets | Explain current share, target share, and drift |
| Suggestion detail dialog | Trade proposal reasoning and illustrative after mix | Explain one proposed, blocked, or absent action |
| My plan | An independent user-entered educational calculator | Edit inputs, compare targets, run a what-if, view explanations |
| Sign in / account | Local identity for saving personal planner inputs | Explain create account, sign in/out, and local storage boundary |
| Data & examples | Dataset volume, validation, exports, edge cases, labels | Show fixed seed and separate ground truth |
| How it works | Simple overview of the business workflow | Connect holdings, target, drift, and rule checks |
| Presentation Guide | Quick demo script, definitions, and FAQs | Explain how a fresher can present the project |

## Common questions and beginner-friendly answers

### Is this real investment advice?

No. It is an educational simulator. All prices and holdings in sample accounts are synthetic, and the user-entered calculator is not a suitability assessment.

### Does it connect to a broker or Indian stock exchange?

No. It does not request live NSE/BSE data, connect to a broker, or place orders.

### How is a portfolio value calculated?

For the sample dataset, the system multiplies each holding's quantity by the latest available synthetic price and adds the values. The personal planner instead starts from the value and percentages typed into its form.

### What does a percentage point difference mean?

If an investment category is currently 42% and its target is 35%, its drift is +7 percentage points. It is seven points above its planned share; it is not an investment return of 7%.

### Why can a trade be blocked?

The example policy may stop a trade because it is below the minimum, exceeds available units, uses an ineligible instrument, lacks a price, or would go over the turnover limit. The reason should remain visible for review.

### What is the difference between Ready, Review, and On target?

They are generated proposal statuses. On target indicates no rebalance action is needed under the sample rules. Ready means a proposal can be considered under the generated checks. Review flags an exception or a condition needing attention. These labels are not personalized investment suitability advice.

### Why use synthetic data?

Synthetic data makes the project repeatable, safe to share, and able to include known examples without disclosing private customer information or depending on a data license.

### Which packages do I install?

None. Python 3.10 or later is required, but the server, generator, and validator use Python's standard library. The website is plain HTML, CSS, and JavaScript and needs no Node packages.

### Is the account system production-ready?

No. It is a small local demo. It does not include email verification, password recovery, encrypted storage, public hosting controls, or a complete operational security program.

### What would you improve next?

I would add licensed market data and the Indian exchange calendar, then implement more complete tax, liquidity, and lot-level rules. For real users, I would replace local demo authentication with a professionally hosted identity service and add account recovery, monitoring, privacy controls, and security review.

## Presentation reminders

- Explain the goal first, then show the screen that supports it.
- Say “percentage points” when describing allocation drift.
- Pause after each page and ask whether the audience wants to inspect an example.
- Distinguish the sample database portfolios from local login accounts.
- Distinguish the planner's browser calculation from the generated database proposals.
- Call every output simulated or illustrative; do not present it as financial advice or a real order.
- If you do not know an answer, say what the code does today and what would need to be added.
