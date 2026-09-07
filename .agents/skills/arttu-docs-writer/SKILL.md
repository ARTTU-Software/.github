---
name: arttu-docs-writer
description: Generate and update system-level architectural documentation for embedded firmware modules inside local board repositories (./docs/modules/). Triggers when completing a firmware feature, module, state machine, or refactor to document dataflow, concurrency models, hardware interfaces, and failure recovery. Forbids line-by-line code walks, AI-style buzzwords, and em dashes. Do NOT use for reading or querying existing documentation (use arttu-docs-assistant), enforcing C coding standards (use arttu-cstyle), or on-target debugging (use arttu-stm32-debugging).
---

# Embedded Documentation Writer Guide

Guides the agent in writing and maintaining system-level, architectural documentation for embedded firmware modules directly inside board repositories.

Priority order: **System Architecture > Concurrency & Flow > Hardware Coupling > Code Anchors**.

---

## 1. Core Philosophy: Systems Over Code

Explain runtime behavior, not C source code line-by-line.

* **Module Ownership**: Define boundaries and responsibilities against the rest of the vehicle.
* **Concurrency & Lifecycles**: Detail interactions between threads, ISRs, and hardware peripherals.
* **Architectural Rationale**: State why designs exist (e.g. ping-pong buffers for flash latency, seqlocks to avoid ISR stalls).
* **Zero Code Narration**: Never narrate code statements or line numbers. Invariants endure; syntax changes.

---

## 2. Triggering & Scope Rules

* **Trigger Point**: Activate when a feature, driver, state machine, or significant refactor is completed, or when the user explicitly requests module documentation.
* **Target Location**: Write or update files in `./docs/modules/<category>/<module>.md` within the local firmware repository.
* **Surgical Scope**: Touch only the documentation pages directly affected by the current code changes. Never re-audit, reformat, or touch unrelated documents.
* **Local Index Linking**: When adding a new module document, add its reference to `./docs/modules/index.md` or the relevant category index page.

---

## 3. Strict Engineering Voice & Anti-AI Banlist

Firmware engineers require dense, high-signal technical information. Synthetic AI prose is strictly forbidden.

### Prohibited Writing Patterns
* **Zero Em Dashes**: Never use em dashes (`—`, `&mdash;`, or `--` as dash). Use colons, parentheses, commas, or hyphens.
* **Zero Filler Introductions**: Start immediately with the module's concrete function.
* **Zero AI Buzzwords**: Banned: "seamlessly", "testament to", "crucial", "robust", "delve", "deep dive", "pivotal role", "leverage", "comprehensive suite", "it is worth noting that".
* **Zero Code Narration & Boilerplate**: No line-by-line walks or dumping function prototypes.

### Required Engineering Voice
* **Dense & Concise**: State facts, show the diagram, give the numbers, stop. Under 2 minutes to read.
* **First-Person Team Perspective**: When referencing the team, use "we", "us", or "our" instead of third-person ("the team", "the developers").
* **Concrete Parameters & Units**: Specify rates (50 Hz), buffers (16 KiB), timeouts (10 ms), baud (1 Mbps).
* **Explicit Trade-Offs**: State failure modes directly (e.g. "slow SD drops samples, never blocks execution").

---

## 4. Checklist-Driven Module Blueprint

Every generated or updated module page must answer the following core engineering questions:

### 1. Responsibility & Boundaries
* What physical problem does this module solve?
* What does this module own vs what does the rest of the car or firmware own?

### 2. Concurrency & Execution Context
* Which execution context runs this code: FreeRTOS/ThreadX thread, timer callback, ISR, DMA stream, or main loop?
* What are the execution rates, task priorities, and wake triggers (semaphore, event flags, timer)?
* How is shared state synchronized (seqlocks, mutexes, ring buffers, atomic primitives)?

### 3. Dataflow or State Machine (Mermaid Diagram Mandatory)
Whenever data movement, concurrency handoffs, or state transitions exist, include a Mermaid diagram following the team standards from `adding-mermaid-diagrams.md`:
* **The Column Layout (Multi-Process Flows)**:
  * Top-level flowchart must be Left-to-Right (`flowchart LR`).
  * Group major concurrent pathways into separate `subgraph` blocks (e.g. Producers, Shared State, Consumers).
  * Set the internal direction of each subgraph to Top-to-Bottom (`direction TB`) so flows run down parallel columns that fit widescreen viewports.
* **Per-Diagram Zoom Control (`data-zoom`)**:
  * For standard layouts, omit wrapper (defaults to 1.0).
  * For dense, multi-column diagrams, wrap in `<div data-zoom="0.8">` or `0.9` so the entire layout is visible on initial load.
  * For small diagrams needing larger text, use `<div data-zoom="1.15">`.
