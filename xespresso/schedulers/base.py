import os

class Scheduler:
    """
    Abstract base class for job schedulers used in xespresso.

    This class defines the interface and shared logic for all scheduler types
    (e.g., SLURM, Bash, PBS). It handles job script generation and submission,
    and includes support for loading environment configuration scripts.

    Attributes:
        calc (Calculator): The calculator instance associated with the job.
        queue (dict): Dictionary containing scheduler parameters and metadata.
        command (str): The command to execute the job (with placeholders resolved).
        job_file (str): Name of the job script file to be written.
        script_dir (str): Directory where the job script will be saved.
        config_script (str): Contents of the environment configuration script, if found.

    Methods:
        _load_config_script():
            Searches for and loads a configuration script from predefined locations.
            Returns the script content as a string.

        write_script():
            Abstract method. Must be implemented by subclasses to write the job script.

        submit_command():
            Abstract method. Must be implemented by subclasses to return the submission command.
    """

    def __init__(self, calc, queue, command):
        self.calc = calc
        self.queue = queue
        self.command = command
        self.job_file = ".job_file"
        self.script_dir = calc.directory
        self.config_script = self._load_config_script()

    def _load_config_script(self):
        """
        Loads an optional environment configuration script.

        If 'config' is specified in the queue dictionary, attempts to load it from $HOME.
        Otherwise, searches for default config files in $HOME and the current directory.

        Returns:
            str: Contents of the configuration script, or an empty string if not found.
        """
        config_files = [
            os.path.join(os.environ["HOME"], ".xespressorc"),
            ".xespressorc"
        ]

        if "config" in self.queue:
            cf = os.path.join(os.environ["HOME"], self.queue["config"])
            if os.path.exists(cf):
                with open(cf, "r") as f:
                    return f.read()

        for cf in config_files:
            if os.path.exists(cf):
                with open(cf, "r") as f:
                    return f.read()

        return ""

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
