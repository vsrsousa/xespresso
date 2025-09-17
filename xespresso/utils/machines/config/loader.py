"""
loader.py

Utility for loading machine configurations for xespresso workflows.

This module supports:
- Parsing machine profiles from a JSON config file
- Local and remote execution modes
- Key-based SSH authentication only (password-based authentication is no longer supported)
- Optional job resources, environment setup, and cleanup commands
- Normalization of script blocks (prepend/postpend) to ensure compatibility
- Interactive fallback if machine name is invalid
- Logging and warnings for traceability

Default config path: ~/.xespresso/machines.json
Default machine name: "local_desktop"

Example usage:
from xespresso.utils.machines.config.loader import load_machine
queue = load_machine()  # Loads default machine
"""

import os
import json
from xespresso.utils import warnings as warnings
from xespresso.utils.logging import get_logger

logger = get_logger()
warnings.apply_custom_format()

DEFAULT_CONFIG_PATH = os.path.expanduser("~/.xespresso/machines.json")
DEFAULT_MACHINE_NAME = "local_desktop"

def normalize_script_block(block):
    """
    Ensures that script blocks (prepend/postpend) are returned as strings.
    Accepts either a string or a list of strings.
    """
    if isinstance(block, list):
        return "\n".join(block)
    return block or ""

def load_machine(config_path: str = DEFAULT_CONFIG_PATH, machine_name: str = DEFAULT_MACHINE_NAME) -> dict | None:
    """
    Loads and parses a machine configuration block into a queue dictionary.
    If the machine name is invalid, suggests available options interactively.

    Parameters:
    - config_path (str): Path to the JSON config file
    - machine_name (str): Name of the machine to load

    Returns:
    - queue (dict): Parsed configuration for scheduler and remote execution
    - None: If config file is missing or malformed
    """
    if not os.path.exists(config_path):
        warnings.warn(
            f"Machine config file not found at {config_path}.\n"
            f"To create one, run:\n"
            f" from xespresso.utils.machines.config.creator import create_machine\n"
            f" create_machine(path='{config_path}')\n"
            f"Returning None."
        )
        logger.error(f"Config file not found: {config_path}")
        return None

    try:
        with open(config_path) as f:
            config = json.load(f)
        logger.info(f"Loaded config from {config_path}")
    except Exception as e:
        logger.error(f"Failed to parse config file: {e}")
        return None

    machines = config.get("machines", {})
    if machine_name not in machines:
        logger.warning(f"Machine '{machine_name}' not found in config.")
        print(f"❌ Machine '{machine_name}' not found.")
        print("🧭 Available machines:")
        for name in machines:
            print(f" - {name}")
        retry = input("Enter a valid machine name or press Enter to cancel: ").strip()
        if retry and retry in machines:
            machine_name = retry
            logger.info(f"Retrying with machine: {machine_name}")
        else:
            print("❌ Aborted. No machine loaded.")
            logger.info("User aborted machine selection.")
            return None

    machine = machines[machine_name]

    queue = {
        "execution": machine.get("execution", "local"),
        "scheduler": machine.get("scheduler", "direct"),
        "use_modules": machine.get("use_modules", False),
        "modules": machine.get("modules", []),
        "resources": machine.get("resources", {}),
        "prepend": normalize_script_block(machine.get("prepend")),
        "postpend": normalize_script_block(machine.get("postpend"))
    }

    if queue["execution"] == "local":
        queue["local_dir"] = machine.get("workdir", "./")
        logger.info(f"Loaded local machine: {machine_name}")

    elif queue["execution"] == "remote":
        queue["remote_host"] = machine["host"]
        queue["remote_user"] = machine["username"]
        auth = machine.get("auth", {})
        method = auth.get("method", "key")

        if method != "key":
            logger.error(f"Unsupported authentication method: {method}")
            raise ValueError(f"Unsupported authentication method: {method}")

        queue["remote_auth"] = {
            "method": "key",
            "ssh_key": auth.get("ssh_key", "~/.ssh/id_rsa"),
            "port": auth.get("port", 22)
        }
        queue["remote_dir"] = machine["workdir"]
        logger.info(f"Loaded remote machine: {machine_name}")

    return queue

def list_machines(config_path: str = DEFAULT_CONFIG_PATH) -> list[str]:
    """
    Returns a list of machine names defined in the config file.

    Parameters:
    - config_path (str): Path to the JSON config file

    Returns:
    - list[str]: List of machine names
    """
    if not os.path.exists(config_path):
        logger.warning(f"Config file not found at {config_path}")
        return []
    try:
        with open(config_path) as f:
            config = json.load(f)
        return list(config.get("machines", {}).keys())
    except Exception as e:
        logger.error(f"Failed to read machine list: {e}")
        return []
