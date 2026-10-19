---
title: Keeping generated CAN headers current
editLink: false
---

# Keeping generated CAN headers current

The common library stores a CAN message-description file, the DBC, alongside C headers generated from it. This check catches changes that update one without updating the other.

```mermaid
%%{init: {"htmlLabels": false}}%%
flowchart TB
    CHANGE["PR changes DBC,<br/>generator or generated<br/>header; or manual run"] --> CHECKOUT["Check out common;<br/>install Python 3.11"]
    CHECKOUT --> GENERATE["Run dbc_to_c_builder.py"]
    GENERATE --> DIFF["Compare generated<br/>headers with committed<br/>versions"]
    DIFF --> SAME{"Both headers unchanged?"}
    SAME -->|Yes| PASS["Pass: committed output<br/>matches generator"]
    SAME -->|No| FAIL["Fail: regenerate locally<br/>and review header<br/>changes"]
    classDef event fill:#253e64,stroke:#82b4ff,color:#f3f7ff
    classDef work fill:#203f3b,stroke:#66c5ae,color:#f0fff9
    classDef check fill:#514122,stroke:#e8bf63,color:#fff8e8
    classDef failure fill:#512d3d,stroke:#ef91ac,color:#fff1f6
    class CHANGE event
    class CHECKOUT,GENERATE,DIFF,PASS work
    class SAME check
    class FAIL failure
```

## What is compared

The workflow regenerates `drivers/can/can_signal_defs.h` and `drivers/can/can_board_defs.h` from the checked-out inputs, then runs:

```sh
python dbc_to_c_builder.py
git diff --exit-code -- drivers/can/can_signal_defs.h drivers/can/can_board_defs.h
```

A difference fails the job. Regenerate locally, review the changes, and commit the intended headers with the DBC or generator update. This confirms agreement with the generator; vehicle CAN interface requirements need their own review.

## Trigger and ownership

The PR path filter covers `MAIN_DBC.dbc`, `dbc_to_c_builder.py` and the two headers. A manual run is also available. The job uses Ubuntu, Python 3.11 and contents-read permission. This procedure belongs to common, alongside its unit tests and release caller.

Source: [common DBC workflow](https://github.com/ARTTU-Software/common/blob/dev/.github/workflows/dbc_codegen.yml).

[Back to CI/CD overview](/architecture/github)
