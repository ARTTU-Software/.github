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

## 2. Standard MCP Call Recipes

Always use these exact parameter patterns when calling call_mcp_tool:

### Recipe A: Trace Inbound Callers (trace_path)
Use to find who calls a function or who consumes a shared buffer before modifying it:
call_mcp_tool(ServerName='codebase-memory-mcp', ToolName='trace_path', Arguments={
  'project': '<PROJECT_NAME>',
  'function_name': 'apply_kalman_to_sensor',
  'direction': 'inbound',
  'depth': 3
})

### Recipe B: Trace Outbound Callees (trace_path)
Use to map all dependencies, drivers, or downstream functions invoked by an entry point:
call_mcp_tool(ServerName='codebase-memory-mcp', ToolName='trace_path', Arguments={
  'project': '<PROJECT_NAME>',
  'function_name': 'board_fsm_mode_process_sensors_action',
  'direction': 'outbound',
  'depth': 2
})

### Recipe C: Direct Function Extraction (get_code_snippet)
Read the exact implementation and docstring without guessing line offsets or reading entire files:
call_mcp_tool(ServerName='codebase-memory-mcp', ToolName='get_code_snippet', Arguments={
  'project': '<PROJECT_NAME>',
  'qualified_name': '<PROJECT_NAME>.Core.Src.App.DataProcessing.data_processing.apply_kalman_to_sensor'
})

### Recipe D: Scoped Symbol Search (search_graph)
Search for identifiers while filtering out vendor HAL/CMSIS noise:
call_mcp_tool(ServerName='codebase-memory-mcp', ToolName='search_graph', Arguments={
  'project': '<PROJECT_NAME>',
  'name_pattern': '.*adc.*buffer.*',
  'file_pattern': 'Core/**'
})

### Recipe E: Graph-Augmented Search (search_code in Compact Mode)
Search text patterns with graph deduplication into containing functions and line ranges:
call_mcp_tool(ServerName='codebase-memory-mcp', ToolName='search_code', Arguments={
  'project': '<PROJECT_NAME>',
  'pattern': 'kalman_takasu',
  'mode': 'compact'
})

### Recipe F: Subsystem Degree-Ranked Skeleton Map (query_graph)
Generate an automated, token-compact repo map of an entire module or folder ranked by fan-in:
call_mcp_tool(ServerName='codebase-memory-mcp', ToolName='query_graph', Arguments={
  'project': '<PROJECT_NAME>',
  'query': "MATCH (f:Function) WHERE f.file_path STARTS WITH 'Core/Src/App/DataProcessing' OPTIONAL MATCH (caller)-[:CALLS]->(f) RETURN f.return_type, f.name, f.signature, count(caller) AS callers ORDER BY callers DESC"
})

### Recipe G: Signal Dataflow Tracing (trace_path with mode='data_flow')
Inspect variable and pointer propagation with parameter expressions across hops (e.g. tracking &sensor pointers):
call_mcp_tool(ServerName='codebase-memory-mcp', ToolName='trace_path', Arguments={
  'project': '<PROJECT_NAME>',
  'function_name': 'apply_kalman_to_sensor',
  'mode': 'data_flow'
})

### Recipe H: Pre-Commit Impact Analysis (detect_changes)
Calculate transitive blast radius and list all impacted symbols before committing or creating a PR:
call_mcp_tool(ServerName='codebase-memory-mcp', ToolName='detect_changes', Arguments={
  'project': '<PROJECT_NAME>',
  'base_branch': 'dev',
  'depth': 2
})

### Recipe I: Architectural Cluster & Hotspot Map (get_architecture)
Discover de-facto module clusters via Leiden community detection and high fan-in communication hubs:
call_mcp_tool(ServerName='codebase-memory-mcp', ToolName='get_architecture', Arguments={
  'project': '<PROJECT_NAME>',
  'path': 'Core/Src/App',
  'aspects': ['clusters', 'hotspots']
})

---

## 3. Prescriptive Discovery Protocol (Hybrid Strategy)

Follow this prescriptive 4-step sequence before modifying or designing any firmware module:

1. Step 1: Specification & Architecture Check (markdown-docs + get_architecture)
   - Query markdown-docs:search_docs with directory="<REPO_PATH>/docs" (absolute path) for module specs, CAN frame layouts, and pinouts.
   - Run Recipe I (get_architecture with aspects=['clusters', 'hotspots']) to view de-facto architectural seams and communication hubs without file scanning.
2. Step 2: Subsystem Mapping & Hybrid Search (query_graph or search_code)
   - For unfamiliar folders, run Recipe F (query_graph) to extract the entire subsystem's degree-ranked function signatures in one call (~200 tokens).
   - For specific identifiers or types, run Recipe E (search_code in mode="compact") or Recipe D (search_graph).
3. Step 3: Call-Graph & Dataflow Impact (trace_path)
   - Run Recipe A (trace_path inbound) on the target symbol to map all callers across tasks, ISRs, and FSM states.
   - For sensor, ADC, or CAN signal flow, run Recipe G (trace_path with mode="data_flow") to trace argument expressions across hops.
4. Step 4: Targeted Symbol Snippet Extraction (get_code_snippet)
   - ALWAYS call get_code_snippet to inspect the exact function implementation and line bounds (~300 tokens).
   - If codebase MCP reading is exhausted or the symbol is unindexed, fall back to windowed view_file(StartLine, EndLine) (≤50 lines). NEVER read whole source files (>100 lines) unwindowed.

---

## 4. When to Use Targeted Direct Grep (grep_search)

Use grep_search with a scoped SearchPath specifically for:
- Macro definitions (#define) and register bitmasks (e.g. ADC_CR2_ADON).
- Direct peripheral register manipulation (e.g. ADC1->CR).
- Exact error messages, log strings, or CAN DBC frame names.
- Non-C configuration files (project.yml, CMakeLists.txt, *.json).
Do NOT use grep_search blindly across the entire repo for C functions or structs—use search_code instead.
