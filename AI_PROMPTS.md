# AI-assisted development prompts

The following professional project specifications summarize the AI-assisted development work. They document project requirements and implementation scope without reproducing personal conversation text.

## 1. Portfolio rebalancing solution

Design and implement an explainable portfolio rebalancing application. Compare investor holdings with effective target allocations, calculate market values and allocation drift, apply policy constraints, estimate fees, create traceable proposals and trade outcomes, and calculate illustrative post-trade allocations. Clearly explain decisions, exceptions, and limitations.

## 2. Synthetic data and validation

Build a deterministic, parameterized synthetic data generator for investor profiles, portfolios, instruments, holdings, dated market prices, target allocations, fee schedules, constraints, proposals, trades, and post-trade allocations. Use stable identifiers, valid foreign keys, documented fields and relationships, and reproducible seeds. Generate valid baseline records before adding separately labelled edge cases. Export SQLite, CSV, and JSON outputs with a manifest, ground truth, and validation summary. Validate keys, relationships, enumerations, arithmetic, dates, rules, and repeatability.

## 3. Local web application and Indian presentation

Create a complete, beginner-friendly web application using INR and Indian number/date formats. Provide an overview, searchable sample accounts with proposal results, account details, methodology, example data, exports, and a presentation guide. Include a personal allocation planner with editable targets, comparison presets, simulated price scenarios, rule explanations, downloadable results, and clear educational-use disclosures. Use synthetic data only; do not connect to a broker, place orders, or imply investment advice.

## 4. Account access and plan persistence

Add account registration and sign-in for users who want to save and restore personal plans. Hash passphrases with a unique salt, use server-managed expiring sessions and secure cookie attributes where HTTPS is available, protect state-changing requests against cross-site request forgery, and isolate plans by account. Keep authentication storage separate from generated sample data. Document local-demo limitations and production deployment requirements.

## 5. Documentation and delivery

Document the application architecture, business rules, assumptions, limitations, required runtime, package dependencies, setup commands, data generation, validation, and demo steps. Keep setup reproducible and suitable for a beginner to run and present.
