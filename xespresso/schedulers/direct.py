import os
from .base import SchedulerBase

class DirectSSHScheduler(SchedulerBase):
    def generate_script(self):
        job_path = os.path.join(self.calc.directory, "run.sh")

        with open(job_path, "w") as fh:
            fh.write("#!/bin/bash\n")

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
        return "bash run.sh"

