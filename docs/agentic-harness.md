---
title: Agentic Harness Architecture
description: How repository instructions and automated checks help us use coding assistants on ARTTU software.
editLink: false
outline: 2
---

# Using coding assistants on our software

An assistant working on our firmware needs to know which files it can change, how the board is organised, and which tests to run. The agent harness brings those instructions and checks together in each repository.

We use the word **harness** for this collection of project rules, writing and debugging guides, and small programs that check the assistant’s work. It runs on the developer’s computer through the coding tool they use. It is separate from the checks GitHub runs when someone proposes a change.

The diagram below follows one change. The assistant first reads the relevant instructions, works on the task, and checks its changes before handing them back for review.

```mermaid
flowchart TB
    TASK["A developer asks for a change"] --> READ["Read project rules and find the relevant code"]
    READ --> EDIT["Make the change"]
    EDIT --> CHECK["Check the resulting files and run tests"]
    CHECK --> REVIEW["Developer reviews the result"]
    REVIEW --> GITHUB["GitHub runs the repository's checks"]

    classDef task fill:#253e64,stroke:#82b4ff,color:#f3f7ff
    classDef process fill:#203f3b,stroke:#66c5ae,color:#f0fff9
    classDef check fill:#514122,stroke:#e8bf63,color:#fff8e8
    classDef failure fill:#512d3d,stroke:#ef91ac,color:#fff1f6
    class TASK task
    class READ,EDIT process
    class CHECK check
    class REVIEW,GITHUB process
```

The instructions guide the work. The automated checks catch some mistakes. A developer still needs to review the result, especially when it affects hardware.

## Follow a small firmware change

Suppose we ask an assistant to change how a sensor reading is processed. Before editing, it needs to find where the reading comes from, which part of the firmware uses it, and what should happen if the sensor stops responding.

The repository’s instructions direct it to inspect those relationships first. A code-search service can help find functions and their callers without reading many unrelated files. When that service is unavailable, the assistant can read the relevant source directly and explain what it could not verify.

If the change affects a pin, a CAN message, or another hardware connection, the assistant must check the agreed specifications before changing the interface. Code alone does not establish what the hardware was intended to do.

### Give it the right guide

The repository includes short guides called **skills**. Each covers a particular kind of work, such as writing embedded C, checking hardware documentation, or debugging a board. The assistant loads the guide that applies to the task.

This keeps task-specific detail out of the general instructions. A documentation change should not require a guide to programming a microcontroller over a debug cable.

| When the task involves… | The guide covers… |
| --- | --- |
| Unfamiliar code | Finding the relevant functions, callers, and data flow |
| Embedded C | Memory use, execution limits, and coding conventions |
| Hardware interfaces | Checking specifications and resolving disagreements |
| Documentation | Explaining the system before introducing implementation detail |
| A physical board | Connecting a debugger, inspecting state, and investigating faults |
| Simulated firmware | Reproducing failures and keeping repeatable regression tests |

```mermaid
flowchart TB
    WORK["What does the task involve?"] --> CODE["Find code and its callers"]
    WORK --> C["Write or review embedded C"]
    WORK --> HW["Check a hardware interface"]
    WORK --> DOC["Explain the system"]
    WORK --> DEBUG["Investigate a failure"]
    DEBUG --> BOARD["Physical board: SWD"]
    DEBUG --> SIM["Emulated board: Renode and GDB"]

    classDef task fill:#253e64,stroke:#82b4ff,color:#f3f7ff
    classDef process fill:#203f3b,stroke:#66c5ae,color:#f0fff9
    classDef check fill:#514122,stroke:#e8bf63,color:#fff8e8
    classDef failure fill:#512d3d,stroke:#ef91ac,color:#fff1f6
    class WORK task
    class CODE,C,DOC process
    class HW check
    class DEBUG,BOARD,SIM failure
```

### Check edits before they run

Coding tools can call a small program immediately before carrying out an operation. This is called a **hook**. Our pre-tool hook inspects supported reads and edits.

