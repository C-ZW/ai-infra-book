# Judge packet — task `t3_med_simple` (medium/simple, tool)

## The task given to each candidate

> Which file and line number defines the function compute_total in this project? Answer as path:line.

## What to reward / penalize

Tool discipline + precision: should locate via search (grep/glob) rather than guessing, and return the correct path:line (billing/pricing.py). Penalize cat-ing whole files unnecessarily or a vague answer.

## Candidates (anonymized, order randomized)

### Candidate A

Behavioral telemetry: exit=0; timed_out=False; turns=2; wall=16.5s; answer_chars=23; files_added=[]; files_modified=[]; files_deleted=[]

Answer:
````
`billing/pricing.py:16`
````

### Candidate B

Behavioral telemetry: exit=0; timed_out=False; turns=3; wall=13.1s; answer_chars=23; files_added=[]; files_modified=[]; files_deleted=[]

Answer:
````
`billing/pricing.py:16`
````

### Candidate C

Behavioral telemetry: exit=0; timed_out=False; turns=3; wall=15.6s; answer_chars=23; files_added=[]; files_modified=[]; files_deleted=[]

Answer:
````
`billing/pricing.py:16`
````
