---
name: arttu-stm32-debugging
description: Drive on-target hardware debugging, inspect/write variables via ELF symbols, flash firmware, and analyze HardFault crashes on STM32 MCUs using STM32CubeCLT/STM32CubeProgrammer CLI. Use when connecting over SWD, verifying core status, reading/injecting RAM variables with linker boundary protection, inspecting peripheral registers, or decoding crashes with addr2line. Do NOT use for generic C code formatting (use arttu-cstyle), high-level vehicle documentation lookups (use arttu-docs-assistant), or writing module docs (use arttu-docs-writer).
compatibility: Requires STM32CubeCLT or STM32CubeProgrammer and arm-none-eabi binutils installed; ST-LINK connected to target.
---

# STM32 Debugging & Hardware Operations Guide

Drives on-target hardware debugging, variable inspection, safe memory injection, flashing, and crash analysis directly from the terminal.

---

## 1. Toolchain & Probe Discovery

### Tool Discovery
Verify tools exist on `PATH` or resolve from default STM32CubeCLT install paths:
* **CLI**: `STM32_Programmer_CLI` (Win: `C:\ST\STM32CubeCLT_*\STM32CubeProgrammer\bin\STM32_Programmer_CLI.exe`)
* **Binutils**: `arm-none-eabi-nm`, `arm-none-eabi-addr2line` (Win: `C:\ST\STM32CubeCLT_*\GNU-tools-for-STM32\bin\`)
* **CMSIS SVDs**: `C:\ST\STM32CubeCLT_*\STMicroelectronics_CMSIS_SVD\`

> [!NOTE]
> In Windows PowerShell, when invoking an executable path containing spaces or quotes, always precede the command with the call operator `&` (e.g. `& "C:\ST\STM32CubeCLT_1.18.0\...\STM32_Programmer_CLI.exe" -l`).

### Probe Enumeration Protocol
Always check connected ST-LINK probes first:
```bash
STM32_Programmer_CLI -l
```
* **Exactly 1 probe found**: Proceed without serial flag.
* **2+ probes found**: Identify the target `ST-LINK SN : <SERIAL>` and require `sn=<SERIAL>` on all connection strings:
  ```bash
  STM32_Programmer_CLI -c port=SWD sn=002900174741500520383831 mode=HOTPLUG shared ...
  ```
* **0 probes found**: Abort. Alert the user to verify USB connection and ST-LINK power LED.

---

## 2. Safe Launching & Connection (`mode=HOTPLUG shared`)

### Mandatory Runtime Flags
For all live inspection and variable reads/writes, you **MUST** use:
1. `mode=HOTPLUG`: Attaches over SWD without asserting reset (`nRST`) and keeps the CPU running uninterrupted. Prevents watchdog trips (IWDG/WWDG) and shutdown relay openings.
2. `shared`: Enables ST-LINK Server multiplexing so STM32CubeIDE, serial terminals, and CubeMonitor can access the probe simultaneously without "device busy" collisions.

```bash
# Check CPU status ('Running', 'Halted', or 'Sleep')
STM32_Programmer_CLI -c port=SWD mode=HOTPLUG shared -score
```

---

## 3. Reading Runtime Variables via ELF Symbols

### Step 1: Resolve Address & Size
Map the C variable identifier to its physical RAM address from the build artifact (`.elf`):
```bash
arm-none-eabi-nm -C -S path/to/firmware.elf | grep -w "<variable_name>"
# Windows PowerShell fallback:
# arm-none-eabi-nm -C -S path/to/firmware.elf | Select-String " <variable_name> "
```
*Tip: If `-w` yields no match, remove it to find static file-scope variables with compiler suffixes (e.g. `<variable_name>.0`).*

*Example Output:* `20000140 00000004 D apps1_filtered` $\to$ Address `0x20000140`, Size `4` bytes.

### Step 2: Read RAM via SWD (Width-Matched)
Match the read command to the variable size:
* **1-byte (`uint8_t`, `bool`)**: `STM32_Programmer_CLI -c port=SWD mode=HOTPLUG shared -q -r8 0x20000140 1`
* **2-byte (`uint16_t`, `int16_t`)**: `STM32_Programmer_CLI -c port=SWD mode=HOTPLUG shared -q -r16 0x20000140 2`
* **4-byte (`uint32_t`, `float`)**: `STM32_Programmer_CLI -c port=SWD mode=HOTPLUG shared -q -r32 0x20000140 4`

### Step 3: Decode Output
* **Integer / Hex**: Convert directly (e.g., `0x00000003` $\to$ `3`).
* **IEEE-754 Single-Precision Float**: `STM32_Programmer_CLI` prints the 32-bit register MSB-first. Unpack using **big-endian (`>f`)**:
  ```bash
  python -c "import struct; print('Value:', struct.unpack('>f', bytes.fromhex('42280000'))[0])"
  ```
  *Output:* `Value: 42.0`

---

## 4. Safe Memory Injection & Closed-Loop Verification

Writing directly to hardware must never corrupt Flash memory (`0x08000000`) or Option Bytes (`0x1FFFF000`).

### Step 1: Mandatory Linker Script Boundary Inspection
1. Locate the active linker script (`.ld`) and read the `MEMORY` block:
   ```bash
   # Linux / macOS / Git Bash:
   find . -name "*.ld"
   # Windows PowerShell:
   Get-ChildItem -Filter *.ld -Recurse | Select-Object -ExpandProperty FullName
   ```
2. Identify all valid RAM regions marked with `(xrw)` or `(rw)` (e.g. `RAM`, `CCMRAM`, `DTCMRAM`, `SRAM1`, `SRAM2`).
3. Compute the span for each region, handling units:
   * `K` = multiply by $1024$ (e.g. `128K` $= 128 \times 1024 = 131,072 = \text{0x20000}$).
   * `M` = multiply by $1024 \times 1024$.
   * Span: `[ORIGIN, ORIGIN + LENGTH)`.
4. **Validation**: Target address must reside entirely within at least one valid RAM region. **If target touches FLASH or Option Bytes, ABORT IMMEDIATELY.**

### Step 2: Width-Matched Write Execution
> [!CAUTION]
> **Never use `-w32` on an 8-bit or 16-bit variable.** Writing 32 bits to an 8-bit variable will overwrite the adjacent 3 bytes of RAM, corrupting neighboring variables!

* **1-Byte Variables (`uint8_t`)**:
  ```bash
  STM32_Programmer_CLI -c port=SWD mode=HOTPLUG shared -w8 0x20000140 0x01
  ```
* **2-Byte Variables (`uint16_t`)**:
  ```bash
  STM32_Programmer_CLI -c port=SWD mode=HOTPLUG shared -w16 0x20000140 0x0100
  ```
* **4-Byte Variables (`uint32_t`, `float`)**:
  ```bash
  STM32_Programmer_CLI -c port=SWD mode=HOTPLUG shared -w32 0x20000140 0x42280000
  ```
* **Atomic Multi-Word Writes**: If modifying multiple related variables simultaneously (e.g. dual sensor channels to prevent cross-channel divergence trips), halt briefly and resume immediately:
  ```bash
  STM32_Programmer_CLI -c port=SWD mode=HOTPLUG shared -halt -w32 0x20000140 0x42280000 -w32 0x20000144 0x42280000 -run
  ```

### Step 3: Closed-Loop Readback Verification
After every write, immediately issue a read command (`-r8`/`-r16`/`-r32`) to verify the new value was written.
* If the readback matches: Confirm injection success.
* If the readback does not match: Inform the user that an active ISR, DMA stream, or FreeRTOS task is immediately overwriting the variable in hardware.

---

## 5. Register Inspection & SVD Decoding

### Core CPU Registers
`-coreReg` halts the CPU core. **Always append `-run`** to resume target execution:
```bash
STM32_Programmer_CLI -c port=SWD mode=HOTPLUG shared -coreReg R0 R1 R2 R3 PC LR SP XPSR -run
```

### Peripheral Registers & Token-Efficient SVD Lookups
1. Calculate target address: `Base + Offset` (e.g., STM32F4 `CAN1` base `0x40006400`, `ESR` offset `0x18` = `0x40006418`).
2. Read without halting:
   ```bash
   STM32_Programmer_CLI -c port=SWD mode=HOTPLUG shared -r32 0x40006418 4
   ```
3. Query the SVD without loading the entire 3MB file into context:
   ```bash
   python -c "import xml.etree.ElementTree as ET; tree = ET.parse(r'C:\ST\STM32CubeCLT_1.18.0\STMicroelectronics_CMSIS_SVD\STM32F405.svd'); print([f.find('name').text for p in tree.iter('peripheral') if p.find('name').text=='CAN1' for r in p.iter('register') if r.find('name').text=='ESR' for f in r.iter('field')])"
   ```

---

## 6. Automated HardFault Crash Diagnosis

When firmware triggers `HardFault_Handler`:

### Step 1: Run ST HardFault Analyzer
```bash
STM32_Programmer_CLI -c port=SWD mode=HOTPLUG shared -hf
```
Extracts:
* Active stack pointer (`PSP` for FreeRTOS tasks, `MSP` for ISRs)
* Exception stack frame: `R0-R3`, `R12`, `LR`, `PC`, `xPSR`
* `CFSR` flags: `DIVBYZERO`, `UNALIGNED`, `PRECISERR`, `INVSTATE`

### Step 2: Map Faulting PC to C Source Line
```bash
arm-none-eabi-addr2line -e path/to/firmware.elf -f -C <FAULTING_PC_ADDRESS>
```
*Output identifies the exact function, source file, and line number.*

---

## 7. Firmware Flashing & Target Recovery

> [!IMPORTANT]
> Do NOT use `mode=HOTPLUG` when flashing single-bank flash. Flashing while the CPU fetches instructions from the same flash bank will cause bus stalls or faults. Flashing requires halting the core.

* **Flash, Verify, and Reset**:
  ```bash
  STM32_Programmer_CLI -c port=SWD shared -w path/to/firmware.elf -v -rst
  ```
* **Flash Without Reset (Preserves live hardware state)**:
  ```bash
  STM32_Programmer_CLI -c port=SWD shared -w path/to/firmware.elf -v
  ```
* **Target Recovery (Under Reset Mass Erase)**:
  ```bash
  # If nRST pin is wired to ST-LINK:
  STM32_Programmer_CLI -c port=SWD mode=UR -e all
  # If nRST pin is NOT wired (SWD-only 3-wire):
  STM32_Programmer_CLI -c port=SWD reset=SWrst -e all
  ```

---

## 8. Session Hygiene Checklist

Before concluding any session:
1. Run `-score` to confirm target is in `Running` state.
2. If halted, issue `-run` before disconnecting.

---

## 9. Troubleshooting Matrix

| Error Message | Root Cause | Solution |
| :--- | :--- | :--- |
| `No debug probe detected` | ST-LINK disconnected / driver missing | Reseat USB cable; check device manager for ST-LINK driver. |
| `No STM32 target found` | Target unpowered or SWD lines disconnected | Check target 3.3V rail; inspect SWCLK, SWDIO, GND. |
| `Target is in low power mode` | MCU is in `Stop` or `Standby` | Add `LPM` flag: `-c port=SWD mode=HOTPLUG shared LPM`. |
| `Device is busy / probe locked` | Debugger locked by another process | Ensure `shared` flag is present to route via STLinkServer. |
| `Address out of bounds` | Target write address outside RAM | Check `.ld` file and verify symbol address from `.elf`. |
| `Readback mismatch after write` | Variable overwritten by firmware | Injected variable is actively being updated by a running ISR, DMA, or FreeRTOS task. |
