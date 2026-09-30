---
name: arttu-code-discovery
description: Explore codebase architecture, trace function callers and callees, map dataflow, and extract symbol implementations using the codebase-memory-mcp knowledge graph. Use when investigating unfamiliar code, checking downstream consumers of shared buffers or driver functions, locating symbol definitions, or performing impact analysis before editing. Do NOT use for writing or modifying C code (use arttu-cstyle), querying vehicle documentation or CAN specs (use arttu-docs-assistant), hardware debugging (use arttu-stm32-debugging), or authoring module documentation (use arttu-docs-writer).
compatibility: Requires an active codebase-memory-mcp server instance.
---

# ARTTU Code Discovery & Knowledge Graph Guide

Guides the agent in performing token-efficient architecture exploration, dependency tracing, and symbol inspection via codebase-memory-mcp.

---

## 1. Project Resolution & Auto-Indexing

Before running queries, resolve the target project name:

1. Call list_projects to check indexed repositories.
2. Match the current repository root directory to a project entry (e.g., C-embeddedDev-Formula_Student-CANGateway-with-harness).
3. If the project is missing or returns 'Project not found', trigger auto-indexing immediately:
   call_mcp_tool(ServerName='codebase-memory-mcp', ToolName='index_repository', Arguments={'repo_path': '.', 'mode': 'full'})
   Note: Indexing completes in 10-15 seconds and persists for the session.

---

## 2. Standard MCP Call Recipes (Priority Order)

Always use these exact parameter patterns when calling call_mcp_tool:

### Recipe A: Direct Function Extraction (get_code_snippet) — Priority 1
Read the exact function body, line bounds, and docstrings without reading whole files or guessing offsets:
call_mcp_tool(ServerName='codebase-memory-mcp', ToolName='get_code_snippet', Arguments={
  'project': '<PROJECT_NAME>',
  'qualified_name': '<PROJECT_NAME>.Core.Src.App.DataProcessing.data_processing.apply_kalman_to_sensor'
})

### Recipe B: Shared Buffer & Hardware Variable Tracing — Priority 2
Map all writers (producers) and readers (consumers) of any volatile flag, DMA array, or global variable:
1. Locate references and line bounds via `search_code(pattern='<var_name>', mode='compact')`.
2. Trace the controlling ISR or processing function callers using `trace_path`:
call_mcp_tool(ServerName='codebase-memory-mcp', ToolName='trace_path', Arguments={
  'project': '<PROJECT_NAME>',
  'function_name': 'HAL_ADC_ConvCpltCallback',
  'direction': 'inbound',
  'edge_types': ['CALLS', 'WRITES', 'USAGE']
})
*Note: `trace_path` argument is strictly `function_name`. Do NOT pass raw variable names directly to `trace_path`.*

### Recipe C: Trace Inbound Callers (trace_path) — Priority 3
Find every function, ISR, or task that calls a target function:
call_mcp_tool(ServerName='codebase-memory-mcp', ToolName='trace_path', Arguments={
  'project': '<PROJECT_NAME>',
  'function_name': 'apply_kalman_to_sensor',
  'direction': 'inbound',
  'depth': 3
})

### Recipe D: Signal Dataflow & Parameter Propagation (trace_path with mode='data_flow') — Priority 4
Inspect variable, pointer, and buffer argument expressions across hops (e.g. tracking &sensor pointers):
call_mcp_tool(ServerName='codebase-memory-mcp', ToolName='trace_path', Arguments={
  'project': '<PROJECT_NAME>',
  'function_name': 'apply_kalman_to_sensor',
  'mode': 'data_flow'
})

### Recipe E: Graph-Augmented Search (search_code in Compact Mode) — Priority 5
Search text patterns with graph deduplication into containing functions, signatures, and line bounds:
call_mcp_tool(ServerName='codebase-memory-mcp', ToolName='search_code', Arguments={
  'project': '<PROJECT_NAME>',
  'pattern': 'kalman_takasu',
  'mode': 'compact'
})
*Search Query Discipline: Search exact C identifiers or tokens only (`adc1_buffer`, `apply_kalman`). NEVER search for filenames (`*.h`, `*.c` — use file search tools), and NEVER search natural language sentences (e.g. `"high frequency"`).*

### Recipe F: Scoped Symbol & Structure Discovery (search_graph with Labels) — Priority 6
Search by label (`Variable`, `Field`, `Function`, `Macro`, `Class`) while scoping to application directories:
call_mcp_tool(ServerName='codebase-memory-mcp', ToolName='search_graph', Arguments={
  'project': '<PROJECT_NAME>',
  'label': 'Variable',
  'name_pattern': '.*adc.*buffer.*',
  'file_pattern': 'Core/**'
})

