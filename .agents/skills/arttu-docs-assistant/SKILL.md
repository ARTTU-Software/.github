---
name: arttu-docs-assistant
description: Locate, synchronize, and query ARTTU Formula Student vehicle documentation via the markdown-docs MCP server. Use when answering questions regarding ARTTU CAN IDs, pinouts, board specs, sensor filtering, and subsystem firmware cross-referencing. Do NOT use for generic C/C++ programming (use arttu-cstyle), hardware debugging (use arttu-stm32-debugging), or writing module docs (use arttu-docs-writer).
compatibility: Requires git CLI, network access for initial clone/pull, and an active markdown-docs MCP server instance.
---

# ARTTU Documentation Assistant

Guides the agent in locating, updating, and querying the ARTTU Formula Student documentation repository with minimal token usage.

---

## 1. Documentation Resolution & Setup

The ARTTU technical docs reside in:
`git@github.com:ARTTU-Software/documentation.git` (HTTPS: `https://github.com/ARTTU-Software/documentation.git`).

### Discovery Order
Before executing queries, resolve the local documentation path in the following sequence:
1. Environment variable `$ARTTU_DOCS_DIR` (if defined).
2. Local workspace: `./documentation` or `../documentation`.
3. Global user cache:
   - Linux/macOS: `~/.arttu/documentation`
   - Windows: `%USERPROFILE%\.arttu\documentation`

Verify the directory contains a `.git` folder or root `INDEX.md`/`README.md`. Store the resolved path as `DOC_ROOT`.

### Missing Documentation Protocol
If no directory is discovered:
1. Stop. Do not attempt exploratory filesystem searches.
2. Ask the user:
   > "The ARTTU vehicle documentation is needed to verify CAN IDs, pinouts, and hardware specs. May I clone the repository (~5 MB) to `~/.arttu/documentation` (or your preferred path)?"
3. Upon confirmation, execute non-interactively:
   ```bash
   GIT_TERMINAL_PROMPT=0 git clone git@github.com:ARTTU-Software/documentation.git "<TARGET_PATH>" || \
   GIT_TERMINAL_PROMPT=0 git clone https://github.com/ARTTU-Software/documentation.git "<TARGET_PATH>"
   ```
4. If authentication fails, inform the user to configure SSH keys or GitHub CLI auth (`gh auth login`).

### Synchronization / Freshness
When the user mentions recent CAN updates, telemetry changes, or DBC modifications:
```bash
git -C "<DOC_ROOT>" pull --ff-only
```

---

## 2. Token-Efficient MCP Query Guidelines

Strictly follow these execution patterns when interacting with the `markdown-docs` MCP tools:

```
                  ┌──────────────────────┐
                  │ Technical Identifier │
                  └──────────┬───────────┘
                             │ search_docs
                             ▼
                  ┌──────────────────────┐
                  │ 1-3 Matching Files   │
                  └──────────┬───────────┘
            ┌────────────────┴────────────────┐
     Heading Clear?                    Heading Unclear?
            │                                 │
            ▼                                 ▼
      get_section                       list_headings
                                              │
                                              ▼
                                         get_section
```

### Rule 1: Search with Exact Identifiers (`search_docs`)
- Always search using strict technical identifiers:
  - CAN IDs (e.g., `0x0A1`, `0x0E0`)
  - Function / Type names (e.g., `is_apps_valid`, `telemetry_t`, `Generic_Kalman_Settings_t`)
  - Subsystem boards (e.g., `BSPD`, `TSAL`, `AMS`, `CAN-Gateway`)
- Avoid natural language queries (e.g., "how sensor calibration works").
- **Zero Results Fallback:** If an exact identifier returns no hits, strip formatting (e.g., query `0A1` instead of `0x0A1`) or inspect the subsystem directory outline using `list_headings`.

### Rule 2: Fetch Headings, Never Entire Documents (`get_section`)
- Never ingest entire files when looking for targeted parameters.
- If the document structure is unknown, call `list_headings(file)` first, identify the relevant subsection, and call `get_section(file, heading)`.
- Use relative paths from `DOC_ROOT` if the MCP server is mounted to the documentation repository root; otherwise, use absolute paths.

### Rule 3: Extract Dense Specifications (`find_code_blocks`)
- For register configurations, pin mappings, DBC tables, or C struct layouts, call `find_code_blocks(file, language="c")`.
- Extract only code and tables, skipping narrative explanations.

---

## 3. Firmware Cross-Referencing & Discrepancy Handling

1. **Code Anchors:** When documentation references source code lines (e.g., `repos/CAN-Gateway/Core/Src/...#L42`):
   - Cite the exact repository, file path, line number, and commit/branch if documented.
   - If the corresponding firmware project is open in the active IDE workspace, resolve the path relative to the workspace root and link it.
2. **Truth Hierarchy:** When discrepancies exist between documents:
   1. **Level 1 (Highest Authority):** Firmware C header files (`.h`), register defines, and `.dbc` files.
   2. **Level 2:** Board-level module documentation (`docs/modules/...`).
   3. **Level 3 (Lowest Authority):** High-level architectural overview guides.
   *Always flag discrepancies explicitly to the user:*  
   `"Note: Architecture overview lists CAN ID as 0x0A2, but board-level header specifies 0x0A1. Using 0x0A1 per Level 1 truth hierarchy."`
