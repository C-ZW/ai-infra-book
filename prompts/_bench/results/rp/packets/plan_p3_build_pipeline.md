# Judge packet — task `plan_p3_build_pipeline` (medium/hard, tool)

## The task given to each candidate

> Produce an implementation plan — do NOT implement anything, output only the plan. Task to plan: build an expense-report tool with three components (a CSV parser, an aggregator that totals amount by category, a formatter that renders a report sorted by total descending), wired in main(), with a test per component. Read expenses.csv / README to ground the plan. Cover: the components and their interfaces, ordered steps, how you would verify each, and risks or clarifying questions.

## What to reward / penalize

PLAN QUALITY for a from-scratch multi-component build. A strong plan defines the three components AND their interfaces/data shapes (record type, aggregator output, formatter input), sequences build+test per component then integration in main(), and flags risks (CSV parsing edge cases, amount as float/Decimal, empty categories, sort tie-break). Must stay at plan altitude. Penalize a monolithic non-decomposed plan, undefined interfaces, missing tests/verification, or implementing instead of planning.

## Candidates (anonymized, order randomized)

### Candidate A

Behavioral telemetry: exit=0; timed_out=False; turns=4; wall=76.8s; answer_chars=7010; files_added=[]; files_modified=[]; files_deleted=[]

Answer:
````
Both files read. The project is language-agnostic (no `package.json`, `pyproject.toml`, or sources yet — just the CSV and README), so I'll default the plan to **Python 3 with the stdlib `csv` module + `pytest`** and flag that as the top clarifying question. Rationale: zero runtime deps, stdlib CSV handling, and a tiny test surface. Everything below maps cleanly onto another language if you'd rather.

Grounding facts from the data: header is `date,category,amount`; 7 data rows; categories total to rent `900.00`, entertainment `40.00`, food `36.25`, transport `6.40` — so the correct sorted report is rent → entertainment → food → transport. I'll use this as the golden expected output in tests.

---

# Implementation Plan: expense-report tool

## 0. Assumptions (callout)
- Language: **Python 3.11+**, stdlib `csv`, `decimal.Decimal` for money, `pytest` for tests. (See clarifying Q1 — swap if wrong.)
- Layout: `expense_report.py` (the three components + `main`), `test_expense_report.py`, run via `python expense_report.py expenses.csv`.
- Money is parsed as `Decimal`, never `float`, to avoid binary-float rounding on currency.

## 1. Components and interfaces

Three pure, independently-testable functions plus a thin `main`. Each is pure (no I/O) except the parser's file-open wrapper and `main`'s print — this is what makes per-component testing clean.

**Data type**
```
@dataclass(frozen=True)
class Expense:
    date: str          # kept as raw string; not needed for aggregation
    category: str
    amount: Decimal
```

**a) Parser**
```
def parse_expenses(lines: Iterable[str]) -> list[Expense]
def parse_expenses_file(path: str) -> list[Expense]   # thin wrapper: open + delegate
```
- Takes an iterable of text lines (or a file stream), *not* a path, so tests pass `io.StringIO` with no fixture files. The `_file` wrapper handles opening with explicit `encoding="utf-8-sig"` (strips BOM) and `newline=""`.
- Uses `csv.DictReader`; validates header is exactly `date,category,amount`.
- Per row: strip whitespace; validate column count; parse `amount` via `Decimal(...)` inside try/except; normalize `category` (decide case policy — see Q3).
- **Failure return:** raises a named `ParseError(row_number, reason)` — not a bare `Exception` — so `main` can report *which* line broke. Decide skip-vs-fail policy (Q2).

**b) Aggregator**
```
def aggregate(records: Iterable[Expense]) -> dict[str, Decimal]
```
- Pure. Sums `amount` per `category` into a dict, starting each at `Decimal("0")`.
- Empty input → `{}` (not an error).
- No rounding here; preserves full precision. Rounding/quantization is the formatter's job.

**c) Formatter**
```
def format_report(totals: Mapping[str, Decimal]) -> str
```
- Pure. Sorts items by total **descending**, with a defined tiebreak: `key=lambda kv: (-kv[1], kv[0])` (category name ascending) so output is deterministic on ties.
- Quantizes each total to 2 dp (`q.quantize(Decimal("0.01"))`) for display.
- Returns a string (does not print) so it's assertable in tests. Empty totals → a defined string (e.g. header + "(no expenses)").

