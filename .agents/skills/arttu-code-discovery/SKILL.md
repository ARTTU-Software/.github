---
name: arttu-code-discovery
description: Explore unfamiliar ARTTU code, trace callers and dataflow, and assess change impact using bounded graph evidence and source fallbacks.
compatibility: Uses codebase-memory-mcp when available; targeted source discovery remains supported without MCP.
---

# Task-directed discovery

Answer the current question with the smallest sufficient evidence. Reuse unchanged evidence; expand exploration when a missing relationship affects correctness.

1. Resolve the absolute Git root, graph project, and current generation once at task start or after compaction. Use `list_projects`/`index_status`; index only a missing project. If transport fails, record the limitation and use targeted source tools instead of retry loops.
2. Choose a scope: a named symbol, a changed file, or a subsystem. For a symbol, use bounded `search_graph` then its qualified name with `get_code_snippet`. For a subsystem, request a degree-ranked skeleton or scoped clusters first. For exact identifiers use `search_code(pattern="identifier", mode="compact")`.
3. Establish the relationships needed for the task: inbound callers for contract changes; outbound dependencies for failure/concurrency behavior; producers, consumers and ISR/accessor paths for shared data. Use data-flow mode for sensor/CAN/DMA argument propagation. Do not interpret missing edges as proof of no consumer.
4. Batch `check_index_coverage` for every evidence path and scopes relevant to negative/exhaustive claims. Read stale or missed ranges before relying on them; complete relevant pagination. Obtain exact snippets for material behavior.
5. Stop exploring when requirements, ownership, impact and the unresolved questions relevant to the edit are understood. A one-line change does not need the full architecture workflow.

Use the available tool schemas and actual server names. Do not assume `call_mcp_tool`, invented qualified names, or a fixed indexing time. Useful bounded recipes are in [references/graph-recipes.md](references/graph-recipes.md); load only the relevant recipe.

## Preserve system understanding cheaply

For investigations spanning tasks/compaction, save one short evidence card per subsystem with:

- scope and source anchors;
- ownership and execution context (task, ISR, DMA);
- producer/consumer relationships and key invariants;
- error/recovery paths and unanswered questions;
- graph generation, coverage limitations, and checks actually performed.

Use `.agents/hooks/context_cache.py save <name> --files <relative source/config paths> --generation <current-generation>` with the card JSON on stdin. Fields: `scope`, `facts`, `relationships`, `unknowns`, `checks`, `coverage`. Omit generation only for source-only evidence. Include every source/config file the facts depend on. The cache is local, ignored by Git, and capped at 8 KiB per card.

Restore with `context_cache.py show <name> --generation <current-generation>`. A changed HEAD, file hash, missing file or graph generation produces a cache miss. Do not trust an old graph card when the current generation is unknown. Revalidate safety-critical assumptions before editing; the cache saves rediscovery, not verification.

## Fallbacks and output discipline

For filenames/non-code configuration use `rg --files` or scoped `rg`. When MCP lacks coverage, locate the identifier first, then use `python .agents/hooks/read_context.py <path> --start N --end M` (at most 100 lines for large files). Read cohesive files of at most 200 lines whole. Avoid sequential paging, repeated architecture calls, and dumping entire graph result pages.

Use the documentation skill for changed hardware contracts; ordinary Python/tooling inspection does not require vehicle specifications. Pass evidence scope, generation, pagination and coverage gaps if delegation is explicitly requested; avoid delegating simple reads.
