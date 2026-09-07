# AGENTS.md - ARTTU Formula Student

You are building embedded firmware and tooling for **ARTTU Formula Student Racing**. Safety, determinism, and hardware boundary isolation are non-negotiable.

## Architecture
Distributed multi-ECU automotive architecture (STM32 Cortex-M MCUs) communicating over Classic CAN/FDCAN via central DBC definitions, with state-driven control (FSM) and bare-metal/FreeRTOS deterministic execution.

## Essential Commands

| Action | Command | Scope / Notes |
| :--- | :--- | :--- |
| **Run All Unit Tests** | `ceedling test:all` | Mandatory verification before every commit/PR |
| **Run Single Module Test** | `ceedling test:<module>` | Fast iteration (e.g. `ceedling test:moving_avg`) |
| **Clean Test Artifacts** | `ceedling clobber` | Run when mock headers or dependencies get stale |
| **Build Documentation** | `npm run docs:build` | In `documentation/` directory (VitePress verification) |
| **Create Pull Request** | `gh pr create --base dev --title "<title>" --body-file "<file>"` | Non-interactive PR creation (requires `--base dev`) |
| **Check PR CI Status** | `gh pr checks` | Verify remote GitHub Actions workflow passes |

## Universal Invariants & Guardrails

### 1. Requirements & Ambiguity
* If requirements, pinouts, timing budgets, or CAN IDs are ambiguous, **STOP and run `/grill-me`** (or ask clarifying questions) to interview the developer before writing code.
* Keep changes minimal and atomic (<100 lines per logical step). Never refactor unrelated files or change project formatting.

### 2. File & Memory Boundaries
* **CubeMX Generated Code**: In CubeMX files (`main.c`, `stm32g4xx_it.c`), **never** place code outside `/* USER CODE BEGIN <x> */` and `/* USER CODE END <x> */` blocks. Unmarked code is destroyed on `.ioc` regeneration.
* **HAL Isolation**: Hardware abstraction layer calls (`HAL_*`, direct peripheral registers) belong strictly in `bsp/` and `drivers/`. Application code must remain hardware-agnostic.
* **System Files**: Never edit CMSIS headers (`core_cm*.h`), vendor HAL source, linker scripts (`*.ld`), or startup code (`startup_*.s`) without explicit approval.
* **Deterministic Allocation**: Zero dynamic memory allocation (`malloc`/`free`) permitted anywhere in runtime code.

### 3. Git & Workflow Hygiene
* **Target Branch**: Never push or open PRs directly to `main`. All PRs must target `dev/` using conventional branch prefixes (`feat/`, `fix/`, `refactor/`, `test/`, `docs/`).
* **Pull Requests via GitHub CLI (`gh`)**: Always create PRs using the GitHub CLI with non-interactive flags (`--base dev`, `--title`, and `--body`/`--body-file`). Never run bare `gh pr create` without arguments, as interactive prompts freeze agent execution. Always verify CI checks pass with `gh pr checks`.
* **Open Draft PR Early**: Signal work-in-progress before writing substantial code (`--draft`).
* **No Binaries**: Never commit compiled artifacts (`.bin`, `.hex`, `.elf`, `.o`, `.a`).

### 4. Verification Gate
* Every code modification must compile and pass unit tests with Ceedling (`ceedling test:all`) prior to committing.
* Never claim code builds or tests pass without executing the verification command and inspecting output.

## On-Demand Skills Directory

Load the corresponding skill when performing these specialized workflows:

* **Writing or Modifying C Firmware**: Load [arttu-cstyle](.agents/skills/arttu-cstyle/SKILL.md).  
  *Enforces type discipline (`stdint.h`), Cortex-M single-precision float suffixes (`f`), deterministic timeout loops, ISR ring buffers, MISRA-adjacent safety, and Ceedling mock patterns.*
* **Hardware Debugging & Flashing**: Load [arttu-stm32-debugging](.agents/skills/arttu-stm32-debugging/SKILL.md).  
  *Enforces non-intrusive SWD connection (`mode=HOTPLUG shared`), ELF symbol RAM inspection, memory injection guardrails, and HardFault crash analysis via `addr2line`.*
* **Vehicle Architecture & Specs**: Load [arttu-docs-assistant](.agents/skills/arttu-docs-assistant/SKILL.md).  
  *Queries the vehicle documentation repository, pinout mappings, CAN DBC definitions, and MCP documentation servers.*
* **Authoring Documentation**: Load [arttu-docs-writer](.agents/skills/arttu-docs-writer/SKILL.md).  
  *Enforces Diátaxis framework compliance, VitePress conventions, Mermaid automotive diagrams, and team voice.*
