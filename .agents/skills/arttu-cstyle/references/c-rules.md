# Embedded C Style & Hardware Safety Guide

Defines mandatory coding standards, deterministic patterns, and hardware safety constraints for embedded firmware.

Priority order when making trade-offs: **Safety > Determinism > Maintainability > Readability**.

## Contents

- 1. Architectural Boundaries: HAL/register isolation
- 2. Naming Conventions: types, functions, macros, variables
- 3. Type Discipline & FPU Precision: numeric types and float calculations
- 4. Hardware Determinism & Bounded Loops: polling timeouts
- 5. Memory Safety & Stack Protection: allocation, stack budgets, alignment
- 6. Concurrency, Volatile & Atomic Access: publication and ISR constraints
- 7. Defensive Programming & Error Handling: API contracts and recovery
- 8. Variable Scoping & const Correctness: ownership and immutable tables
- 9. Macro Safety & Constant Definitions
- 10. Header Guard & Include Discipline
- 11. Doxygen Documentation Standards
- 12. Automated Refactoring Strategy

---

## 1. Architectural Boundaries

Application and domain logic must remain decoupled from vendor hardware abstraction layers (HAL) and direct peripheral register access.

### Interface Boundary Rule
* Forbidden in `app/` or similar:
  ```c
  HAL_GPIO_WritePin(...);
  HAL_UART_Transmit(...);
  SPI1->DR = data;
  ```
* Required: Vendor HAL APIs and direct register manipulation belong exclusively to `bsp/`, `drivers/`, or `interface/` implementations. Domain code interacts solely through abstract driver interfaces. If a HAL function is needed in domain logic, wrap it in a small driver.

---

## 2. Naming Conventions

* **Types**: `snake_case_t` (e.g., `motor_controller_t`, `can_frame_t`, `sensor_data_t`). Forbidden: `MotorController`, `CAN_FRAME_T`, `s_motor`.
* **Public Functions**: `module_action()` (e.g., `can_driver_init()`, `imu_read_accel()`).
* **Private Functions**: Static file-scope with `module_action()` or `prv_action()` (e.g., `static error_t motor_compute_pwm(void)`).
* **Constants and Macros**: `MODULE_UPPERCASE` (e.g., `CAN_RX_QUEUE_DEPTH`, `MOTOR_MAX_RPM`).
* **Variables**: `snake_case`. Private static variables should use clean identifiers without cryptic Hungarian notation.

---

## 3. Type Discipline & FPU Precision

### Fixed-Width Integer Types
Include `<stdint.h>` for fixed-width numeric data. Preserve required ABI types such as `int main(void)` and character types for text; the rules below apply to numeric protocol/register data:
* Forbidden: `int`, `short`, `long`, `unsigned`, `char` (for numeric data).
* Required: `int8_t`, `int16_t`, `int32_t`, `uint8_t`, `uint16_t`, `uint32_t`, `int64_t`, `uint64_t`.

### Boolean Values
Always include `<stdbool.h>` and use `bool`, `true`, `false`. Never use raw integers (`u8 flag = 1`) as booleans.

### Single-Precision Floating-Point Literals
On a target with a single-precision FPU, mixing a float expression with an unsuffixed floating literal can introduce double arithmetic. Use `f` suffixes and single-precision math functions for float calculations. A constant initializer such as `float dt = 0.001;` is normally converted at compile time; it does not establish a runtime performance penalty. Check target FPU capabilities and generated code when performance matters.
* Forbidden:
  ```c
  float dt = 0.001;        // Use an f suffix for consistency
  float speed = rad * 9.55; // Invokes software double multiplication
  ```
* Required:
  ```c
  float dt = 0.001f;
  float speed = rad * 9.55f;
  ```

---

## 4. Hardware Determinism & Bounded Loops

Firmware must never lock up due to unresponsive peripheral hardware or gated clocks.

### Mandatory Hardware Polling Timeouts
Unbounded polling loops can permanently lock the CPU and trigger hardware watchdogs. Every hardware flag check must have a deterministic cycle or tick limit.
* Forbidden:
  ```c
  while (!(SPI1->SR & SPI_SR_TXE)); // Hangs forever if clock is disabled
  ```
