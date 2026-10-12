# BMS-Master fixture

Use only in BMS-Master. Check current `docs/modules/bms/renode.md` and `test/renode/run_tests.py` before reproducing a scenario. Follow repository graph discovery/coverage rules for structural queries. Paths and values below are retrieval aids, not fixed hardware specifications.

## Regression suite

From the repository root:

```powershell
cmake --preset Debug -DBMS_BUILD_RENODE_TESTS=ON
cmake --build --preset Debug --target bms_renode
python test/renode/run_tests.py
```

Default ELF: `build/Debug/bms_renode.elf`. Runner options: `--renode`, `--elf`, `--log`. Documented Windows Renode: `C:/Program Files/Renode/renode.exe`; verify it exists. The runner owns a separate headless Robot XML-RPC instance with an automatically selected port, logs/config under `build/renode/`, and cleanup on exit. Renode MCP controls a monitor connection; do not assume it attaches to the runner's instance.

## Interactive reproduction

On a fresh owned MCP instance, substitute absolute paths:

```text
include @"<repo>/test/renode/BQ79600Model.cs"
mach create
machine LoadPlatformDescription @"<repo>/test/renode/bms.repl"
sysbus LoadELF @"<repo>/build/Debug/bms_renode.elf"
emulation RunFor "0.01"
sysbus GetSymbolAddress "bms_probe_boot"
```

Read the boot symbol as a double word and require 1. Then reproduce the fixture clock adjustment:

```text
sysbus.nvic Frequency 500000000
sysbus WriteDoubleWord 0xE000E018 0
sysbus GetSymbolAddress "_tx_timer_system_clock"
```

Read the timer, run for `"0.1"`, read again and require 9..11 ticks. Check `bms_probe_owner_sequence` progresses. Attach GDB afterward for runtime failures, earlier only for boot diagnosis.

The H743/H7 platform approximates H733 with adjusted RAM sizes. ThreadX assembly assumes 500 MHz while simulated SystemInit resets RCC to 64 MHz. The fixture adjustment validates scheduling after setup, not production clock startup.

## Mailbox and faults

While paused, resolve/clear `bms_probe_done`, then publish `bms_probe_command` last. Advance the selected test's virtual duration. Require done to equal the command and `bms_probe_error` to be zero; inspect `bms_probe_detail` on failure. Read current runner/probe source for command numbers and durations.

Model MMIO base: `0xA1000000`; fault mode offset: `0x10`. Current modes: 0 healthy, 1 corrupt CRC, 2 missing tail board, 3 stuck ready, 4 ADC reset value, 5 wrong device header, 6 late reply. Confirm the current runner/model before injection. Reproduce healthy acquisition, inject a fault, verify invalidation/bounded failure, clear the mode, then verify recovery on the same link. Check protocol-error and COMM CLEAR counters as the chosen test requires.

The sideband is test-only and has no physical board equivalent. Never apply those addresses to a physical MCU. Simulation does not validate GPIO wiring, SPI speed/mode, analog settling, balancing heat or shutdown latency. Its 20 ms transaction ceiling is a regression bound, not an accepted vehicle deadline.
