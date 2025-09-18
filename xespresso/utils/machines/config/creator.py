"""
creator.py

Utility for interactively creating or editing machine configurations for xespresso workflows.

This module supports:
- Creating new machine profiles
- Editing existing profiles via edit_machine()
- Local and remote execution modes
- Key-based SSH authentication only
- Optional job resources for Slurm
- Launcher command with {nprocs} placeholder
- Logging and warnings for traceability

Usage:
from xespresso.utils.machines.config.creator import create_machine
create_machine()  # Launch interactive setup
"""

import os
import json
from xespresso.utils.auth import (
    generate_ssh_key,
    install_ssh_key,
    test_ssh_connection
)
from xespresso.utils.machines.config.edit import edit_machine
from xespresso.utils import warnings as warnings
from xespresso.utils.logging import get_logger

logger = get_logger()
DEFAULT_CONFIG_PATH = os.path.expanduser("~/.xespresso/machines.json")

def create_machine(path: str = DEFAULT_CONFIG_PATH):
    warnings.apply_custom_format()
    logger.info("Starting interactive machine configuration.")
    os.makedirs(os.path.dirname(path), exist_ok=True)

    config = {"machines": {}}
    if os.path.exists(path):
        try:
            with open(path) as f:
                config = json.load(f)
            logger.info(f"Loaded existing config from {path}")
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return

    machine_name = input("Machine name (e.g. local_desktop, cluster_a): ").strip()
    if not machine_name:
        logger.warning("Machine name was left empty.")
        print("❌ Machine name cannot be empty.")
        return

    if machine_name in config["machines"]:
        print(f"⚠️ Machine '{machine_name}' already exists.")
        print("Options:")
        print(" [1] Overwrite from scratch")
        print(" [2] Edit existing configuration")
        choice = input("Choose an option [1/2]: ").strip()

        if choice == "2":
            edit_machine(machine_name, path)
            return
        elif choice == "1":
            print("🔄 Proceeding to overwrite from scratch.")
        else:
            print("❌ Invalid choice. No changes made.")
            logger.warning(f"Invalid overwrite option selected: '{choice}'")
            return

    execution = input("Execution mode [local/remote]: ").strip().lower() or "local"
    scheduler = input("Scheduler [direct/slurm]: ").strip() or "direct"
    workdir = input("Workdir path on machine: ").strip() or "./xespresso"

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
        machine["port"] = int(input("SSH port [22]: ").strip() or "22")
        machine["username"] = input("SSH username: ").strip()

        ssh_key = input("Path to SSH key [~/.ssh/id_rsa.pub]: ").strip() or "~/.ssh/id_rsa.pub"
        ssh_key = os.path.expanduser(ssh_key)

        if not os.path.isfile(ssh_key):
            logger.warning(f"SSH key not found at {ssh_key}")
            print(f"⚠️ SSH key '{ssh_key}' not found.")
            create_key = input("Do you want to generate a new SSH key pair now? [y/N]: ").strip().lower()
            if create_key == "y":
                try:
                    generate_ssh_key(ssh_key.replace(".pub", ""))
                    logger.info(f"SSH key generated at {ssh_key.replace('.pub', '')}")
                    print("✅ Key created. You may now install it on the remote server.")
                    test = input("Test SSH connectivity before installing key? [y/N]: ").strip().lower()
                    if test == "y":
                        test_ssh_connection(machine["username"], machine["host"], None, machine["port"])
                    install = input("Install this key on the remote server now? [y/N]: ").strip().lower()
                    if install == "y":
                        install_ssh_key(machine["username"], machine["host"], ssh_key, machine["port"])
                except Exception as e:
                    logger.error(f"Failed to generate SSH key: {e}")
                    print("❌ Failed to generate SSH key.")
            else:
                print("ℹ️ You will need to create and install this key manually before accessing the remote machine.")
                logger.info("User declined to generate SSH key.")
                test = input("Do you want to test SSH connectivity now (may require password)? [y/N]: ").strip().lower()
                if test == "y":
                    test_ssh_connection(machine["username"], machine["host"], None, machine["port"])
        else:
            machine["auth"] = {"method": "key", "ssh_key": ssh_key}
            logger.info(f"Using existing SSH key: {ssh_key}")
            test = input("Test SSH connectivity with this key? [y/N]: ").strip().lower()
            if test == "y":
                success = test_ssh_connection(machine["username"], machine["host"], ssh_key.replace(".pub", ""), machine["port"])
                if success:
                    print("✅ SSH key is already installed and working.")
                    logger.info("SSH key validated successfully.")
                else:
                    print("⚠️ SSH connection failed. You may need to install the key.")
                    install = input("Install this key on the remote server now? [y/N]: ").strip().lower()
                    if install == "y":
                        install_ssh_key(machine["username"], machine["host"], ssh_key, machine["port"])
                        retest = input("Test SSH connectivity again? [y/N]: ").strip().lower()
                        if retest == "y":
                            test_ssh_connection(machine["username"], machine["host"], ssh_key.replace(".pub", ""), machine["port"])

        machine["auth"] = {"method": "key", "ssh_key": ssh_key}

    if scheduler == "slurm":
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

        machine["resources"] = {k: v for k, v in machine["resources"].items() if v is not None}
        logger.info(f"Resources defined: {machine['resources']}")

    resources = machine.get("resources", {})
    if execution == "remote":
        nodes = resources.get("nodes", 1)
        ntasks = resources.get("ntasks-per-node", 1)
        nprocs = nodes * ntasks
    else:
        try:
            nprocs_input = input("Number of processes for local execution [1]: ").strip()
            nprocs = int(nprocs_input) if nprocs_input else 1
        except ValueError:
            print("⚠️ Invalid input. Using default nprocs = 1.")
            nprocs = 1

    machine["nprocs"] = nprocs

    print("🧭 Define the launcher command used to run Quantum ESPRESSO.")
    print("You may use the placeholder {nprocs}, which will be replaced at runtime.")
    print("Examples:")
    print(" - mpirun -np {nprocs}          (direct or manual MPI)")
    print(" - srun --mpi=pmi2              (Slurm with Intel MPI)")
    print("Note: For Slurm with Intel MPI, use 'srun --mpi=pmi2' without {nprocs}.")
    default_launcher = "mpirun -np {nprocs}"
    launcher = input(f"Launcher command [{default_launcher}]: ").strip() or default_launcher
    machine["launcher"] = launcher
    logger.info(f"Launcher set to: {launcher}")

    config["machines"][machine_name] = machine

    try:
        with open(path, "w") as f:
            json.dump(config, f, indent=2)
        print(f"✅ Machine '{machine_name}' saved to {path}")
        logger.info(f"Machine '{machine_name}' saved successfully.")
    except Exception as e:
        print("❌ Failed to save machine configuration.")
        logger.error(f"Failed to write config file: {e}")