**d) main**
```
def main(argv: list[str]) -> int
```
- Reads path from `argv[1]` (default `expenses.csv`); wires `parse_expenses_file → aggregate → format_report`; prints result; returns exit code (0 ok, non-zero on `ParseError`/missing file). Guarded by `if __name__ == "__main__": sys.exit(main(sys.argv))`.

## 2. Ordered steps
1. Scaffold `expense_report.py` with the `Expense` dataclass and `ParseError`.
2. Implement **parser** (stream version + file wrapper). Verify (3a).
3. Implement **aggregator**. Verify (3b).
4. Implement **formatter**. Verify (3c).
5. Wire **`main`**; run end-to-end against real `expenses.csv`. Verify (3d).
6. Write `test_expense_report.py` — one test per component + one end-to-end. Run full suite.
7. Decide test runner is available (`pip install pytest` or fall back to stdlib `unittest`).

Build bottom-up (parser → aggregator → formatter → main) so each layer is verified before the next depends on it.

## 3. How to verify each
- **Parser:** feed `StringIO` of the known CSV → assert 6... *(actually 7)* records, correct types, `amount` is `Decimal`. Separate tests: missing file raises, header-only yields `[]`, malformed row (2 columns) raises `ParseError` with the right row number, non-numeric amount raises.
- **Aggregator:** feed hand-built `Expense` list → assert `{"food": Decimal("36.25"), "transport": Decimal("6.40"), "rent": Decimal("900.00"), "entertainment": Decimal("40.00")}`. Plus empty-input → `{}`.
- **Formatter:** feed the totals dict → assert exact output string with order **rent, entertainment, food, transport**. Add a tie case (two categories equal total) to lock the tiebreak.
- **main / end-to-end:** run `python expense_report.py expenses.csv`, capture stdout, assert it matches the golden report; assert exit code 0. Run nonexistent path → non-zero exit, error on stderr.
- **Tooling:** `pytest -q` (or `python -m unittest`). Optionally `python -m py_compile expense_report.py` as a smoke check.

## 4. Risks / failure modes (Anxious-Engineer pass)
- **Float money drift** — using `float` would make sums like `0.1+0.2` wrong; mitigated by `Decimal` end-to-end.
- **Malformed rows** — wrong column count, empty `amount`, non-numeric `amount`, stray whitespace, trailing blank line. Policy must be explicit: fail-fast vs skip-and-warn (Q2).
- **Encoding/BOM** — a UTF-8 BOM would corrupt the first header name; mitigated with `utf-8-sig`.
- **Category casing/whitespace** — `Food` vs `food`, `"food "` would split one category into two buckets (Q3).
- **Negative amounts (refunds)** — allowed? They can make a total negative and reorder the report. Currently unhandled — needs a decision (Q4).
- **Tie ordering** — equal totals are non-deterministic without a secondary key; handled by the `(-total, name)` sort key.
- **Empty / header-only file** — must yield an empty report, not crash.
- **Locale decimals** — `"1.234,56"` (comma decimal) would fail `Decimal`; out of scope unless data can be localized.

## 5. Clarifying questions
1. **Language/stack** — Python+pytest as assumed, or a specific language (JS/TS, Go)? This changes every interface.
2. **Bad-row policy** — fail the whole run on the first malformed row, or skip it with a warning and total the rest?
3. **Category normalization** — case-insensitive and whitespace-trimmed (merge `Food`/`food `), or treat strings exactly as written?
4. **Negative amounts** — permitted (refunds) or rejected as invalid?
5. **Output format** — exact report shape (currency symbol, column alignment, grand-total line)? I'll default to `category    total` aligned columns with 2-dp amounts and no currency symbol.

The single most dangerous unhandled case: if the bad-row policy (Q2) is "skip silently," a malformed `amount` line would vanish from the totals and the report would look complete while being quietly wrong — which financial output should never do. Do you want fail-fast or skip-with-warning?
````

### Candidate B

Behavioral telemetry: exit=0; timed_out=False; turns=4; wall=70.4s; answer_chars=7217; files_added=[]; files_modified=[]; files_deleted=[]

Answer:
````
I have everything I need. Here's the implementation plan — grounded in the actual `expenses.csv` (7 data rows, columns `date,category,amount`) and `README.md` (three required components + `main()` + one test each).

---

# Implementation Plan: expense-report tool

