# ART TU Cluj-Napoca Software Stack 2026

![Car 2025](<../docs/img/20250824_10-55-24_8545_kohler-X3 (1).jpg>)
Top-level overview for the ART TU Cluj-Napoca Formula Student software stack. This organization contains all code powering the 2026 racecar.

### Contributing
Review the [**Coding Guidelines**](../docs/coding_guidelines.md) before opening a Pull Request. CI checks are strictly enforced on all board firmware.

### Architecture
We use a multi-repository structure. Each major hardware board and system has its own dedicated repository and team:

#### Core Systems
- [**`ECU`**](link-to-repo) - Electronic Control Unit firmware.
- [**`CAN-Gateway`**](link-to-repo) - Sensor aggregation / filtering.
- [**`GI`**](link-to-repo) — Galvanic Isolator
- [**`Dashboard`**](link-to-repo) — UI, Main Drivers, Display
- [**`Telemetry`**](link-to-repo) — Car-to-pit data transmission and real-time visualization.

#### Data & Analytics
- [**`Backend`**](link-to-repo) — Grafana + InfluxDB + Marple + Middleman Architecture

#### Shared Libraries
- [**`Commons`**](link-to-repo) — Shared C/C++ libraries used across multiple boards (CAN drivers, math utilities, struct definitions).

---

### Teams & Access
Access is managed via GitHub Teams. If you lack access to a repository, request it from your subteam lead by pinging the relevant group:
* `@ART-TU/ecu-team`
* `@ART-TU/can-gateway-team`
* `@ART-TU/gi-team`
* `@ART-TU/dashboard-team`
* `@ART-TU/telemetry` & `@ART-TU/backend`
