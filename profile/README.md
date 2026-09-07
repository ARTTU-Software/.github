# ART TU Cluj-Napoca Software Stack

![ART TU 2026 Racecar](https://raw.githubusercontent.com/ARTTU-Software/.github/main/docs/img/art26_racecar.png)

Engineering overview for the **ART TU Cluj-Napoca** Formula Student software stack. We design, test, and run the distributed embedded firmware, real-time telemetry, and trackside data analytics powering our electric racecars at the Technical University of Cluj-Napoca.

---

### Architecture Overview

We use a modular multi-repository architecture. Each major physical board and software subsystem maintains its own repository, communicating over deterministic CAN bus networks using centralized DBC definitions.

#### Embedded ECUs (STM32 Cortex-M)
* [**`ECU`**](https://github.com/ARTTU-Software/ECU): Main vehicle control unit. Runs torque demand calculation, APPS/brake implausibility checks, safety interlocks, and inverter CAN control.
* [**`CAN-Gateway`**](https://github.com/ARTTU-Software/CAN-Gateway): High-speed sensor aggregation. Samples suspension potentiometers, wheel speeds, and steering angle; applies digital filtering and routes packets between CAN domains.
* [**`Dashboard`**](https://github.com/ARTTU-Software/Dashboard): Cockpit driver interface. Drives the steering wheel display, button matrix, warning indicators, and Ready-to-Drive Sound (RTDS).
* [**`Telemetry`**](https://github.com/ARTTU-Software/Telemetry): Vehicle wireless gateway. Transmits live telemetry data over Wi-Fi/LTE to pit lane and logs high-rate packets to local storage.
* [**`Galvanic-Isolator`**](https://github.com/ARTTU-Software/Galvanic-Isolator): High-voltage / low-voltage electrical isolation monitoring and fault signal transmission.
* [**`LVSOC-26`**](https://github.com/ARTTU-Software/LVSOC-26): Low-voltage accumulator state-of-charge tracking and power distribution monitoring.

#### Shared Foundations & Infrastructure
* [**`common`**](https://github.com/ARTTU-Software/common): Central C driver library shared across all firmware boards. Contains CAN abstraction, circular buffers, DSP filters, and math utilities.
* [**`STM32-Template`**](https://github.com/ARTTU-Software/STM32-Template): Standardized board template pre-configured with STM32CubeMX, FreeRTOS, Ceedling unit tests, and AI coding guardrails.
* [**`Backend`**](https://github.com/ARTTU-Software/Backend): Pit-side telemetry ingest pipeline, InfluxDB time-series storage, and live Grafana dashboards.
* [**`utilities`**](https://github.com/ARTTU-Software/utilities): Diagnostic scripts, DBC conversion tools, flashing utilities, and automation scripts.
* [**`documentation`**](https://github.com/ARTTU-Software/documentation): Centralized documentation hub built with VitePress covering architecture, wiring, and protocols.

---

### Contributing & Code Standards

We enforce rigorous safety and verification standards across all automotive code:
* **Target Branch**: Never push directly to `main`. Open pull requests against `dev/` using conventional branch prefixes (`feat/`, `fix/`, `refactor/`, `test/`).
* **Verification**: All embedded C changes must compile cleanly and pass unit tests with Ceedling (`ceedling test:all`) before review.
* **Deterministic Execution**: Zero dynamic memory allocation (`malloc`/`free`) in runtime code; hardware access strictly isolated to driver layers.

For complete rules, see our [**Coding Guidelines**](https://github.com/ARTTU-Software/.github/blob/main/docs/coding_guidelines.md).

---

### Repository Access

> [!NOTE]
> All vehicle firmware and telemetry repositories are private. If you are a team member looking for access to the private codebase, request the **Member** organization role from the software lead or an administrator.

---

### Connect with Us
* **Website**: [arttu.ro](https://arttu.ro)
* **Organization Hub**: [ARTTU-Software](https://github.com/ARTTU-Software)
