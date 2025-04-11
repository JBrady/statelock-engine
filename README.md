# StateLock Engine

StateLock Engine is a lightweight middleware toolkit designed to enhance memory management, context hygiene, and workflow stability for LLM and agentic applications (e.g., using frameworks like CrewAI, LangChain). It provides tools to audit, manage, and snapshot the state of memory blocks used by AI systems.

In essence, StateLock Engine acts as the structured, persistent, and managed "working memory" layer that sophisticated, long-running AI applications need but which standard LLM context windows and basic databases don't provide effectively.

## Core Problem Addressed

Long-running LLM workflows often suffer from issues like:
*   Context window limitations and "cognitive decay".
*   Context contamination leading to inaccurate responses or loops.
*   Difficulty in managing and pruning relevant information (RAG saturation).
*   Lack of easy mechanisms for session recovery.

StateLock Engine aims to provide building blocks to mitigate these problems through structured memory management.

## Features (Current - Memory Block Assistant API & UI)

This implementation provides a core API and a simple web UI for managing semantic memory blocks:

*   **FastAPI Backend:** Provides a web API (`main.py`) for interacting with memory blocks.
*   **Streamlit Frontend:** Provides a user-friendly web interface (`ui.py`) for managing and querying blocks.
*   **Memory Block Storage (`POST /memory_blocks/`):** Allows storing text content, optionally with a name. Generates a semantic embedding using Sentence Transformers (`all-MiniLM-L6-v2` by default) and stores the embedding, name, and original content in a local ChromaDB vector database.
*   **Semantic Query (`GET /memory_blocks/query`):** Accepts query parameters `query_text` (string) and optional `n_results` (int, default 5). Returns the most semantically similar memory blocks based on vector distance.
*   **List Blocks (`GET /memory_blocks/`):** Retrieves a list of all stored memory blocks (including ID, name, and content).
*   **Delete Block (`DELETE /memory_blocks/{block_id}`):** Removes a specific memory block by its unique ID.
*   **Bulk Delete Blocks (`POST /memory_blocks/delete_bulk`):** Removes multiple specified memory blocks by their IDs.
*   **Vector Database:** Uses ChromaDB for persistent local storage of embeddings and metadata (`./chroma_db` directory).
*   **Configuration:** Uses a `.env` file for basic configuration (database path, embedding model).

## Installation & Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/JBrady/statelock-engine.git
    cd statelock-engine
    ```
2.  **Create and activate a virtual environment (Python 3.11 Recommended):**
    ```bash
    # Ensure you have Python 3.11 available
    python3.11 -m venv .venv 
    # On Windows
    .venv\Scripts\activate
    # On macOS/Linux
    source .venv/bin/activate
    ```
3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Configure Environment:**
    Create a `.env` file in the project root with the following content (adjust if needed):
    ```dotenv
    CHROMA_DB_PATH="./chroma_db"
    EMBEDDING_MODEL_NAME="all-MiniLM-L6-v2"
    # OPENAI_API_KEY=your_key_here # If using OpenAI embeddings in the future
    ```
5.  **Run the API Server (Required for UI):**
    Open a terminal and run:
    ```bash
    uvicorn main:app --reload
    ```
    The API will be available at `http://127.0.0.1:8000`.

6.  **Run the Streamlit UI (Optional, Recommended):**
    Open a *second* terminal (while the API server is running) and run:
    ```bash
    streamlit run ui.py
    ```
    The UI will typically open automatically in your browser at `http://localhost:8501`.

## Usage

There are two main ways to interact with the Memory Block Assistant:

**1. Streamlit UI (Recommended)**

*   Ensure the API server (`uvicorn main:app --reload`) is running in one terminal.
*   Run the Streamlit app (`streamlit run ui.py`) in a second terminal.
*   Open the Streamlit URL (usually `http://localhost:8501`) in your browser.
*   The UI provides options to:
    *   View existing memory blocks.
    *   Add new blocks.
    *   Query blocks using semantic search.
    *   Select and delete blocks individually or in bulk.

**2. Direct API Interaction (e.g., using `curl`)**

You can also interact with the API endpoints directly. The FastAPI interactive documentation is a great way to explore this:

*   **Interactive Docs:** With the API server running, navigate to `http://127.0.0.1:8000/docs`. This UI allows you to test all endpoints directly.

*   **Example using `curl`:**

    *   **Add a memory block:**
        ```bash
        curl -X 'POST' \
          'http://127.0.0.1:8000/memory_blocks/' \
          -H 'accept: application/json' \
          -H 'Content-Type: application/json' \
          -d '{
            "content": "The user prefers concise answers.",
            "name": "User Preference - Brevity"
          }'
        ```

    *   **Query for similar blocks:**
        ```bash
        # Note: Use GET and URL encoding for query parameters
        curl -X 'GET' \
          'http://127.0.0.1:8000/memory_blocks/query?query_text=How%20should%20I%20respond%20to%20the%20user%3F&n_results=2' \
          -H 'accept: application/json'
        ```

    *   **List all blocks:**
        ```bash
        curl -X 'GET' 'http://127.0.0.1:8000/memory_blocks/' -H 'accept: application/json'
        ```

    *   **Delete a block (replace `{block_id}` with an actual ID):**
        ```bash
        curl -X 'DELETE' 'http://127.0.0.1:8000/memory_blocks/{block_id}' -H 'accept: application/json'
        ```

    *   **Delete multiple blocks (replace IDs):**
        ```bash
        curl -X 'POST' \
          'http://127.0.0.1:8000/memory_blocks/delete_bulk' \
          -H 'accept: application/json' \
          -H 'Content-Type: application/json' \
          -d '{
            "block_ids": ["some-uuid-1", "another-uuid-2"]
          }'
        ```

## Future Development

This API serves as the foundation for the Memory Block Manager component of the StateLock Engine. Future work may include:

*   Integration into agentic workflows (e.g., LangChain, CrewAI).
*   Development of other StateLock components (Prompt Injector, RAG Triage, Session Snapshot).
*   More sophisticated block management features (tagging, automatic pruning).
*   Support for different embedding models and vector databases.
*   Potential GUI or more advanced CLI clients.

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## License

(Specify License - e.g., MIT License)
