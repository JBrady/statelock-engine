# StateLock Engine

StateLock Engine is a lightweight middleware toolkit designed to enhance memory management, context hygiene, and workflow stability for LLM and agentic applications (e.g., using frameworks like CrewAI, LangChain). It provides tools to audit, manage, and snapshot the state of memory blocks used by AI systems.

## Core Problem Addressed

Long-running LLM workflows often suffer from issues like:
*   Context window limitations and "cognitive decay".
*   Context contamination leading to inaccurate responses or loops.
*   Difficulty in managing and pruning relevant information (RAG saturation).
*   Lack of easy mechanisms for session recovery.

StateLock Engine aims to provide building blocks to mitigate these problems through structured memory management.

## Features (Current - MVP)

*   **CLI Interface:** Provides commands for managing the toolkit's state.
*   **Memory Block Auditing:** Checks memory blocks against configurable rules (age, required tags).
*   **Memory Block Collapse:** Archives or prunes older/less relevant memory blocks based on configurable thresholds and strategies.
*   **State Snapshots:** Creates timestamped backups of the configuration, memory ledger, and optionally other project files.
*   **Configuration:** Uses a `config.yaml` file for easy setup of rules and paths.
*   **Memory Ledger:** Tracks memory block metadata in `memory_ledger.json`.

## Installation & Setup

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd statelock-engine
    ```
2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv .venv
    # On Windows
    .venv\\Scripts\\activate
    # On macOS/Linux
    source .venv/bin/activate
    ```
3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Initialize the project:** (Creates default `config.yaml` and `memory_ledger.json` if they don't exist)
    ```bash
    python cli.py init
    ```

## Usage (CLI)

The main entry point is `cli.py`.

*   **Initialize:**
    ```bash
    python cli.py init
    ```
*   **Audit Memory:**
    ```bash
    python cli.py audit [--config path/to/config.yaml]
    ```
*   **Collapse Memory:**
    ```bash
    # See what would be done (dry run)
    python cli.py collapse --dry-run [--config path/to/config.yaml]

    # Perform the collapse operation
    python cli.py collapse [--config path/to/config.yaml]
    ```
*   **Create Snapshot:**
    ```bash
    python cli.py snapshot [-m "Optional snapshot message"] [--config path/to/config.yaml]
    ```

## Configuration (`config.yaml`)

The `config.yaml` file controls the behavior of the toolkit:

*   `project_name`: Identifier for the project.
*   `memory_ledger_path`: Path to the JSON file tracking memory blocks.
*   `audit`: Rules for the `audit` command (e.g., `max_age_days`, `max_total_blocks`).
*   `collapse`: Settings for the `collapse` command:
    *   `enabled`: Toggle the command.
    *   `strategy`: How to handle selected blocks (`archive` currently).
    *   `thresholds`: Criteria for triggering collapse (e.g., `max_age_days`, `max_total_blocks`).
    *   `selection`: How to choose blocks to collapse (`priority`, `keep_min_blocks`).
*   `memory_blocks`: Rules applying to individual blocks (e.g., `required_tags`).
*   `snapshots`: Settings for the `snapshot` command:
    *   `snapshot_directory`: Where to store snapshots.
    *   `include_patterns`: Glob patterns for files/dirs to include in snapshots.
    *   `exclude_patterns`: Glob patterns for files/dirs to exclude.

## Memory Ledger (`memory_ledger.json`)

This JSON file stores an inventory of memory blocks. Each block is an object keyed by a unique ID, containing metadata like:

*   `creation_timestamp` (ISO 8601 format)
*   `status` (`active`, `archived`, etc.)
*   `tags` (List of strings)
*   `summary` (Brief description)
*   `related_blocks` (List of IDs)
*   `archived_timestamp` (Added when collapsed via `archive` strategy)
*   *(Other custom fields)*

## Future Plans

*   Implement `prune` strategy for collapse.
*   Develop API endpoints for programmatic interaction.
*   **Prompt Injector:** Component to wrap LLM calls, automatically injecting relevant memory and context guards.
*   **RAG Triage Layer:** System to analyze, score, and manage knowledge base content used for RAG.
*   **Session Recovery:** More robust mechanisms to restore agent state from snapshots.
*   **Memory-Aware Task Runner:** Integration point for frameworks to adjust behavior based on memory state.

## Contributing

(Details TBD)
