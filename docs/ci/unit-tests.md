---
title: Unit tests and coverage
editLink: false
---

# Unit tests and coverage

Unit tests give a small piece of code known inputs and compare the answer with an expected value. Ceedling runs our C tests on the GitHub runner. Coverage reporting also records which source code the tests exercised.

```mermaid
%%{init: {"flowchart": {"htmlLabels": false}}}%%
flowchart TB
    CALL["Firmware caller requests<br/>unit tests"] --> ENV["Check out source and<br/>submodules; install Ruby<br/>and dependencies"]
    ENV --> MODE{"Coverage enabled?"}
    MODE -->|Yes, default| GCOV["Run Ceedling gcov:all"]
    MODE -->|No| TEST["Run Ceedling test:all"]
    GCOV --> COLLECT["Always collect reports<br/>for the selected mode"]
    TEST --> COLLECT
    COLLECT --> FOUND{"Required reports exist?"}
    FOUND -->|No| FAIL["Fail collection; inspect<br/>test and plugin errors"]
    FOUND -->|Yes| REPORT["Publish test checks;<br/>save ceedling-reports<br/>artifact"]
    REPORT --> COV["Coverage mode: add job<br/>summary and attempt PR<br/>comment"]
    classDef event fill:#253e64,stroke:#82b4ff,color:#f3f7ff
    classDef work fill:#203f3b,stroke:#66c5ae,color:#f0fff9
    classDef check fill:#514122,stroke:#e8bf63,color:#fff8e8
    classDef failure fill:#512d3d,stroke:#ef91ac,color:#fff1f6
    class CALL event
    class ENV,GCOV,TEST,COLLECT,REPORT,COV work
    class MODE,FOUND check
    class FAIL failure
```

## Reading the result

Start with the Ceedling execution log. A failed assertion identifies the test and the expected and actual values. If no tests ran, check dependency installation and `project.yml` before interpreting the report publisher.

Download `ceedling-reports` for the generated files. A missing JUnit report is a reporting or configuration failure. Projects must enable the appropriate report plugins and formats.

Coverage helps locate code that needs tests. Executing a line does not establish that the test checked every relevant outcome.

## Report paths and custom build directories

Collection runs even after a test failure. It searches `**/artifacts/gcov/` with coverage enabled and `**/artifacts/test/` otherwise. This supports a custom Ceedling build root, such as `out/`, without changing the workflow.

The selected directories must contain `junit_tests_report.xml`. Coverage mode also requires `gcovr/coverage.txt`. Missing required reports fail collection; a report from the other mode cannot substitute for them. Collection includes all matching directories for the selected mode.

The workflow publishes JUnit results with failures and inconclusive results treated as errors, saves the report directories, and adds coverage to the job summary. Creating or updating the coverage PR comment is attempted separately; comment failure is tolerated.

## Workflow contract

| Setting | Behaviour |
| --- | --- |
| `coverage` input | Boolean, defaults to `true`; select `false` for projects without the gcov plugin |
| Environment | Ubuntu, Ruby 3.2, Bundler caching and `gcovr` |
| With a `Gemfile` | Run `bundle exec ceedling` |
| Without a `Gemfile` | Install Ceedling directly and run `ceedling` |
| Permissions | Contents read, pull requests write, checks write |
| Saved artifact | `ceedling-reports` |

Source: [ceedling-test.yml](https://github.com/ARTTU-Software/.github/blob/main/.github/workflows/ceedling-test.yml).

[Back to CI/CD overview](/architecture/github)
