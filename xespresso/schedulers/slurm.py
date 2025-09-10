import os
import logging

logger = logging.getLogger(__name__)

def generate(calc, queue, command, config_script):
    jobname = calc.prefix
    job_file_path = os.path.join(calc.directory, "job_file")
    
    with open(job_file_path, "w") as fh:
        fh.writelines("#!/bin/bash\n")
        fh.writelines("#SBATCH --no-requeue\n")
        fh.writelines("#SBATCH --get-user-env\n")
        fh.writelines("#SBATCH --job-name=%s\n" % jobname)
        fh.writelines("#SBATCH --output=%s.out\n" % calc.prefix)
        fh.writelines("#SBATCH --error=%s.err\n" % calc.prefix)
#        fh.writelines("#SBATCH --wait\n")
        
        # Diretivas do SLURM
        for key, value in queue.items():
            if key in ["config", "scheduler"]:
                continue
            if value:
                fh.writelines("#SBATCH --%s=%s\n" % (key, value))
        
        # Comandos do xespressorc (module load, export, etc.)
        if config_script:
            fh.writelines("\n# Configurações do xespressorc\n")
            fh.writelines(config_script)
            fh.writelines("\n")
        
        # Comando principal
        fh.writelines("\n# Comando de execução\n")
        fh.writelines("%s\n" % command)
    
    calc.command = "sbatch job_file"
    logger.debug("SLURM command: %s" % calc.command)
