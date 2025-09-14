from .base import Scheduler
import os

class BashScheduler(Scheduler):
    """
    Scheduler for direct bash execution (no job manager).

    This class generates a simple bash script that runs the resolved execution
    command directly. It includes any environment setup script loaded by the
    base Scheduler class. Useful for local runs or environments without a job scheduler.

    Attributes:
        Inherited from Scheduler:
            calc (Calculator): The calculator instance.
            queue (dict): Scheduler configuration parameters.
            command (str): Execution command with placeholders resolved.
            job_file (str): Name of the job script file.
            script_dir (str): Directory where the job script is written.
            config_script (str): Optional environment setup script content.
            post_script (str): Optional post-execution commands.

    Methods:
        write_script(): Writes a bash script (.job_file) with structured layout.
        submit_command(): Returns the bash execution command (e.g., 'bash .job_file').
    """

    def write_script(self):
        lines = ["#!/bin/bash", ""]  # Shebang + blank line

        # Prepend block (includes modules and config)
        if self.config_script:
            lines.append(self.config_script)
            lines.append("")  # Blank line after config

        # Main execution command
        lines.append(self.command)
        lines.append("")  # Blank line after command

        # Post-execution block
        if self.post_script:
            lines.append(self.post_script)

        # Write to job file
        with open(os.path.join(self.script_dir, self.job_file), "w") as f:
            f.write("\n".join(lines))

    def submit_command(self):
        """
        Returns the bash execution command.

        Returns:
            str: Command to run the job script via bash.
        """
        return f"bash {self.job_file}"