* Required:
  ```c
  uint32_t timeout_cycles = SPI_TIMEOUT_MAX_CYCLES;
  while (!(SPI1->SR & SPI_SR_TXE)) {
      if (--timeout_cycles == 0U) {
          return ERR_TIMEOUT;
      }
  }
  ```

---

## 5. Memory Safety & Stack Protection

### Dynamic Allocation Ban
Heap operations (`malloc()`, `calloc()`, `realloc()`, `free()`, `pvPortMalloc()`, `vPortFree()`) are forbidden in runtime source. They introduce non-deterministic latency and risk heap fragmentation faults.
* Allocate all buffers statically in `.bss` or `.data` at compile time:
  ```c
  static uint8_t rx_ring_buffer[UART_RX_BUFFER_SIZE];
  ```

### Task Stack Protection
Budget stack use for each task/ISR, including nested calls and worst-case interrupt nesting. Move buffers exceeding that budget to explicitly owned static storage; verify reentrancy and synchronization. Size alone does not establish an overflow:
* Forbidden inside task functions:
  ```c
  void task_telemetry(void *arg) {
      uint8_t scratchpad[1024]; // Needs a measured task-stack budget
      ...
  }
  ```
* Required:
  ```c
  static uint8_t telemetry_scratchpad[1024]; // Allocated in .bss
  ```

### Memory Alignment & Pointer Casting
Never cast arbitrary `uint8_t*` packet buffers directly to multi-byte structs or `uint32_t*`. On Cortex-M0/M0+ or when unaligned access traps are enabled, unaligned reads trigger an immediate `HardFault`.
* Use `memcpy` or explicit byte-deserialization:
  ```c
  uint32_t value;
  memcpy(&value, &rx_payload[offset], sizeof(value));
  ```

---

## 6. Concurrency, Volatile & Atomic Access

### Restricted Use of `volatile`
The `volatile` qualifier requires observable accesses to the qualified object. It does not provide atomicity, inter-thread synchronization, a compiler memory barrier, or CPU ordering of other accesses. Use the appropriate atomics/critical sections, compiler/CPU barriers, and DMA/cache ownership protocol separately. Volatile is appropriate for:
1. Hardware peripheral registers (CMSIS SFR definitions).
2. Global variables modified inside an ISR and read in thread context.
3. Flags modified by DMA controller hardware.

Do not use `volatile` on ordinary thread-local or static variables.

### 64-Bit Variable Tearing
On 32-bit ARM targets, shared 64-bit reads/writes (`uint64_t`, `int64_t`, `double`) are not automatically atomic; generated instructions and bus transactions depend on the target/compiler. Accessing a 64-bit value shared between an ISR and a thread without protection results in torn reads.
* Protect shared multi-word reads and writes with critical sections:
  ```c
  uint32_t primask = __get_PRIMASK();
  __disable_irq();
  uint64_t safe_ticks = g_system_ticks_64;
  __set_PRIMASK(primask);
  ```

### ISR Execution Rules
* Keep ISRs minimal: Clear hardware pending flags, copy data into a ring buffer or queue, notify a worker task, and exit.
* Never call blocking functions (`vTaskDelay`, `osDelay`, mutex waits) or non-reentrant standard library routines (`printf`, `sprintf`) inside an ISR.

---

## 7. Defensive Programming & Error Handling

### Pointer Validation
All public API functions must validate pointer arguments before dereferencing:
```c
if ((buffer == NULL) || (length == 0U)) {
    return ERR_INVALID_PARAM;
}
```

### Return Value Checking
Callers must never ignore return codes from functions that can fail:
```c
error_t status = spi_transmit(packet, sizeof(packet));
if (status != ERR_OK) {
    motor_emergency_stop();
    return status;
}
```

### Unified Error Types
Use typed enumeration return codes across the project. Magic integer returns (`return -1;`) are forbidden:
```c
typedef enum {
    ERR_OK               = 0,
    ERR_TIMEOUT          = 1,
    ERR_BUSY             = 2,
    ERR_INVALID_PARAM    = 3,
    ERR_NOT_INITIALIZED  = 4,
    ERR_BUFFER_FULL      = 5,
    ERR_HARDWARE_FAULT   = 6
} error_t;
```

