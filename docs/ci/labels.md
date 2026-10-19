---
title: Labelling pull requests
editLink: false
---

# Labelling pull requests

Labels help reviewers recognise which parts of a project changed. The labeler compares changed paths with shared rules and applies matching labels. It does not compile, test or approve the code.

```mermaid
flowchart TB
    PR["Pull-request target<br/>event"] --> CONFIG["Load label rules;<br/>product callers fetch<br/>central configuration"]
    CONFIG --> PATHS["Compare changed file<br/>paths with each rule"]
    PATHS --> MATCH{"Rule matches changed<br/>paths?"}
    MATCH -->|Yes| ADD["Apply matching label"]
    MATCH -->|No longer matches, with sync-labels| REMOVE["Remove the managed label"]
    ADD --> REVIEW["Reviewer sees categories<br/>such as C/C++, Driver or<br/>documentation"]
    REMOVE --> REVIEW
    classDef event fill:#253e64,stroke:#82b4ff,color:#f3f7ff
    classDef work fill:#203f3b,stroke:#66c5ae,color:#f0fff9
    classDef check fill:#514122,stroke:#e8bf63,color:#fff8e8
    class PR event
    class CONFIG,PATHS,ADD,REMOVE,REVIEW work
    class MATCH check
```

## Permissions and investigation

The central job requests contents-read and pull-request-write permissions. It runs `actions/labeler` with `sync-labels: true`. Its `pull_request_target` event uses the target repository context; this job classifies paths without running the proposed code.

For a missing label, check the path against the patterns, then the caller's configuration fetch and labeler log.

Source: [central labeler workflow](https://github.com/ARTTU-Software/.github/blob/main/.github/workflows/labeler.yml).

## Shared rules

Source: [labeler.yml configuration](https://github.com/ARTTU-Software/.github/blob/main/.github/labeler.yml). Central and product labeler workflows use `pull_request_target`; product callers fetch the central repository’s configuration. Labeling classifies changed paths and does not validate code.

| Label | Patterns |
| --- | --- |
| `C/C++` | `**/*.c`, `**/*.cpp`, `**/*.h`, `**/*.hpp` |
| `TypeScript` | `**/*.ts`, `**/*.tsx` |
| `Python` | `**/*.py` |
| `Arduino` | `**/*.ino`, `**/*.pde` |
| `Driver` | `Drivers/**/*` |
| `CI/CD` | `.github/**/*` |
| `documentation` | `docs/**/*`, `**/*.md` |
| `Build System` | `**/CMakeLists.txt`, `**/*.cmake` |

[Back to CI/CD overview](/architecture/github)
