import os
import logging

# Logger específico para este módulo
logger = logging.getLogger(__name__)

def generate(calc, queue, command, config_script):
    # Para execução direta, podemos precisar carregar os módulos primeiro
    if config_script:
        # Se houver configurações do xespressorc, criar um script wrapper
        wrapper_path = os.path.join(calc.directory, "job_file")
        with open(wrapper_path, "w") as fh:
            fh.writelines("#!/bin/bash\n")
            fh.writelines(config_script)
            fh.writelines("\n%s\n" % command)
        
        os.chmod(wrapper_path, 0o755)  # Tornar executável
        calc.command = f"bash {wrapper_path}"
    else:
        calc.command = command
    
    logger.debug("Direct command: %s" % calc.command)