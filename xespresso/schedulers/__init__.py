from .slurm import SlurmScheduler
from .direct import DirectSSHScheduler

def get_scheduler(calc, command, queue):
    scheduler_type = queue.get("scheduler", "slurm").lower()

    if scheduler_type == "slurm":
        return SlurmScheduler(calc, command, queue)
    elif scheduler_type == "direct":
        return DirectSSHScheduler(calc, command, queue)
    else:
        raise ValueError(f"Unsupported scheduler type: {scheduler_type}")

