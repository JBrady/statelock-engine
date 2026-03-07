# STATELOCK REPO DRIFT CHECKLIST  
  
STATELOCK REPO DRIFT CHECKLIST  
  
Purpose  
Use this checklist to compare the actual statelock-engine repo against the canonical StateLock architecture and identify drift, gaps, naming inconsistencies, and misplaced responsibilities.  
  
How to use  
For each section:  
- mark PASS if the repo clearly matches the intended architecture  
- mark PARTIAL if the concept exists but is scattered, implied, or mixed with other responsibilities  
- mark FAIL if it is missing or clearly misplaced  
- add notes with actual repo paths  
  
Suggested status markers:  
[PASS]  
[PARTIAL]  
[FAIL]  
  
Status marker meanings:  
PASS = clear module/ownership exists  
PARTIAL = exists but blurred or scattered  
FAIL = missing or badly misplaced  
  
1. ARTIFACT LAYER  
  
1.1 Canonical artifact schema exists  
Expected:  
A clear, canonical definition of what an artifact is.  
  
Look for:  
- artifact model/schema/type definitions  
- artifact metadata fields  
- artifact type enum/classification  
- provenance fields  
  
Status: [ ]  
Actual repo path(s):  
Notes:  
  
1.2 Artifact schema is the single source of truth  
Expected:  
Artifact structure is not duplicated inconsistently across backend, API, and UI.  
  
Look for drift:  
- multiple conflicting artifact definitions  
- API payload shape not matching internal schema  
- UI inventing fields not present in backend  
  
Status: [ ]  
Actual repo path(s):  
Notes:  
  
1.3 Provenance is explicitly represented  
Expected:  
Artifact origin/evidence is modeled directly, not implied.  
  
Look for:  
- source conversation IDs  
- source spans/messages  
- timestamps  
- reinforcement history references  
  
Status: [ ]  
Actual repo path(s):  
Notes:  
  
  
2. OBSERVATION LAYER  
  
2.1 Observation logic exists as a distinct component  
Expected:  
Conversation/event parsing is separated from routes and UI.  
  
Look for:  
- observer  
- candidate extractor  
- event parser  
- signal detector  
  
Status: [ ]  
Actual repo path(s):  
Notes:  
  
2.2 Observation produces candidates rather than writing memory directly  
Expected:  
Observation detects signals.  
Memory Engine decides what persists.  
  
Look for drift:  
- observer directly mutating storage  
- routes directly creating artifacts  
- extraction and persistence tightly coupled  
  
Status: [ ]  
Actual repo path(s):  
Notes:  
  
2.3 Contradiction/correction detection exists  
Expected:  
There is logic for detecting when new information conflicts with existing memory.  
  
Status: [ ]  
Actual repo path(s):  
Notes:  
  
  
3. MEMORY ENGINE  
  
3.1 Memory Engine exists as a distinct decision layer  
Expected:  
A component responsible for artifact creation, reinforcement, conflict handling, and confidence updates.  
  
Look for:  
- memory_engine  
- reinforcement logic  
- confidence logic  
- artifact merge/update logic  
  
Status: [ ]  
Actual repo path(s):  
Notes:  
  
3.2 Memory Engine is distinct from storage  
Expected:  
Storage stores.  
Memory Engine decides.  
  
Look for drift:  
- one giant module doing storage + decision logic  
- archive code also handling confidence and reinforcement  
  
Status: [ ]  
Actual repo path(s):  
Notes:  
  
3.3 Confidence scoring is explicit  
Expected:  
Confidence is modeled and updated deliberately.  
  
Status: [ ]  
Actual repo path(s):  
Notes:  
  
3.4 Reinforcement is explicit  
Expected:  
Repeated confirmations/uses of an artifact are tracked.  
  
Status: [ ]  
Actual repo path(s):  
Notes:  
  
  
4. MEMORY ARCHIVE  
  
4.1 Persistent archive exists  
Expected:  
Long-term memory storage is represented explicitly.  
  
Look for:  
- archive store  
- repository  
- DB or structured local store  
- vector index companion  
  
Status: [ ]  
Actual repo path(s):  
Notes:  
  
4.2 Archive supports provenance + reinforcement persistence  
Expected:  
The archive stores not just artifact text but its metadata/history.  
  
Status: [ ]  
Actual repo path(s):  
Notes:  
  
4.3 Archive and vector store are conceptually separated  
Expected:  
Structured storage and semantic index are not treated as the same thing.  
  
Look for drift:  
- “retrieval” is just Chroma calls  
- vector store is the only memory layer  
  
Status: [ ]  
Actual repo path(s):  
Notes:  
  
  
5. RETRIEVAL ENGINE  
  
5.1 Retrieval exists as its own module  
Expected:  
A retrieval pipeline distinct from storage and prompting.  
  
Look for:  
- semantic search  
- filtering  
- ranking  
- candidate pipeline  
  
Status: [ ]  
Actual repo path(s):  
Notes:  
  
5.2 Retrieval is multi-stage  
Expected:  
There is some equivalent of:  
- semantic search  
- candidate filtering  
- activation/ranking  
- handoff to context assembly  
  
Status: [ ]  
Actual repo path(s):  
Notes:  
  
5.3 Activation scoring exists explicitly  
Expected:  
Artifact relevance is weighted dynamically.  
  
Look for:  
- scoring.py  
- activation.py  
- ranker logic  
- weighting of confidence/recency/reinforcement/pins  
  
Status: [ ]  
Actual repo path(s):  
Notes:  
  
5.4 Retrieval is not just similarity search  
Expected:  
Semantic search is only one stage, not the full retrieval story.  
  
Status: [ ]  
Actual repo path(s):  
Notes:  
  
  
6. ACTIVE CONTEXT + MEMORY PACKET  
  
