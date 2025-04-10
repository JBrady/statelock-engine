import click
import os
import json
import yaml
from datetime import datetime, timedelta, timezone
import shutil
import glob


# Default structures
DEFAULT_CONFIG = {
    "project_name": "DefaultProject",
    "memory_ledger_path": "memory_ledger.json",
    "snapshot_directory": ".statelock_snapshots/",
    "audit": {
        "max_total_blocks": 100,
        "max_block_age_days": 30,
    },
    "collapse": {
        "enabled": True,
        "strategy": "archive",
        "thresholds": {
            "max_total_blocks": 80,
            "max_age_days": 20,
        },
        "selection": {
            "priority": "oldest_creation",
            "keep_min_blocks": 10,
        },
    },
    "memory_blocks": {"required_tags": []},
    "snapshots": {
        "include_patterns": ["*.log", "agent_outputs/"],
        "exclude_patterns": [
            ".venv/",
            "__pycache__/",
            "*.pyc",
            ".git/",
            ".statelock_snapshots/",
        ],
    },
}

DEFAULT_LEDGER = {"schema_version": "1.0", "blocks": {}}


# --- Helper Functions ---


def load_config(config_path):
    """Safely load the YAML configuration file."""
    if not os.path.exists(config_path):
        click.echo(f"Error: Configuration file not found at {config_path}", err=True)
        click.echo("Please run 'statelock init' or provide the correct path.")
        return None
    try:
        with open(config_path, "r") as f:
            config_data = yaml.safe_load(f)
        if not isinstance(config_data, dict):
            click.echo(f"Error: Invalid YAML format in {config_path}", err=True)
            return None
        return config_data
    except yaml.YAMLError as e:
        click.echo(f"Error parsing configuration file {config_path}: {e}", err=True)
        return None
    except IOError as e:
        click.echo(f"Error reading configuration file {config_path}: {e}", err=True)
        return None


def load_ledger(ledger_path):
    """Safely load the JSON memory ledger file."""
    if not os.path.exists(ledger_path):
        click.echo(f"Error: Memory ledger file not found at {ledger_path}", err=True)
        click.echo("Ensure the path in config.yaml is correct or run 'statelock init'.")
        return None
    try:
        with open(ledger_path, "r") as f:
            ledger_data = json.load(f)
        if not isinstance(ledger_data, dict) or "blocks" not in ledger_data:
            click.echo(
                f"Error: Invalid JSON format or missing 'blocks' key in {ledger_path}",
                err=True,
            )
            return None
        return ledger_data
    except json.JSONDecodeError as e:
        click.echo(f"Error parsing memory ledger file {ledger_path}: {e}", err=True)
        return None
    except IOError as e:
        click.echo(f"Error reading memory ledger file {ledger_path}: {e}", err=True)
        return None


def save_ledger(ledger_path, ledger_data):
    """Safely save the JSON memory ledger file."""
    try:
        with open(ledger_path, "w") as f:
            json.dump(ledger_data, f, indent=2)
        return True
    except IOError as e:
        click.echo(f"Error writing memory ledger file {ledger_path}: {e}", err=True)
        return False
    except TypeError as e:
        click.echo(f"Error serializing ledger data to JSON: {e}", err=True)
        return False


# --- CLI Commands ---


@click.group()
def cli():
    """StateLock Engine: A middleware toolkit for managing LLM/Agent memory, context, and RAG hygiene."""
    pass


@cli.command()
def init():
    """Initialize StateLock Engine config and memory ledger in the current directory."""
    config_path = "config.yaml"
    ledger_path = DEFAULT_CONFIG.get(
        "memory_ledger_path", "memory_ledger.json"
    )  # Get path from default

    click.echo("Initializing StateLock Engine project...")

    # Create config.yaml if it doesn't exist
    if not os.path.exists(config_path):
        try:
            with open(config_path, "w") as f:
                yaml.dump(DEFAULT_CONFIG, f, default_flow_style=False, sort_keys=False)
            click.echo(f"Created default configuration file: {config_path}")
        except IOError as e:
            click.echo(f"Error creating {config_path}: {e}", err=True)
    else:
        click.echo(f"Configuration file already exists: {config_path}")

    # Create memory_ledger.json if it doesn't exist
    # Use the path defined *in the default config* in case it was customized there
    if not os.path.exists(ledger_path):
        try:
            with open(ledger_path, "w") as f:
                json.dump(DEFAULT_LEDGER, f, indent=2)
            click.echo(f"Created default memory ledger file: {ledger_path}")
        except IOError as e:
            click.echo(f"Error creating {ledger_path}: {e}", err=True)
    else:
        click.echo(f"Memory ledger file already exists: {ledger_path}")

    # Ensure snapshot directory exists (uses path from default config)
    snapshot_dir = DEFAULT_CONFIG.get("snapshot_directory", ".statelock_snapshots/")
    if not os.path.exists(snapshot_dir):
        try:
            os.makedirs(snapshot_dir)
            click.echo(f"Created snapshot directory: {snapshot_dir}")
        except OSError as e:
            click.echo(
                f"Error creating snapshot directory {snapshot_dir}: {e}", err=True
            )
    # No message if it already exists, as it's less critical than config/ledger


