# expense-report

Build a small expense-report tool over `expenses.csv` (columns:
`date,category,amount`).

Required components:
1. **parser** — read `expenses.csv` into records.
2. **aggregator** — total `amount` per `category`.
3. **formatter** — render a report, categories sorted by total descending.

Wire them together in a `main()`, and add a test per component.
