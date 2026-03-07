# StateLock Glossary  
  
**Artifact**  
A memory artifact is the fundamental unit of knowledge stored by StateLock.  
  
Artifacts represent distilled information extracted from conversations rather than raw text.  
  
Examples include:  
- user preferences  
- project details  
- resolved decisions  
- recurring patterns  
- corrections  
  
Artifacts contain structured metadata such as:  
- confidence score  
- reinforcement history  
- provenance  
- artifact type  
  
Artifacts are stored in the Memory Archive.  
  
  
**Memory Archive**  
The Memory Archive is the long-term storage layer for all artifacts.  
  
It acts as the persistent autobiographical memory of the user.  
  
Key characteristics:  
- persists across sessions  
- persists across language models  
- stores structured artifact records  
- maintains provenance and reinforcement history  
  
Artifacts remain in the archive indefinitely unless removed by the user.  
  
  
**Observation Layer**  
The Observation Layer analyzes conversation events and detects potential memory signals.  
  
Responsibilities include:  
- parsing conversation messages  
- extracting candidate artifacts  
- detecting preferences or decisions  
- identifying reinforcement signals  
- detecting contradictions or corrections  
  
The Observation Layer produces memory candidates, which are evaluated by the Memory Engine.  
  
  
**Memory Engine**  
The Memory Engine governs how memory artifacts are created and evolve.  
  
Responsibilities include:  
- validating memory candidates  
- assigning artifact types  
- computing confidence scores  
- reinforcing existing artifacts  
- detecting conflicts between artifacts  
  
The Memory Engine determines when artifacts are created, updated, or flagged.  
  
  
**Provenance**  
Provenance refers to the origin of a memory artifact.  
  
It describes where the artifact came from and the evidence that produced it.  
  
Provenance may include:  
- conversation identifiers  
- message spans  
- timestamps  
- reinforcement events  
  
Provenance ensures that memory remains transparent and verifiable.  
  
  
**Retrieval Engine**  
The Retrieval Engine determines which artifacts should be activated for the current conversation.  
  
Because the memory archive may contain thousands of artifacts, the retrieval system selects only the most relevant subset.  
  
Responsibilities include:  
- semantic search  
- relevance filtering  
- activation scoring  
- ranking artifacts by relevance  
  
The Retrieval Engine produces the candidate set used to assemble the active context.  
  
  
**Activation**  
Activation refers to the dynamic weighting of memory artifacts relative to the current conversation.  
  
Artifacts remain stored indefinitely in the archive, but their influence varies depending on relevance.  
  
Activation may depend on:  
- semantic similarity  
- reinforcement history  
- artifact confidence  
- recency  
- user-pinned importance  
  
Artifacts with higher activation scores are more likely to be included in the active context.  
  
  
**Active Context**  
The Active Context is the set of artifacts currently influencing the language model.  
  
It represents the temporary working memory used during a conversation.  
  
Active Context is assembled dynamically by the Retrieval Engine and Active Context Assembly components.  
  
Because language models have token limits, only a small subset of artifacts can be active at any given time.  
  
  
**Memory Packet**  
The Memory Packet is the structured representation of the Active Context that is inserted into the model prompt.  
  
It contains summarized artifacts organized into categories such as:  
- preferences  
- project knowledge  
- relevant decisions  
- contextual reminders  
  
The Memory Packet ensures the model receives stable context without requiring full conversation history.  
  
  
**Conversation Interface**  
The Conversation Interface manages the interaction between the user and the language model.  
  
Responsibilities include:  
- capturing user messages  
- displaying model responses  
- maintaining the immediate conversation buffer  
- triggering observation events  
  
The interface itself does not manage long-term memory.  
  
  
**Language Model Interface**  
The Language Model Interface connects StateLock to external AI models.  
  
Responsibilities include:  
- constructing prompts  
- inserting memory packets  
- sending requests to models  
- receiving responses  
  
StateLock is designed to remain model-independent, allowing users to switch between models without losing memory continuity.  
  
  
**Model Independence**  
Model Independence is a core architectural principle of StateLock.  
  
Memory exists outside the language model, allowing users to switch between AI systems without losing accumulated understanding.  
  