## 0. Assumptions & key decisions (please confirm — see §6)
- **Language: Python 3 (stdlib only).** No manifest or existing code in the repo, and the README is language-agnostic. Python gives us `csv` (robust parsing), `decimal`, and `unittest` with zero dependencies. *If you want another language, this plan maps 1:1.*
- **Money is `Decimal`, never `float`.** `12.50 + 8.00 + 15.75` and friends must total `36.25` exactly. Binary floats silently drift (e.g. classic `0.1+0.2`), and an expense report that's off by a cent is a bug report. `Decimal(str(amount))` is the non-negotiable boundary.
- **Layout:** one module `expense_report.py` (parser + aggregator + formatter + `main`) and one test file `test_expense_report.py`. Small tool → one module is clearer than four files; the three functions stay independently testable.

## 1. Components & interfaces

A small typed record carries data between stages:

```
@dataclass(frozen=True)
class Expense:
    date: str          # kept as raw string; not needed for totals (see risks)
    category: str
    amount: Decimal
```

**1. Parser** — `parse_expenses(path: str) -> list[Expense]`
- Opens the file with `newline=""`, `encoding="utf-8"`, parses via `csv.DictReader`.
- Validates the header is exactly `date,category,amount` (fail fast if not — a shifted column means every amount is wrong).
- Per row: strip whitespace; reject wrong field count, empty category, empty/non-numeric amount.
- Converts amount with `Decimal(value)`, wrapping `InvalidOperation` in a **named, line-numbered error**.
- **Failure contract:** raises a custom `ExpenseParseError(line_no, reason)` — never returns half-parsed/silent-skipped data by default (see §6 Q4).

**2. Aggregator** — `aggregate(expenses: Iterable[Expense]) -> dict[str, Decimal]`
- Folds into `{category: total}`. Pure function, no I/O.
- Empty input → empty dict (not an error).
- Category match is exact/case-sensitive (data is already lowercase; see §6 Q5).

**3. Formatter** — `format_report(totals: Mapping[str, Decimal]) -> str`
- Sorts items by **total descending**, with a **secondary sort by category name ascending** so equal totals produce deterministic, repeatable output (no ties in this data, but transport/food-style ties are inevitable in real data — a nondeterministic report is untestable).
- Renders aligned columns, amounts quantized to 2 dp (`.quantize(Decimal("0.01"))`).
- Empty totals → a defined string (e.g. `"No expenses."`), not a blank/crash.
- Pure function: takes a mapping, returns a string (does not print) — keeps it unit-testable.

**Wiring** — `main(argv=None) -> int`
- Resolves CSV path: `argv[1]` if given, else default `"expenses.csv"`.
- `parse → aggregate → format`, prints the report, returns exit code `0`.
- Catches `ExpenseParseError`/`FileNotFoundError`, writes a clear message to `stderr`, returns non-zero. `if __name__ == "__main__": sys.exit(main())`.

**Expected output for the committed data** (the verification oracle):
```
rent           900.00
entertainment   40.00
food            36.25
transport        6.40
```
(rent 900.00 > entertainment 40.00 > food 36.25 > transport 6.40.)

## 2. Ordered steps
1. **Scaffold** `expense_report.py` with the `Expense` dataclass, `ExpenseParseError`, and the four function stubs/signatures above.
2. **Formatter first** (pure, no I/O — easiest to pin behavior): implement sort + alignment + empty case.
3. **Aggregator**: implement the fold; confirm against hand-computed totals.
4. **Parser**: implement header check, row validation, `Decimal` conversion, error raising.
5. **`main()`**: wire the three together, add path arg + error handling + exit codes.
6. **Tests**: `test_expense_report.py` with one test per component (§3), plus a tiny fixture.
7. **Run** the suite and the tool end-to-end against the real `expenses.csv`; diff against the expected output in §1.

## 3. How I'd verify each component
- **Parser test:** feed a 2–3 line in-memory/`tmp_path` CSV → assert it returns the right count of `Expense` rows with `Decimal` amounts. Add one negative case: a non-numeric amount raises `ExpenseParseError` with the offending line number.
- **Aggregator test:** hand-built `[Expense]` list with a repeated category → assert exact `Decimal` totals (e.g. food `Decimal("36.25")`). Include the empty-list → `{}` case.
- **Formatter test:** pass `{"rent": Decimal("900.00"), "food": Decimal("36.25"), "transport": Decimal("6.40")}` → assert the output lines are in descending order and rent precedes food precedes transport. Add a **tie case** (two equal totals) → assert alphabetical secondary order.
- **End-to-end (manual):** `python expense_report.py expenses.csv` → byte-compare to §1's expected block. Also run with a missing file → assert non-zero exit and a readable error.
- **Suite:** `python -m unittest -v` is green.

