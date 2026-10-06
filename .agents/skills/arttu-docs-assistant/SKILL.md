---
name: arttu-docs-assistant
description: Locate and check vehicle specifications before changing CAN IDs, pinouts, sensors, ADC/DMA mappings, or board interfaces; resolve disagreements with implementation.
compatibility: Uses markdown-docs-mcp when available; scoped Markdown search is the fallback.
---

# Vehicle specification lookup

Use this workflow when a task depends on vehicle/hardware requirements. Do not require a vehicle-documentation checkout for unrelated tooling or prose.

## Locate the authoritative documents

Resolve `DOC_ROOT` from `ARTTU_DOCS_DIR`, `./documentation`, `../documentation`, then `~/.arttu/documentation`. The technical documentation repository is `https://github.com/ARTTU-Software/documentation.git`. Also inspect relevant board-local `docs/modules/` and the shared DBC location when the task needs them.

If the necessary documentation is absent, ask for its location or authorization to fetch it; continue unrelated work. Do not guess CAN IDs, timing budgets, pin mappings or DMA ordering. Fetch updates when a recent specification change matters, then record the document commit/version used.

## Query the actual server

The configured `markdown-docs-mcp` exposes `view_toc`, `search`, `read_section`, and `analyze_document`. It operates on individual files; it does not expose directory-wide `search_docs`, `get_section`, `list_headings`, or `find_code_blocks`.

1. Find candidate files with scoped `rg --files` or `rg -l --glob '*.md' '<technical identifier>' <DOC_ROOT>`. Start with board/subsystem paths and return filenames only.
2. For a known identifier, call `search(file_path=<absolute file>, query=<identifier>, max_results=10)`. This is literal/regex search, not semantic search. Choose the returned section id.
3. When the heading is unknown, use `view_toc(file_path=<absolute file>, depth=2)`, then expand only the required subtree using a returned `start_id`.
4. Fetch `read_section(file_path=<absolute file>, section_id=<returned id>)`. IDs are opaque; never fabricate them from heading text. Use returned continuation/from_line when a section is capped. Inspect anomalies with `analyze_document` only when the TOC reports them.
5. Extract the requirement, units, source anchor and version. Stop once the contract needed for the edit is clear.

The shared MCP configurations cap TOC/section output at 8 KiB. Avoid loading whole datasheets or every matching section. If MCP is unavailable, use scoped `rg -n` and the bounded read helper; disclose the fallback.

## Resolve discrepancies

Distinguish intended requirements (approved specifications, hardware schematics and agreed DBC definitions) from observed implementation (headers, register configuration and code). Cite both sides when they disagree. Do not automatically make current code authoritative: it may contain the defect being investigated. Resolve interface ambiguity with the developer before changing behavior.

Record the applicable CAN/pin/timing contract in the task's compact evidence card with its document/configuration source files. Invalidate cached facts when those sources change. Preserve unresolved discrepancies as unknowns, not assumptions.
