import os
import logging
from xespresso.schedulers import slurm, direct, pbs

logger = logging.getLogger(__name__)

def set_queue(calc, package=None, parallel=None, queue=None, command=None):
    if queue is None:
        queue = calc.queue
    else:
        calc.queue = queue

    if package is None:
        package = calc.package
    else:
        calc.package = package
    if parallel is None:
        parallel = calc.parallel
    else:
        calc.parallel = parallel
        
    if command is None:
        command = os.environ.get("ASE_ESPRESSO_COMMAND")

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

    logger.debug("Espresso command: %s" % command)

    scheduler_type = queue.get("scheduler", "slurm").lower()

    if scheduler_type == "slurm":
        slurm.generate(calc, queue, command)
    elif scheduler_type == "direct":
        direct.generate(calc, queue, command)
    elif scheduler_type == "pbs":
        pbs.generate(calc, queue, command)
    else:
        raise ValueError(f"Tipo de scheduler não reconhecido: {scheduler_type}")

