import os
import json
import shutil
from xespresso import Espresso
from xespresso.scheduler import set_queue
from xespresso.remote_runner import RemoteRunner

class RemoteEspresso(Espresso):
    """
    A subclass of Espresso that supports remote execution via SSH.

    Attributes:
        remote_runner (RemoteRunner): Handles SSH connection and file transfer.
        remote_subdir (str): Name of the remote job directory.
        test_dir (str): Optional local directory for testing job file generation.
    """

    name = "espresso"

    def __init__(
        self,
        *args,
        atoms=None,
        remote_runner=None,
        remote_subdir=None,
        queue=None,
        package=None,
        parallel=None,
        command=None,
        test_dir=None,
        **kwargs
    ):
        super().__init__(
            *args,
            atoms=atoms,
            queue=queue,
            package=package,
            parallel=parallel,
            command=command,
            **kwargs
        )
        self.remote_runner = remote_runner
        self.remote_subdir = remote_subdir
        self.test_dir = test_dir
        if atoms is not None:
            self.atoms = atoms

    def get_potential_energy(self, atoms=None, force_consistent=False):
        """
        Runs a Quantum ESPRESSO calculation remotely and returns the potential energy.

        Steps:
        - Writes input files locally
        - Generates job script using set_queue()
        - Copies .upf files into job folder if needed
        - Transfers files to remote host
        - Submits job remotely
        - Retrieves results
        - Parses and returns energy
        """
        if atoms is not None:
            self.atoms = atoms

        self._prepare_pseudos()

        # Generate input files (.pwi, .asei)
        self.write_input(self.atoms)

        # Generate job script (.job_file)
        set_queue(self)

        # Execute remotely if runner is defined
        if self.remote_runner:
            self.remote_runner.transfer_inputs(self.directory, self.remote_subdir)
            self.remote_runner.submit_remote_job(self.remote_subdir)
            self.remote_runner.retrieve_results(self.remote_subdir, self.directory)

        # Read results and return energy
        self.read_results()
        return self.results.get("energy", 0.0)

    def _prepare_pseudos(self):
        """
        Ensures pseudopotentials are present in the job directory.
        If running remotely, copies .upf files from local pseudo_dir to job folder.
        Raises an error if pseudopotentials are missing or files not found.
        If pseudopotentials are not explicitly set, attempts to auto-detect from atoms.
        """
        if not hasattr(self, "pseudo_dir") or not self.pseudo_dir:
            raise ValueError("❌ No pseudo_dir defined. Please set it using calc.set(pseudo_dir='...')")

        # Auto-detect pseudopotentials if not explicitly set
        if not hasattr(self, "pseudopotentials") or not self.pseudopotentials:
            if not hasattr(self, "atoms") or self.atoms is None:
                raise ValueError("❌ Cannot auto-detect pseudopotentials: atoms not defined.")

            elements = set(atom.symbol for atom in self.atoms)
            available_files = [f for f in os.listdir(self.pseudo_dir) if f.lower().endswith(".upf")]
            auto_pseudos = {}

            for el in elements:
                matches = [f for f in available_files if f.lower().startswith(el.lower())]
                if matches:
                    auto_pseudos[el] = matches[0]  # Use the first match
                else:
                    raise FileNotFoundError(f"❌ No pseudopotential file found for element '{el}' in {self.pseudo_dir}")

            self.pseudopotentials = auto_pseudos

        # Copy .upf files into job folder if running remotely
        if self.remote_runner:
            for element, filename in self.pseudopotentials.items():
                src = os.path.join(self.pseudo_dir, filename)
                dst = os.path.join(self.directory, filename)
                if not os.path.exists(src):
                    raise FileNotFoundError(f"❌ Pseudopotential file not found: {src}")
                shutil.copy(src, dst)

    def test_local_submission_setup(self, verbose=True):
        """
        Tests local job script generation using set_queue(self).
        Does not perform remote submission or result retrieval.

        Returns:
            bool: True if .job_file was generated successfully, False otherwise.
        """
        os.makedirs(self.test_dir, exist_ok=True)
        original_dir = getattr(self, "directory", None)
        self.directory = self.test_dir
        set_queue(self)
        if original_dir is not None:
            self.directory = original_dir

        job_path = os.path.join(self.test_dir, ".job_file")
        if os.path.exists(job_path):
            if verbose:
                print("✅ .job_file successfully generated at:", job_path)
                with open(job_path) as f:
                    print(f.read())
            return True
        else:
            if verbose:
                print("❌ .job_file not found. Make sure set_queue(self) was called correctly.")
            return False

    @classmethod
    def from_config(cls, atoms=None, remote_subdir=None, profile="default", **kwargs):
        """
        Automatically loads remote configuration from ~/.xespresso_config.json.

        Args:
            atoms (Atoms): Atomic structure to simulate.
            remote_subdir (str): Remote job directory name.
            profile (str): Profile name in the config file (default: 'default').

        Returns:
            RemoteEspresso: Configured instance ready for remote execution.
        """
        config_path = os.path.expanduser("~/.xespresso_config.json")
        if not os.path.exists(config_path):
            raise FileNotFoundError("❌ Config file ~/.xespresso_config.json not found.")

        with open(config_path) as f:
            config = json.load(f)

        profiles = config.get("remotes", {})
        remote_config = profiles.get(profile)
        if not remote_config:
            raise ValueError(f"❌ Remote profile '{profile}' not found in config.")

        runner = RemoteRunner(**remote_config)
        return cls(atoms=atoms, remote_runner=runner, remote_subdir=remote_subdir, **kwargs)
