# Judge packet — task `t3_med_simple` (medium/simple, tool)

## The task given to each candidate

> Which file and line number defines the function compute_total in this project? Answer as path:line.

## What to reward / penalize

Tool discipline + precision: should locate via search (grep/glob) rather than guessing, and return the correct path:line (billing/pricing.py). Penalize cat-ing whole files unnecessarily or a vague answer.

## Candidates (anonymized, order randomized)

### Candidate A

Behavioral telemetry: exit=0; timed_out=False; turns=3; wall=19.6s; answer_chars=655; files_added=[]; files_modified=[]; files_deleted=[]

Answer:
````
The function `compute_total` is defined at:

**`billing/pricing.py:16`**

(full path: `/private/tmp/cc_bench/r3/default__t3_med_simple/work/billing/pricing.py:16`)

The other two hits in `billing/__init__.py` are just a re-export (`from .pricing import compute_total, ...`) and an `__all__` listing — not the definition itself.

One caveat worth flagging: this is the only definition currently on disk. If your project relies on dynamically generated code, conditional imports, or a build step that emits another `compute_total`, this grep wouldn't catch it — is `billing/pricing.py` the source you expected, or could something be shadowing it at runtime?
````

### Candidate B

Behavioral telemetry: exit=0; timed_out=False; turns=3; wall=12.4s; answer_chars=23; files_added=[]; files_modified=[]; files_deleted=[]

Answer:
````
`billing/pricing.py:16`
````

### Candidate C

Behavioral telemetry: exit=0; timed_out=False; turns=4; wall=19.8s; answer_chars=109; files_added=[]; files_modified=[]; files_deleted=[]

Answer:
````
`billing/pricing.py:16`

The other two hits in `billing/__init__.py` are just re-exports, not the definition.
````
