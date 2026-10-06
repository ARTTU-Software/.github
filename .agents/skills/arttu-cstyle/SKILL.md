---
name: arttu-cstyle
description: Apply ARTTU embedded C safety and coding conventions when writing or reviewing firmware, drivers, ISR code, or state machines.
---

# Embedded C invariants

Apply these constraints to changed code. Avoid unrelated formatting/refactors. Detailed patterns remain in [references/c-rules.md](references/c-rules.md). When changing public headers, read its Header Guard & Include Discipline and Doxygen Documentation Standards sections. For concurrency, polling or packet-decoding changes, read the corresponding safety sections before implementation. Do not skip a relevant contract to save tokens.

- Priority: safety, determinism, maintainability, readability.
- Keep HAL/register access in `bsp/`, `drivers/`, or `interface/`; application/domain code uses driver interfaces. Preserve CubeMX generated regions and USER CODE delimiters. Vendor/CMSIS, linker and startup changes require approval.
- No dynamic allocation in runtime source, including RTOS heap wrappers. Give static buffers explicit ownership; static storage does not make concurrent use safe. Budget task/ISR stacks using worst-case execution paths.
- Use fixed-width integer types for numeric protocol/register data and `bool` for logical values. Preserve required ABI types (for example `int main(void)`) and character types for text. Use `f` literals/single-precision math when appropriate to the target FPU; measure runtime promotion costs instead of assuming them.
- Bound every hardware polling wait and handle timeout/failure explicitly. Keep ISRs bounded, nonblocking and free of mutex waits, allocation and non-reentrant formatted I/O.
- Validate public API pointer/length contracts and check fallible return codes. Use consistent typed errors and defined recovery behavior.
- Volatile controls accesses to an object; it does not provide atomicity, synchronization or memory barriers. Protect shared state with the correct critical-section/atomic/publication protocol. Consider DMA and cache coherency separately. Shared multiword values may tear.
- Deserialize packet bytes with `memcpy` or explicit byte operations; do not cast arbitrary packet buffers to aligned structs/words.
- Use file-scope static ownership and const configuration tables. Pass inspected data through const-qualified pointers. Make concurrency semantics explicit in accessors.
- Types use `snake_case_t`, functions use `module_action()`, variables use `snake_case`, and constants/macros use `MODULE_UPPERCASE`. Private functions/data have file-scope static ownership; do not introduce unowned exported globals.
- Header guards use `INC_<UPPERCASE_FILENAME>_H` with a matching closing comment; preserve existing approved naming exceptions. Include only direct dependencies and forward-declare pointer-only types. Public functions/types in headers require concise Doxygen contracts covering parameters, units, output ownership and failure returns where applicable.
- Parenthesize macro parameters and bodies; name physical units, buffer lengths and timing thresholds. Keep these team conventions explicit rather than inferring them from inconsistent legacy code.

For review, identify the changed symbol/source anchor, its concrete consequence, and the minimal remedy. Use the discovery skill for callers/dataflow, and vehicle specifications when interfaces change. Verify a cohesive batch with unit tests and the required target build; do not claim MISRA/functional-safety compliance from these conventions alone.