### Recipe G: Subsystem Degree-Ranked Skeleton Map (query_graph) — Priority 7
Generate an automated, token-compact repo map of an entire module or folder ranked by fan-in (~200 tokens):
call_mcp_tool(ServerName='codebase-memory-mcp', ToolName='query_graph', Arguments={
  'project': '<PROJECT_NAME>',
  'query': "MATCH (f:Function) WHERE f.file_path STARTS WITH 'Core/Src/App/DataProcessing' OPTIONAL MATCH (caller)-[:CALLS]->(f) RETURN f.return_type, f.name, f.signature, count(caller) AS callers ORDER BY callers DESC"
})

### Recipe H: Pre-Commit Impact Analysis (detect_changes) — Priority 8
Calculate transitive blast radius and list all impacted symbols before committing or creating a PR:
call_mcp_tool(ServerName='codebase-memory-mcp', ToolName='detect_changes', Arguments={
  'project': '<PROJECT_NAME>',
  'base_branch': 'dev',
  'depth': 2
})

### Recipe I: Architectural Cluster & Hotspot Map (get_architecture) — Priority 9
Discover de-facto module clusters via Leiden community detection and high fan-in communication hubs:
call_mcp_tool(ServerName='codebase-memory-mcp', ToolName='get_architecture', Arguments={
  'project': '<PROJECT_NAME>',
  'path': 'Core/Src/App',
  'aspects': ['clusters', 'hotspots']
})

### Recipe J: Targeted Section Extraction from Docs (get_section) — Priority 10
When reading architecture or pinout documents, extract only the target section instead of viewing entire markdown files:
call_mcp_tool(ServerName='markdown-docs', ToolName='get_section', Arguments={
  'file': '<REPO_PATH>/docs/modules/data-processing/adc-buffer.md',
  'heading': 'Architecture'
})

---

## 3. Prescriptive Discovery Protocol (Hybrid Strategy)

Follow this prescriptive 4-step sequence before modifying or designing any firmware module:

1. Step 1: Specification & Architecture Check (markdown-docs + get_architecture)
   - Query `markdown-docs:search_docs` with `directory="<REPO_PATH>/docs"` (absolute path) for module specs, CAN frame layouts, and pinouts.
   - Use `markdown-docs:get_section(file="<doc>", heading="<heading>")` to read the exact heading needed (~100 tokens).
   - Run Recipe I (`get_architecture` with `aspects=['clusters', 'hotspots']`) to view de-facto architectural seams and communication hubs without file scanning.
2. Step 2: Subsystem Mapping & Hybrid Search (query_graph or search_code)
   - For unfamiliar folders, run Recipe G (`query_graph`) to extract the entire subsystem's degree-ranked function signatures in one call (~200 tokens).
   - For specific identifiers, variables, or types, run Recipe E (`search_code` in `mode="compact"`).
3. Step 3: Call-Graph, Variable & Dataflow Impact (trace_path)
   - For shared arrays or DMA buffers, use Recipe B (`search_code` to locate references, then `trace_path` on the ISR/accessor function).
   - Run Recipe C (`trace_path` inbound) on functions to map callers across tasks, ISRs, and FSM states.
   - For sensor, ADC, or CAN signal flow, run Recipe D (`trace_path` with `mode="data_flow"`) to trace argument expressions across hops.
4. Step 4: Targeted Symbol Snippet Extraction (get_code_snippet)
   - ALWAYS call `get_code_snippet` to inspect the exact function implementation and line bounds (~150-300 tokens).
   - Never dump or crawl large files. Small cohesive files (≤200 lines, e.g. headers, test files, configs) may be viewed in a single call.

---

## 4. Critical Anti-Patterns (Zero-Tolerance)

1. **NO Sequential Windowed Reads (The Paging Loophole)**: NEVER read through a large source file in sequential slices (`1-100`, `101-200`, `201-300`). This floods context history and triggers quadratic token billing. Always extract the target function with `get_code_snippet`.
2. **NO Delegating Reads to Research Subagents**: Do NOT spawn subagents just to read files. It adds 30+ seconds of coordination latency, duplicates context tokens, and loses precision. Use `get_code_snippet` directly in ~150 tokens.
3. **NO Non-Symbol Searches in `search_code`**: Never search for filenames (`*.h`, `*.c`) or natural language prose (`"high frequency"`) via `search_code`. Use file listing for paths, and C identifiers for code search.

---

## 5. When to Use Targeted Direct Grep (grep_search)

Use grep_search with a scoped SearchPath specifically for:
- Macro definitions (#define) and register bitmasks (e.g. ADC_CR2_ADON).
- Direct peripheral register manipulation (e.g. ADC1->CR).
- Exact error messages, log strings, or CAN DBC frame names.
- Non-C configuration files (project.yml, CMakeLists.txt, *.json).
Do NOT use grep_search blindly across the entire repo for C functions, structs, or variables—use search_code or search_graph instead.
