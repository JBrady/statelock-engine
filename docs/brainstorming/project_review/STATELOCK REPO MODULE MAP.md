# STATELOCK REPO MODULE MAP  
  
Purpose  
Map the conceptual architecture of StateLock to concrete repo modules so that:  
- documentation aligns with implementation  
- naming stays consistent  
- architectural drift becomes visible  
- future work has a canonical target structure  
  
  
TOP-LEVEL REPO SHAPE  
  
statelock-engine/  
├─ apps/  
│  ├─ web/  
│  └─ api/                        (optional if backend is split as app)  
├─ core/  
│  ├─ artifacts/  
│  ├─ observation/  
│  ├─ memory/  
│  ├─ retrieval/  
│  ├─ context/  
│  ├─ prompts/  
│  ├─ models/  
│  └─ orchestration/  
├─ services/  
│  ├─ embeddings/  
│  ├─ vectorstore/  
│  ├─ storage/  
│  ├─ telemetry/  
│  └─ ingestion/  
├─ schemas/  
├─ tests/  
├─ docs/  
├─ scripts/  
└─ data/                         (local/dev only if needed)  
  
  
CANONICAL CONCEPT → REPO MODULE MAP  
  
  
1. Artifact  
Concept:  
A structured memory record stored by StateLock.  
  
Canonical repo module:  
core/artifacts/  
  
Suggested contents:  
- models.py or artifact.py  
- artifact_types.py  
- validators.py  
- provenance.py  
  
Responsibilities:  
- artifact schema definition  
- artifact typing  
- provenance fields  
- validation rules  
- artifact lifecycle helpers  
  
Notes:  
This should be the single source of truth for what an artifact is.  
  
  
2. Memory Archive  
Concept:  
Persistent long-term storage for artifacts.  
  
Canonical repo module:  
core/memory/  
services/storage/  
services/vectorstore/  
  
Suggested split:  
- core/memory/archive.py  
- core/memory/repository.py  
- services/storage/sqlite_store.py or json_store.py  
- services/vectorstore/chroma_store.py  
  
Responsibilities:  
- artifact persistence  
- artifact lookup  
- reinforcement history persistence  
- provenance persistence  
- archive queries  
- vector indexing  
  
Notes:  
“Memory Archive” is the concept.  
Implementation may span both structured storage and vector storage.  
  
  
3. Observation Layer  
Concept:  
Processes conversations and extracts memory candidates.  
  
Canonical repo module:  
core/observation/  
  
Suggested contents:  
- observer.py  
- candidate_extractor.py  
- signal_detection.py  
- contradiction_detection.py  
- event_parser.py  
  
Responsibilities:  
- parse user/assistant turns  
- detect memory-worthy statements  
- detect reinforcement signals  
- detect corrections and contradictions  
- emit candidate artifacts  
  
Notes:  
This layer should NOT directly own persistence.  
It should produce candidates/events for the Memory Engine.  
  
  
4. Memory Engine  
Concept:  
Creates, updates, reinforces, and reconciles artifacts.  
  
Canonical repo module:  
core/memory/  
  
Suggested contents:  
- memory_engine.py  
- reinforcement.py  
- confidence.py  
- conflict_resolution.py  
- artifact_merge.py  
  
Responsibilities:  
- create artifacts from candidates  
- reinforce existing artifacts  
- compute/update confidence  
- merge similar artifacts  
- flag contradictions  
- manage artifact state transitions  
  
Notes:  
Observation detects.  
Memory Engine decides.  
  
  
5. Provenance  
Concept:  
Evidence trail showing where an artifact came from.  
  
Canonical repo module:  
core/artifacts/provenance.py  
or  
core/memory/provenance.py  
  
Responsibilities:  
- provenance schema  
- source conversation references  
- source span references  
- reinforcement event references  
- evidence formatting for inspection UI  
  
Notes:  
Provenance is important enough that it should not be an afterthought buried in misc utils.  
  
  
6. Retrieval Engine  
Concept:  
Selects relevant artifacts for the current conversation.  
  
Canonical repo module:  
core/retrieval/  
  
Suggested contents:  
- retrieval_engine.py  
- semantic_search.py  
- filters.py  
- ranking.py  
- candidate_pipeline.py  
  
