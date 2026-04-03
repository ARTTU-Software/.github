## 🧭 Coding Guidelines

Rules to keep the codebase relatively (hopefully) clean.

# Repository Structure & Organization
* **Repo-per-Board**: Each repository represents exactly one hardware board (ECU, Dashboard, etc.).
* **The `lib/commons` Submodule**: Shared drivers and math utilities are linked via Git Submodules. **Do not** manually copy code from `Commons` into your repo.
* **Atomic Commits**: Keep commits small. One logical change per commit (e.g., "Add CAN mailbox filtering" not "Work on car").

# Branch Conventions
We use a **Mainline/Feature** workflow. **All development must be merged into `dev/` first** for integration testing before reaching the production-ready `main` branch.

| Type | Prefix | Use Case |
| :--- | :--- | :--- |
| **Integration** | `dev/` | The primary branch for active development and subteam integration. |
| **Feature** | `feat/` | New functionality (e.g., `feat/add-can-filter`). **Merge into `dev/`**. |
| **Bugfix** | `fix/` | Fixing a bug (e.g., `fix/can-timing-offset`). **Merge into `dev/`**. |
| **Refactor** | `ref/` | Code cleanup with no functional changes. **Merge into `dev/`**. |
| **Testing** | `test/` | Experimental code or new unit tests. |
| **Docs** | `docs/` | Documentation only. |

> **Important**: Never push directly to `main`. Open a Pull Request from your `feat/` or `fix/` branch into `dev/`. Once `dev/` is stable and tested on the car, a lead will merge `dev/` into `main`.

# Code Style
* **Indentation**: Use 4 spaces. Do not use tabs.
* **Naming**: Use `camelCase` or `snake_case` for variables/functions. Use `ALL_CAPS` for macros and `#defines`.
* **Clarity**: Variable names should be descriptive (e.g., `apps_throttle_percentage` not `atp`).
* **Comments**: Explain the **why**, not the **what**. Assume the reader knows C/C++, but doesn't know your specific logic.

# Development Practices
* **CI/CD Compliance**: Your code **must** pass the Ceedling unit tests in GitHub Actions before a PR can be merged.
* **No Binaries**: Never commit `.bin`, `.hex`, `.o`, or `.elf` files. These belong in GitHub **Releases**.
* **Draft PRs**: Open a Draft PR early in the process. It acts as a signal to the team that you are working on a specific module.
* **Portability**: Keep board-specific HAL code isolated from logic. Logic should be testable on a PC via Ceedling.

### Reviews & Releases
* **Peer Review**: All PRs require at least one approval from a subteam lead.
* **Releases**: When a version is flashed onto the car for testing or competition, it must be tagged (e.g., `v1.0.2`) and a GitHub Release created with the compiled binary attached.
* **Main Branch**: The `main` branch is for "Car-Ready" code only. It should always be in a state that is safe to run.

### About Using AI Tools
* **Verification**: AI is a tool, but you should use it with caution. It can hallucinate like hell and mess up the whole codebase.
* **Compilation**: Ensure AI hasn't hallucinated functions or broken cross-file dependencies.
* **Logic Check**: If you don't understand what the AI wrote, do not merge it.

<pre align="center">
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⣤⣤⣄⠀⠀⠀⠀⠀⠀⠀⠀⢀⣀⣀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣴⠟⠉⠉⠻⣦⡀⠀⠀⠀⠀⠀⣴⠞⠛⠻⣦⡀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⣼⠃⠀⠀⠀⠀⠈⣷⠀⠀⠀⢀⡾⠃⠀⠀⠀⠘⣷⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⢸⡇⠀⠀⠀⠀⠀⠀⢹⡄⠀⠀⣾⠁⠀⠀⠀⠀⠀⢸⡇⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⣿⠀⠀⠀⠀⠀⠀⠀⠈⣧⠀⢸⡇⠀⠀⠀⠀⠀⠀⠘⡧
⠀⠀⠀⠀⠀⠀⠀⠀⣿⠀⠀⠀⠀⠀⠀⠀⠀⣿⠀⢸⠇⠀⠀⠀⠀⠀⠀⢰⡇
⠀⠀⠀⠀⠀⠀⠀⠀⣿⠀⠀⠀⠀⠀⠀⠀⠀⣿⠀⢸⡀⠀⠀⠀⠀⠀⠀⢸⡇⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⢸⡆⠀⠀⠀⠀⠀⠀⠀⣿⠀⢸⡇⠀⠀⠀⠀⠀⠀⣸
⠀⠀⠀⠀     ⠀⠀⠘⣧⠀⠀⠀⠀⠀⠀⠀⠘⠳⠛⠀⠀⠀⠀⠀⠀⢠⡟⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠙⠂⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠸⠃⠀⠀⠀
⠀⠀⠀⠀⠀⠀⢀⣤⠶⠛⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⣴⠟⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠙⠇⠂⠀
⠀⠀⠀⢀⡾⠃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⢸⡄
⠀⠀⠀⣼⠃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠊⢣
⠀⠀⠀⢻⡀⣀⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣰
⠀⠀⠀⢨⡟⠋⠙⣧⠀⠀⣰⣦⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⡀⠀⠀⠀⠀⠀⣿
⢠⡞⠛⠻⡧⠀⠀⢻⣄⡀⠈⠉⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠿⠿⠀⠀⠀⠀⢰⡏
⠈⣷⠀⠀⠁⠀⠀⠘⠛⠳⢦⣀⠀⠀⠀⢀⡀⠀⠀⢀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣼⠃
⠀⠙⢷⣄⡀⠀⣤⣤⣤⡄⠀⢹⡆⠀⠀⠀⣽⡷⣿⡋⠀⠀⠀⠀⠀⠀⠀⢠⡾⠁
⠀⠀⠀⢿⡁⠸⣇⡀⣀⡤⠀⢸⡇⠀⠀⠀⠀⠀⠈⠁⠀⠀⠀⠀⢀⣠⡼⠋
⠀⠀⠀⠘⢷⣄⠈⠛⠉⠀⣠⠞⠛⢳⡶⢤⣤⣤⣴⡶⠶⠶⠚⠛⢩⡿⢦⡄
⠀⠀⠀⠀⠀⠉⠛⠛⠛⢻⡁⠀⠀⠀⠙⠳⠶⠖⠛⠀⠀⠀⠀⣴⣋⣠⡾⠇
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⢻⣦⣄⡀⠀⠀⠀⠀⠀⠀⠀⣰⣾⠁⠉⠁⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢻⣌⠙⠳⢶⡶⠶⠶⠞⣫⡿⠁
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⠛⠒⠛⠛⠶⠶⠞⠉
</pre>
