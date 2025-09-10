def generate(calc, queue, command):
    jobname = calc.prefix
    job_path = f"{calc.directory}/.job_file"

    with open(job_path, "w") as fh:
        fh.write("#!/bin/bash\n")
        fh.write(f"#PBS -N {jobname}\n")
        fh.write(f"#PBS -o {calc.prefix}.out\n")
        fh.write(f"#PBS -e {calc.prefix}.err\n")
        for key, value in queue.items():
            if key not in ["scheduler", "config"] and value:
                fh.write(f"#PBS -l {key}={value}\n")

        config_path = queue.get("config")
        if config_path:
            try:
                with open(config_path) as script_file:
                    fh.write(script_file.read() + "\n")
            except FileNotFoundError:
                pass

        fh.write(f"{command}\n")

    calc.command = "qsub .job_file"
