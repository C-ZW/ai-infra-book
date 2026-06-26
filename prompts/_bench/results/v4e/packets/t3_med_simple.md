# Judge packet — task `t3_med_simple` (medium/simple, tool)

## The task given to each candidate

> Which file and line number defines the function compute_total in this project? Answer as path:line.

## What to reward / penalize

Tool discipline + precision: should locate via search (grep/glob) rather than guessing, and return the correct path:line (billing/pricing.py). Penalize cat-ing whole files unnecessarily or a vague answer.

## Candidates (anonymized, order randomized)

### Candidate A

Behavioral telemetry: exit=0; timed_out=False; turns=3; wall=11.9s; answer_chars=192; files_added=[]; files_modified=[]; files_deleted=[]

Answer:
````
The canonical source is:

`prompts/_bench/seeds/t3/billing/pricing.py:16`

(The sandbox copy at `prompts/_bench/_sandboxes/v4e/v1__t3_med_simple/work/billing/pricing.py:16` is a derived copy.)
````

### Candidate B

Behavioral telemetry: exit=0; timed_out=False; turns=3; wall=11.6s; answer_chars=23; files_added=[]; files_modified=[]; files_deleted=[]

Answer:
````
`billing/pricing.py:16`
````

### Candidate C

Behavioral telemetry: exit=0; timed_out=False; turns=3; wall=14.5s; answer_chars=47; files_added=[]; files_modified=[]; files_deleted=[]

Answer:
````
`prompts/_bench/seeds/t3/billing/pricing.py:16`
````
