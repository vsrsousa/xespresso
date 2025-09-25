"""
machine_config.py

Utility for managing machine configurations for xespresso workflows.

This module supports:
- Parsing machine profiles from a JSON config file
- Interactive creation of new machine profiles
- Local and remote execution modes
- Key-based and password-based SSH authentication
- Optional job resources, environment setup, and cleanup commands

Default config path: ~/.xespresso/machines.json
Default machine name: "local_desktop"

Example usage:
    from xespresso.machines.machine_config import load_machine, create_machine

    queue = load_machine()  # Load default machine
    if queue is None:
        create_machine()     # Create config interactively
        queue = load_machine()
"""

import os
import json
import warnings

def custom_warning_format(message, category, filename, lineno, file=None, line=None):
    return f"{category.__name__}: {message}\n"

warnings.formatwarning = custom_warning_format

DEFAULT_CONFIG_PATH = os.path.expanduser("~/.xespresso/machines.json")
DEFAULT_MACHINE_NAME = "local_desktop"

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
            f"    from xespresso.machines.machine_config import create_machine\n"
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
        "prepend": machine.get("prepend", []),
        "postpend": machine.get("postpend", [])
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
                "ssh_key": auth.get("ssh_key", "~/.ssh/id_rsa")
            }
        elif method == "password":
            queue["remote_auth"] = {
                "method": "password",
                "password": auth.get("password", "")
            }
        else:
            raise ValueError(f"Unsupported auth method: {method}")

        queue["remote_dir"] = machine["workdir"]

    return queue

def create_machine(path: str = DEFAULT_CONFIG_PATH):
    """
    Interactively adds a new machine to the config file.
    If the file exists, it appends to the 'machines' block.
    If not, it creates a new config file.

    Parameters:
    - path (str): Path to the config file
    """
    print("⚙️ Let's add a new machine configuration.")

    os.makedirs(os.path.dirname(path), exist_ok=True)

    # Load existing config if present
    if os.path.exists(path):
        with open(path) as f:
            config = json.load(f)
    else:
        config = {"machines": {}}

    machine_name = input("Machine name (e.g. local_desktop, cluster_a): ").strip()
    if not machine_name:
        print("❌ Machine name cannot be empty.")
        return

    if machine_name in config["machines"]:
        print(f"⚠️ Machine '{machine_name}' already exists. Overwriting...")

    execution = input("Execution mode [local/remote]: ").strip().lower() or "local"
    scheduler = input("Scheduler [direct/slurm]: ").strip() or "direct"
    workdir = input("Workdir path on machine: ").strip() or "./qe_local"

    machine = {
        "execution": execution,
        "scheduler": scheduler,
        "workdir": workdir,
        "modules": [],
        "use_modules": False,
        "prepend": [],
        "postpend": [],
        "resources": {}
    }

    if execution == "remote":
        machine["host"] = input("Remote host (e.g. hpc.example.com): ").strip()
        machine["username"] = input("SSH username: ").strip()
        method = input("Auth method [key/password]: ").strip().lower() or "key"
        if method == "key":
            ssh_key = input("Path to SSH key [~/.ssh/id_rsa]: ").strip() or "~/.ssh/id_rsa"
            machine["auth"] = {"method": "key", "ssh_key": ssh_key}
        elif method == "password":
            password = input("SSH password: ").strip()
            machine["auth"] = {"method": "password", "password": password}
        else:
            print("❌ Unsupported auth method.")
            return

        # Prompt for resources
        print("🧮 Define job resources (press Enter to skip any):")
        nodes = input("Number of nodes: ").strip()
        ntasks_per_node = input("Tasks per node: ").strip()
        time = input("Walltime (e.g. 01:00:00): ").strip()
        partition = input("Partition name: ").strip()

        machine["resources"] = {
            "nodes": int(nodes) if nodes else None,
            "ntasks-per-node": int(ntasks_per_node) if ntasks_per_node else None,
            "time": time if time else None,
            "partition": partition if partition else None
        }

        # Remove empty values
        machine["resources"] = {k: v for k, v in machine["resources"].items() if v is not None}

    config["machines"][machine_name] = machine

    with open(path, "w") as f:
        json.dump(config, f, indent=2)

    print(f"✅ Machine '{machine_name}' saved to {path}")
