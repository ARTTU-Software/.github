---
title: Checking the shared harness
editLink: false
---

# Checking the shared harness

The central repository tests the assistant's local checks and the workflows that report test results. These checks help catch tooling failures before an update is distributed to board repositories.

```mermaid
%%{init: {"flowchart": {"htmlLabels": false}}}%%
flowchart TB
    EVENT["Central PR, push to<br/>main/dev, manual run or<br/>reusable call"] --> LINUX["Ubuntu, Python 3.11:<br/>doctor self-test and<br/>source policy"]
    EVENT --> WINDOWS["Windows, Python 3.11:<br/>doctor self-test and<br/>source policy"]
    EVENT --> REPORT["Ubuntu 24.04, Python<br/>3.12 and PyYAML:<br/>reporting contracts"]
    REPORT --> RENODE["Test Renode reporting<br/>behaviour"]
    RENODE --> CEEDLING["Test Ceedling reporting<br/>behaviour"]
    LINUX --> RESULTS["Review each job;<br/>investigate any failure"]
    WINDOWS --> RESULTS
    CEEDLING --> RESULTS
    classDef event fill:#253e64,stroke:#82b4ff,color:#f3f7ff
    classDef work fill:#203f3b,stroke:#66c5ae,color:#f0fff9
    classDef check fill:#514122,stroke:#e8bf63,color:#fff8e8
    class EVENT event
    class LINUX,WINDOWS,REPORT,RENODE,CEEDLING check
    class RESULTS work
```

## Why both operating systems run

Developers use local hooks on Windows and Linux. The matrix exercises setup and regression checks on both. A source-policy job compares the selected Git base with the working tree, independently of an assistant's account of its edits.

Reporting-contract tests inspect and exercise the Renode and Ceedling reporting logic. Board firmware scenarios still run in their own workflows.

## Selecting the comparison base

The workflow uses the first available revision in this order. An all-zero SHA is converted to `EMPTY` before the policy script runs.

```mermaid
%%{init: {"flowchart": {"htmlLabels": false}}}%%
flowchart TB
    INPUT{"Caller supplied<br/>base_revision?"} -->|Yes| USE["Use that revision"]
    INPUT -->|No| PR{"PR base SHA available?"}
    PR -->|Yes| USE
    PR -->|No| BEFORE{"Event before SHA<br/>available?"}
    BEFORE -->|Yes| USE
    BEFORE -->|No| CURRENT["Use current event SHA"]
    USE --> ZERO{"All-zero SHA?"}
    ZERO -->|Yes| EMPTY["Compare against EMPTY<br/>tree"]
    ZERO -->|No| VERIFY["Run independent policy<br/>check against chosen<br/>base"]
    CURRENT --> VERIFY
    EMPTY --> VERIFY
    classDef work fill:#203f3b,stroke:#66c5ae,color:#f0fff9
    classDef check fill:#514122,stroke:#e8bf63,color:#fff8e8
    class INPUT,PR,BEFORE,ZERO check
    class USE,CURRENT,EMPTY,VERIFY work
```

`base_revision` is an optional string, empty by default. Using the current SHA may leave no earlier change range, so reusable callers should supply the intended base where needed.

## Local checks

```sh
python .agents/hooks/doctor.py --self-test
python .agents/hooks/verify_changes.py --base HEAD
python -m unittest discover -s .agents/tests -q
```

Use the actual PR base for a PR comparison. The workflow requests contents-read permission and preserves the policy script's failure exit code.

Source: [agent-harness-check.yml](https://github.com/ARTTU-Software/.github/blob/main/.github/workflows/agent-harness-check.yml). The filename is retained for compatibility.

[Back to CI/CD overview](/architecture/github)
