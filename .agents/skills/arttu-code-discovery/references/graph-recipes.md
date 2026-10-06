# Bounded graph recipes

Tool arguments below are examples, not a replacement for the connected server's schema. Use the project and qualified names returned by that server. Start at depth 1-2; request deeper hops only when they answer an unresolved question.

## Symbol and impact

`search_graph(project=P, name_pattern=".*identifier.*", file_pattern="<scope>/**", limit=20)` locates candidates. Extract a material implementation with `get_code_snippet(project=P, qualified_name=<returned-name>, include_neighbors=false)`. Check returned line bounds before expanding a very large function; inspect only task-relevant branches with source windows and record uninspected ranges instead of printing its entire body.

`trace_path(project=P, function_name=<resolved-function>, direction="inbound", depth=2, limit=20)` finds candidate callers. Use outbound direction for hardware dependencies and failure propagation. Check both directions for shared-contract changes. Enable `include_tests=true` when test consumers matter; they are excluded by default. Use `include_evidence=true` to resolve uncertain edges, rather than paying for confidence columns on every query. Inspect callback registration/function pointers in source when the graph cannot represent them.

`search_code(project=P, pattern="adc_buffer", mode="compact", limit=10, context=0, path_filter=<confirmed-scope>)` locates relevant identifiers; trace the owning ISR/accessors. Search_code has no offset: compare returned match/result totals and narrow scope when truncated. `trace_path` takes a function name, not a raw buffer name. Use `mode="data_flow"` and `parameter_name` for relevant argument expressions. Trace cursors require identical query arguments and expire after reindexing. Confirm supported edge types before requesting writer/reader relationships.

## Subsystem map

Use `get_architecture(project=P, path=<confirmed-scope>, aspects=["clusters", "hotspots"])` for unfamiliar subsystem ownership and hubs. Do not repeat it for every symbol.

For a compact skeleton, use `query_graph` with a confirmed file path prefix and supported properties:

```cypher
MATCH (f:Function) WHERE f.file_path STARTS WITH '<confirmed-prefix>'
OPTIONAL MATCH (caller)-[:CALLS]->(f)
RETURN f.qualified_name, f.name, count(caller) AS callers
ORDER BY callers DESC LIMIT 20
```

This is a ranked sample, not an exhaustive map. Follow pagination for exhaustive findings. Never infer that a function has no dynamic/ISR callers solely from zero recorded edges.

## Evidence and checkpoints

Batch `check_index_coverage(project=P, paths=[<all evidence paths>], scopes=[<relevant scopes>])`. Follow the exact connected schema, including pagination where provided. Record generation/freshness, excluded files and missed ranges; read those ranges before relying on the graph.

Before a firmware commit/PR, `detect_changes(project=P, base_branch="dev", depth=2)` helps find downstream impact. Verify the branch exists and distinguish the task's changes from preexisting work. If the graph is unavailable, use a targeted Git diff plus bounded source/caller searches and disclose that limitation.

## Evidence card example

```json
{
  "scope": "ADC processing: ISR to scheduler",
  "facts": ["Core/Src/App/adc.c:41: ISR publishes the completed buffer index"],
  "relationships": ["ISR -> buffer index -> scheduler -> filter"],
  "unknowns": ["DMA overrun recovery has not been inspected"],
  "checks": ["Inbound/outbound traces of the accessor inspected"],
  "coverage": ["Verify tier; callback registration checked in source"]
}
```

Replace every example fact with evidence from the actual task. Include producer/consumer ownership, publication ordering and failure behavior, not a list of function names alone. A card records inspected scope; it does not convert unanswered questions into facts.