## 4. Failure modes explicitly handled
Missing file; empty file (header only → empty report, not a crash); blank/whitespace rows; wrong column count; non-numeric/empty amount; unexpected header order; quoted fields or embedded commas (handled for free by `csv`, not hand-splitting); equal totals (deterministic tie-break); `float` drift (avoided via `Decimal`).

## 5. Out of scope (unless requested)
Currency symbols/locale formatting, multi-file/glob input, date filtering, grand-total line, config flags, packaging/CLI framework.

## 6. Risks & clarifying questions
1. **Language** — Plan assumes Python 3 stdlib. Confirm, or name your target (Node, Go, etc.).
2. **Report format** — I assumed plain aligned text, 2-dp, no currency symbol, no header row. Do you want a header (`CATEGORY  TOTAL`) and/or a **grand-total line**? *Recommend: add a grand total; it's the first thing a reviewer eyeballs.*
3. **Numeric type** — Confirm `Decimal` (recommended) over `float`. Output precision = 2 dp?
4. **Malformed rows: fail-fast vs skip-and-warn** — I default to **fail-fast** (reject the whole run on a bad row) to protect data integrity. If this feeds a flaky upstream, you may prefer skip-with-stderr-warning. Which?
5. **Category normalization** — Data is already lowercase. Should `Food` and `food` merge (case-insensitive) or stay distinct? *Recommend: distinct for now; revisit if real data is messy.*
6. **Negative amounts / refunds** — None in the sample. Allow them (summed normally) or reject as invalid? *Recommend: allow.*
7. **`date` column** — Unused for totals. Keep it parsed-but-ignored (as planned) or validate it as a real date? *Recommend: keep raw; don't add validation nobody consumes.*

---

The single most dangerous unhandled case if we ship the "obvious" version: using `float` for `amount` — every total would *look* right in casual testing yet drift by sub-cent amounts on larger real datasets, and you'd only discover it when someone reconciles the report against a bank statement. Shall I lock in `Decimal` and fail-fast parsing as the defaults, or do you want skip-and-warn parsing instead?
````

### Candidate C

Behavioral telemetry: exit=0; timed_out=False; turns=7; wall=73.5s; answer_chars=6454; files_added=[]; files_modified=[]; files_deleted=[]

Answer:
````
Grounded in the actual files. Here's the plan.

---

## Context (from the repo)

- `expenses.csv` — header `date,category,amount`, 7 data rows, currency amounts with 2 decimals, one trailing blank line. Categories repeat (`food`, `transport`, `rent`, `entertainment`).
- `README.md` — wants 3 components (parser → aggregator → formatter), wired in `main()`, **one test per component**.
- No language, build config, or git repo present. Python 3.13 and Node 24 both available.

## Key decision (please confirm — see clarifying questions)

**Language: Python 3, stdlib only** (`csv`, `decimal`, `unittest`). Rationale: smallest tool that satisfies "test per component" with zero dependencies; `csv` handles quoting/edge cases for free. I'll proceed on this default unless you say otherwise.

**Money: `decimal.Decimal`, not `float`.** `12.50 + 8.00 + 15.75` in binary float drifts (e.g. `36.249999…`); a report that's a cent off is a silent data-correctness bug. Decimal is exact for currency.

## Proposed layout

```
expense_report.py        # parser, aggregator, formatter, main()
test_expense_report.py   # one test class per component
expenses.csv             # exists
```

Single module keeps a 3-function tool navigable; splitting into a package is over-engineering at this size.

## Components and interfaces

**1. Parser**
```python
@dataclass(frozen=True)
class Expense:
    date: str
    category: str
    amount: Decimal

def parse(rows: Iterable[str]) -> list[Expense]      # core: takes lines/file object
def parse_file(path: str) -> list[Expense]           # thin wrapper: opens path, calls parse
```
- Core takes an iterable of lines (or file object) so tests need no fixture file on disk.
- Uses `csv.DictReader`; validates header has `date,category,amount`.
- Skips blank lines (handles the trailing newline in the data).
- Normalizes: `category.strip().lower()`, `date.strip()`.
- Raises a **named** `ParseError(line_no, reason)` on: missing/extra columns, non-decimal amount, missing header. Decision per clarifying-Q whether bad rows raise vs. skip-with-warning.

