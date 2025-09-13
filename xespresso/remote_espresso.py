import os
import json
import shutil
import logging
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
        pseudo_dir (str): Local directory containing .upf pseudopotential files.
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
            package=package or 'pw',
            parallel=parallel,
            command=command,
            **kwargs
        )
        self.remote_runner = remote_runner
        self.remote_subdir = remote_subdir
        self.test_dir = test_dir
        if atoms is not None:
            self.atoms = atoms

    def set(self, **kwargs):
        """
        Sets calculation parameters and attaches pseudo_dir as an attribute.

        Stores all parameters in self.parameters and exposes pseudo_dir
        for direct access and internal use.
        """
        self.parameters.update = kwargs
        if "pseudo_dir" in kwargs:
            self.pseudo_dir = kwargs["pseudo_dir"]
        if "pseudopotentials" in kwargs:
            self.pseudopotentials = kwargs["pseudopotentials"]

    def get_potential_energy(self, atoms=None, force_consistent=False):
        """
        Runs a Quantum ESPRESSO calculation remotely and returns the potential energy.
        """
        if atoms is not None:
            self.atoms = atoms

        self._prepare_pseudos()
        self.write_input(self.atoms)
        set_queue(self)

        if self.remote_runner:
            self.remote_runner.transfer_inputs(self.directory, self.remote_subdir)
            self.remote_runner.submit_remote_job(self.remote_subdir)
            self.remote_runner.retrieve_results(self.remote_subdir, self.directory)

        self.read_results()
        return self.results.get("energy", 0.0)

    def _prepare_pseudos(self):
        """
        Smart pseudopotential setup for remote execution.
        - If parameters["pseudo_dir"] is defined → assume remote path
        - If pseudo_dir attribute is defined → copy files locally into ./pseudos and set pseudo_dir = './pseudos'
        - If neither is defined → raise error
        """
        # Case 1: User explicitly defined remote pseudo_dir
        if "pseudo_dir" in self.parameters:
            logging.info(f"📁 Using remote pseudo_dir: {self.parameters['pseudo_dir']} — no copying needed.")
            return

        # Case 2: User defined local pseudo_dir (attribute)
        if hasattr(self, "pseudo_dir") and self.pseudo_dir:
            logging.info("🧬 Using local pseudo_dir — copying files and setting pseudo_dir = './pseudos'")
            self.parameters["pseudo_dir"] = "./pseudos"

            # Auto-detect pseudopotentials if not set
            if not hasattr(self, "pseudopotentials") or not self.pseudopotentials:
                if not hasattr(self, "atoms") or self.atoms is None:
                    raise ValueError("❌ Cannot auto-detect pseudopotentials: atoms not defined.")

                elements = set(atom.symbol for atom in self.atoms)
                available_files = [f for f in os.listdir(self.pseudo_dir) if f.lower().endswith(".upf")]
                auto_pseudos = {}

                for el in elements:
                    el_lower = el.lower()
                    matches = [f for f in available_files if f.lower().startswith(el_lower)]
                    if matches:
                        auto_pseudos[el] = matches[0]
                        logging.info(f"🔍 Found pseudopotential for {el}: {matches[0]}")
                    else:
                        raise FileNotFoundError(
                            f"❌ No pseudopotential file found for element '{el}' in {self.pseudo_dir}"
                        )

                self.pseudopotentials = auto_pseudos
                self.parameters["pseudopotentials"] = self.pseudopotentials

            # Copy files to ./pseudos folder inside job directory
            if self.remote_runner:
                pseudo_target_dir = os.path.join(self.directory, "pseudos")
                os.makedirs(pseudo_target_dir, exist_ok=True)

                for element, filename in self.pseudopotentials.items():
                    src = os.path.join(self.pseudo_dir, filename)
                    dst = os.path.join(pseudo_target_dir, filename)
                    if not os.path.exists(src):
                        raise FileNotFoundError(f"❌ Pseudopotential file not found: {src}")
                    shutil.copy(src, dst)
                    logging.info(f"📤 Copied {filename} from {src} to {dst}")
            return

        # Case 3: Nothing defined — raise error
        raise ValueError("❌ No pseudo_dir defined. Please set either parameters['pseudo_dir'] or pseudo_dir attribute.")

    def test_connection(self):
        """
        Proxy method to test SSH connectivity via the attached RemoteRunner.

        Returns:
            bool: True if connection is successful, False otherwise.
        """
        if self.remote_runner:
            return self.remote_runner.test_connection()
        print("⚠️ No remote_runner defined.")
        return False

    def test_local_submission_setup(self, verbose=True):
        """
        Tests job script generation locally without remote execution.
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
        Loads remote configuration from ~/.xespresso_config.json.
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

