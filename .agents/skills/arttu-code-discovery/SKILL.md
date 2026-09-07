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

---

## 3. Prescriptive Discovery Protocol

Follow this exact 3-step sequence before modifying any existing firmware module:

1. Step 1 (Specs): Query markdown-docs:search_docs for module architectural notes and Mermaid dataflow diagrams.
2. Step 2 (Impact): Query codebase-memory-mcp:trace_path (inbound) on the symbol to map every caller across tasks, ISRs, and FSM states.
3. Step 3 (Snippet): ALWAYS call get_code_snippet to inspect the exact function implementation and obtain line bounds. If codebase MCP reading is exhausted or the symbol is unindexed, fall back to windowed view_file(StartLine, EndLine) (≤50 lines). NEVER read whole source files (>100 lines) unwindowed.

---

## 4. When to Fall Back to ripgrep (grep_search)

Fall back to grep_search or find_by_name ONLY for:
- Exact string literals, #define macro values, or error strings.
- Non-C configuration files (project.yml, CMakeLists.txt, *.json).
- When codebase-memory-mcp returns 0 results for a local symbol.
