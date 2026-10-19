---
name: arttu-docs-writer
description: Write or revise ARTTU engineering documentation, including firmware modules, architecture, and development tooling. Explain systems in plain language for students and design judges, then guide readers into technical detail. Use for requested documentation and after firmware features or refactors. Hardware specification lookup uses arttu-docs-assistant; C review and hardware debugging use their respective skills.
---

# Engineering documentation

Write for someone interested in the car who may not know our software tools. Help them understand what happens, why we chose it, and where to look next. Technical depth belongs after the reader has enough context to use it.

## Audience and reading order

- Start with the concrete purpose in ordinary language. Explain what the system does for us and the problem it addresses. Do not open with an acronym list, component inventory, slogan, or performance claim.
- Guide the reader through one real example before cataloguing implementation details. For CI, follow a proposed software change; for firmware, follow a measurement, command, or fault.
- Introduce a technical term when it becomes useful and explain it at first use. For example: "A pull request is a proposed change that another team member can review." Avoid explaining a tool using several more unexplained tools.
- Arrange the page in layers: purpose and small overview, guided walkthrough, design choices and limitations, then reference detail. Each section should build on the one before it.
- Keep the opening useful to a student or design judge. Put implementation contracts and full input tables on deeper pages within a collapsed VitePress sidebar group. "Dropdown" means sidebar navigation, not in-page `<details>` blocks. Keep the overview readable as a normal document, and preserve existing public routes when arranging the child pages. Do not remove necessary detail to meet an arbitrary reading-time target.
- Use connected paragraphs for explanations. Use lists for real sequences and tables for comparisons or lookup. Do not turn every sentence into a bullet, bold label, heading, or question-and-answer fragment.

## Plain language is required

Use concrete subjects and active verbs: "The build produces a firmware file" rather than "The pipeline facilitates artifact generation." Use "we" when describing a verified team decision; do not invent intent, history, or benefits.

Remove stock AI phrasing, sales language, and ornamental transitions. Prohibited examples include "delve", "deep dive", "leverage", "foster", "seamlessly", "robust", "comprehensive", "pivotal", "crucial", "a testament to", "unlock", "empower", "at its core", "in today's", "it is worth noting", and "importantly". A banned-word scan is a final check, not a substitute for editing the argument.

Also remove these patterns even when no banned word appears:

- slogans such as "From code to confidence" or "Turning changes into evidence";
- vague labels such as "software assurance ecosystem" when "software checks" says what we mean;
- repeated claims about reliability, quality, efficiency, or safety without a specific mechanism and evidence;
- empty contrasts such as "This isn't just X; it's Y";
- sentences announcing that a section is important or that the reader can explore it;
- repeated summaries that restate the opening without adding an implication or next action.

Prefer ordinary words where they preserve meaning: "use", "check", "shared", "copy", "failure", "result". Keep established technical names when needed, but explain them. Do not replace precision with vague simplifications.

Do not use em dashes, `&mdash;`, or `--` as prose punctuation. Use a period, comma, colon, or parentheses. Command options such as `--base` remain valid.

## Explain decisions and limits

- Support material behavior with current code/configuration and the applicable evidence workflow. Distinguish approved hardware requirements from observed implementation.
- State a design choice together with its reason or consequence: "Lint waits for the build because it needs the compiler settings."
- Say what happens when something fails, who sees it, and what happens next. Explain disabled, optional, or partially adopted behavior where it matters.
- Distinguish a configured workflow from a successful run, a passing test from complete coverage, and simulation from hardware verification. State relevant limits once beside the claim; avoid repeated defensive disclaimers.
- Never invent measurements, deployment status, branch protection, design rationale, hardware facts, or guarantees. Date adoption snapshots and identify their source revisions when those facts can change.
- Preserve useful material when restructuring. Move detailed contracts into a maintained reference. Keep explicitly requested historical content clearly dated and separated from current guidance.

## Diagrams and layout