**2. Aggregator**
```python
def aggregate(expenses: Iterable[Expense]) -> dict[str, Decimal]
```
- Sums `amount` per `category`. Pure function, no I/O.
- Empty input → `{}` (not an error).
- Starts each category at `Decimal("0")`; preserves Decimal precision.

**3. Formatter**
```python
def format_report(totals: Mapping[str, Decimal]) -> str
```
- Sorts by total **descending**, **tie-break by category name ascending** (determinism — without this, equal totals order is undefined and tests flake).
- Renders each line `category` + right-aligned amount at 2 dp (`{:.2f}`), plus a `TOTAL` line.
- Empty totals → a defined "no expenses" string, not a blank/crash.

**4. main()**
```python
def main(argv: list[str]) -> int
```
- Path from `argv[1]` else default `expenses.csv`.
- `parse_file → aggregate → format_report → print`.
- Wraps `FileNotFoundError` and `ParseError` into a stderr message + non-zero exit code; returns `0` on success.
- Guarded by `if __name__ == "__main__": sys.exit(main(sys.argv))`.

## Ordered steps

1. Scaffold module with `Expense`, `ParseError`, and the four signatures (stubbed).
2. Implement **parser** (core + file wrapper, header validation, skip-blank, normalization, error path).
3. Implement **aggregator** (pure sum).
4. Implement **formatter** (sort desc + tie-break, 2-dp alignment, empty case).
5. Wire **main()** (arg/default path, error handling, exit codes).
6. Write `test_expense_report.py` — one test class per component (below).
7. Run tests + a real `python3 expense_report.py` against the bundled CSV; confirm totals reconcile by hand.

## Verification per component

- **Parser**: feed an in-memory list of lines → assert exact `[Expense(...)]`; assert blank line skipped; assert `ParseError` raised on a row with a non-numeric amount and on a bad header. (`assertRaises`.)
- **Aggregator**: feed known `Expense` list → assert exact dict, e.g. `food = Decimal("36.25")`, `transport = Decimal("6.40")`; assert `aggregate([]) == {}`.
- **Formatter**: feed a known totals dict (including a deliberate tie) → assert the **exact** output string, proving descending order + tie-break + 2-dp formatting; assert empty-dict case.
- **Whole tool**: `python3 -m unittest` (zero deps, no discovery config needed) and one manual run; hand-check `food=36.25, rent=900.00, transport=6.40, entertainment=40.00` so `rent` sorts first.

Expected report order from the real data: `rent (900.00) → entertainment (40.00) → food (36.25) → transport (6.40)`.

## Risks / failure modes

- **Float money** → cent-level drift. Mitigated by Decimal (above).
- **Undefined tie-break** → non-deterministic order, flaky test. Mitigated by secondary sort on category.
- **Category drift** — `"Food"`, `"food "`, `"food"` aggregate separately and silently inflate the category count. Mitigated by strip+lowercase normalization (confirm this is wanted — it's lossy on display casing).
- **Malformed amount** (e.g. `$12.50`, `12,50`, empty) → `Decimal` raises `InvalidOperation`; caught and re-raised as `ParseError` with line number rather than a bare stack trace.
- **Negative amounts** (refunds) — currently allowed and summed; could make a category total negative and reorder the report. Need a decision.
- **Empty / header-only file** → must produce an empty report, not divide-by-zero or crash.
- **BOM / encoding** — a UTF-8 BOM on the header would break column matching; open with `encoding="utf-8-sig"`.
- **Duplicate/extra columns or reordered header** → `DictReader` validation guards this.

## Clarifying questions

1. **Language** — Python 3 (my default), or Node/another? Changes everything downstream.
2. **Bad rows** — fail fast (`ParseError`, exit non-zero) or skip-and-warn and still report the rest?
3. **Category normalization** — fold case/whitespace (`Food`==`food`), or treat exactly as written?
4. **Negative amounts** — valid (refunds) or rejected?
5. **Output** — plain text to stdout enough, or do you want totals also as CSV/JSON, and any currency symbol/locale?

The most dangerous unhandled case: if `amount` ever arrives as `float` instead of `Decimal` anywhere in the chain, totals will look right in tests with small inputs and silently go a cent wrong on larger real data — do you want the parser to *hard-reject* any amount that doesn't round-trip exactly through `Decimal`, so that failure is loud instead of latent?
````