6.1 Active Context exists explicitly  
Expected:  
There is a real intermediate working-memory object or module between retrieval and prompt formatting.  
  
Look for:  
- active_context  
- context builder  
- selected artifact set  
- token budget logic  
  
Status: [ ]  
Actual repo path(s):  
Notes:  
  
6.2 Token budget enforcement exists  
Expected:  
The system has some logic for limiting what enters the prompt.  
  
Status: [ ]  
Actual repo path(s):  
Notes:  
  
6.3 Memory Packet formatting is distinct from retrieval  
Expected:  
Prompt-ready memory formatting is separate from search/ranking.  
  
Look for:  
- memory packet  
- packet formatter  
- prompt sections  
- memory context builder  
  
Status: [ ]  
Actual repo path(s):  
Notes:  
  
6.4 Prompt assembly is distinct from model adapters  
Expected:  
The model adapter should not be deciding memory structure.  
  
Look for drift:  
- OpenAI/Anthropic adapter building memory summaries itself  
- retrieval output going directly into provider-specific code  
  
Status: [ ]  
Actual repo path(s):  
Notes:  
  
  
7. MODEL INTERFACE  
  
7.1 Model adapter layer exists  
Expected:  
There is a unified abstraction over multiple LLM providers.  
  
Look for:  
- adapters  
- gateway  
- registry  
- provider abstraction  
  
Status: [ ]  
Actual repo path(s):  
Notes:  
  
7.2 Model independence is reflected in code structure  
Expected:  
Memory system is not tightly bound to one provider.  
  
Look for drift:  
- retrieval assumes OpenAI-specific flow  
- memory packet structure embedded in one provider adapter  
- provider-specific artifacts or archive structures  
  
Status: [ ]  
Actual repo path(s):  
Notes:  
  
  
8. ORCHESTRATION / ENGINE CORE  
  
8.1 There is a StateLock Engine Core  
Expected:  
A top-level runtime/pipeline component orchestrates:  
observation → memory → retrieval → context → model  
  
Look for:  
- engine  
- runtime  
- pipeline  
- session manager  
  
Status: [ ]  
Actual repo path(s):  
Notes:  
  
8.2 Routes/UI are thin and delegate to the engine  
Expected:  
App surfaces call into engine/orchestration rather than implementing core logic directly.  
  
Look for drift:  
- API routes doing retrieval directly  
- UI pages calling memory mutation logic  
- orchestration spread across multiple random files  
  
Status: [ ]  
Actual repo path(s):  
Notes:  
  
  
9. TELEMETRY / OBSERVABILITY  
  
9.1 Telemetry exists as a distinct concern  
Expected:  
Observation events, memory mutations, retrieval stages, or traces are logged somewhere.  
  
Look for:  
- trace store  
- run logger  
- event log  
- metrics  
  
Status: [ ]  
Actual repo path(s):  
Notes:  
  
9.2 Telemetry is not mixed into business logic everywhere  
Expected:  
Logging/tracing helpers exist without turning every core module into spaghetti.  
  
Status: [ ]  
Actual repo path(s):  
Notes:  
  
9.3 Telemetry supports UI inspection  
Expected:  
The UI can surface runs, traces, activation info, or artifact history from structured telemetry.  
  
Status: [ ]  
Actual repo path(s):  
Notes:  
  
  
10. SHARED SCHEMAS / CONTRACTS  
  
10.1 Shared schemas exist  
Expected:  
Common typed models/contracts are defined once and reused.  
  
Look for:  
- schema package  
- typed data models  
- DTOs / shared contracts  
  
Status: [ ]  
Actual repo path(s):  
Notes:  
  
10.2 Backend and UI terminology align  
Expected:  
Docs, code, and UI use the same core vocabulary:  
artifact, archive, observation, retrieval, active context, memory packet  
  
Look for drift:  
- “memory” in docs but “fact” in code  
- “packet” in docs but “summary block” in UI  
- “archive” in docs but “store” everywhere else with no distinction  
  
Status: [ ]  
Actual repo path(s):  
Notes:  
  
  
11. DOCS ↔ REPO ALIGNMENT  
  
11.1 Manifesto aligns with implementation direction  
Expected:  
Repo still reflects the core goal:  
solve context rot and preserve long-term continuity  
  
Status: [ ]  
Notes:  
  
11.2 System Principles are reflected in implementation  
Expected:  
- user-owned memory  
- model independence  
- persistent storage  
- dynamic activation  
  
Status: [ ]  
Notes:  
  
11.3 Memory Model aligns with repo  
Expected:  
Artifacts, provenance, confidence, reinforcement, contradiction handling all have code homes.  
  
Status: [ ]  
Notes:  
  
11.4 Retrieval Engine doc aligns with repo  
Expected:  
Repo has corresponding stages/components for retrieval.  
  
Status: [ ]  
Notes:  
  
11.5 System Architecture doc aligns with repo  
Expected:  
Conceptual components map to real modules with minimal ambiguity.  
  
Status: [ ]  
Notes:  
  
  
12. DRIFT SUMMARY  
  
Missing canonical modules:  
-   
-   
-   
  
Modules that exist but are misplaced:  
-   
-   
-   
  
Concepts present in docs but not clearly present in code:  
-   
-   
-   
  
Concepts present in code but not clearly documented:  
-   
-   
-   
  
Terminology drift detected:  
-   
-   
-   
  
Highest-priority refactor targets:  
1.  
2.  
3.  
  
  
13. FINAL ASSESSMENT  
  
Overall architecture alignment:  
[HIGH]  
[MEDIUM]  
[LOW]  
  
Repo health relative to canonical StateLock architecture:  
[STRONG]  
[MIXED]  
[DRIFTING]  
  
Short conclusion:  