* **Flow Lines & Connections**:
  * Use solid arrows (`-->`) with concise label text for primary data or transition flow.
  * Use dotted arrows (`-.->`) for secondary connections (such as asynchronous helper calls or notifications) to keep the primary flow clean.
* **Mermaid Syntax Invariants (Zero Parse Errors)**:
  * Never use comparison operators (`<`, `>`, `<=`, `>=`) inside edge labels `|...|` or decision shapes `{...}`. Mermaid treats `<` and `>` as arrowheads/HTML tags. Use words (e.g. `Exceeds 15%`, `Positive`) or double quotes.
  * Double-quote node labels containing parentheses, brackets, colons, or carets: `NODE["Label (Details)"]`.
* **State Machines**: Use `stateDiagram-v2` or `flowchart TD` for discrete state controllers, fault branches, and recovery loops.

### 4. Hardware & Peripheral Wiring
* Document hardware coupling: UART, FDCAN, SPI, I2C, ADC, Timers, DMA streams.
* Document physical constraints: CAN IDs, pinouts, baud rates, and DMA chunk sizes.

### 5. Failure Modes & Buffering Policies
* What happens when downstream consumers stall (e.g., dropped packets vs backpressure)?
* How does the module handle bus-off errors, timeouts, or sensor disconnects?
* How does the module bound data loss during unexpected power cuts?

### 6. GitHub-Flavored Alerts for Nuances
Use GitHub-style alerts instead of raw container syntax:
* `> [!NOTE]` for operational background or live file maintenance notices.
* `> [!TIP]` for architectural rationale and design choices.
* `> [!WARNING]` for active work-in-progress, disabled toggles, or known caveats.
* `> [!CAUTION]` for hardware risk, bus-off locks, or memory corruption hazards.

### 7. LaTeX Math Equations (When Applicable)
When documenting mathematical models (Kalman filters, sensor scaling, torque calculations, or filter cutoff frequencies), use LaTeX math syntax:
* **Inline Math**: Use single dollar signs: `$f_s = 1\text{ kHz}$`, `$\tau = R \cdot C$`.
* **Display Math**: Use double dollar signs for formulas:
  ```latex
  $$V_{\text{out}} = \frac{\text{ADC}_{\text{raw}} \cdot V_{\text{ref}}}{2^{12} - 1}$$
  ```
* Define physical variables and units directly below the formula. Show only the applied formula implemented in code, avoiding textbook theoretical derivations.

---

## 5. Code Anchoring & Referencing Policy

* **No Full Function Bodies**: Never paste full C functions. Permitted: key structs, atomic/seqlock primitives, or concise API tables.
* **Zero Source Code Links**: Source files (`.c`, `.h`, `.py`) are not web pages. Never hyperlink them or write `file:///` URLs. Cite them strictly in inline backticks (e.g. `can_driver.c`, `system_var.h`).
* **VitePress Route Resolution**:
  * Cross-reference `.md` pages using clean relative paths without `.md` extension (e.g., `[CAN Driver](../communication/can-driver)`).
  * Root board overview pages (e.g., `/firmware/can-gateway`) resolve relative `./modules/` as `/firmware/modules/` (404); use full routes (e.g., `/firmware/can-gateway/modules/`).
  * Never invent anchor hashes (`#some-anchor`); only link to anchors that exist as real heading IDs on the target page.

---

## 6. Pre-Submission Quality Checklist

Before finalizing any documentation page, verify:

* [ ] Text is short, concise, and stripped of narrative filler.
* [ ] GitHub-flavored alerts used (`> [!NOTE]`, `> [!TIP]`, `> [!WARNING]`, `> [!CAUTION]`).
* [ ] LaTeX math formatted with `$...$` or `$$...$$` if mathematical equations exist.
* [ ] Zero hyperlinks to source files (`.c`, `.h`); cited only as inline backticks.
* [ ] Documentation links omit `.md` extension and target real routes and existing anchors.
* [ ] Mermaid diagrams contain zero unquoted comparison operators (`<`, `>`) or unquoted special characters.
* [ ] Zero em dashes present anywhere in the document.
* [ ] Zero banned AI buzzwords ("seamlessly", "crucial", "robust").
* [ ] Zero line-by-line code walkthroughs.
* [ ] Mermaid diagram included if dataflow or states exist.
* [ ] Concurrency and execution context explicitly identified (threads, ISRs, rates).
* [ ] Concrete numbers and units provided for all buffers, rates, and timeouts.
* [ ] Team referenced with "we"/"us"/"our" rather than third-person names.
* [ ] Local `modules/index.md` updated if a new file was created.
