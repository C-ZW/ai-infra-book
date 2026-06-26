# Judge packet — task `t3_med_simple` (medium/simple, tool)

## The task given to each candidate

> Which file and line number defines the function compute_total in this project? Answer as path:line.

## What to reward / penalize

Tool discipline + precision: should locate via search (grep/glob) rather than guessing, and return the correct path:line (billing/pricing.py). Penalize cat-ing whole files unnecessarily or a vague answer.

## Candidates (anonymized, order randomized)

### Candidate A

Behavioral telemetry: exit=0; timed_out=False; turns=2; wall=16.4s; answer_chars=442; files_added=[]; files_modified=[]; files_deleted=[]

Answer:
````
`billing/pricing.py:16`

It's defined as `def compute_total(items, discount_pct=0.0):` — the only definition in the project.

One thing worth flagging since it's the most dangerous unhandled case: that `discount_pct` default is unbounded — nothing in the signature stops a caller passing `120` (negative total) or a string (TypeError mid-loop). Do you want me to check how `compute_total` validates `items` and `discount_pct` at its boundary?
````

### Candidate B

Behavioral telemetry: exit=0; timed_out=False; turns=4; wall=18.4s; answer_chars=23; files_added=[]; files_modified=[]; files_deleted=[]

Answer:
````
`billing/pricing.py:16`
````

### Candidate C

Behavioral telemetry: exit=0; timed_out=False; turns=4; wall=18.9s; answer_chars=269; files_added=[]; files_modified=[]; files_deleted=[]

Answer:
````
`billing/pricing.py:16`

Only one definition exists — `def compute_total(items, discount_pct=0.0)`. Note that if it's also assigned/aliased elsewhere or shadowed by an import, the call site could resolve to something other than this line; the search found no such case.
````
