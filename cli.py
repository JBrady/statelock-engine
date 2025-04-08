import click
import os
import json
import yaml
from datetime import datetime, timedelta, timezone


# Default structures
DEFAULT_CONFIG = {
    "project_name": "DefaultProject",
    "memory_ledger_path": "memory_ledger.json",
    "snapshot_directory": ".neuronbox_snapshots/",
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
            ".neuronbox_snapshots/",
        ],
    },
}

DEFAULT_LEDGER = {"schema_version": "1.0", "blocks": {}}


# --- Helper Functions ---

def load_config(config_path):
    """Safely load the YAML configuration file."""
    if not os.path.exists(config_path):
        click.echo(f"Error: Configuration file not found at {config_path}", err=True)
        click.echo("Please run 'neuronbox init' or provide the correct path.")
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
        click.echo(f"Ensure the path in config.yaml is correct or run 'neuronbox init'.")
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

# --- CLI Commands ---


@click.group()
def cli():
    """NeuronBox: A middleware toolkit for managing LLM/Agent memory, context, and RAG hygiene."""
    pass


@cli.command()
def init():
    """Initialize NeuronBox config and memory ledger in the current directory."""
    config_path = "config.yaml"
    ledger_path = DEFAULT_CONFIG.get(
        "memory_ledger_path", "memory_ledger.json"
    )  # Get path from default

    click.echo("Initializing NeuronBox project...")

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
    snapshot_dir = DEFAULT_CONFIG.get(
        "snapshot_directory", ".neuronbox_snapshots/"
    )
    if not os.path.exists(snapshot_dir):
        try:
            os.makedirs(snapshot_dir)
            click.echo(f"Created snapshot directory: {snapshot_dir}")
        except OSError as e:
            click.echo(f"Error creating snapshot directory {snapshot_dir}: {e}", err=True)
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
    now = datetime.now(timezone.utc) # Use timezone-aware datetime

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
                    created_dt = datetime.fromisoformat(created_str.replace('Z', '+00:00'))
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
                 warnings_found += 1 # Count missing timestamp as a warning

    # 3. Check required tags
    required_tags_rule = block_rules.get("required_tags", [])
    if required_tags_rule: # Only check if the list is not empty
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
    help="Show what would be collapsed without changing anything.",
)
def collapse(config, dry_run):
    """Collapse or prune memory blocks based on config rules."""
    # Logic to read config, read ledger, identify blocks, perform collapse/prune
    mode = "(Dry Run)" if dry_run else ""
    click.echo(f"Collapsing memory blocks using config: {config} {mode}")
    # TODO: Implement collapse logic
    pass


@cli.command()
@click.option(
    "--name", prompt="Snapshot name", help="A descriptive name for this snapshot."
)
@click.option("--config", default="config.yaml", help="Path to the configuration file.")
def snapshot(name, config):
    """Create a snapshot of the current agent/project state (config, ledger, etc.)."""
    # Logic to gather state (config, ledger, potentially other specified files) and save it
    click.echo(f"Creating snapshot '{name}' using config: {config}")
    # TODO: Implement snapshot logic
    pass


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
