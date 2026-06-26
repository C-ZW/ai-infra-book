# Judge packet — task `t3_med_simple` (medium/simple, tool)

## The task given to each candidate

> Which file and line number defines the function compute_total in this project? Answer as path:line.

## What to reward / penalize

Tool discipline + precision: should locate via search (grep/glob) rather than guessing, and return the correct path:line (billing/pricing.py). Penalize cat-ing whole files unnecessarily or a vague answer.

## Candidates (anonymized, order randomized)

### Candidate A

Behavioral telemetry: exit=0; timed_out=False; turns=2; wall=10.6s; answer_chars=112; files_added=[]; files_modified=[]; files_deleted=[]

Answer:
````
`billing/pricing.py:16`

It's the only definition; the other hits in `billing/__init__.py` are just a re-export.
````

### Candidate B

Behavioral telemetry: exit=0; timed_out=False; turns=3; wall=14.5s; answer_chars=132; files_added=[]; files_modified=[]; files_deleted=[]

Answer:
````
`billing/pricing.py:16`

That's the only definition in the project (a Python function `def compute_total(items, discount_pct=0.0)`).
````

### Candidate C

Behavioral telemetry: exit=0; timed_out=False; turns=3; wall=13.5s; answer_chars=192; files_added=[]; files_modified=[]; files_deleted=[]

Answer:
````
`billing/pricing.py:16`

The definition is `def compute_total(items, discount_pct=0.0):` in `billing/pricing.py`. (The other two hits in `billing/__init__.py` are re-exports, not definitions.)
````
