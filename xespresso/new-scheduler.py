import os
import logging
from xespresso.schedulers import slurm, direct, pbs

logger = logging.getLogger(__name__)

# Definir as configurações globais aqui
CONFIG_FILES = [os.path.join(os.environ["HOME"], ".xespressorc"), ".xespressorc"]

def get_xespresso_config(queue):
    """Lê as configurações do arquivo xespressorc"""
    script = ""
    
    if "config" in queue:
        cf = os.path.join(os.environ["HOME"], queue["config"])
        if os.path.exists(cf):
            with open(cf, "r") as file:
                script = file.read()
    else:
        for cf in CONFIG_FILES:
            if os.path.exists(cf):
                with open(cf, "r") as file:
                    script = file.read()
                break
    return script

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
    else:
        # Se não tem placeholder PARALLEL, adicionar o runner no início
        command = f"{parallel} {command}"
        
    logger.debug("Espresso command: %s" % command)

    scheduler_type = queue.get("scheduler", "slurm").lower()

    # Passar a função de configuração para os módulos
    if scheduler_type == "slurm":
        slurm.generate(calc, queue, command, get_xespresso_config(queue))
    elif scheduler_type == "direct":
        direct.generate(calc, queue, command, get_xespresso_config(queue))
    elif scheduler_type == "pbs":
        pbs.generate(calc, queue, command, get_xespresso_config(queue))
    else:
        raise ValueError(f"Tipo de scheduler não reconhecido: {scheduler_type}")