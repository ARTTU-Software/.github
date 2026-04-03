## 🧭 Coding Guidelines

Some basic rules to keep the codebase consistent, readable, and not nakaz:

# Structure & Organization
- Follow the folder layout in the repo (don’t dump files randomly pls).
- Each board (BMS, ECU, IMU, etc.) has its own `src/` and `include/` directories. If on STM32, follow basic design guidelines.
- Shared code (drivers, utilities, math, etc.) goes in [/common](../common).
- Try to keep commits small and focused — (hopefully) one logical change per commit.

# Code Style
- Use **consistent indentation** (tabs or 4 spaces, just don’t mix them).
- Keep variable and function names **clear and descriptive**. You don't wanna guess what a function does for 10min.
- Use `camelCase` or `snake_case` for variables and functions, `ALL_CAPS` for macros and defines.
- Comments: explain *why*, not *what*. The code already shows *what* it does. At most, dedicate a sentence to what the function does at the top.
- Don’t leave commented out blocks of old code lying around, use Git revisions for history.

# Development Practices 
- Always build and test before pushing.
- Don’t commit binaries, build outputs, or local configs, add them to `.gitignore`. This breaks compilation for other people, keep that in mind.
- Document any new module or hardware interface in [docs](.).
- Keep code portable where possible, avoid using chip specific stuff in common code.
- If you’re touching multiple areas, **open a draft Pull Request** (PR) early so others can see progress.

# Reviews & Versioning
- Get another person to review critical code (especially safety-related stuff).
- Keep a short changelog or version tag for each major firmware update.
- Write clear commit messages, “nakaz mare whatever 123" is not clear I think.
- **Work in separate branches that will be merged into master by a responsible**

# Branch Naming 🤯
To keep the repository organized, follow this format for branch names:
| Type | Description | Example |
|------|--------------|----------|
| `feature/` | For new features or modules | `feature/can-flashing` |
| `bugfix/` | For fixing specific bugs | `bugfix/telemetry-crash` |
| `hotfix/` | For urgent fixes that need to go directly to `main` | `hotfix/build-failure` |
| `refactor/` | For restructuring or cleaning up code without new features | `refactor/common-drivers` |
| `docs/` | For documentation-only changes | `docs/add-coding-guidelines` |
| `test/` | For experimental or temporary testing | `test/add-GI-test` |

Example: docs/project-structure


# About Using AI Tools
- You *can* use AI to speed up coding, but **don’t trust it blindly** *please*.
- Always check and understand what it outputs before committing.
- If something looks off, test it or ask for a second opinion.
- AI is a tool, not a substitute for knowing what your code actually does.
- Don't automatically accept changes, try to keep agents at a minimum. You'd be surprised how many times they make the code not compile from 5 different files.


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