---

## 8. Variable Scoping & `const` Correctness

* **Zero Naked Globals**: Plain global variables (`int speed;`) are forbidden. Use file-scope static variables accessed via dedicated get/set interface functions:
  ```c
  static motor_state_t s_motor_state;

  error_t motor_get_state(motor_state_t * const out_state) {
      if (out_state == NULL) {
          return ERR_INVALID_PARAM;
      }
      *out_state = s_motor_state;
      return ERR_OK;
  }
  ```
* **Immutable Data**: Mark constant tables, configuration defaults, and calibration gains as `const` so the linker places them in Flash memory instead of consuming precious RAM:
  ```c
  static const float pid_gains[3] = {1.5f, 0.02f, 0.1f};
  ```
* **Read-Only Pointers**: Pointers passed for inspection must qualify target memory as const:
  ```c
  error_t telemetry_send(const uint8_t * const data, uint16_t length);
  ```

---

## 9. Macro Safety & Constant Definitions

* **Eliminate Magic Numbers**: Every physical quantity, register bitmask, buffer length, or timing threshold must be a named `#define` or enum value.
* **Parenthesize Macro Definitions**: All parameters and expression bodies in macro definitions must be wrapped in parentheses:
  ```c
  #define SENSOR_RAW_TO_VOLTS(raw)  (((float)(raw) * 3.3f) / 4095.0f)
  ```

---


## 10. Header Guard & Include Discipline

### Standard Header Guard Format
To match project conventions and automated header guard extensions, all header files must use include guards prefixed with `INC_` and capitalized identifiers matching the file name, with the closing guard commented:

```c
#ifndef INC_<UPPERCASE_FILENAME>_H
#define INC_<UPPERCASE_FILENAME>_H

/* Header declarations */

#endif /* INC_<UPPERCASE_FILENAME>_H */
```

Examples from codebase:
* `data_processing.h` -> `INC_DATA_PROCESSING_H`
* `adc_buffer.h` -> `INC_ADC_BUFFER_H`
* `DP_scheduler_vals.h` -> `INC_DP_SCHEDULER_H`

Do not use bare `#pragma once`. Always include the comment tag on `#endif`.

### Include Minimization & Forward Declarations
* Never include heavy header files inside `.h` files when only pointers are referenced. Use forward declarations:
  ```c
  struct sensor_instance;
  ```
* Include only direct type dependencies (such as `<stdint.h>`, `<stdbool.h>`, or `"stdtypes.h"`).

---

## 11. Doxygen Documentation Standards

All public interfaces, exported functions, and data structures in header files must include concise Doxygen comments:

### Function Documentation
```c
/**
 * @brief Brief one-line summary of what the function accomplishes.
 *
 * Optional detailed explanation of algorithms, state machine transitions,
 * or hardware constraints if non-trivial.
 *
 * @param param_name Purpose of parameter, expected units or ranges.
 * @param[out] out_result Description of output pointer destination.
 * @return error_t ERR_OK on success, or specific error enum on failure.
 */
error_t sensor_read_filtered(uint8_t channel, float * const out_result);
```

### Struct & Enum Documentation
```c
/**
 * @brief Discrete operational states for the drive inverter.
 */
typedef enum {
    INVERTER_STATE_OFF         = 0, /**< Gate drivers disabled */
    INVERTER_STATE_PRECHARGE   = 1, /**< Precharge contactor closed */
    INVERTER_STATE_READY       = 2, /**< High voltage active and ready */
    INVERTER_STATE_FAULT       = 3  /**< Critical fault latched */
} inverter_state_t;
```

Keep documentation dense and technical. Avoid redundant filler text that merely repeats the function name.

---

## 12. Automated Refactoring Strategy

When scanning or reviewing firmware:
1. **Identify**: Locate the exact file, line number, and anti-pattern.
2. **Impact Assessment**: Classify the consequence: Hardware Crash, Watchdog Timeout, Stack Overflow, Performance Degradation, or Maintainability Issue.
3. **Remediation**: Provide the corrected, safe implementation inline following the checklist above.
