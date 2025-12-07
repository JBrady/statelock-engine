# StateLock Engine

StateLock Engine is a lightweight middleware toolkit designed to enhance memory management, context hygiene, and workflow stability for LLM and agentic applications. It provides tools to audit, manage, and snapshot the state of memory blocks used by AI systems.

## Core Problem Addressed

Long-running LLM workflows often suffer from issues like:
*   Context window limitations.
*   Context contamination.
*   Difficulty in managing and pruning relevant information.

StateLock Engine provides structured, persistent memory for agents.

## Features

*   **Modular API:** Built with FastAPI, designed for extensibility.
*   **Session Support:** Isolate memories by `session_id` (e.g., distinct users or agent runs).
*   **Structured Metadata:** Memories support names, tags, and automatic timestamps.
*   **Vector Search:** Semantically retrieve memories using local embeddings (SentenceTransformers) and ChromaDB.

## Installation & Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/JBrady/statelock-engine.git
    cd statelock-engine
    ```
2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
3.  **Configure Environment:**
    Create a `.env` file (optional, defaults provided):
    ```dotenv
    CHROMA_DB_PATH="./chroma_db"
    EMBEDDING_MODEL_NAME="all-MiniLM-L6-v2"
    ```
4.  **Run the API Server:**
    ```bash
    uvicorn main:app --reload
    ```
    The API will be available at `http://127.0.0.1:8000`.

## Usage (API)

**Interactive Docs:** Navigate to `http://127.0.0.1:8000/docs` to see the full Swagger UI.

### Examples

*   **Add a memory block:**
    ```bash
    curl -X 'POST' 'http://127.0.0.1:8000/memories/' \
      -H 'Content-Type: application/json' \
      -d '{
        "content": "The user prefers concise answers.",
        "name": "User Preference - Brevity",
        "session_id": "user_123",
        "tags": ["preference"]
      }'
    ```

*   **Query memories:**
    ```bash
    curl -X 'POST' 'http://127.0.0.1:8000/memories/query' \
      -H 'Content-Type: application/json' \
      -d '{
        "query_text": "How should I respond?",
        "session_id": "user_123",
        "top_k": 2
      }'
    ```

*   **List memories:**
    ```bash
    curl -X 'GET' 'http://127.0.0.1:8000/memories/?session_id=user_123'
    ```

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