Responsibilities:  
- semantic search over archive  
- candidate filtering  
- ranking  
- retrieval orchestration  
- handoff to context assembly  
  
Notes:  
This is one of the core differentiators of StateLock.  
It should stay clearly separated from raw storage.  
  
  
7. Activation  
Concept:  
Dynamic weighting of artifacts relative to the current conversation.  
  
Canonical repo module:  
core/retrieval/activation.py  
or  
core/retrieval/scoring.py  
  
Responsibilities:  
- activation score calculation  
- recency weighting  
- confidence weighting  
- reinforcement weighting  
- pinned/locked weighting  
- type weighting  
  
Notes:  
Activation is a subcomponent of retrieval, not a separate top-level system.  
  
  
8. Active Context  
Concept:  
Temporary working memory selected for the current conversation.  
  
Canonical repo module:  
core/context/  
  
Suggested contents:  
- active_context.py  
- context_builder.py  
- context_budget.py  
- context_selection.py  
  
Responsibilities:  
- assemble selected artifacts into working set  
- enforce token budget  
- maintain current turn context state  
- expose context for prompt building  
  
Notes:  
This is the bridge between retrieval and prompting.  
It should be treated as a first-class component.  
  
  
9. Memory Packet  
Concept:  
Structured prompt-ready representation of Active Context.  
  
Canonical repo module:  
core/prompts/  
or  
core/context/packet.py  
  
Suggested contents:  
- memory_packet.py  
- packet_formatter.py  
- prompt_sections.py  
  
Responsibilities:  
- convert active context into prompt-safe structure  
- organize artifacts by category  
- format concise memory summaries  
- prepare insertion blocks for model prompts  
  
Notes:  
“Active Context” is the internal working set.  
“Memory Packet” is the prompt-facing formatted version.  
  
  
10. Conversation Interface  
Concept:  
User-facing conversation flow and message capture.  
  
Canonical repo module:  
apps/web/  
and/or  
apps/api/routes/chat.py  
  
Suggested contents:  
- chat UI  
- conversation session state  
- chat endpoints  
- message event bridge  
  
Responsibilities:  
- receive user messages  
- display model responses  
- maintain immediate turn buffer  
- forward conversation events to StateLock pipeline  
  
Notes:  
This is the app surface, not the memory logic.  
  
  
11. Language Model Interface  
Concept:  
Connection layer to external or local models.  
  
Canonical repo module:  
core/models/  
  
Suggested contents:  
- model_adapter.py  
- openai_adapter.py  
- anthropic_adapter.py  
- gemini_adapter.py  
- ollama_adapter.py  
- deepseek_adapter.py  
- registry.py  
  
Responsibilities:  
- unify model invocation  
- abstract provider-specific differences  
- support model switching  
- return normalized response objects  
  
Notes:  
This is where model independence becomes real.  
  
  
12. Cognitive Layer  
Concept:  
The combined runtime formed by Observation Layer + Memory Engine + Archive + Retrieval.  
  
Canonical repo module:  
core/orchestration/  
or  
core/engine/  
  
Suggested contents:  
- statelock_engine.py  
- pipeline.py  
- runtime.py  
- session_manager.py  
  
Responsibilities:  
- orchestrate the full cognitive pipeline  
- coordinate observation → memory → retrieval → context assembly  
- maintain conversation continuity loop  
- expose high-level engine interface to apps/api  
  
Notes:  
This should be the practical implementation of:  
“StateLock Engine Core”  
  
  
13. Telemetry / Observability  
Concept:  
Inspection surfaces for how memory and retrieval behave.  
  
Canonical repo module:  
services/telemetry/  
and UI in apps/web/  
  
Suggested contents:  
- run_logger.py  
- trace_store.py  
- metrics.py  
- event_log.py  
  
Responsibilities:  
- log observation events  
- log memory mutations  
- log retrieval stages  
- log activation scores  
- support UI inspection/debugging  
  
Notes:  
This is not the core product idea, but it is essential for trust and debugging.  
  
  
14. Embeddings Service  
Concept:  
Generates semantic representations for retrieval.  
  
Canonical repo module:  
services/embeddings/  
  
Suggested contents:  
- embedder.py  
- sentence_transformer_embedder.py  
- cache.py  
  
