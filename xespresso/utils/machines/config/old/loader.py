"""
machine_config.py

Utility for managing machine configurations for xespresso workflows.

This module supports:
- Parsing machine profiles from a JSON config file
- Interactive creation of new machine profiles
- Local and remote execution modes
- Key-based SSH authentication only (password-based authentication is no longer supported)
- Optional job resources, environment setup, and cleanup commands

Default config path: ~/.xespresso/machines.json
Default machine name: "local_desktop"

Example usage:
    from xespresso.utils.machine_config import parse_machine_config, create_machine_config

    queue = parse_machine_config()  # Load default machine
    if queue is None:
        create_machine_config()     # Create config interactively
        queue = parse_machine_config()
"""

import os
import json
from xespresso.utils import warnings as warnings

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

def load_machine(config_path: str = DEFAULT_CONFIG_PATH,
		   machine_name: str = DEFAULT_MACHINE_NAME) -> dict | None:
    """
    Loads and parses a machine configuration block into a queue dictionary.
    Returns None if the config file is missing.

    Parameters:
    - config_path (str): Path to the JSON config file
    - machine_name (str): Name of the machine to load

    Returns:
    - queue (dict): Parsed configuration for scheduler and remote execution
    - None: If config file is missing
    """
    if not os.path.exists(config_path):
        warnings.warn(
            f"Machine config file not found at {config_path}.\n"
            f"To create one, make sure to import and call:\n"
            f"    from xespresso.utils.machines.config.creator import create_machine\n"
            f"    create_machine(path='{config_path}')\n"
            f"Returning None."
        )
        return None

    with open(config_path) as f:
        config = json.load(f)

    if "machines" not in config or machine_name not in config["machines"]:
        raise KeyError(f"Machine '{machine_name}' not found in config")

    machine = config["machines"][machine_name]

    queue = {
        "execution": machine.get("execution", "local"),
        "scheduler": machine.get("scheduler", "direct"),
        "use_modules": machine.get("use_modules", False),
        "modules": machine.get("modules", []),
        "resources": machine.get("resources", {}),
        "prepend": normalize_script_block(machine.get("prepend")),
        "postpend": normalize_script_block(machine.get("postpend")),
        "launcher": machine.get("launcher", "mpirun -np {nprocs}"),
        "nprocs": machine.get("nprocs", 1)
    }

    if queue["execution"] == "local":
        queue["local_dir"] = machine.get("workdir", "./")

    elif queue["execution"] == "remote":
        queue["remote_host"] = machine["host"]
        queue["remote_user"] = machine["username"]

        auth = machine.get("auth", {})
        method = auth.get("method", "key")
        
        if method != "key":
            raise ValueError(f"Unsupported authentication method: {method}")
        
        queue["remote_auth"] = {
            "method": "key",
            "ssh_key": auth.get("ssh_key", "~/.ssh/id_rsa"),
            "port": auth.get("port", 22)
        }

        queue["remote_dir"] = machine["workdir"]

    return queue