Use a small diagram when relationships, timing, data movement, or state changes are easier to see than describe. Give it a sentence of context and explain the consequence afterward. Labels should make sense without reading the implementation first.

- Show the main path first. Separate secondary flows and detailed diagrams farther down the page. Avoid an organization-wide web of arrows in the opening.
- Use Mermaid for all diagrams. Do not use generated images, hand-authored SVG, canvas, or other diagram formats. Use diagrams throughout the explanation where they clarify different relationships, rather than relying on a single opening flowchart. Put the more detailed diagrams on the relevant sidebar child pages.
- Choose direction to fit the reading width. Use top-to-bottom on narrow pages; use parallel columns only when they improve understanding. Do not shrink dense diagrams until text becomes unreadable.
- Quote Mermaid node labels containing special characters. Avoid raw comparison operators in labels; use words or quoted text. Validate diagram syntax.
- Use Mermaid colours and subgraphs to distinguish responsibilities, successful paths, checks, and failures. Pie charts may show actual proportions when the underlying numbers are available; identify the source and date, and label historical results clearly. Never invent measurements to fill a chart.
- Use normal VitePress Markdown, headings, lists, tables, and standard callouts. Do not add custom page CSS, HTML cards, hero sections, decorative title panels, or metric counters. The existing `<div data-zoom="…">` wrappers for Mermaid zoom are the only custom layout containers to use.
- Keep warnings for a decision or failure readers need to act on. Use the repository's established GitHub alerts or VitePress containers. Avoid filling the page with badges and callouts.

## Firmware-specific detail

Explain runtime behavior rather than narrating C statements. For firmware modules, cover these where applicable after the introductory walkthrough:

- responsibility, module ownership, and interfaces to the rest of the car;
- execution context (task, ISR, DMA, callback, or main loop), triggers, rates, and priorities;
- producers, consumers, shared-state ownership, and synchronization;
- relevant hardware interfaces, approved CAN IDs/pins, physical units, and buffer sizes;
- timeouts, stalled consumers, dropped data or backpressure, faults, and recovery.

Include a flow or state diagram when handoffs or transitions matter. Use exact verified units and parameters; explain their effect rather than listing numbers without context. For implemented mathematical models, use LaTeX math and define variables and units. Avoid unrelated textbook derivations.

Do not paste complete functions or give line-by-line code walks. Small interface tables, important data structures, or a short synchronization example are appropriate only when they help the explanation. Cite source identifiers sparingly. Link to maintained source pages only where useful and valid; never use `file:///` links.

## Scope and publication

Update only pages and indexes needed by the request. Firmware module pages normally live in `docs/modules/<category>/<module>.md`; shared tooling documentation lives in the owning repository's `docs/`. Honour an explicitly requested location.

Add new pages to the relevant index/navigation. For VitePress, verify the public rewrite, actual heading anchors, and relative links after rendering. Preserve existing public routes during a move. Keep deployment instructions in the repository that owns deployment.

## Final editing and verification pass

1. Read the opening as someone who does not know the tools. Can they explain the purpose and follow the example? Rewrite sentences that depend on unstated background.
2. Read each paragraph aloud in ordinary conversation. Remove stiff phrasing, slogans, repetition, unexplained abbreviations, and unnecessary nouns made from verbs.
3. Check that technical detail remains available and that every material claim matches its source. Make uncertainty and incomplete adoption explicit where relevant.
4. Scan for prohibited phrases and em dashes in newly written prose. Preserve explicitly requested historical quotations unchanged and mark them historical.
5. Build/render the changed pages, check diagrams and links, and inspect the layout at desktop and narrow widths when presentation changes. Verify that sidebar groups expand to the correct deeper pages, Mermaid diagrams and pie charts render, and the pages contain no custom CSS, decorative cards, or in-page dropdowns. Report blocked checks accurately.
6. For firmware pages, check the applicable ownership, execution, hardware, and failure details. Update the local index when adding a page.
