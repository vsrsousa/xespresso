from .base import Scheduler
import os

class SlurmScheduler(Scheduler):
    """
    Scheduler for SLURM-based job submission systems.

    This class generates a SLURM-compatible job script using parameters from the
    `queue` dictionary and the resolved execution `command`. It includes SBATCH
    directives, environment setup, and optional post-execution commands.

    Supported keys in `queue`:
        - "job_name", "output", "error": Standard SLURM directives
        - Any other key (except "scheduler", "config") is treated as a SBATCH option
        - "prepend": Shell commands to run before the main job
        - "modules": List of modules to load (if "use_modules" is True)
        - "use_modules": Boolean flag to enable module loading
        - "postpend": Shell commands to run after the main job
        - "xespressorc": Optional filename of a shell config file in $HOME

    Methods:
        write_script(): Writes a SLURM job script (.job_file) with structured layout.
        submit_command(): Returns the SLURM submission command (e.g., 'sbatch .job_file').
    """

    def write_script(self):
        lines = ["#!/bin/bash", ""]

        # Unified SBATCH directive block
        sbatch_keys = {
            "job-name": self.queue.get("job_name", self.calc.prefix),
            "output": self.queue.get("output", f"{self.calc.prefix}.out"),
            "error": self.queue.get("error", f"{self.calc.prefix}.err"),
            "wait": None  # --wait is a flag, no value needed
        }

        # Add core directives
        for key, value in sbatch_keys.items():
            if value is not None:
                lines.append(f"#SBATCH --{key}={value}")
            else:
                lines.append(f"#SBATCH --{key}")

        # Add user-defined SBATCH directives
        for key, value in self.queue.items():
            if key in [
                "scheduler", "config", "prepend", "modules", "use_modules",
                "postpend", "xespressorc", "job_name", "output", "error"
            ]:
                continue
            if value:
                lines.append(f"#SBATCH --{key}={value}")

        lines.append("")  # Blank line after SBATCH block

        # Environment setup
        if self.config_script:
            lines.append(self.config_script)
            lines.append("")

        # Main execution command
        lines.append(self.command)
        lines.append("")

        # Post-execution block
        if self.post_script:
            lines.append(self.post_script)

        # Write to job file
        with open(os.path.join(self.script_dir, self.job_file), "w") as f:
            f.write("\n".join(lines))

    def submit_command(self):
        return f"sbatch {self.job_file}"
