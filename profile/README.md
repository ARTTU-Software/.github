# ART TU Cluj-Napoca Software Stack

![ART TU Racecar](https://raw.githubusercontent.com/ARTTU-Software/.github/main/docs/img/arttu_car_banner.png)

Engineering overview for the **ART TU Cluj-Napoca** Formula Student software stack. We design, test, and deploy the distributed embedded firmware, wireless telemetry pipelines, and cloud analytics powering our electric racecar at the Technical University of Cluj-Napoca.

---

> [!IMPORTANT]
> **Repository Access**: All vehicle firmware and telemetry repositories are private. If you want access, please reach out to the software lead or an administrator to request the **Member** team role in the organization.

> [!TIP]
> **Coding Standards**: Review our [**Coding Guidelines**](https://github.com/ARTTU-Software/.github/blob/main/docs/coding_guidelines.md) before opening a Pull Request.

---

### Public Repositories & Foundations

* [**`common`**](https://github.com/ARTTU-Software/common): Central C driver library shared across all firmware boards (CAN abstraction, circular buffers, DSP filters, and math utilities).
* [**`STM32-Template`**](https://github.com/ARTTU-Software/STM32-Template): Standardized board template pre-configured with STM32CubeMX, FreeRTOS, Ceedling unit tests, and AI coding guardrails.
* [**`Backend`**](https://github.com/ARTTU-Software/Backend): Pit-side telemetry ingest pipeline, InfluxDB time-series storage, and live Grafana dashboards.
* [**`utilities`**](https://github.com/ARTTU-Software/utilities): Diagnostic scripts, DBC conversion tools, flashing utilities, and automation helpers.
* [**`documentation`**](https://github.com/ARTTU-Software/documentation): Centralized documentation hub built with VitePress covering architecture, wiring, and protocols.

---

### External Resources
* **Getting Started**: [docs.cloud.arttu-formulastudent.ro/getting-started/](https://docs.cloud.arttu-formulastudent.ro/getting-started/)