For example, STM32CubeMX generates parts of the board’s startup code. It also marks blocks where we can keep our own changes. If an assistant changes generated text outside those blocks, a later CubeMX update could erase the change. The harness checks that supported edits preserve the generated text and the existing block markers.

It also checks for some other common mistakes: adding recognised dynamic-memory calls, putting recognised hardware-access calls in application code, or changing protected system files without an approved exception.

These checks recognise specific tools and code patterns. They cannot understand every script or prove that an edit is correct. Unsupported operations can get past the pre-tool check, which is why we also inspect the final files.

```mermaid
flowchart TB
    EDIT["Recognized file edit"] --> PLAN["Reconstruct the proposed change"]
    PLAN --> CHECK["Check generated text, protected files, and known code patterns"]
    CHECK --> RESULT{"Policy satisfied?"}
    RESULT -->|Yes| ALLOW["Allow the tool to run"]
    RESULT -->|No| DENY["Block the edit and explain why"]
    SCRIPT["Opaque or unrecognized operation"] -.-> GAP["May bypass preflight"]
    GAP -.-> DIFF["Inspect the final Git diff"]

    classDef task fill:#253e64,stroke:#82b4ff,color:#f3f7ff
    classDef process fill:#203f3b,stroke:#66c5ae,color:#f0fff9
    classDef check fill:#514122,stroke:#e8bf63,color:#fff8e8
    classDef failure fill:#512d3d,stroke:#ef91ac,color:#fff1f6
    class EDIT,SCRIPT task
    class PLAN,ALLOW process
    class CHECK,RESULT,DIFF check
    class DENY,GAP failure
```

### Check the result before finishing

When the assistant finishes, another hook compares the files with Git’s recorded version. This catches relevant source changes even if they were made through a different editing route.

For changed source or protected system files, the stop check also runs the Ceedling unit tests, or reuses a successful result when the verification inputs are unchanged. Ceedling is the test runner we use to check C code on the development computer. If configuration or dependencies are missing, verification fails and the assistant must report the problem.

The assistant must also run the board’s required firmware build. That produces code for the microcontroller; it is a separate check from host unit tests and is not run automatically by the stop hook.

A failed stop check asks for a correction or a clear report that verification is blocked. Repeated failures are reported without forcing an endless repair loop. The fact that an assistant has ended its turn is not a test result.

```mermaid
flowchart TB
    DONE["Assistant finishes the change"] --> DIFF["Check the Git diff"]
    DIFF --> SOURCE{"Source checks needed?"}
    SOURCE -->|No| REPORT["Report the work and verification"]
    SOURCE -->|Yes| POLICY["Apply source policy"]
    POLICY --> CACHE{"Same inputs as a successful test run?"}
    CACHE -->|Yes| REUSE["Reuse the recorded test result"]
    CACHE -->|No| TEST["Run Ceedling"]
    REUSE --> REPORT
    TEST --> RESULT{"Tests passed?"}
    RESULT -->|Yes| REPORT
    RESULT -->|No| FIX["Fix the failure or report verification blocked"]
    BUILD["Developer or assistant runs the required target build separately"] -.-> REPORT

    classDef task fill:#253e64,stroke:#82b4ff,color:#f3f7ff
    classDef process fill:#203f3b,stroke:#66c5ae,color:#f0fff9
    classDef check fill:#514122,stroke:#e8bf63,color:#fff8e8
    classDef failure fill:#512d3d,stroke:#ef91ac,color:#fff1f6
    class DONE,BUILD task
    class DIFF,SOURCE,POLICY,CACHE,TEST,RESULT check
    class REPORT,REUSE process
    class FIX failure
```

## Why we keep reads small

An assistant has a limited amount of working context. Filling it with unrelated files makes it harder to keep track of the task. We therefore ask it to find the relevant symbols first and read only the source needed to understand them.

Small, cohesive files can be read whole. For files longer than 200 lines, the supported file-read checks require a function extract or a window of at most 100 lines.