Responsibilities:  
- generate embeddings for artifacts  
- generate embeddings for queries/conversation state  
- cache embedding results  
  
Notes:  
This should be implementation-specific, not mixed into retrieval logic.  
  
  
15. Vector Store  
Concept:  
Similarity index for semantic retrieval.  
  
Canonical repo module:  
services/vectorstore/  
  
Suggested contents:  
- chroma_store.py  
- vector_index.py  
- query_api.py  
  
Responsibilities:  
- upsert artifact embeddings  
- nearest-neighbor search  
- archive similarity lookup  
  
Notes:  
Keep vector infra separate from artifact semantics.  
  
  
16. Schemas  
Concept:  
Shared data contracts across engine, API, and UI.  
  
Canonical repo module:  
schemas/  
  
Suggested contents:  
- artifact.py  
- conversation.py  
- retrieval.py  
- context.py  
- model_io.py  
- telemetry.py  
  
Responsibilities:  
- common typed models  
- serialization contracts  
- API payload definitions  
  
Notes:  
This becomes very useful once the UI and backend evolve in parallel.  
  
  
RECOMMENDED CANONICAL RUNTIME FLOW  
  
apps/web or chat endpoint  
→ core/orchestration/statelock_engine.py  
→ core/observation/  
→ core/memory/  
→ services/storage + services/vectorstore/  
→ core/retrieval/  
→ core/context/  
→ core/prompts/  
→ core/models/  
→ response  
→ telemetry + observation feedback loop  
  
  
MINIMUM CANONICAL MODULES STATELOCK MUST HAVE  
  
If the repo is messy, these are the minimum modules that should clearly exist in some form:  
  
- artifacts  
- observation  
- memory  
- retrieval  
- context  
- prompts  
- models  
- orchestration  
- telemetry  
  
If any of these are missing entirely, that is a likely architecture/documentation drift point.  
  
  
COMMON DRIFT SIGNALS TO WATCH FOR  
  
1. Observation logic mixed directly into API routes  
Bad smell:  
chat endpoint does extraction, reinforcement, retrieval, and prompting itself  
  
Desired:  
routes are thin  
core modules do the real work  
  
  
2. Retrieval and vector store treated as the same thing  
Bad smell:  
“retrieval” means only Chroma query code  
  
Desired:  
vector search is one retrieval stage, not the whole retrieval engine  
  
  
3. Artifact schema scattered across multiple folders  
Bad smell:  
artifact shape defined in API payloads, DB models, and UI independently  
  
Desired:  
single canonical artifact schema  
  
  
4. Prompt building mixed into model adapters  
Bad smell:  
provider adapters decide memory formatting  
  
Desired:  
memory packet is built before model adapter layer  
  
  
5. Memory Engine and Archive collapsed into one blob  
Bad smell:  
storage logic and memory decision logic tightly coupled  
  
Desired:  
archive stores  
engine decides  
  
  
6. Active Context not represented explicitly  
Bad smell:  
retrieval outputs go straight into prompt string generation  
  
Desired:  
retrieval → active context → memory packet → prompt  
  
  
REPO ALIGNMENT QUESTIONS  
  
When comparing this map to the actual repo, ask:  
  
- Where is the canonical artifact schema?  
- Where does candidate extraction happen?  
- Where does confidence scoring live?  
- Where does contradiction detection live?  
- Where is activation scoring implemented?  
- Is Active Context a real object/module or just implied?  
- Where is the memory packet formatted?  
- Are model adapters separate from prompt assembly?  
- What module acts as the StateLock Engine Core?  
- Where are telemetry events stored?  
  
  
BOTTOM-LINE CANONICAL STRUCTURE  
  
If StateLock had to be summarized as concrete repo modules, the cleanest version is:  
  
apps/web                  → user-facing UI  
apps/api                  → endpoints  
core/artifacts            → artifact definitions  
core/observation          → candidate extraction  
core/memory               → memory evolution logic  
core/retrieval            → search/filter/rank  
core/context              → active context assembly  
core/prompts              → memory packet formatting  
core/models               → model adapters  
core/orchestration        → StateLock Engine Core  
services/embeddings       → embedding provider  
services/vectorstore      → semantic index  
services/storage          → persistent store  
services/telemetry        → observability/tracing  
schemas                   → shared contracts  
docs                      → design docs  
