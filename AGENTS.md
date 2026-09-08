# AGENTS.md - ARTTU Formula Student

You are building embedded firmware and tooling for **ARTTU Formula Student Racing**. Safety, determinism, and hardware boundary isolation are non-negotiable.

## Architecture
Distributed multi-ECU automotive architecture (STM32 Cortex-M MCUs) communicating over Classic CAN/FDCAN via central DBC definitions, with state-driven control (FSM) and bare-metal/FreeRTOS deterministic execution.

**Step 0 (Mandatory)**: Before starting ANY task, immediately load [arttu-code-discovery](.agents/skills/arttu-code-discovery/SKILL.md). Before any CODE task, load [arttu-cstyle](.agents/skills/arttu-cstyle/SKILL.md). Before any DOCUMENTATION task, immediately load [arttu-docs-assistant](.agents/skills/arttu-docs-assistant/SKILL.md).

## Essential Commands

| Action | Command | Scope / Notes |
| :--- | :--- | :--- |
| **Inspect Symbol Implementation** | `get_code_snippet(qualified_name="<symbol>", project="<proj>")` | Zero-file-read extraction of function body & line bounds |
| **Trace Shared Buffer / Variable** | `trace_path(function_name="<var>", edge_types=["WRITES"|"USAGE"])` | Map all writers & readers of DMA buffers, flags, and arrays |
| **Trace Call Graph** | `trace_path(function_name="<func>", direction="inbound"|"outbound")` | Map callers/callees across tasks, buffers, and ISRs |
| **Search Code (Compact)** | `search_code(pattern="<name>", mode="compact", project="<proj>")` | Graph-augmented search: signatures + line bounds (~150 tokens) |
| **Search Graph Symbols** | `search_graph(name_pattern=".*<name>.*", file_pattern="Core/**")` | Scoped discovery by label (`Variable`, `Field`, `Macro`) |
| **Verify Impact Radius** | `detect_changes(base_branch="dev", depth=2, project="<proj>")` | Transitive impact analysis of modified symbols before commit |
| **Architecture & Clusters** | `get_architecture(path="<prefix>", aspects=["clusters", "hotspots"])` | Leiden community detection & de-facto architectural seams |
| **Run All Unit Tests** | `ceedling test:all` | Mandatory verification before every commit/PR |
| **Run Single Module Test** | `ceedling test:<module>` | Fast iteration (e.g. `ceedling test:moving_avg`) |
| **Create Pull Request** | `gh pr create --base dev --title "<title>" --body-file "<file>"` | Non-interactive PR creation (requires `--base dev`) |

## Code Discovery & Tool Hierarchy

Follow this prescriptive 4-step sequence before inspecting raw code or modifying any firmware module:

1. **Step 1: Specification & Architecture Check (`markdown-docs` + `get_architecture`)**
   * Call `search_docs(directory="<REPO_PATH>/docs", query="<module>")` using the absolute path to the repository `docs/` folder to verify pinouts, CAN IDs, and hardware specs.
   * Call `get_architecture(path="Core/Src/App", aspects=["clusters", "hotspots"])` to view de-facto architectural seams, module clusters, and communication hubs without file reads.
2. **Step 2: Subsystem Mapping & Hybrid Search (`query_graph` + `search_code`)**
   * For whole-folder or subsystem mapping, run `query_graph` to extract the degree-ranked function skeleton in ~200 tokens (Recipe G in `arttu-code-discovery`).
   * For specific identifiers, variables, or types, use `search_code(pattern="<name>", mode="compact")` or `search_graph` scoped by label.
3. **Step 3: Impact & Dataflow Analysis (`codebase-memory-mcp`)**
   * If the project is not listed in `list_projects` or returns `Project not found`, run auto-indexing immediately: `index_repository(repo_path=".", mode="full")`.
   * For shared buffers, arrays, or flags, run `trace_path(function_name="<var>", edge_types=["WRITES", "USAGE"])` to identify all producers and consumers across tasks and ISRs.
   * Trace function callers and callees (`trace_path` with `direction="inbound"` or `"outbound"`).
   * For sensor, ADC, or CAN signal flow, use `trace_path` with `mode="data_flow"` to inspect parameter expressions across hops.
4. **Step 4: Mandatory Symbol Reader (`get_code_snippet`)**
   * NEVER read whole source files to inspect a function. ALWAYS call `get_code_snippet(qualified_name="<symbol>")` first. It extracts the exact function implementation, docstrings, and start/end line numbers in ~300 tokens instead of ~5,000 tokens.
   * **Targeted Direct Grep (`grep_search`)**: Scope with `SearchPath` specifically for `#define` macros, register bitmasks, error strings, or non-C config files (`CMakeLists.txt`, `project.yml`). Do not grep blindly across the repo for functions, structs, or variables.
   * **Windowed Read Rule**:
     * Small cohesive files (≤200 lines, e.g. headers, test files, configs): Full-file view permitted in a single call.
     * Large files (>200 lines): Windowed reading (≤100 lines) or `get_code_snippet` is strictly mandatory. NEVER dump large files unwindowed.

## Universal Invariants & Guardrails

### 1. Requirements & Ambiguity
* If requirements, pinouts, timing budgets, or CAN IDs are ambiguous, **STOP and run `/grill-me`** (or ask clarifying questions) to interview the developer before writing code.
* Keep changes minimal and atomic (<100 lines per logical step). Never refactor unrelated files or change project formatting.

