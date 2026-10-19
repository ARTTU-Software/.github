---
title: Reviewing code with Clang-Tidy
editLink: false
---

# Reviewing code with Clang-Tidy

Clang-Tidy reads source code and looks for patterns associated with bugs or unnecessary work. It uses the firmware build's compiler settings to understand the target and included headers.

```mermaid
%%{init: {"htmlLabels": false}}%%
flowchart TB
    BUILD["Firmware build succeeds"] --> ARTIFACT["stm32-artifacts contains<br/>compile_commands.json"]
    ARTIFACT --> DOWNLOAD["Download artifact into<br/>build/"]
    DOWNLOAD --> TARGET["Install ARM toolchain;<br/>locate system headers"]
    TARGET --> ANALYSE["Clang-Tidy checks<br/>changed code with<br/>selected rules"]
    ANALYSE --> FINDINGS{"Checks reported<br/>failures?"}
    FINDINGS -->|Yes| FAIL["Fail job; show findings<br/>for review"]
    FINDINGS -->|No| PASS["Analysis job passes"]
    ANALYSE --> REVIEW["Publish job summary and<br/>PR review feedback"]
    classDef event fill:#253e64,stroke:#82b4ff,color:#f3f7ff
    classDef work fill:#203f3b,stroke:#66c5ae,color:#f0fff9
    classDef check fill:#514122,stroke:#e8bf63,color:#fff8e8
    classDef failure fill:#512d3d,stroke:#ef91ac,color:#fff1f6
    class BUILD event
    class ARTIFACT,DOWNLOAD,TARGET,ANALYSE,REVIEW,PASS work
    class FINDINGS check
    class FAIL failure
```

## Reading a finding

Read the diagnostic alongside the changed code and its callers. Decide whether the suggested problem is real for this target, then fix the code or explain why the finding does not apply. Understand the result before changing a rule.

The job waits for the firmware build. If it cannot find the compile database, check the upstream artifact and the caller's dependency before investigating analysis rules.

## Workflow contract

The optional `artifact_name` input defaults to `stm32-artifacts`. The caller orders lint after the build with `needs`. The job downloads the artifact into `build/` and supplies ARM target and system-header arguments to Clang-Tidy.

Enabled rule families are `bugprone-*`, `clang-analyzer-*` and `performance-*`. The YAML excludes selected rules for reserved identifiers, swappable parameters, unsafe buffers, integer-to-pointer performance findings and fixed-address dereferences. Refer to that list when investigating a particular rule.

`Drivers`, `Middlewares`, `test` and `build` are ignored. `lines-changed-only: 2` limits review scope. This provides focused feedback on changes, rather than a complete analysis of the repository.

Clang-Format is disabled. Clang-Tidy reviews, summaries and PR thread updates are enabled; `checks-failed > 0` fails the job. Permissions are contents read, pull requests write and checks write.

Source: [linter.yml](https://github.com/ARTTU-Software/.github/blob/main/.github/workflows/linter.yml).

[Back to CI/CD overview](/architecture/github)
