---
name: renode-gdb-debug
description: Debug emulated embedded firmware using Renode MCP and GDB MCP, reproduce failures, and preserve scripted regression tests. Use for simulation control, fault injection and source debugging; physical SWD and flashing use the board's hardware-debugging workflow.
---

# Renode and GDB debugging

Use Renode MCP for interactive simulation control and GDB MCP for source diagnosis. Keep the repository's scripts as the reproducible pass/fail authority. MCP does not improve the emulator's peripheral fidelity or replace assertions.

## Choose the workflow

- For regression verification, run the existing runner and required build. Do not translate the suite into agent tool calls.
- For a failure, identify the ELF, platform, models, setup, virtual durations and assertions. Reproduce the fixture in a separate interactive instance before attaching GDB.
- For exploration, inject faults while paused and advance bounded virtual time. Turn useful findings into regression tests when code/test changes are requested.
- In BMS-Master, read [references/bms-master.md](references/bms-master.md). Elsewhere, discover the repository's equivalent fixture rather than copying BMS addresses or clocks.

## Establish the session

Discover actual Renode/GDB tool schemas before use. Names below refer to the currently exposed tools, not a universal wrapper.

Check `renode_status` and `gdb_list_sessions`. Reuse a relevant session only when its ownership, platform and ELF are established. Do not reset or stop unrelated sessions. The current Renode tools expose one active instance without session IDs.

Start an owned headless instance using `renode_start`, selecting an installed executable and free monitor port. Load an existing `.resc` with `renode_load_script`, or reproduce setup using `renode_execute`. Use absolute paths and Renode's `@` syntax, quoting paths containing spaces. Load custom model code before the platform that references it, then load the matching ELF. Check boot state after a short bounded run.

`renode_execute` supports arbitrary monitor commands, symbol lookup, model configuration and `emulation RunFor "100ms"`. Use `renode_read_memory`/`renode_write_memory` for widths supported by their schemas (currently 1, 2, 4 bytes). Resolve symbol addresses from the loaded ELF. Pause before multi-field injections and publish the command/ready field last, following the fixture's ownership protocol.

UART reads require a UART explicitly exposed through `CreateServerSocketTerminal`; availability of `renode_read_uart` does not establish a UART socket.

## Attach GDB to firmware

Keep monitor, GDB and UART ports distinct.

1. While paused, execute `machine StartGdbServer 3333` through Renode MCP, choosing another free port if necessary.
2. Use `gdb_start` with an ARM-capable debugger such as `arm-none-eabi-gdb` and the repository working directory. Preserve its returned `sessionId` for all GDB calls.
3. Through `gdb_command`, issue `file "C:/absolute/path/firmware.elf"`, then `target remote localhost:3333`. Renode already loaded the image; do not assume `gdb_load` programs the target.
4. Verify connection/location using registers, source or backtrace. Set a reachable breakpoint with `gdb_set_breakpoint`, optionally conditional. Inspect values using `gdb_print`, memory with `gdb_examine`, and frames with `gdb_backtrace`.
5. Use `gdb_step`, `gdb_next` and `gdb_finish` on a stopped CPU. Source stepping requires debug information; otherwise report the limitation and inspect instructions/registers. Use `gdb_command` for watchpoints or commands absent from dedicated tools.

`gdb_attach(pid)` attaches to a host process, not firmware through Renode. Attaching to the Renode process debugs the emulator itself.

Avoid concurrent execution control through Renode and GDB. Ensure execution has stopped before switching to monitor stepping/injection. GDB CPU stops halt virtual time; debugger wall time does not establish a firmware timeout. Avoid unbounded continue without a verified reachable stop; prefer bounded monitor runs and explicit state checks. If a tool blocks waiting for a stop, use its documented interrupt mechanism. If none is available, report the blocked session instead of guessing interruption APIs.

## Verify and clean up

Record the ELF/build, model/platform, injected values, virtual durations, stop conditions and expected/observed result. Preserve enough commands to reproduce independently of chat history.

A debugger-modified run is diagnostic evidence. Verify fixes by rerunning scripts without debugger mutations and following repository checks. Distinguish simulation results from physical-board validation.

Terminate only GDB/Renode processes created for this task, unless the user wants them left available. If MCP is disconnected or incompatible, use the repository runner or installed CLI and disclose the limitation. Tool availability alone does not prove a successful connection.

See Renode's [GDB documentation](https://renode.readthedocs.io/en/latest/debugging/gdb.html) for remote attachment and virtual-time behavior, and [testing API](https://renode.readthedocs.io/en/latest/basic/renode-testing-api.html) for Robot monitor commands.
