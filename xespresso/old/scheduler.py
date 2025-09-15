import os
import logging
from xespresso.schedulers.factory import get_scheduler
from xespresso.config import VERBOSE_ERRORS
from xespresso.utils.slurm import check_slurm_available

def set_queue(calc, package=None, parallel=None, queue=None, command=None):
    """
    Configures the calculator for job submission.

    If a scheduler is defined in the queue, generates a job script and sets the submission command.
    Otherwise, sets the command directly for manual/local execution.

    Behavior:
    - Replaces placeholders in the command string using calc attributes.
    - If SLURM is selected, validates SLURM availability using check_slurm_available().
    - Supports other scheduler types via get_scheduler().
    - Verbosity is controlled by the global flag VERBOSE_ERRORS, set via the environment variable
      XESPRESSO_VERBOSE_ERRORS.

    Args:
        calc: ASE calculator object.
        package (str, optional): Executable name (e.g., 'pw').
        parallel (str, optional): Parallel execution command (e.g., 'mpirun -np 4').
        queue (dict, optional): Scheduler configuration dictionary.
        command (str, optional): Command template string.

    Raises:
        RuntimeError: If SLURM is selected but not available.
        ValueError: If scheduler initialization fails.
    """

    logger = logging.getLogger(__name__)
    queue = queue or calc.queue
    calc.queue = queue
    package = package or calc.package
    parallel = parallel or calc.parallel
    command = command or os.environ.get("ASE_ESPRESSO_COMMAND", "")

    # Replace placeholders
    if "PACKAGE" in command:
        command = command.replace("PACKAGE", package)
    if "PREFIX" in command:
        command = command.replace("PREFIX", calc.prefix)
    if "PARALLEL" in command:
        command = command.replace("PARALLEL", parallel)

    print("Command after set_queue:", calc.command)
    logger.debug(f"Espresso command: {command}")

    # No scheduler defined — use direct command
    if not queue or "scheduler" not in queue:
        calc.command = command
        if hasattr(calc, "profile"):
            calc.profile.command = command
        print(f"No scheduler defined. Using direct command: {command}")
        print(f"Ase profile command: {calc.profile.command}")
        logger.debug(f"No scheduler defined. Using direct command: {command}")
        return

    # Validate SLURM if selected
    if queue.get("scheduler") == "slurm":
        try:
            check_slurm_available()
        except RuntimeError as e:
            msg = f"SLURM scheduler is not available: {e}"
            raise RuntimeError(msg) if VERBOSE_ERRORS else RuntimeError(msg) from None

    # Initialize scheduler (supports slurm, bash, etc.)
    try:
        scheduler = get_scheduler(calc, queue, command)
    except Exception as e:
        msg = f"Failed to initialize scheduler '{queue.get('scheduler')}': {e}"
        raise ValueError(msg) if VERBOSE_ERRORS else ValueError(msg) from None

    scheduler.write_script()
    calc.command = scheduler.submit_command()
    if hasattr(calc, "profile"):
        calc.profile.command = calc.command

    print(f"Using scheduler {scheduler} to run as {command}")
    print(f"Ase profile command: {calc.profile.command}")
    logger.debug(f"Queue command: {calc.command}")