Examples of interchangeable models include:  
- ChatGPT  
- Claude  
- Gemini  
- DeepSeek  
- MiniMax  
- local open-source models  
  
The memory layer remains constant while the intelligence engine changes.  
  
  
**Cognitive Layer**  
The Cognitive Layer refers to the combined system of:  
- Memory Archive  
- Observation Layer  
- Memory Engine  
- Retrieval Engine  
  
Together these components form the persistent memory infrastructure surrounding the language model.  
  
This layer enables StateLock to function as a continuity engine for AI conversations.  
  
  
**Purpose of this Glossary**  
This glossary defines the canonical terminology for the StateLock project.  
  
All documentation, architecture descriptions, and code modules should use these terms consistently.  
  
If terminology begins to drift across documents or implementations, this glossary acts as the reference point for correction.  
  
  
  
  
  
  
## Canonical Component Map  
  
This section maps StateLock glossary terms to their corresponding conceptual software components.    
It serves as a bridge between documentation and implementation.  
  
**Artifact**  
Represents a structured memory record stored in the system.  
  
**Conceptual module:**  
artifact model / artifact schema  
  
Typical responsibilities:  
- artifact structure definition  
- metadata fields  
- artifact validation  
  
  
**Memory Archive**  
Persistent storage for all memory artifacts.  
  
**Conceptual module:**  
memory store / archive store  
  
Typical responsibilities:  
- artifact persistence  
- indexing  
- provenance storage  
- reinforcement history storage  
  
  
**Observation Layer**  
Processes conversation events and extracts memory candidates.  
  
**Conceptual module:**  
observer / conversation observer  
  
Typical responsibilities:  
- message parsing  
- signal detection  
- candidate artifact extraction  
- contradiction signal detection  
  
  
**Memory Engine**  
Handles artifact creation, reinforcement, and evolution.  
  
**Conceptual module:**  
memory processor / artifact manager  
  
Typical responsibilities:  
- artifact creation  
- artifact updates  
- confidence scoring  
- conflict detection  
- reinforcement tracking  
  
  
**Retrieval Engine**  
Selects relevant artifacts from the archive for the current conversation.  
  
**Conceptual module:**  
retriever / activation engine  
  
Typical responsibilities:  
- semantic search  
- relevance filtering  
- activation scoring  
- artifact ranking  
  
  
**Activation**  
Dynamic weighting applied to artifacts during retrieval.  
  
**Conceptual module:**  
activation scorer  
  
Typical responsibilities:  
- scoring algorithms  
- recency weighting  
- reinforcement weighting  
- confidence weighting  
- pin/lock priority  
  
  
**Active Context**  
Temporary working memory assembled for the current conversation.  
  
**Conceptual module:**  
context builder  
  
Typical responsibilities:  
- artifact selection  
- token budget enforcement  
- context assembly  
  
  
**Memory Packet**  
Structured representation of Active Context that is inserted into the prompt.  
  
**Conceptual module:**  
prompt memory formatter  
  
Typical responsibilities:  
- artifact summarization  
- context formatting  
- prompt injection structure  
  
  
**Conversation Interface**  
Handles user interaction and message flow.  
  
**Conceptual module:**  
chat interface / conversation manager  
  
Typical responsibilities:  
- message capture  
- conversation buffering  
- event triggers for observation layer  
  
  
**Language Model Interface**  
Connects StateLock to external LLM APIs or local models.  
  
**Conceptual module:**  
model adapter / LLM gateway  
  
Typical responsibilities:  
- prompt construction  
- API communication  
- model switching  
- response handling  
  
  
**Cognitive Layer**  
The Cognitive Layer is the combined system formed by the Memory Archive, Observation Layer, Memory Engine, and Retrieval Engine.  
  
**Conceptual module:**  
StateLock Engine Core  
  
This module represents the runtime system responsible for managing the entire cognitive pipeline.  
  
Typical responsibilities:  
- orchestrating the observation pipeline  
- managing memory creation and reinforcement  
- coordinating retrieval and activation scoring  
- assembling active context  
- maintaining long-term conversational continuity  
  
  
  
  
  
  
  
  
