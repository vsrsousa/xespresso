import os
import logging
from xespresso.schedulers import get_scheduler

logger = logging.getLogger(__name__)

def set_queue(calc, package=None, parallel=None, queue=None, command=None):
    if queue is None:
        queue = calc.queue
    else:
        calc.queue = queue

    package = package or calc.package
    parallel = parallel or calc.parallel
    command = command or os.environ.get("ASE_ESPRESSO_COMMAND", "")

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

    logger.debug("Espresso command: %s", command)

    scheduler = get_scheduler(calc, command, queue)
    scheduler.generate_script()
    calc.command = scheduler.get_submission_command()

    logger.debug("Queue command: %s", calc.command)

