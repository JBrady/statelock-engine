# StateLock Memory Model  
  
**Overview**  
  
StateLock introduces a structured memory layer that sits between the user and the language model.  
  
Instead of relying solely on raw conversation history, StateLock extracts and maintains **memory artifacts** that represent important information discovered during conversations.  
  
All artifacts are stored in a long-term memory archive that persists across conversations and across AI models.  
  
These artifacts form a long-term working memory that persists across sessions and across different AI models.  
  
The purpose of the memory model is to:  
	•	prevent context rot  
	•	maintain conversational continuity  
	•	accumulate useful knowledge over time  
	•	allow users to inspect and correct memory  
  
⸻  
  
**Memory Artifact**  
  
A **memory artifact** is the fundamental unit of persistent knowledge in StateLock.  
  
A memory artifact represents a distilled piece of information that the system believes is important to remember.  
  
Examples:  
	•	“User prefers concise technical explanations.”  
	•	“User is building a project called StateLock.”  
	•	“User prefers step-by-step explanations for complex topics.”  
	•	“The user’s dog Mika has CKD.”  
  
Artifacts should represent **meaning**, not raw text.  
  
⸻  
  
**Memory Artifact Structure**  
  
Each artifact should contain structured fields.  
  
Example structure:  
  
```
artifact_id
type
content
confidence
created_at
last_reinforced_at
reinforcement_count
source_conversations
source_spans
status

```
  
Example artifact:  
  
```
artifact_id: A124
type: user_preference
content: "User prefers concise technical explanations."
confidence: 0.92
created_at: 2026-03-07
last_reinforced_at: 2026-03-09
reinforcement_count: 3
source_conversations: [conv14, conv22]
source_spans: [msg34, msg102]
status: active

```
  
**Artifact Types**  
  
Artifacts may belong to different semantic categories.  
  
Examples include:  
  
**User Preferences**  
	•	explanation style  
	•	communication preferences  
	•	formatting preferences  
  
**Projects**  
	•	active projects  
	•	ongoing goals  
	•	recurring topics  
  
**Facts**  
	•	stable factual information about the user or their work  
  
**Decisions**  
	•	choices made during a project  
	•	resolved issues  
  
**Patterns**  
	•	recurring reasoning styles  
	•	thinking patterns  
  
⸻  
  
**Memory Creation**  
  
Memory artifacts are created when the system detects signals that indicate information should persist.  
  
Signals may include:  
	•	explicit statements from the user  
	•	repeated patterns  
	•	reinforced preferences  
	•	confirmed decisions  
	•	high-importance project information  
  
Memory creation should favor **high confidence signals** to avoid noise.  
  
Example triggers:  
  
```
User: "I always prefer step-by-step explanations."
User: "For this project we are using Rust."
User: "I hate overly verbose responses."

```
  
**Confidence Score**  
  
Each artifact maintains a **confidence score** between 0 and 1.  
  
Confidence represents how certain the system is that the artifact reflects a stable truth.  
  
Confidence may increase when:  
	•	the same information appears again  
	•	the user confirms the artifact  
	•	the artifact is used successfully in future conversations  
  
Confidence may decrease when:  
	•	conflicting evidence appears  
	•	the user corrects the artifact  
  
⸻  
  
**Reinforcement**  
  
Artifacts are strengthened through **reinforcement events**.  
  
Example:  
  
Conversation 1:  
User says they prefer concise explanations.  
  
Artifact created.  
  
Conversation 5:  
User again asks for shorter answers.  
  
Artifact reinforced.  
  
```
reinforcement_count += 1
confidence += small_increment

```
  
Over time, strongly reinforced artifacts become highly reliable.  
  
  
**Contradiction Detection**  
  
StateLock must detect contradictions between artifacts.  
  
Example:  
  
Artifact A  
“User prefers concise explanations.”  
  
Artifact B  
“User prefers detailed explanations.”  
  
When conflicting evidence appears, the system should:  
	•	flag the contradiction  
	•	reduce confidence  
	•	request clarification if necessary  
  
Contradictions should be visible in the observability interface.  
  
⸻  
  
**Memory Persistence and Activation**  
  
StateLock favors **retention over deletion**.  
  
Memory artifacts should be retained indefinitely by default unless explicitly deleted by the user.  
  
However, persistence does not mean that all memories should influence the AI equally at all times.  
  
Instead, StateLock separates **memory storage** from **memory activation**.  
  
Artifacts remain stored in the long-term memory archive, but their influence on the current conversation is determined dynamically.  
  
Activation weight may depend on factors such as:  
	•	semantic relevance to the current conversation  
	•	recency of reinforcement  
	•	artifact confidence  
	•	artifact type  
	•	user-pinned importance  
	•	current conversation intent  
  
Older memories remain available in the archive but may be activated less frequently if they are no longer relevant.  
  
This approach prevents the system from forgetting important information while avoiding clutter in the active reasoning context.  
  
Users may also explicitly:  
	•	pin artifacts to keep them highly active  
	•	lock artifacts to prevent automatic changes  
	•	archive artifacts to reduce activation  
	•	delete artifacts entirely  
  
In this model, **memory is preserved broadly, but influence is selective**.  
  
⸻  
  
**User Control**  
  
Users must be able to interact with memory artifacts directly.  
  
Available actions include:  
	•	view artifact  
	•	edit artifact  
	•	delete artifact  
	•	pin artifact  
	•	lock artifact  
  
Pinned or locked artifacts should never decay automatically.  
  
⸻  
  
**Memory Retrieval**  
  
When generating a prompt for an LLM, StateLock selects relevant artifacts.  
  
Selection criteria may include:  
	•	semantic similarity to the current topic  
	•	artifact confidence  
	•	artifact type  
	•	recency of reinforcement  
  
Only a subset of artifacts should be included in the prompt to avoid context overload.  
  
⸻  
  
**Model Interaction**  
  
Language models do not modify memory directly.  
  
Instead:  
	1.	StateLock observes conversation events.  
	2.	StateLock updates artifacts.  
	3.	StateLock decides which artifacts to supply to the model.  
  
This ensures that the memory system remains **model-independent**.  
  
⸻  
  
**Long-Term Behavior**  
  
Over time, the artifact graph becomes a structured representation of:  
	•	the user’s knowledge  
	•	the user’s preferences  
	•	the user’s projects  
	•	the user’s reasoning patterns  
  
This allows the AI to maintain continuity across extremely long time horizons.  
  
⸻  
  
