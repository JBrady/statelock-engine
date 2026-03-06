# StateLock Memory Graph Architecture

## 1. Executive Summary

The **Memory Graph** concept is both **sound** and **useful**, as long as it is framed correctly:

- it should **not** replace Core memory blocks,
- it should **not** replace vector retrieval,
- and it should live **primarily in Observability**, not in Core.

Repo-aligned interpretation:

- **Core** remains the stable memory sidecar runtime for durable semantic memory blocks stored and queried through the existing Chroma-backed APIs.
- **Observability** is the natural home for richer graph structures because it already owns conversations, turns, spans, working context, provenance, contradictions, telemetry, governance, distillation, and promotion records.
- The first useful graph should be treated as a **relationship/provenance structure** backing continuity and promotion, not as a “full knowledge graph platform”.

Evidence:

- [`README.md`](../README.md#L3) defines StateLock as a memory sidecar and says it does not route model calls.
- [`docs/architecture-tracks.md`](./architecture-tracks.md#L14) assigns Core to memory block storage/retrieval and Observability to traceability/governance.
- [`app/models/schemas.py`](../app/models/schemas.py#L8) and [`app/services/memory_service.py`](../app/services/memory_service.py#L98) show Core’s memory contract is intentionally simple and not graph-oriented.
- [`experimental/observability/app/db/models.py`](../experimental/observability/app/db/models.py#L46) already contains graph-like link fields on spans (`semantic_neighbors_json`, `provenance_json`, `contradictions_json`).

## 2. Why a Memory Graph Is Worth Considering

Vector memory and graph structure solve different problems.

Vector memory is good for:

- fuzzy recall
- semantic similarity
- approximate retrieval across wording variation

Graph structure is good for:

- provenance neighborhoods
- contradiction neighborhoods
- relationship-aware expansion
- episodic linkage
- promotion lineage
- structured continuity around entities, projects, decisions, and runs

The repo already hints at this split:

- Core hybrid query is still fundamentally a similarity/recency recall system ([`app/services/memory_service.py`](../app/services/memory_service.py#L167))
- Observability already expands selected context via provenance links, which is graph-like behavior ([`experimental/observability/app/context_builder/builder.py`](../experimental/observability/app/context_builder/builder.py#L67))

That makes the strongest architecture:

- **vector memory = recall engine**
- **graph memory = structure engine**

## 3. Current Repo Reality and Existing Relevant Structures

### Core today

Core stores independent memory blocks with a narrow schema:

- `content`
- `name`
- `session_id`
- `tags`
- timestamps
- deterministic IDs via `external_id`

Evidence:

- [`app/models/schemas.py`](../app/models/schemas.py#L8)
- [`app/services/memory_service.py`](../app/services/memory_service.py#L103)

Important implication:

Core does **not** currently model:

- entities
- relationships
- provenance edges
- contradiction graphs
- decision lineage

### Observability today

Observability already has several graph-like structures, even though they are not formalized as a graph subsystem:

- conversations link turns
- turns link to spans via `source_turn_ids_json`
- spans link to other spans via:
  - `semantic_neighbors_json`
  - `provenance_json`
  - `contradictions_json`
- working contexts select span sets
- telemetry snapshots link runs to turns and selected spans
- memory entries link back to source turns and spans

Evidence:

- [`experimental/observability/app/db/models.py`](../experimental/observability/app/db/models.py#L31)
- [`experimental/observability/app/db/models.py`](../experimental/observability/app/db/models.py#L46)
- [`experimental/observability/app/db/models.py`](../experimental/observability/app/db/models.py#L81)
- [`experimental/observability/app/db/models.py`](../experimental/observability/app/db/models.py#L95)
- [`experimental/observability/app/db/models.py`](../experimental/observability/app/db/models.py#L112)

The context builder already uses these links operationally:

- it selects procedural memory
- scores spans
- expands the selected set through provenance links

Evidence:

- [`experimental/observability/app/context_builder/builder.py`](../experimental/observability/app/context_builder/builder.py#L40)
- [`experimental/observability/app/context_builder/builder.py`](../experimental/observability/app/context_builder/builder.py#L67)
- [`experimental/observability/app/context_builder/builder.py`](../experimental/observability/app/context_builder/builder.py#L198)

Additional evidence:

- serializers already expose span links as a `links` object with `semantic_neighbors`, `provenance`, and `contradictions` in [`experimental/observability/app/services/serializers.py`](../experimental/observability/app/services/serializers.py#L119)
- the Observability repo guide already describes spans as having trust/provenance/thread assignment and the context builder as expanding via provenance links in [`experimental/observability/docs/REPO_GUIDE.md`](../experimental/observability/docs/REPO_GUIDE.md#L53) and [`experimental/observability/docs/REPO_GUIDE.md`](../experimental/observability/docs/REPO_GUIDE.md#L72)

### Repo-aligned conclusion

Implemented now:

- **partial graph-like structures in Observability**

Missing now:

- explicit graph schema
- explicit node/edge types
- promotion/projection lineage graph

## 4. Why Graphs Are Different from Memory Blocks

Core memory blocks answer:

- “What durable fact-like content should be stored and retrieved?”

Graphs answer:

- “How do artifacts relate?”
- “What was derived from what?”
- “Which items contradict or reinforce each other?”
- “Which episode produced this memory?”
- “Which project, tool, user, or decision neighborhood does this belong to?”

That difference matters because the current architecture already assumes:

- Core should stay narrow and boring
- Observability should carry richer continuity structure

A graph is therefore best understood as:

- a **relationship layer** above raw artifacts and memory entries,
- not a replacement for durable memory blocks.

## 5. Hybrid Model: Vector Recall + Graph Structure

Recommended hybrid model:

1. **Vector recall**
   - find semantically relevant blocks or entries
2. **Graph expansion**
   - follow important links such as provenance, contradiction, episode, applies-to, or supersession
3. **Selection/promotion logic**
   - decide what enters working context, what is reinforced, and what should project into Core

Repo grounding:

- Core already covers vector-like retrieval through Chroma and hybrid query ([`app/services/memory_service.py`](../app/services/memory_service.py#L167))
- Observability already covers relationship-aware context expansion through provenance links ([`experimental/observability/app/context_builder/builder.py`](../experimental/observability/app/context_builder/builder.py#L67))

Therefore:

- **do not replace Core retrieval with a graph**
- **do not force Core to become graph-native**
- **use graph structure mainly inside Observability**

## 6. Candidate Graph Node Types

Recommended early node types:

### Graph-native now or soon

- `conversation`
- `turn`
- `span`
- `thread`
- `working_context`
- `telemetry_snapshot`
- `memory_entry`
- `promotion_artifact` (future schema layer)
- `promotion_decision` (future schema layer)
- `projection_record` (future schema layer)

These are repo-aligned because close equivalents already exist in Observability.

Evidence:

- [`experimental/observability/app/db/models.py`](../experimental/observability/app/db/models.py#L16)
- [`docs/architecture-promotion-schemas.md`](./architecture-promotion-schemas.md#L131)

### Useful conceptual node types after the first phase

- `entity` (user, agent, team, system, tool)
- `project`
- `episode`
- `document`
- `decision`
- `constraint`

These are useful, but most are **conceptual/future** because the repo does not yet have first-class models for them.

### Core-specific note

Core memory blocks can appear as **referenced nodes** through `ProjectionRecord`, but Core itself should not become the owner of a graph subsystem in the first phase.

## 7. Candidate Relationship Types

The most useful early relationship types are the ones already implied by current data or immediately required by promotion/provenance.

### High-value early relationships

- `derived_from`
- `produced_by`
- `belongs_to`
- `applies_to`
- `contradicts`
- `reinforces`
- `supersedes`
- `used_in_context`
- `selected_for`
- `projected_to_core`

### Why these matter

- `derived_from` captures provenance and distillation lineage
- `contradicts` captures conflict neighborhoods
- `supersedes` captures retirement/deprecation chains
- `projected_to_core` makes the Observability → Core boundary explicit

### Repo evidence

Existing nearby structures:

- `provenance_json` on spans maps naturally to `derived_from`
- `contradictions_json` maps naturally to `contradicts`
- `source_turn_ids_json` / `source_span_ids_json` on memory entries map naturally to `derived_from`
- `selected_span_ids_json` on working contexts maps naturally to `selected_for` / `used_in_context`

Evidence:

- [`experimental/observability/app/db/models.py`](../experimental/observability/app/db/models.py#L62)
- [`experimental/observability/app/db/models.py`](../experimental/observability/app/db/models.py#L88)
- [`experimental/observability/app/db/models.py`](../experimental/observability/app/db/models.py#L125)
- [`experimental/observability/app/services/serializers.py`](../experimental/observability/app/services/serializers.py#L119)

## 8. Provenance on Nodes and Edges

Provenance should attach to both nodes and edges.

### Node-level provenance

Useful for:

- who/what created the node
- source conversation/run/session
- summary trust and timestamps

### Edge-level provenance

Useful for:

- why the relationship exists
- what evidence supports it
- whether it came from heuristic logic, distillation, telemetry, or human review
- whether the link is disputed, superseded, or high-confidence

Repo-aligned recommendation:

- keep provenance rich on the Observability side
- keep Core-side provenance minimal and indirect via `ProjectionRecord`

Why:

- Core has no rich provenance schema slots today
- Observability already has the richer structures and is the right owner

## 9. How Graphs Fit the Stratified Memory Model

Not every memory layer benefits equally from graph structure.

### Layer 0: Raw Archive

Graph usefulness: **high**

Why:

- conversations, turns, spans, logs, and tool traces form natural linked neighborhoods

Repo status:

- partially represented in Observability now

### Layer 1: Working Memory

Graph usefulness: **medium to high**

Why:

- working context benefits from neighborhood expansion and structured selection

Repo status:

- already partly graph-like via provenance expansion

### Layer 2: Durable Semantic Memory

Graph usefulness: **low to medium inside Core**

Why:

- Core’s main job is durable recall, not relationship traversal
- some relationship awareness may be helpful, but should stay outside Core initially

Repo status:

- Core currently stores flat blocks only

### Layer 3: Episodic Memory

Graph usefulness: **high**

Why:

- episodes are inherently linked to people, projects, incidents, and derived lessons

Repo status:

- only partially represented today

### Layer 4: Procedural / Experience Memory

Graph usefulness: **high**

Why:

- strategies often apply to entities, tools, projects, and prior outcomes

Repo status:

- partially represented through procedural memory entries plus telemetry/governance counters

### Layer 5: Policy / Constraints Layer

Graph usefulness: **medium**

Why:

- constraints often apply to projects, agents, routes, or workflows

Repo recommendation:

- keep this mainly in docs/config/policy registries; do not treat it as ordinary Core memory

## 10. How Graphs Fit the Promotion Engine and Projection Boundary

The Memory Graph should support the Promotion Engine, not replace it.

Recommended role:

- graph neighborhoods provide context for promotion evidence
- promotion decisions can create or update graph edges
- `ProjectionRecord` becomes the explicit edge from Observability-owned promoted knowledge to a Core memory block

Examples:

- `promotion_artifact --derived_from--> span`
- `promotion_artifact --derived_from--> telemetry_snapshot`
- `promotion_decision --supported_by--> promotion_evidence`
- `projection_record --projected_to_core--> core_memory_block`
- `memory_entry --contradicts--> memory_entry`

Repo-aligned conclusion:

- graph structure belongs mostly in **Observability**
- the Core boundary remains the reduced semantic projection described in [`docs/architecture-promotion-schemas.md`](./architecture-promotion-schemas.md#L412)

## 11. What Should Stay Out of Core

Core should not become the owner of:

- graph traversal logic
- provenance graphs
- contradiction graphs
- run/session trace graphs
- promotion evidence graphs
- episodic or procedural/experience relationship neighborhoods

Why:

- this would violate the existing Core vs Observability split
- it would widen the Core runtime far beyond its current stable contract

Evidence:

- Core responsibilities in [`docs/architecture-tracks.md`](./architecture-tracks.md#L14)
- Core memory schema in [`app/models/schemas.py`](../app/models/schemas.py#L8)

The only justified Core role is:

- continuing to store durable semantic blocks,
- optionally referenced by graph edges on the Observability side.

## 12. Minimal Viable Graph Schema

A minimal useful graph schema should stay small.

Recommended early shape:

```yaml
GraphNode:
  node_id: string
  node_type: string
  owner_track: enum[core, observability]
  ref_id: string
  title: string | null
  summary: string | null
  status: string | null
  created_at: datetime
  updated_at: datetime | null
  metadata: object

GraphEdge:
  edge_id: string
  edge_type: string
  src_node_id: string
  dst_node_id: string
  weight: float | null
  confidence: float | null
  status: string | null
  provenance_refs: object
  created_at: datetime
  updated_at: datetime | null
```

### Why this is enough

It supports:

- relationship neighborhoods
- provenance-aware traversal
- contradiction/supersession chains
- projection edges into Core

without introducing a dedicated graph database or a bloated ontology.

### Important constraint

The earliest graph should be **Observability-owned**, with `owner_track = core` used only for referenced Core memory blocks or projections.

## 13. Recommended Storage Strategy for Early Versions

Early versions should use:

- **SQLite node/edge tables or adjacency tables inside Observability**

Not:

- a dedicated graph backend
- graph-native Core persistence

Why:

- Observability already uses SQLite-backed structured models
- the graph can start as a small relationship layer adjacent to existing rows
- this is lower-risk than introducing a new infrastructure dependency

Repo evidence:

- Observability models are already SQLAlchemy/SQLite-backed in [`experimental/observability/app/db/models.py`](../experimental/observability/app/db/models.py#L16)
- no graph backend or graph service exists in the repo today

Practical interpretation:

- first phase: graph-ish adjacency tables in Observability
- later phase: only consider a dedicated graph backend if real traversal/query needs justify it

## 14. Recommended Implementation Sequence

1. **Document the graph role**
   - this document
2. **Keep graph ownership in Observability**
   - do not widen Core
3. **Normalize existing implicit links**
   - provenance, contradictions, semantic neighbors, source refs
4. **Add minimal node/edge schema**
   - enough for provenance and relationship neighborhoods
5. **Connect graph edges to PromotionArtifact / PromotionDecision / ProjectionRecord**
   - only after promotion schemas stabilize
6. **Use graph for better context expansion and promotion analysis**
   - before considering any graph-native runtime features
7. **Evaluate whether Core needs any selective read-through later**
   - default answer should remain “probably not”

## 15. Open Questions

1. Should the first graph schema model only Observability-native nodes, with Core blocks represented only through `ProjectionRecord`, or should Core blocks become direct node refs from the start?
2. Should graph edges be explicit first-class rows, or should the first version normalize only the existing span/memory link fields into a common read model?
3. Which entity nodes are worth first-class promotion earliest: user, agent, project, tool, or decision?
4. Should episodic clusters be explicit graph nodes, or remain inferred from conversation/thread neighborhoods at first?
5. When contradiction exists between semantic/procedural memories, should the graph store both the contradiction edge and the supersession edge, or only one plus status?

## Cross-Reference

- Stratified memory model: [`docs/architecture-memory-stratification.md`](./architecture-memory-stratification.md)
- Promotion engine: [`docs/architecture-promotion-engine.md`](./architecture-promotion-engine.md)
- Promotion boundary schemas: [`docs/architecture-promotion-schemas.md`](./architecture-promotion-schemas.md)
- Track ownership and continuity framing: [`docs/architecture-continuity-layer.md`](./architecture-continuity-layer.md)
