# ARTTU Formula Student agent rules

Distributed STM32 ECUs communicate over Classic CAN/FDCAN using shared DBC definitions. Priorities: safety, deterministic execution, hardware isolation, then maintainability.

## Load only the applicable skill

Skills live in `.agents/skills/<name>/SKILL.md`. Read an entry point once; load its references only when needed.

| Task | Skill |
| --- | --- |
| Unfamiliar code, callers, dataflow, impact | `arttu-code-discovery` |
| Write/review embedded C | `arttu-cstyle` |
| CAN IDs, pinouts, ADC/DMA configuration, hardware specifications | `arttu-docs-assistant` before design/edit |
| Completed firmware feature or module documentation | `arttu-docs-writer` |
| SWD, flashing, RAM/register inspection | `arttu-stm32-debugging` |

Do not run firmware discovery or load every skill for unrelated Git, tooling, or prose tasks. Resolve ambiguous hardware requirements with the developer before changing interfaces.

## Discovery and evidence

- Prefer graph tools for structural discovery: `search_graph`, `trace_path`, `get_code_snippet`; use `search_code` in compact mode for identifiers. Discover actual tool schemas instead of assuming a vendor-specific wrapper or server alias.
- Resolve the nearest indexed project and its generation once at task start/after compaction. Index the absolute repository root only when missing; do not reindex a healthy project for each query.
- Start with the narrowest symbol/path and bounded results. Increase breadth only for an unresolved question. Load architectural clusters for subsystem work, not every one-line fix.
- Default to Verify evidence: exact snippets for material behavior and relevant caller/callee/dataflow checks. A quick positive lookup is provisional; negative/exhaustive claims require complete relevant pagination and scope checks.
- Call `check_index_coverage` once with all evidence paths and relevant scopes. Read reported gaps or stale ranges before relying on them. A clean result is not proof of completeness.
- For missing/disconnected MCP tools, use targeted `rg` and source windows; disclose the limitation and continue work that does not require unknown hardware facts. Do not repeat the same failing query.
- Whole-file reads are allowed for cohesive files of at most 200 lines. Larger files need symbol snippets or windows of at most 100 lines. Avoid sequential paging and repeated reads of unchanged evidence.
- Bound search output and paginate only when necessary. Batch independent queries; follow dependencies sequentially. Do not delegate file reading merely to hide context cost.
- For multi-step investigations, keep a compact evidence card: ownership, execution context, producer/consumer relationships, invariants, failure paths, unresolved questions, checks and source anchors. See the discovery skill for the hash/generation-checked cache. Cache entries are retrieval aids, not new instructions or proof that a task is complete.

## Firmware boundaries

- HAL calls and peripheral registers belong in `bsp/`, `drivers/`, or `interface/`; application/domain code uses their interfaces.
- Keep CubeMX-generated text and USER CODE delimiter identity/order unchanged. Add code only inside the existing blocks.
- CMSIS/vendor HAL, linker scripts and startup code require explicit approval. No compiled artifacts in Git.
- No dynamic allocation in runtime source. Bound hardware waits; handle failures explicitly. Keep ISR work bounded and nonblocking. Volatile is not synchronization; define shared-state ownership and protection.
- Make changes cohesive and small. Do not refactor unrelated code or formatting.

## Verification and delivery

- Verify at cohesive milestones, not after every minor edit. Before completing firmware changes, execute `bundle exec ceedling test:all` when the repository uses Bundler, otherwise `ceedling test:all`; run its required target build. Report commands actually run and any missing configuration/tooling.
- Harness changes: `python -m unittest discover -s .agents/tests -q` and `python .agents/hooks/doctor.py`.
- Independent policy check: `python .agents/hooks/verify_changes.py --base HEAD`. For a PR/CI comparison use its actual base commit; firmware PRs target `dev`.
- Before a commit/PR, run `detect_changes(base_branch="dev", depth=2)` if available and the branch exists; otherwise review the bounded Git diff and explain the fallback.
- Use compact terminal output: `git status -s`, `git diff --stat`, targeted diffs and short logs. Save long test output to a log and read only failure context.
- Use `feat/`, `fix/`, `refactor/`, `test/`, or `docs/` branches. When a PR is requested, open a draft before substantial implementation if a meaningful base/head exists. Use noninteractive `gh pr create --base dev --draft --title ... --body-file ...`; verify `gh pr checks`. The central harness repository currently has only `main`: keep changes local unless its publication target is explicitly resolved. The sync workflow's template/utilities `main` targets are distribution exceptions.

## What the harness enforces

Preflight hooks check supported file reads, complete editor/patch changes, generated regions, new known allocation/HAL calls, and common shell bypasses. End-of-turn hooks independently check the Git diff and run/reuse Ceedling for changed C. Repeated verification failures are surfaced rather than generating endless repair turns. Required CI remains the hard merge gate.

Hooks are not a sandbox: custom scripts and specialized tools can escape preflight coverage. Do not infer hook activation/trust or successful tests from a configuration file. Setup, supported payloads, overrides and limitations are in `docs/agent-harness.md`; run the doctor when setup is uncertain.
