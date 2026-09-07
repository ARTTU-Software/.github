# ART TU Cluj-Napoca Software Stack

![ART TU Racecar](https://raw.githubusercontent.com/ARTTU-Software/.github/main/docs/img/arttu_car_banner.png)

Engineering overview for the **ART TU Cluj-Napoca** Formula Student software stack. We design, test, and deploy the distributed embedded firmware, wireless telemetry pipelines, and cloud analytics powering our electric racecar at the Technical University of Cluj-Napoca.

---

> [!IMPORTANT]
> **Repository Access**: All vehicle firmware and telemetry repositories are private. If you want access, please reach out to the software lead or an administrator to request the **Member** team role in the organization.

> [!TIP]
> **Coding Standards**: Review our [**Coding Guidelines**](https://github.com/ARTTU-Software/.github/blob/main/docs/coding_guidelines.md) before opening a Pull Request.

<details>
<summary>📋 <b>Quick Review: Firmware Invariants & PR Rules</b></summary>

* **Branch Hygiene**: Never push directly to `main`. Open pull requests from `feat/`, `fix/`, `refactor/`, or `test/` into `dev/`.
* **Verification Gate**: All C code must compile cleanly and pass Ceedling unit tests (`ceedling test:all`) before review.
* **Deterministic Allocation**: Zero dynamic memory allocation (`malloc`/`free`) permitted anywhere in runtime code.
* **Hardware Isolation**: Direct HAL calls belong strictly in driver layers; application logic remains portable and hardware-agnostic.
* Full details: [docs/coding_guidelines.md](https://github.com/ARTTU-Software/.github/blob/main/docs/coding_guidelines.md).
</details>

---

### Vehicle Architecture

Our distributed automotive architecture communicates over high-speed CAN networks using centralized DBC definitions:

#### Embedded Control Units (STM32 Cortex-M)
* [**`ECU`**](https://github.com/ARTTU-Software/ECU): Main vehicle control unit. Runs torque demand calculation, APPS/brake implausibility checks, safety state machine, and inverter CAN control.
* [**`CAN-Gateway`**](https://github.com/ARTTU-Software/CAN-Gateway): High-speed sensor aggregation (suspension potentiometers, wheel speeds, steering angle, etc.), low-pass digital filtering, CAN message routing, and low-current hardware actuation.
* [**`Dashboard`**](https://github.com/ARTTU-Software/Dashboard): Cockpit driver interface driving the TFT display and CI indicators.
* [**`Telemetry`**](https://github.com/ARTTU-Software/Telemetry): Vehicle wireless gateway. Transmits live racecar data directly to the cloud and logs high-rate packets to local storage.
* [**`Galvanic-Isolator`**](https://github.com/ARTTU-Software/Galvanic-Isolator): Inverter isolation board protecting low-voltage electronics from high-voltage inverter domains.
* [**`LVSOC-26`**](https://github.com/ARTTU-Software/LVSOC-26): Low-voltage accumulator state-of-charge tracking and power distribution monitoring.

#### Shared Foundations & Infrastructure
* [**`common`**](https://github.com/ARTTU-Software/common): Central C driver library shared across all firmware boards (CAN abstraction, circular buffers, DSP filters, and math utilities).
* [**`STM32-Template`**](https://github.com/ARTTU-Software/STM32-Template): Standardized board template pre-configured with STM32CubeMX, FreeRTOS, Ceedling unit tests, and AI coding guardrails.
* [**`Backend`**](https://github.com/ARTTU-Software/Backend): Pit-side telemetry ingest pipeline, InfluxDB time-series storage, and live Grafana dashboards.
* [**`utilities`**](https://github.com/ARTTU-Software/utilities): Diagnostic scripts, DBC conversion tools, flashing utilities, and automation helpers.
* [**`documentation`**](https://github.com/ARTTU-Software/documentation): Centralized documentation hub built with VitePress covering architecture, wiring, and protocols.

---

### External Resources
* **Getting Started**: [docs.cloud.arttu-formulastudent.ro/getting-started/](https://docs.cloud.arttu-formulastudent.ro/getting-started/)
* **Team Website**: [arttu.ro](https://arttu.ro)

