"""
loader.py

Utility for loading machine configurations for xespresso workflows.

This module supports:
- Parsing machine profiles from a JSON config file
- Local and remote execution modes
- Key-based and password-based SSH authentication
- Optional job resources, environment setup, and cleanup commands
- Normalization of script blocks (prepend/postpend) to ensure compatibility

Default config path: ~/.xespresso/machines.json
Default machine name: "local_desktop"

Example usage:
    from xespresso.utils.machines.config.loader import load_machine
    queue = load_machine()  # Loads default machine
"""

import os
import json
from xespresso.utils import warnings as warnings

# Apply custom warning formatting globally
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
            f"  from xespresso.utils.machines.config.creator import create_machine\n"
            f"  create_machine(path='{config_path}')\n"
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
        "modules": machine.get("modules", []),  # Always a list
        "resources": machine.get("resources", {}),
        "prepend": normalize_script_block(machine.get("prepend")),
        "postpend": normalize_script_block(machine.get("postpend"))
    }

    if queue["execution"] == "local":
        queue["local_dir"] = machine.get("workdir", "./")

    elif queue["execution"] == "remote":
        queue["remote_host"] = machine["host"]
        queue["remote_user"] = machine["username"]

        auth = machine.get("auth", {})
        method = auth.get("method", "key")

        if method == "key":
            queue["remote_auth"] = {
                "method": "key",
                "ssh_key": auth.get("ssh_key", "~/.ssh/id_rsa"),
                "port": auth.get("port", 22)
            }
        elif method == "password":
            queue["remote_auth"] = {
                "method": "password",
                "password": auth.get("password", ""),
                "port": auth.get("port", 22)
            }
        else:
            raise ValueError(f"Unsupported auth method: {method}")

        queue["remote_dir"] = machine["workdir"]

    return queue
