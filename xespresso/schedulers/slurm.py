from .base import Scheduler
import os

class SlurmScheduler(Scheduler):
    """
    Scheduler for SLURM-based job submission systems.

    This class generates a SLURM-compatible job script using parameters from the
    `queue` dictionary and the resolved execution `command`. It also includes any
    environment configuration script loaded by the base Scheduler class.

    Attributes:
        Inherited from Scheduler:
            calc (Calculator): The calculator instance.
            queue (dict): Scheduler configuration parameters.
            command (str): Execution command with placeholders resolved.
            job_file (str): Name of the job script file.
            script_dir (str): Directory where the job script is written.
            config_script (str): Optional environment setup script content.

    Methods:
        write_script():
            Writes a SLURM job script (.job_file) with SBATCH directives and environment setup.

        submit_command():
            Returns the SLURM submission command (e.g., 'sbatch .job_file').
    """

    def write_script(self):
        lines = [
            "#!/bin/bash",
            f"#SBATCH --job-name={self.queue.get('job_name', self.calc.prefix)}",
            f"#SBATCH --output={self.queue.get('output', f'{self.calc.prefix}.out')}",
            f"#SBATCH --error={self.queue.get('error', f'{self.calc.prefix}.err')}",
            "#SBATCH --wait"
        ]

        # Add remaining SBATCH options from queue
        for key, value in self.queue.items():
            if key in ["scheduler", "config"]:
                continue
            if value:
                lines.append(f"#SBATCH --{key}={value}")

        # Add environment setup script if available
        if self.config_script:
            lines.append(self.config_script)

        # Add the execution command
        lines.append(self.command)

        # Write to job file
        with open(os.path.join(self.script_dir, self.job_file), "w") as f:
            f.write("\n".join(lines))

    def submit_command(self):
        """
        Returns the SLURM submission command.

        Returns:
            str: Command to submit the job script via sbatch.
        """
        return f"sbatch {self.job_file}"
