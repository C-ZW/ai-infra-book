# Judge packet — task `t3_med_simple` (medium/simple, tool)

## The task given to each candidate

> Which file and line number defines the function compute_total in this project? Answer as path:line.

## What to reward / penalize

Tool discipline + precision: should locate via search (grep/glob) rather than guessing, and return the correct path:line (billing/pricing.py). Penalize cat-ing whole files unnecessarily or a vague answer.

## Candidates (anonymized, order randomized)

### Candidate A

Behavioral telemetry: exit=0; timed_out=False; turns=2; wall=13.2s; answer_chars=439; files_added=[]; files_modified=[]; files_deleted=[]

Answer:
````
`billing/pricing.py:16`

The function `compute_total` is defined at line 16 of `billing/pricing.py` (a Python `def compute_total(items, discount_pct=0.0):`).

One caveat worth flagging: that grep matched a single definition, but if this project has any test mocks, re-exports, or shadowing definitions elsewhere, a name can be redefined. Want me to confirm there's no second definition or re-export of `compute_total` anywhere in the tree?
````

### Candidate B

Behavioral telemetry: exit=0; timed_out=False; turns=4; wall=13.9s; answer_chars=107; files_added=[]; files_modified=[]; files_deleted=[]

Answer:
````
`billing/pricing.py:16`

Single definition found, in Python: `def compute_total(items, discount_pct=0.0):`.
````

### Candidate C

Behavioral telemetry: exit=0; timed_out=False; turns=4; wall=16.6s; answer_chars=185; files_added=[]; files_modified=[]; files_deleted=[]

Answer:
````
`billing/pricing.py:16`

That's the sole definition (`def compute_total(items, discount_pct=0.0)`); the other two hits in `billing/__init__.py` are just the re-export, not a definition.
````
