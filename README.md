# .github

Organization-wide configuration and automation repository for **ARTTU Formula Student Racing** (`ARTTU-Software`).

---

### Contents

1. **Organization Profile (`profile/README.md`)**
   The public profile overview rendered on the [`ARTTU-Software`](https://github.com/ARTTU-Software) organization homepage.

2. **AI Agent Guidelines & Modular Skills**
   * [`AGENTS.md`](./AGENTS.md): Universal invariants, architecture guardrails, and verification commands.
   * [`.agents/skills/`](./.agents/skills/): Specialized, on-demand domain skills:
     * `arttu-cstyle`: C determinism, single-precision floats, HAL isolation, ring buffers.
     * `arttu-stm32-debugging`: Non-intrusive SWD, memory reads, HardFault register analysis.
     * `arttu-docs-assistant`: Vehicle doc discovery, CAN IDs, pinouts, and specs.
     * `arttu-docs-writer`: Diátaxis framework, Mermaid diagrams, team engineering voice.

3. **Multi-Repo Synchronization Automation (`.github/sync.yml`)**
   The GitHub Actions workflow [`.github/workflows/sync-agent-rules.yml`](./.github/workflows/sync-agent-rules.yml) automatically keeps all downstream board repositories updated with current agent rules and skills via Draft Pull Requests.

4. **Shared Workflows (`.github/workflows/`)**
   Organization-wide reusable CI/CD workflows, linters, and testing templates.