@cli.command()
@click.option("--config", default="config.yaml", help="Path to the configuration file.")
def audit(config):
    """Audit memory blocks based on rules in the config file."""
    config_data = load_config(config)
    if not config_data:
        return

    ledger_path = config_data.get("memory_ledger_path", "memory_ledger.json")
    ledger_data = load_ledger(ledger_path)
    if not ledger_data:
        return

    click.echo(f"Auditing memory blocks using config: {config}")
    click.echo(f"Ledger file: {ledger_path}")

    audit_rules = config_data.get("audit", {})
    block_rules = config_data.get("memory_blocks", {})
    blocks = ledger_data.get("blocks", {})

    active_blocks = {
        block_id: block_data
        for block_id, block_data in blocks.items()
        if block_data.get("status") == "active"
    }

    warnings_found = 0
    now = datetime.now(timezone.utc)  # Use timezone-aware datetime

    # 1. Check max total active blocks
    max_total_blocks_rule = audit_rules.get("max_total_blocks")
    if max_total_blocks_rule is not None:
        active_count = len(active_blocks)
        if active_count > max_total_blocks_rule:
            click.echo(
                f"  [WARN] Total active blocks ({active_count}) exceed limit ({max_total_blocks_rule})",
                err=True,
            )
            warnings_found += 1

    # 2. Check max block age
    max_block_age_days_rule = audit_rules.get("max_block_age_days")
    if max_block_age_days_rule is not None:
        age_limit = timedelta(days=max_block_age_days_rule)
        for block_id, block_data in active_blocks.items():
            created_str = block_data.get("creation_timestamp")
            if created_str:
                try:
                    # Attempt to parse ISO 8601 format, assuming UTC if no tz specified
                    created_dt = datetime.fromisoformat(
                        created_str.replace("Z", "+00:00")
                    )
                    # Make it timezone-aware (UTC) if it's naive
                    if created_dt.tzinfo is None:
                        created_dt = created_dt.replace(tzinfo=timezone.utc)

                    if now - created_dt > age_limit:
                        click.echo(
                            f"  [WARN] Block '{block_id}' is older than {max_block_age_days_rule} days (created {created_str})",
                            err=True,
                        )
                        warnings_found += 1
                except ValueError:
                    click.echo(
                        f"  [WARN] Block '{block_id}' has invalid creation_timestamp format: {created_str}",
                        err=True,
                    )
                    warnings_found += 1
            else:
                click.echo(
                    f"  [WARN] Block '{block_id}' is missing creation_timestamp for age check.",
                    err=True,
                )
                warnings_found += 1  # Count missing timestamp as a warning

    # 3. Check required tags
    required_tags_rule = block_rules.get("required_tags", [])
    if required_tags_rule:  # Only check if the list is not empty
        for block_id, block_data in active_blocks.items():
            block_tags = set(block_data.get("tags", []))
            missing_tags = [tag for tag in required_tags_rule if tag not in block_tags]
            if missing_tags:
                click.echo(
                    f"  [WARN] Block '{block_id}' is missing required tags: {', '.join(missing_tags)}",
                    err=True,
                )
                warnings_found += 1

    # --- Audit Summary ---
    if warnings_found > 0:
        click.echo(f"\nAudit complete. Found {warnings_found} warning(s).")
    else:
        click.echo("\nAudit complete. No issues found.")


