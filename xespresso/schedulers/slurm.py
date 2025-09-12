import os
from .base import SchedulerBase

class SlurmScheduler(SchedulerBase):
    def generate_script(self):
        jobname = self.calc.prefix
        job_path = os.path.join(self.calc.directory, ".job_file")

        with open(job_path, "w") as fh:
            fh.write("#!/bin/bash\n")
            fh.write(f"#SBATCH --job-name={jobname}\n")
            fh.write(f"#SBATCH --output={self.calc.prefix}.out\n")
            fh.write(f"#SBATCH --error={self.calc.prefix}.err\n")
            fh.write("#SBATCH --wait\n")

            for key, value in self.queue.items():
                if key in ["config", "prepend_text", "append_text", "scheduler"]:
                    continue
                if value:
                    fh.write(f"#SBATCH --{key}={value}\n")

            if "config" in self.queue:
                config_path = os.path.join(os.environ["HOME"], self.queue["config"])
                if os.path.exists(config_path):
                    with open(config_path, "r") as f:
                        fh.write(f.read() + "\n")

            if "prepend_text" in self.queue:
                for line in self.queue["prepend_text"].splitlines():
                    fh.write(f"{line}\n")

            fh.write(f"{self.command}\n")

            if "append_text" in self.queue:
                for line in self.queue["append_text"].splitlines():
                    fh.write(f"{line}\n")

    def get_submission_command(self):
        return "sbatch .job_file"

