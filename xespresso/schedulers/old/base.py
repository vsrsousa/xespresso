import os

class Scheduler:
    """
    Abstract base class for job schedulers used in xespresso.

    This class defines the interface and shared logic for all scheduler types
    (e.g., SLURM, Bash, Direct). It handles job script generation and submission,
    and includes support for environment setup via the `queue` dictionary.

    Supported keys in `queue`:
        - "prepend": Shell commands to run before the main job (e.g. source profile)
        - "modules": List of modules to load (e.g. ["quantum-espresso"])
        - "use_modules": Boolean flag to enable module loading (default: False)
        - "postpend": Shell commands to run after the main job (e.g. cleanup)
        - "xespressorc": Optional filename of a shell config file in $HOME

    Attributes:
        calc (Calculator): The calculator instance associated with the job.
        queue (dict): Dictionary containing scheduler parameters and metadata.
        command (str): The command to execute the job (with placeholders resolved).
        job_file (str): Name of the job script file to be written.
        script_dir (str): Directory where the job script will be saved.
        config_script (str): Pre-execution environment setup commands.
        post_script (str): Post-execution cleanup or final commands.

    Methods:
        _load_config_script(): Builds the environment setup block.
        _load_post_script(): Loads post-execution commands from queue.
        write_script(): Abstract method. Must be implemented by subclasses.
        submit_command(): Abstract method. Must be implemented by subclasses.
    """

    def __init__(self, calc, queue, command):
        self.calc = calc
        self.queue = queue
        self.command = command
        self.job_file = ".job_file"
        self.script_dir = calc.directory
        self.config_script = self._load_config_script()
        self.post_script = self._load_post_script()

    def _load_config_script(self):
        """
        Builds the environment setup block to be placed before the main execution line.

        Priority:
        1. queue["prepend"]: Custom shell commands (e.g. source env.sh, export VAR=...)
        2. queue["use_modules"] + queue["modules"]: Load modules if explicitly enabled
        3. queue["xespressorc"]: Optional filename in $HOME to source additional setup

        Returns:
            str: Combined shell commands for environment setup.
        """
        lines = []

        # User-defined shell setup
        if "prepend" in self.queue:
            lines.append(self.queue["prepend"])

        # Conditional module loading
        if self.queue.get("use_modules", False):
            modules = self.queue.get("modules", [])
            if isinstance(modules, list) and modules:
                lines.append("module purge")
                for mod in modules:
                    lines.append(f"module load {mod}")

        # Optional config file from $HOME
        config_name = self.queue.get("xespressorc")
        if config_name:
            home_path = os.path.join(os.environ.get("HOME", ""), config_name)
            if os.path.exists(home_path):
                with open(home_path, "r") as f:
                    lines.append(f.read())

        return "\n".join(lines)

    def _load_post_script(self):
        """
        Loads post-execution commands to be placed after the main execution line.

        Returns:
            str: Shell commands for cleanup or final steps.
        """
        return self.queue.get("postpend", "")

    def write_script(self):
        """
        Abstract method to write the job script.

        Subclasses must implement this method to generate the appropriate job file
        based on the scheduler type and queue parameters.
        """
        raise NotImplementedError

    def submit_command(self):
        """
        Abstract method to return the job submission command.

        Subclasses must implement this method to return the correct command
        for submitting the job script (e.g., 'sbatch', 'bash').
        """
        raise NotImplementedError