@cli.command()
@click.option("--config", default="config.yaml", help="Path to the configuration file.")
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be done without making changes.",
)
def collapse(config, dry_run):
    """Collapse or prune memory blocks based on config rules."""
    config_data = load_config(config)
    if not config_data:
        return

    ledger_path = config_data.get("memory_ledger_path", "memory_ledger.json")
    ledger_data = load_ledger(ledger_path)
    if not ledger_data:
        return

    click.echo(f"Collapsing memory blocks using config: {config}")
    if dry_run:
        click.echo("**(Dry Run) No changes will be made.**")

    collapse_rules = config_data.get("collapse", {})
    if not collapse_rules.get("enabled", False):
        click.echo("Collapse feature is disabled in the configuration.")
        return

    thresholds = collapse_rules.get("thresholds", {})
    selection_rules = collapse_rules.get("selection", {})
    strategy = collapse_rules.get("strategy", "archive")  # Default to archive
    blocks = ledger_data.get("blocks", {})

    active_blocks = {
        block_id: block_data
        for block_id, block_data in blocks.items()
        if block_data.get("status") == "active"
    }

    if not active_blocks:
        click.echo("No active blocks found in the ledger.")
        return

    # --- Sort active blocks by priority (only oldest_creation for now) ---
    priority = selection_rules.get("priority", "oldest_creation")
    if priority != "oldest_creation":
        click.echo(
            f"Warning: Unsupported collapse priority '{priority}'. Using 'oldest_creation'.",
            err=True,
        )
        priority = "oldest_creation"

    def get_creation_dt(item):
        timestamp_str = item[1].get("creation_timestamp", "9999-12-31T23:59:59Z")
        try:
            dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt
        except ValueError:
            return datetime(
                9999, 12, 31, 23, 59, 59, tzinfo=timezone.utc
            )  # Put invalid dates last

    sorted_active_blocks = sorted(active_blocks.items(), key=get_creation_dt)

    # --- Check Thresholds ---
    now = datetime.now(timezone.utc)
    threshold_met = False
    blocks_over_age_limit_ids = set()
    num_active = len(sorted_active_blocks)

    # Check max age threshold
    max_age_days_threshold = thresholds.get("max_age_days")
    if max_age_days_threshold is not None:
        age_limit = timedelta(days=max_age_days_threshold)
        for block_id, block_data in sorted_active_blocks:
            created_dt = get_creation_dt((block_id, block_data))
            if now - created_dt > age_limit:
                blocks_over_age_limit_ids.add(block_id)
                threshold_met = True
        if blocks_over_age_limit_ids:
            click.echo(
                f"  - Threshold met: {len(blocks_over_age_limit_ids)} block(s) older than {max_age_days_threshold} days."
            )

    # Check max total blocks threshold
    max_total_blocks_threshold = thresholds.get("max_total_blocks")
    blocks_over_total_limit = 0
    if max_total_blocks_threshold is not None:
        blocks_over_total_limit = max(0, num_active - max_total_blocks_threshold)
        if blocks_over_total_limit > 0:
            threshold_met = True
            click.echo(
                f"  - Threshold met: Total active blocks ({num_active}) exceed limit ({max_total_blocks_threshold}) by {blocks_over_total_limit}."
            )

    if not threshold_met:
        click.echo("\nNo collapse thresholds met. No action taken.")
        return

    # --- Select Blocks for Collapse ---
    keep_min_blocks = selection_rules.get("keep_min_blocks", 0)
    ids_to_keep_min = (
        {item[0] for item in sorted_active_blocks[-keep_min_blocks:]}
        if keep_min_blocks > 0
        else set()
    )

    # Start with blocks over the age limit
    collapse_candidate_ids = blocks_over_age_limit_ids.copy()

    # Add more blocks (oldest first) if needed to meet the total block limit
    current_candidates_count = len(collapse_candidate_ids)
    target_collapse_count_for_total = (
        blocks_over_total_limit  # How many must be removed *at minimum*
    )

    blocks_considered = 0
    for block_id, _ in sorted_active_blocks:  # Iterate oldest first
        blocks_considered += 1
        # Stop considering if we only have the minimum keepers left
        if num_active - blocks_considered < keep_min_blocks:
            break

        if block_id not in collapse_candidate_ids and block_id not in ids_to_keep_min:
            # Add this block if we *still* haven't identified enough blocks
            # to meet the required reduction for the total block count limit.
            if current_candidates_count < target_collapse_count_for_total:
                collapse_candidate_ids.add(block_id)
                current_candidates_count += 1

    # Final check: Remove any that must be kept due to keep_min_blocks
    final_collapse_ids = collapse_candidate_ids - ids_to_keep_min

    if not final_collapse_ids:
        click.echo(
            "\nNo blocks eligible for collapse after applying selection rules (e.g., keep_min_blocks)."
        )
        return

    click.echo(
        f"\nSelected {len(final_collapse_ids)} block(s) for collapse based on strategy '{strategy}':"
    )
    for block_id in sorted(list(final_collapse_ids)):  # Print sorted for consistency
        click.echo(f"  - {block_id}")

    # --- Apply Collapse Strategy ---
    if not dry_run:
        blocks_changed = 0
        for block_id in final_collapse_ids:
            if block_id in ledger_data["blocks"]:
                if strategy == "archive":
                    ledger_data["blocks"][block_id]["status"] = "archived"
                    ledger_data["blocks"][block_id][
                        "archived_timestamp"
                    ] = now.isoformat()
                    blocks_changed += 1
                elif strategy == "prune":
                    del ledger_data["blocks"][block_id]
                    blocks_changed += 1
                else:
                    click.echo(
                        f"  Error: Unknown collapse strategy '{strategy}' for block {block_id}",
                        err=True,
                    )

        if blocks_changed > 0:
            if save_ledger(ledger_path, ledger_data):
                click.echo(
                    f"\nSuccessfully applied '{strategy}' strategy to {blocks_changed} block(s). Ledger updated."
                )
            else:
                click.echo(
                    "\nError saving updated ledger file. Changes may be lost.", err=True
                )
        else:
            click.echo(
                "\nNo blocks were actually modified (this might indicate an internal issue)."
            )
    else:
        click.echo("\n(Dry Run) Ledger file was not modified.")