The code-search service also reports which files it indexed. The assistant must check that information before relying on a search result, and read the source when indexing is incomplete or stale. No search result is a guarantee that every relationship has been found.

For longer investigations, the assistant can save a short local note about what it learned. These notes record the source files and Git version they depend on. If those inputs change, the note must be checked again before reuse.

```mermaid
flowchart TB
    QUESTION["Question about the code"] --> GRAPH["Find symbols and relationships"]
    GRAPH --> COVERAGE{"Index evidence current and covered?"}
    COVERAGE -->|Yes| SNIPPET["Read the exact function or class"]
    COVERAGE -->|No| FILE["Read the missing or stale source"]
    SNIPPET --> TRACE["Check producers, consumers, and failure paths"]
    FILE --> TRACE
    TRACE --> NOTES["Keep a short note tied to source hashes and Git revision"]

    classDef task fill:#253e64,stroke:#82b4ff,color:#f3f7ff
    classDef process fill:#203f3b,stroke:#66c5ae,color:#f0fff9
    classDef check fill:#514122,stroke:#e8bf63,color:#fff8e8
    classDef failure fill:#512d3d,stroke:#ef91ac,color:#fff1f6
    class QUESTION task
    class GRAPH,SNIPPET,FILE,NOTES process
    class COVERAGE,TRACE check
```

## What we still need to check ourselves

The harness can identify certain file and code-pattern violations. It cannot confirm a physical pinout, measure interrupt timing, or decide whether a fault response is safe for the car. Those questions need the relevant specifications, engineering review, and tests.

The same distinction applies to setup. Having hook configuration files in a repository does not mean a particular coding tool has enabled them. We check activation in that tool and test its connection to the code-search and documentation services.

The repository currently provides adapters for Antigravity, Claude Code, Codex, and Cursor. Actual support depends on the installed client accepting and running its configuration.

## Getting it running

The included doctor checks the expected configuration and installed tools. After running it, check that the hooks and search services are active in the coding tool itself.

Run this command from the repository root:

```sh
python .agents/hooks/doctor.py
```

Python 3.11 or later and Git are needed for the harness checks. The search services also need Node.js/npm. Firmware tests and builds need the board repository's dependencies. The [setup reference](/architecture/agentic-harness-reference#setup-and-activation) lists the client configuration paths.

## Keeping repositories in step

We maintain the shared rules, skills, and checking programs in the central `.github` repository. A synchronization workflow proposes updates to the configured product repositories through pull requests. Someone must review and merge those changes before a board repository receives them.

We also test the harness itself on Windows and Linux. These tests check the checking programs and their client message formats; they do not replace board tests.

The [CI/CD overview](/architecture/github) explains how this distribution fits alongside firmware builds, tests, and releases.

```mermaid
flowchart TB
    CENTRAL["Shared instructions, skills, and hook runtime"] --> VALIDATE["Validate the distribution payload"]
    VALIDATE --> PR["Open synchronization pull requests"]
    PR --> REVIEW["Review and merge in each repository"]
    REVIEW --> LOCAL["Updated local assistant tools"]
    CENTRAL -.-> CENTRALONLY["Central tests, CI, and documentation stay central"]
    OWNED["Board-owned Renode callers and tests"] -.-> LOCAL

    classDef task fill:#253e64,stroke:#82b4ff,color:#f3f7ff
    classDef process fill:#203f3b,stroke:#66c5ae,color:#f0fff9
    classDef check fill:#514122,stroke:#e8bf63,color:#fff8e8
    classDef failure fill:#512d3d,stroke:#ef91ac,color:#fff1f6
    class CENTRAL,OWNED task
    class VALIDATE,REVIEW check
    class PR,LOCAL process
    class CENTRALONLY check
```

## Further reading

Expand **Agentic Harness** in the sidebar for [setup and implementation details](/architecture/agentic-harness-reference) and the [earlier benchmark results](/architecture/agentic-harness-benchmarks). The benchmark page restores the original token-allocation pie charts and identifies their historical source.
