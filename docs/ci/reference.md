---
title: CI/CD Workflow Reference
description: Inputs, outputs, permissions, repository adoption, and troubleshooting for ARTTU’s shared GitHub Actions workflows.
editLink: false
outline: [2, 3]
---

# CI/CD Workflow Reference

Start with the [architecture overview](/architecture/github) for the visual explanation. This reference describes locally inspected workflow definitions on 19 October 2026. It does not certify successful remote runs, repository variables/secrets, installed runners, or required merge checks.

## Workflow contracts

Workflow files live in `ARTTU-Software/.github/.github/workflows/`. Product callers generally use `ARTTU-Software/.github/.github/workflows/<file>@main`; caller job permissions must accommodate the called workflow. `main` is a moving reference, not a release pin.

### Ceedling unit tests

Source: [ceedling-test.yml](https://github.com/ARTTU-Software/.github/blob/main/.github/workflows/ceedling-test.yml).

| Input | Type / default | Behavior |
| --- | --- | --- |
| `coverage` | boolean / `true` | `gcov:all` when enabled; `test:all` when false |

The Ubuntu job checks out submodules recursively, installs Ruby 3.2 with Bundler caching, installs `gcovr`, and uses Bundler when `Gemfile` exists. Without it, the workflow installs Ceedling directly. Projects without the gcov plugin must explicitly pass `coverage: false`.

JUnit publication looks for `build/artifacts/**/junit_tests_report.xml` even after failures. When present, `build/artifacts/gcov/gcovr/coverage.txt` is copied into the job summary and an existing coverage PR comment is updated (or created). Publication uses contents-read, pull-request-write, and checks-write permissions. Result-publication errors are not themselves the unit-test verdict; inspect the Ceedling execution step and available reports.

### STM32 firmware build

Source: [stm32-build.yml](https://github.com/ARTTU-Software/.github/blob/main/.github/workflows/stm32-build.yml). No custom workflow inputs.

| Contract | Current value |
| --- | --- |
| Runner | `ubuntu-latest` |
| Toolchain | ARM GCC action with `release: latest` |
| Configuration | CMake + Ninja, `Release`, `build/` |
| Toolchain file | `cmake/gcc-arm-none-eabi.cmake` in the caller repository |
| Firmware version | `github.ref_name` |
| Compiler cache | ccache, 500 MiB maximum, OS/STM32 cache key |
| Artifact | `stm32-artifacts` |
| Contents | `build/**/*.elf`, `**/*.bin`, `**/*.map`, `build/compile_commands.json` |

Checkout includes recursive submodules. C and C++ compiler launchers use ccache. Missing artifact files produce a warning, so check the artifact contents as well as the compile result.

### Static analysis

Source: [linter.yml](https://github.com/ARTTU-Software/.github/blob/main/.github/workflows/linter.yml).

| Input | Default | Requirement |
| --- | --- | --- |
| `artifact_name` | `stm32-artifacts` | Artifact must contain the build’s compile database |

The caller must order lint after the build using `needs`. The workflow downloads the artifact into `build`, installs the ARM toolchain, and supplies target/system include arguments to cpp-linter’s Clang-Tidy invocation.

Enabled families are `bugprone-*`, `clang-analyzer-*`, and `performance-*`, with explicit exclusions for reserved identifiers, swappable parameters, selected unsafe-buffer warnings, integer-to-pointer performance findings, and fixed-address dereference findings. The latter exclusions accommodate embedded MMIO idioms. Exact exclusions remain in the YAML.

`Drivers`, `Middlewares`, `test`, and `build` are ignored. `lines-changed-only: 2` limits review scope. Clang-format is disabled (`style: ''`, `format-review: false`). Clang-Tidy review, summary, and PR thread updates are enabled; `checks-failed > 0` fails the job. This is a focused change review, not an exhaustive whole-repository static-analysis claim.

### Renode execution and reporting

Sources: [renode-test.yml](https://github.com/ARTTU-Software/.github/blob/main/.github/workflows/renode-test.yml) and [STM32-Template caller](https://github.com/ARTTU-Software/STM32-Template/blob/main/.github/workflows/renode.yml). The caller is maintained in the template or adopting board repository, outside the tooling sync payload. The central workflow skips execution and publication for draft pull requests.

| Input | Default | Purpose |
| --- | --- | --- |
| `enabled` | `true` | False skips execution and publication |
| `runner` | `'["renode"]'` | JSON `runs-on` labels array or group/labels object |
| `python-version` | empty | Reuse installed Python, or request setup-python |
| `renode-url` | empty | Optional Linux x64 portable .NET archive over HTTPS |
| `renode-sha256` | empty | Required 64-hex SHA-256 when downloading an archive |
| `renode-path` | empty | Installed executable, otherwise PATH discovery |
| `renode-tests` | empty | Installed directory containing Renode’s `run_tests.py` |
| `arm-gdb` | empty | ARM-capable GDB path for source-debugging tests |
| `setup-command` | empty | Board dependency setup before the build |
| `build-command` | **required** | Build the board’s test ELF(s) |
| `test-command` | `python test/renode/harness/run_tests.py` | Board regression runner |
| `requirements` | `test/renode/harness/requirements.txt` | Robot/test Python dependencies |
| `jobs` | `1` | Independent suite workers; benchmark before increasing |
| `timeout-minutes` | `30` | Execution job limit |
| `artifact-name` | `renode-results` | Unique name per caller matrix variant |

Execution currently requires Linux and Bash. It creates an isolated Python environment under runner temporary storage, selects installed Renode or verifies/downloads the configured archive, installs requirements, runs setup/build/test commands, and uploads `build/renode/results/` with 14-day retention. The runner must honor `RENODE`, `RENODE_JOBS`, and `RENODE_RESULTS_DIR`; `RENODE_TESTS` and `ARM_GDB` are also exported. Existing `test/renode/requirements.txt` and `test/renode/run_tests.py` layouts have explicit compatibility fallbacks.

The archive is validated before extraction. For installed Debian Renode, the workflow can select the underlying `Renode.dll` so Robot process/port discovery uses the native .NET process. Board callers remain responsible for setup commands, model fidelity, ELF/platform compatibility, and useful assertions.

The separate `publish` job runs on Ubuntu 24.04, downloads the report artifact, and publishes `xunit.xml` when present. It adds a summary, an execution-status check, and a marked PR comment that is updated on subsequent runs. The execution check succeeds only when a report exists and the execution job succeeded. Upload/download/report absence remains visible in the summary. Fork contexts do not receive check/comment writes, and the template caller excludes fork PRs entirely.

The **STM32-Template caller** maps these repository variables:

| Variable | Caller behavior |
| --- | --- |
| `RENODE_ENABLED` | Only the string `false` opts out; unset is enabled |
| `RENODE_PATH`, `RENODE_TESTS` | Installed tool and runner-script paths |
| `RENODE_SETUP_COMMAND` | Optional setup |
| `RENODE_BUILD_COMMAND` | Defaults to `python --version` for infrastructure smoke |
| `RENODE_TEST_COMMAND` | Defaults to the harness runner |
| `RENODE_REQUIREMENTS` | Defaults to harness requirements |
| `RENODE_JOBS` | Parsed as JSON number, defaults to 1 |

That caller selects the `salita` runner group with labels `self-hosted`, `Linux`, `X86`, and `renode`, and sets `arm-gdb: /usr/bin/gdb-multiarch`. Its triggers are PR opened/synchronize/reopened/ready-for-review and manual dispatch; concurrency cancels earlier runs of the same workflow/ref. Draft PRs are skipped; marking a PR ready for review starts the workflow. A caller file or passing infrastructure smoke is insufficient evidence of board regression coverage.

### Release and documentation notification

Source: [create-release.yml](https://github.com/ARTTU-Software/.github/blob/main/.github/workflows/create-release.yml).

| Input / secret | Contract |
| --- | --- |
| `artifact_name` | String, empty by default; download is skipped when empty |
| `DOCS_DISPATCH_TOKEN` | Cross-repository authorization for the documentation dispatch |

The workflow checks out full history, optionally downloads artifacts, creates a release with generated notes, and attaches available `.bin`, `.elf`, and `.map` files. Download is `continue-on-error`, and unmatched files are accepted. The release job requests contents-write permission. The dispatch sends `docs-release` to `ARTTU-Software/documentation` with `repo` and `tag` payload fields. Check both release assets and the notification result.

### Harness CI and tooling distribution

Sources: [agent-harness-check.yml](https://github.com/ARTTU-Software/.github/blob/main/.github/workflows/agent-harness-check.yml), [sync-agent-rules.yml](https://github.com/ARTTU-Software/.github/blob/main/.github/workflows/sync-agent-rules.yml), and [sync.yml](https://github.com/ARTTU-Software/.github/blob/main/.github/sync.yml).

`agent-harness-check.yml` accepts optional string `base_revision`, default empty. Its policy base falls back to the PR base SHA, event-before SHA, or current SHA; an all-zero base becomes `EMPTY`. Central harness tests run on Ubuntu/Windows with Python 3.11. Renode reporting-contract tests run separately with Python 3.12 and PyYAML 6.0.3.

The sync plan validates ten destinations, checks the doctor/regression suite and skill distribution, then renders a per-target config using Python. A matrix with `fail-fast: false` isolates target failures. `SYNC_APP_ID` and `SYNC_APP_PRIVATE_KEY` create per-target GitHub App installation tokens requesting contents and PR writes. The file-sync action uses a single batched commit (`chore(tooling): `), labels `automation` and `agent-rules`, and attempts draft conversion afterward. The payload is defined by mappings and the runtime manifest; adding files centrally does not automatically distribute them. Renode callers and board tests are outside the sync payload.

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
| common · `07e08b4` | Ceedling + DBC generated-header check | No build artifact requested | — | `dev` |
| utilities · `fe92638` | — | No build artifact requested | — | `main` |
| Backend · `991f9c0` | — | No build artifact requested | — | — |

All twelve inspected repositories also contain labeler callers that fetch central configuration. Backend separately deploys over SSH on `main` pushes. The documentation repository has a labeler plus its own three-trigger deployment (push to `main`, `docs-release` dispatch, manual). Its deployment operations remain documented there. The older Partners-Database-App coverage entry is retained in the [historical reference](/architecture/github-history); its current workflow state was not reverified in this review.

Telemetry’s current Docker simulation job uses a self-hosted Linux/x64 runner, builds its image and Debug firmware, executes `renode/run_tests.sh`, converts Robot output to `junit.xml`, and retains `renode-report` for 14 days. It is separate from the shared runner/publisher implementation and skips draft PRs.

## Shared PR labels

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

## Finding the right failure evidence

| Symptom | Inspect first |
| --- | --- |
| Ceedling fails before executing tests | Ruby/Bundler dependencies, `project.yml`, gcov availability and the `coverage` input |
| No JUnit or coverage comment | Actual execution result and expected report paths; missing publication is not a passing test |
| Build succeeds but lint cannot start | `needs`, matching artifact name, and `compile_commands.json` contents |
| Renode job remains queued | Runner labels/availability and repository access |
| Renode starts but no board scenario is exercised | Board build/test commands and manifest; distinguish smoke from board regression |
| Renode produces no xUnit | Setup/build/runner failure, execution check, artifact logs and result paths |
| Release lacks firmware assets | Optional download result, artifact name, and matching file paths |
| Documentation stays on older content | Dispatch step, hub deployment result, product tags, and the recorded central-docs submodule commit |
| Sync PR is missing or not draft | Plan job, target App installation/permissions, matrix result, file differences, draft conversion log |
| Green checks do not block a merge | Repository rules and configured required checks |

## Updating these pages

Edit `.github/docs/ci/` alongside workflow changes. Keep the old [historical reference](/architecture/github-history) clearly dated. Publish the central commit before publishing a documentation hub commit that references it, then advance `repos/agent-harness`, build the hub, and verify `/architecture/github` and `/architecture/github-reference`. Source documentation and workflow definitions share ownership; deployment-specific procedures remain in the deploying repository.