@cli.command()
@click.option(
    "--message", "-m", default=None, help="Optional message for the snapshot."
)
@click.option("--config", default="config.yaml", help="Path to the configuration file.")
def snapshot(config, message):
    """Create a snapshot of the current state (config, ledger, specified files)."""
    config_data = load_config(config)
    if not config_data:
        return

    ledger_path = config_data.get("memory_ledger_path", "memory_ledger.json")
    snapshot_base_dir = config_data.get("snapshot_directory", ".statelock_snapshots/")
    snapshot_settings = config_data.get("snapshots", {})
    include_patterns = snapshot_settings.get("include_patterns", [])
    exclude_patterns = snapshot_settings.get("exclude_patterns", [])

    # Ensure base snapshot directory exists
    try:
        os.makedirs(snapshot_base_dir, exist_ok=True)
    except OSError as e:
        click.echo(
            f"Error: Could not create base snapshot directory {snapshot_base_dir}: {e}",
            err=True,
        )
        return

    # Create unique snapshot directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    snapshot_name = f"snapshot_{timestamp}"
    snapshot_target_dir = os.path.join(snapshot_base_dir, snapshot_name)

    try:
        os.makedirs(snapshot_target_dir)
        click.echo(f"Creating snapshot in: {snapshot_target_dir}")
    except OSError as e:
        click.echo(
            f"Error creating snapshot directory {snapshot_target_dir}: {e}", err=True
        )
        return

    files_copied_count = 0
    errors_encountered = 0

    # --- Copy Core Files ---
    # Copy config
    try:
        config_dest = os.path.join(snapshot_target_dir, os.path.basename(config))
        shutil.copy2(config, config_dest)
        files_copied_count += 1
        click.echo(f"  - Copied config: {config}")
    except Exception as e:
        click.echo(f"  Error copying config file {config}: {e}", err=True)
        errors_encountered += 1

    # Copy ledger
    if os.path.exists(ledger_path):
        try:
            ledger_dest = os.path.join(
                snapshot_target_dir, os.path.basename(ledger_path)
            )
            shutil.copy2(ledger_path, ledger_dest)
            files_copied_count += 1
            click.echo(f"  - Copied ledger: {ledger_path}")
        except Exception as e:
            click.echo(f"  Error copying ledger file {ledger_path}: {e}", err=True)
            errors_encountered += 1
    else:
        click.echo(
            f"  Warning: Ledger file not found at {ledger_path}, skipping.", err=True
        )

    # --- Write Snapshot Info ---
    if message:
        info_path = os.path.join(snapshot_target_dir, "snapshot_info.txt")
        try:
            with open(info_path, "w") as f:
                f.write(f"Snapshot Timestamp: {timestamp}\n")
                f.write(f"Message: {message}\n")
            click.echo(f"  - Saved snapshot info message to {info_path}.")
        except IOError as e:
            click.echo(f"  Error writing snapshot info file {info_path}: {e}", err=True)
            errors_encountered += 1

    # --- Copy Additional Included Files ---
    click.echo("Processing include/exclude patterns...")
    files_to_copy = set()

    # Glob for included files/dirs
    for pattern in include_patterns:
        # Use recursive=True for **/ patterns
        try:
            matched_items = glob.glob(pattern, recursive=True)
            if not matched_items:
                click.echo(f"  - No matches found for include pattern: {pattern}")
            for item_path in matched_items:
                files_to_copy.add(os.path.abspath(item_path))
        except Exception as e:
            click.echo(f"  Error processing include pattern '{pattern}': {e}", err=True)
            errors_encountered += 1

    # Filter out excluded files/dirs
    excluded_files = set()
    for pattern in exclude_patterns:
        try:
            # Also glob recursively for excludes
            matched_items = glob.glob(pattern, recursive=True)
            for item_path in matched_items:
                excluded_files.add(os.path.abspath(item_path))
        except Exception as e:
            click.echo(f"  Error processing exclude pattern '{pattern}': {e}", err=True)
            # Don't count this as a copy error, just a pattern error

    # Also exclude the snapshot directory itself and the core files already copied
    excluded_files.add(os.path.abspath(snapshot_base_dir))
    excluded_files.add(os.path.abspath(config))
    if os.path.exists(ledger_path):
        excluded_files.add(os.path.abspath(ledger_path))

    actual_files_to_copy = []
    for file_path in files_to_copy:
        is_excluded = False
        # Check if the file itself or any of its parent directories are excluded
        path_parts = os.path.abspath(file_path).split(os.sep)
        current_check_path = ""
        for part in path_parts:
            current_check_path = os.path.join(current_check_path, part)
            # Handle drive letter case on Windows
            if len(current_check_path) == 2 and current_check_path[1] == ":":
                current_check_path += os.sep

            if current_check_path in excluded_files:
                is_excluded = True
                break
        if not is_excluded:
            actual_files_to_copy.append(file_path)

    # --- Perform the Copying ---
    if actual_files_to_copy:
        click.echo(f"Copying {len(actual_files_to_copy)} additional item(s)...")

    for src_path in actual_files_to_copy:
        try:
            relative_path = os.path.relpath(
                src_path, start=os.getcwd()
            )  # Get path relative to CWD
            dest_path = os.path.join(snapshot_target_dir, relative_path)

            # Ensure the destination parent directory exists
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)

            if os.path.isdir(src_path):
                # Copy directory contents recursively, excluding already excluded items
                shutil.copytree(
                    src_path,
                    dest_path,
                    dirs_exist_ok=True,
                    ignore=lambda dir, files: [
                        f for f in files if os.path.join(dir, f) in excluded_files
                    ],
                )
                click.echo(f"  - Copied directory: {relative_path}")
            elif os.path.isfile(src_path):
                shutil.copy2(src_path, dest_path)  # copy2 preserves metadata
                click.echo(f"  - Copied file: {relative_path}")
            else:
                click.echo(f"  - Skipping unknown type: {relative_path}")
                continue  # Skip if not file or dir

            files_copied_count += 1  # Count item copied

        except Exception as e:
            click.echo(f"  Error copying {src_path} to {dest_path}: {e}", err=True)
            errors_encountered += 1

    # --- Final Summary ---
    click.echo("\n--- Snapshot Summary ---")
    click.echo(f"Snapshot created at: {snapshot_target_dir}")
    click.echo(f"Total items copied: {files_copied_count}")
    if errors_encountered > 0:
        click.echo(f"Errors encountered: {errors_encountered}", err=True)
        click.echo("Snapshot may be incomplete.")
    else:
        click.echo("Snapshot created successfully.")


# Placeholder for potential future command groups
# @cli.group()
# def memory():
#     """Commands for direct memory block manipulation."""
#     pass

# @memory.command()
# def list():
#     """List memory blocks."""
#     pass

if __name__ == "__main__":
    cli()
