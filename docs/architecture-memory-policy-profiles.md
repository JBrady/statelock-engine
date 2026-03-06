# StateLock Memory Policy Profiles and Resource Budgets

## 1. Executive Summary

The **Memory Policy Profiles** concept is **sound and useful** for StateLock.

The repo already has enough architectural separation to support this idea cleanly:

- **Core** remains the stable memory sidecar runtime.
- **Observability** remains the owner of richer continuity logic: context construction, telemetry, governance, distillation, promotion, provenance, and graph structure.
- Policy profiles should therefore act mainly as **configuration and decision policy** over Observability behavior, with only narrow downstream effects on what eventually projects into Core.

Repo-aligned interpretation:

- profiles should shape **what is promoted, retained, summarized, expanded, reviewed, and retired**
- profiles should **not** turn Core into a tunable continuity engine
- profiles should be expressed as **small, understandable budget presets**, not a giant pile of hidden heuristics

Evidence:

- [`README.md`](../README.md#L3) defines StateLock as a memory sidecar and says it does not route model calls.
- [`docs/architecture-tracks.md`](./architecture-tracks.md#L14) assigns Core to stable memory block operations and Observability to traceability/governance.
- [`experimental/observability/app/db/models.py`](../experimental/observability/app/db/models.py#L25) already carries continuity-related knobs such as `max_context_tokens`, `telemetry_mode`, `target_thread_mode`, and `pinned_thread_id`.
- [`app/services/automation_policy.py`](../app/services/automation_policy.py#L31) already shows the repo is comfortable with explicit deterministic save policy logic rather than opaque automation.

## 2. Why Memory Policy Profiles Matter

StateLock should not have one fixed memory appetite.

Different use cases want meaningfully different behavior:

- a privacy-sensitive setup may want narrow retention and stricter review
- a project-heavy workflow may want deeper continuity and more aggressive distillation
- a low-resource laptop may want smaller recall and telemetry budgets
- a long-running agent workflow may want heavier reinforcement and cleanup passes

The important product framing is:

- this is **not** just “how much memory file size is allowed”
- this is a **policy and budget model** for continuity behavior

That matches the repo better than a storage-only framing because many of the important knobs already sit above storage:

- working-context size (`max_context_tokens`)
- telemetry mode
- trust and quarantine signals
- distillation and procedural memory
- reinforcement/deprecation counters

Evidence:

- [`experimental/observability/app/db/models.py`](../experimental/observability/app/db/models.py#L25)
- [`experimental/observability/app/db/models.py`](../experimental/observability/app/db/models.py#L57)
- [`experimental/observability/app/db/models.py`](../experimental/observability/app/db/models.py#L123)

## 3. Current Repo Reality and Why This Is Mostly Future-Looking

This design is mostly **future-looking**, but it is not disconnected from the repo.

### Already implemented or partially represented

- Core memory save/query/upsert and snapshot/restore
- deterministic save triggers in `automation_policy`
- Observability working-context token budget
- telemetry mode and target-thread mode
- procedural memory selection
- reinforcement/deprecation-like signals via success/failure counters and statuses
- graph-like provenance and contradiction links

Evidence:

- [`app/services/memory_service.py`](../app/services/memory_service.py#L98)
- [`app/services/automation_policy.py`](../app/services/automation_policy.py#L9)
- [`experimental/observability/app/db/models.py`](../experimental/observability/app/db/models.py#L25)
- [`experimental/observability/app/db/models.py`](../experimental/observability/app/db/models.py#L123)
- [`experimental/observability/app/context_builder/builder.py`](../experimental/observability/app/context_builder/builder.py#L40)

### Not implemented yet

- named policy profiles
- a unified budget model
- explicit retention/decay policies
- background introspection/cleanup scheduling
- graph-expansion profiles
- profile-scoped promotion thresholds

So the correct framing is:

- **conceptually sound**
- **repo-aligned**
- **mostly future**

## 4. Policy Profiles vs Ordinary User Preferences

These should not be treated as the same thing.

### Ordinary user preferences

Examples:

- tone preferences
- stylistic instructions
- domain preferences
- durable personal/project facts

Those are memory-like content and may eventually project into Core as durable semantic memory.

### Policy profiles

Examples:

- how aggressively to promote memory
- how much context to retrieve
- how deep graph expansion should go
- how much telemetry to retain
- when review is required
- how frequently cleanup or consolidation runs

These are **system behavior controls**, not ordinary memory content.

Recommended owner:

- docs/config/runtime policy first
- Observability decision logic second
- Core only indirectly affected via fewer or more selective semantic projections

## 5. Core Design Dimensions

### 5.1 Storage budget

Useful dimensions:

- archive size / archive retention
- durable memory count
- graph node/edge volume
- telemetry retention
- export bundle size

Repo alignment:

- mostly future
- should live mainly in Observability and export tooling

Why:

- Core today does not expose storage quotas or graph limits
- Observability already owns most large structured artifacts

### 5.2 Cognitive budget

Useful dimensions:

- distillation frequency
- promotion aggressiveness
- experience aggregation effort
- contradiction resolution passes
- introspection/cleanup frequency
- summarization/consolidation frequency
- graph extraction/expansion effort

Repo alignment:

- this is the most important conceptual budget family

Why:

- it directly affects continuity quality without requiring Core changes
- it maps to Observability’s real responsibilities: distillation, promotion, telemetry, governance, and graph structure

### 5.3 Recall budget

Useful dimensions:

- max retrieved memories
- token budget for injected context
- episodic expansion depth
- graph traversal depth
- provenance expansion limits

Repo alignment:

- partly represented already

Evidence:

- Core query top-k exists in [`app/models/schemas.py`](../app/models/schemas.py#L69)
- Observability already stores `max_context_tokens` and uses bounded context assembly in [`experimental/observability/app/db/models.py`](../experimental/observability/app/db/models.py#L25) and [`experimental/observability/app/context_builder/builder.py`](../experimental/observability/app/context_builder/builder.py#L178)

### 5.4 Retention / decay policy

Useful dimensions:

- confidence decay
- archive TTL
- episodic retention windows
- procedural/experience reinforcement thresholds
- auto-retirement / eviction rules

Repo alignment:

- partially represented

Evidence:

- `success_count`, `failure_count`, `last_applied_at`, and `status` on `MemoryEntry` already imply reinforcement/deprecation signals in [`experimental/observability/app/db/models.py`](../experimental/observability/app/db/models.py#L123)

### 5.5 Review / safety policy

Useful dimensions:

- when human review is required
- when policy/constraints candidates require confirmation
- stricter promotion thresholds for privacy-focused profiles
- stronger quarantine/deprecation thresholds under higher-risk profiles

Repo alignment:

- strongly aligned with existing governance/quarantine concepts

Evidence:

- span quarantine support in [`experimental/observability/app/db/models.py`](../experimental/observability/app/db/models.py#L64)
- governance events in [`experimental/observability/app/db/models.py`](../experimental/observability/app/db/models.py#L132)
- deterministic policy/save triggers in [`app/services/automation_policy.py`](../app/services/automation_policy.py#L9)

## 6. Candidate Profiles

Keep the profile set small and understandable.

### Minimal

Best for:

- low-resource setups
- shallow continuity
- short-lived sessions

Expected behavior:

- narrow promotion
- short recall/context budget
- minimal graph expansion
- low telemetry retention
- minimal background cleanup work

### Balanced

Best for:

- default developer/operator use

Expected behavior:

- moderate promotion thresholds
- moderate recall/context budget
- provenance-aware expansion, but shallow
- moderate telemetry retention
- periodic cleanup/consolidation

Recommendation:

- this should be the likely default profile if profiles are added later

### Deep Continuity

Best for:

- long-running assistants
- research copilots
- continuity-heavy personal systems

Expected behavior:

- deeper graph/provenance expansion
- more aggressive distillation and reinforcement
- larger recall and context budgets
- more retained telemetry and episodic structures
- more periodic introspection and consolidation

### Project-Focused

Best for:

- repo/project continuity
- task and architecture memory

Expected behavior:

- favor project facts, decisions, and workflow procedures
- promote project-specific semantic and procedural memory more readily
- constrain recall toward project/session scope
- de-emphasize broad personal/ambient memory

### Privacy-Hardline

Best for:

- sensitive work
- conservative retention

Expected behavior:

- stricter promotion thresholds
- narrower retention windows
- more human-gated promotion for policy/high-impact memories
- weaker background aggregation
- tighter archive and telemetry retention

### Optional note on “Jarvis mode”

“Jarvis mode” is worth documenting only as an **informal nickname** for a high-resource, high-continuity profile.

It should **not** be the formal profile name.

Why:

- it sounds magical and ambiguous
- it obscures the actual budget knobs that matter
- “Deep Continuity” is clearer as an architecture/product term

Recommended treatment:

- formal profile name: `Deep Continuity`
- optional informal description: “Jarvis-like behavior”

## 7. Which Existing/Production Memory Ideas Are Worth Adopting

Worth adopting because they align with transparency, provenance, and the current repo shape:

- **confidence decay**
  - useful for lowering stale or weakly reinforced memories over time
- **contradiction tracking**
  - already strongly foreshadowed by Observability span contradiction links
- **importance / strength weighting**
  - already partly present as `strength` on `MemoryEntry`
- **summarization / consolidation**
  - useful when done visibly and traceably
- **scope-aware memory**
  - highly compatible with session/conversation/project scoping
- **reinforcement through repeated outcomes**
  - already hinted by success/failure counters
- **introspection / cleanup**
  - useful if explicit, logged, and reviewable

Evidence:

- [`experimental/observability/app/db/models.py`](../experimental/observability/app/db/models.py#L61)
- [`experimental/observability/app/db/models.py`](../experimental/observability/app/db/models.py#L123)
- [`experimental/observability/app/context_builder/builder.py`](../experimental/observability/app/context_builder/builder.py#L67)
- [`app/services/automation_policy.py`](../app/services/automation_policy.py#L31)

## 8. Which Ideas Should Be Avoided

These would make StateLock worse:

- opaque black-box ranking with no inspectable reason path
- silent mutation of durable memory with no provenance
- silent deletion/retirement without auditability
- unrestricted graph expansion that hides why context grew
- a huge matrix of tiny knobs instead of a few understandable profiles
- policy profiles masquerading as ordinary memory content
- profile logic inside Core beyond narrow projection-side effects

StateLock’s repo direction clearly favors:

- explicit traceability
- explicit governance
- explicit sidecar contracts

The profile system should preserve those values.

## 9. How Policy Profiles Influence

### Promotion engine

Profiles should influence:

- promotion thresholds
- delayed vs immediate promotion preference
- review requirements
- reinforcement/deprecation sensitivity

### Promotion schemas

Profiles should influence:

- decision mode defaults
- review/safety state thresholds
- projection aggressiveness

They should **not** require changing the canonical schema shapes.

### Memory stratification

Profiles should influence:

- which layers receive more or less attention
- how readily episodic/procedural observations are retained
- whether some layers are aggressively summarized or lightly retained

### Memory graph

Profiles should influence:

- graph extraction effort
- traversal depth
- provenance expansion limits
- contradiction-neighborhood exploration effort

### Observability vs Core

Profiles should mostly act on **Observability behavior**.

Core should only feel them indirectly through:

- fewer or more durable semantic projections
- potentially narrower or broader retrieval defaults if later exposed

That preserves the Core vs Observability split.

## 10. What Should Be Configurable in Early Versions

Recommended early configurable items:

1. `max_context_tokens`
2. promotion aggressiveness level
3. graph/provenance expansion depth
4. telemetry retention level
5. review strictness level
6. cleanup/consolidation cadence

Why these first:

- they map cleanly to current or adjacent repo concepts
- they are understandable
- they mostly live in Observability/configuration rather than requiring Core redesign

Avoid early overexposure of:

- dozens of per-axis weights
- user-facing decay math knobs
- low-level storage quotas

## 11. Recommended Implementation Sequence

1. **Document profile model first**
   - this document
2. **Define 3-5 named presets**
   - no giant knob matrix
3. **Attach presets to Observability continuity behavior**
   - working-context build, promotion, review, retention
4. **Add explicit logging of profile-driven decisions**
   - preserve transparency
5. **Only then add more advanced cleanup/decay logic**
   - after reinforcement/deprecation flows stabilize
6. **Keep Core changes minimal**
   - ideally none beyond eventual consumption of projected semantic outputs

## 12. Open Questions

1. Should profiles be global, per conversation, per session, or all three?
2. Which dimensions belong in the user-visible preset vs internal tuning values?
3. Should `Project-Focused` be a standalone preset or a scope overlay on top of `Balanced` / `Deep Continuity`?
4. When privacy and continuity goals conflict, should the profile enforce hard caps or only stronger review thresholds?
5. Should introspection/cleanup run opportunistically after active sessions, or on an explicit maintenance pass only?

## Cross-Reference

- Stratified memory model: [`docs/architecture-memory-stratification.md`](./architecture-memory-stratification.md)
- Promotion engine: [`docs/architecture-promotion-engine.md`](./architecture-promotion-engine.md)
- Promotion schemas: [`docs/architecture-promotion-schemas.md`](./architecture-promotion-schemas.md)
- Memory graph: [`docs/architecture-memory-graph.md`](./architecture-memory-graph.md)
- Continuity framing: [`docs/architecture-continuity-layer.md`](./architecture-continuity-layer.md)
