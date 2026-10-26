---
title: CI/CD Workflow Reference
description: Inputs, outputs, permissions, repository adoption, and troubleshooting for ARTTU’s shared GitHub Actions workflows.
editLink: false
outline: [2, 3]
---

# CI/CD Workflow Reference

Start with the [architecture overview](/architecture/github) for the visual explanation. This reference describes locally inspected workflow definitions on 19 October 2026. It does not certify successful remote runs, repository variables/secrets, installed runners, or required merge checks.

## Workflow contracts

Each procedure has its own page with diagrams, inputs, outputs and failure guidance. Workflow files live in `ARTTU-Software/.github/.github/workflows/`. The caller chooses events, dependencies and permissions; `@main` follows a moving branch.

### Ceedling unit tests

See [Ceedling unit tests](/architecture/ci/unit-tests).

### STM32 firmware build

See [STM32 firmware build](/architecture/ci/firmware-build).

### Static analysis

See [static analysis](/architecture/ci/static-analysis).

### Renode execution and reporting

See [Renode execution and reporting](/architecture/ci/renode).

### Release and documentation notification

See [release and documentation notification](/architecture/ci/releases).

### Harness CI and tooling distribution

See [harness CI checks](/architecture/ci/harness-checks).

Tooling distribution has its own [sync procedure](/architecture/ci/tooling-sync).

## Repository adoption snapshot

This matrix records **workflow files in the inspected local repository revisions**, not live GitHub status or a claim that every caller succeeds. Local board revisions can be newer than the documentation hub’s product submodule pins. Sync means membership in central `sync.yml`, not confirmed installation. “—” means the inspected top-level workflows did not define that capability.

| Repository · revision | PR pipeline | Release caller | Renode definition | Sync target |
| --- | --- | --- | --- | --- |
| ECU · `22317c8` | Ceedling + build + lint; extra test caller | Firmware assets | — | `dev` |
| CAN-Gateway · `e0e8da1` | Ceedling + build + lint | Firmware assets | — | `dev` |
| Telemetry · `a8eade1` | Ceedling + build + lint | Firmware assets | Board-owned Docker workflow | `dev` |
| Galvanic-Isolator · `e6721a8` | Ceedling + build + lint; extra test caller | Firmware assets | — | `dev` |
| LVSOC-26 · `9d26dde` | Ceedling + build + lint | Firmware assets | — | `dev` |
| Charger · `903617e` | — | No build artifact requested | — | — |
| Dashboard · `d38d97c` | Ceedling + build + lint; extra test caller | Firmware assets | — | `dev` |
| BMS-Master · `2b938c3` | Ceedling + build + lint | Firmware assets | Shared caller | `dev` |
| STM32-Template · `f7636bb` | Ceedling + build + lint | Firmware assets | Shared caller | `main` |
| common · `76140ca` | Ceedling + SharePoint CAN sync + DBC codegen check | CAN database & header release assets | — | `dev` / `main` |
| .github · `c346ede` | Harness CI checks + Tooling sync | Release caller & docs dispatch | Shared caller | `main` |
| utilities · `fe92638` | — | No build artifact requested | — | `main` |
| Backend · `991f9c0` | — | No build artifact requested | — | — |

All twelve inspected repositories also contain labeler callers that fetch central configuration. Backend separately deploys over SSH on `main` pushes. The documentation repository has a labeler plus its own deployment workflow (push to `main` deploys to server; `docs-release` dispatch and manual dispatch deploy immediately to the server and open/update a draft submodule sync PR via `arttu-sync-bot` without directly committing to `main`). Its deployment operations remain documented there. Partners-Database-App was not reverified in this review.

Telemetry’s current Docker simulation job uses a self-hosted Linux/x64 runner, builds its image and Debug firmware, executes `renode/run_tests.sh`, converts Robot output to `junit.xml`, and retains `renode-report` for 14 days. It is separate from the shared runner/publisher implementation and skips draft PRs.

## Shared PR labels

See the [labelling procedure](/architecture/ci/labels) for the rules, permissions and failure guidance.

## Finding the right failure evidence

| Symptom | Inspect first |
| --- | --- |
| Ceedling fails before executing tests | Ruby/Bundler dependencies, `project.yml`, gcov availability and the `coverage` input |
| No JUnit or coverage comment | Ceedling execution and collection logs, mode-specific report paths, plugins and permissions |
| Build succeeds but lint cannot start | `needs`, matching artifact name, and `compile_commands.json` contents |
| Renode job remains queued | Runner labels/availability and repository access |
| Renode starts but no board scenario is exercised | Board build/test commands and manifest; distinguish smoke from board regression |
| Renode produces no xUnit | Setup/build/runner failure, execution check, artifact logs and result paths |
| Release lacks firmware assets | Optional download result, artifact name, and matching file paths |
| Documentation stays on older content | Dispatch step, hub deployment result, product tags, and the recorded central-docs submodule commit |
| Submodule sync PR is missing or failing | Inspect sync-submodules-pr job logs, SYNC_APP_ID / SYNC_APP_PRIVATE_KEY / DOCS_DISPATCH_TOKEN secrets, and App permissions on ARTTU-Software/documentation |
| Sync PR is missing or not draft | Plan job, target App installation/permissions, matrix result, file differences, draft conversion log |
| Green checks do not block a merge | Repository rules and configured required checks |

## Updating these pages

Edit `.github/docs/ci/` alongside workflow changes. Publish the central commit before publishing a documentation hub commit that references it, then advance `repos/agent-harness`, build the hub, and verify the overview, procedure pages and sidebar links. Source documentation and workflow definitions share ownership; deployment-specific procedures remain in the deploying repository.