### 2. File Boundaries
* **CubeMX Generated Code**: In CubeMX files (`main.c`, `stm32g4xx_it.c`), **never** place code outside `/* USER CODE BEGIN <x> */` and `/* USER CODE END <x> */` blocks. Unmarked code is destroyed on `.ioc` regeneration.
* **HAL Isolation**: Hardware abstraction layer calls (`HAL_*`, direct peripheral registers) belong strictly in `bsp/` and `drivers/`. Application code must remain hardware-agnostic.
* **System Files**: Never edit CMSIS headers (`core_cm*.h`), vendor HAL source, linker scripts (`*.ld`), or startup code (`startup_*.s`) without explicit approval.
* **Deterministic Allocation**: Zero dynamic memory allocation (`malloc`/`free`) permitted anywhere in runtime code.

### 3. Git & Terminal Hygiene (Compact Output Rule)
* **Compact Commands Only**: Always invoke commands with flags that restrict output to what is strictly necessary. Never dump thousands of lines of terminal output into context:
  * **Git**: Use `git log -n 5 --oneline` (never bare `--stat` or large `-n`), `git diff --stat` (or targeted file diffs, never bare repo-wide `git diff`), and `git status -s`.
  * **Build & Test**: Prefer single-module runs (`ceedling test:<module>`) during development; avoid running verbose build flags or unconstrained recursive logs.
  * **General**: Never run unconstrained directory trees, recursive finds, or huge log dumps. Pipe or limit outputs (`--limit`, `--summary`, `--oneline`) to preserve context.
* **Target Branch**: Never push or open PRs directly to `main`. All PRs must target `dev/` using conventional branch prefixes (`feat/`, `fix/`, `refactor/`, `test/`, `docs/`).
* **Pull Requests via GitHub CLI (`gh`)**: Always create PRs using the GitHub CLI with non-interactive flags (`--base dev`, `--title`, and `--body`/`--body-file`). Never run bare `gh pr create` without arguments, as interactive prompts freeze agent execution. Always verify CI checks pass with `gh pr checks`.
* **Open Draft PR Early**: Signal work-in-progress before writing substantial code (`--draft`).
* **No Binaries**: Never commit compiled artifacts (`.bin`, `.hex`, `.elf`, `.o`, `.a`).

### 4. In-Session Verification Gate
* **Batched Verification**: Do NOT run Ceedling or target builds in a tight loop after every single minor edit. Run verification only at major logical milestones (e.g. after completing a cohesive implementation batch or test suite) and prior to committing/completing the task.
* **Pre-Commit Impact Verification**: Before committing or opening a PR, always execute `detect_changes(base_branch="dev", depth=2)` to verify that only intended files were modified and that all downstream impacted symbols are accounted for.
* **Mandatory Test Execution**: Never claim code builds or tests pass without executing the verification command (`ceedling test:all`) and inspecting output.
* If tests fail, analyze the assertion failures, apply minimal targeted fixes, and re-test.

## Multi-Vendor Harness Support

This repository supports all major AI agent environments with native lifecycle hooks and MCP tools out-of-the-box:
* **Google Antigravity**: Lifecycle hooks in `.agents/hooks.json` intercept bulk reads (>200 lines), block dynamic memory, and protect CubeMX blocks with native protojson IPC (`decision: "deny"|"allow"`).
* **Claude Code**: Native hooks in `.claude/settings.json` enforce the identical PreToolUse guardrails and post-mutation Ceedling verification via exit codes.
* **OpenAI Codex CLI & Cursor IDE**: Native hook declarations in `.codex/hooks.json` and `.cursor/hooks.json` wire into the universal pre-tool enforcer.

## On-Demand Skills Directory

Load the corresponding skill when performing these specialized workflows:

* **Writing or Modifying C Firmware**: Load [arttu-cstyle](.agents/skills/arttu-cstyle/SKILL.md).  
  *Enforces type discipline (`stdint.h`), Cortex-M single-precision float suffixes (`f`), deterministic timeout loops, ISR ring buffers, MISRA-adjacent safety, and Ceedling mock patterns.*
* **Code Discovery & Call Graph Tracing**: Load [arttu-code-discovery](.agents/skills/arttu-code-discovery/SKILL.md).  
  *Enforces codebase-memory-mcp auto-indexing, inbound/outbound call graph tracing recipes, and targeted symbol snippet extraction.*
* **Hardware Debugging & Flashing**: Load [arttu-stm32-debugging](.agents/skills/arttu-stm32-debugging/SKILL.md).  
  *Enforces non-intrusive SWD connection (`mode=HOTPLUG shared`), ELF symbol RAM inspection, memory injection guardrails, and HardFault crash analysis via `addr2line`.*
* **Vehicle Architecture & Specs**: Load [arttu-docs-assistant](.agents/skills/arttu-docs-assistant/SKILL.md).  
  *Queries the vehicle documentation repository, pinout mappings, CAN DBC definitions, and MCP documentation servers.*
* **Authoring Documentation**: Load [arttu-docs-writer](.agents/skills/arttu-docs-writer/SKILL.md).  
  *Enforces Diátaxis framework compliance, VitePress conventions, Mermaid automotive diagrams, and team voice.*
