def generate(calc, queue, command):
    job_path = f"{calc.directory}/.job_file"

    with open(job_path, "w") as fh:
        fh.write("#!/bin/bash\n")

        config_path = queue.get("config")
        if config_path:
            try:
                with open(config_path) as script_file:
                    fh.write(script_file.read() + "\n")
            except FileNotFoundError:
                pass

        fh.write(f"{command}\n")

    calc.command = "bash .job_file"
