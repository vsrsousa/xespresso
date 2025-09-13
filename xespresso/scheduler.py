from xespresso.schedulers.factory import get_scheduler

def set_queue(calc, package=None, parallel=None, queue=None, command=None):
    """
    Configures the calculator for job submission.
    If a scheduler is defined in the queue, generates a job script and sets the submission command.
    Otherwise, sets the command directly for manual/local execution.
    """
    import os
    import logging
    logger = logging.getLogger(__name__)

    queue = queue or calc.queue
    calc.queue = queue
    package = package or calc.package
    parallel = parallel or calc.parallel
    command = command or os.environ.get("ASE_ESPRESSO_COMMAND", "")

    # Replace placeholders
    if "PACKAGE" in command:
        if "pw" in package:
            command = command.replace("PACKAGE", package, 1)
            command = command.replace("PACKAGE", "pw", 2)
        else:
            command = command.replace("PACKAGE", package)
    if "PREFIX" in command:
        command = command.replace("PREFIX", calc.prefix)
    if "PARALLEL" in command:
        command = command.replace("PARALLEL", parallel)

    logger.debug(f"Espresso command: {command}")

    # ✅ Only proceed with scheduler logic if queue is defined
    if not queue or "scheduler" not in queue:
        calc.command = command
        logger.debug(f"No scheduler defined. Using direct command: {command}")
        return

    scheduler = get_scheduler(calc, queue, command)
    scheduler.write_script()
    calc.command = scheduler.submit_command()

    logger.debug(f"Queue command: {calc.command}")
