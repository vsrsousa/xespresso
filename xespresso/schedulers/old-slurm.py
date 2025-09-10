def generate(calc, queue, command):
    jobname = calc.prefix
    job_path = f"{calc.directory}/.job_file"

    with open(job_path, "w") as fh:
        fh.write("#!/bin/bash\n")
        fh.write(f"#SBATCH --job-name={jobname}\n")
        fh.write(f"#SBATCH --output={calc.prefix}.out\n")
        fh.write(f"#SBATCH --error={calc.prefix}.err\n")
#        fh.write("#SBATCH --wait\n")
        for key, value in queue.items():
            if key not in ["scheduler", "config"] and value:
                fh.write(f"#SBATCH --{key}={value}\n")

        # Injeta script customizado se existir
        config_path = queue.get("config")
        if config_path:
            try:
                with open(config_path) as script_file:
                    fh.write(script_file.read() + "\n")
            except FileNotFoundError:
                pass

        fh.write(f"{command}\n")

    calc.command = "sbatch .job_file"
