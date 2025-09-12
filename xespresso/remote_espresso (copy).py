from xespresso import Espresso
from xespresso.scheduler import set_queue
import os

class RemoteEspresso(Espresso):
    
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
#            test_dir=test_dir,
            **kwargs
        )
        self.remote_runner = remote_runner
        self.remote_subdir = remote_subdir
        self.test_dir=test_dir
        if atoms is not None:
            self.atoms = atoms

    def get_potential_energy(self, atoms=None, force_consistent=False):
        if atoms is not None:
            self.atoms = atoms

        # Gera os arquivos de entrada (.pwi, .asei)
        self.write_input(self.atoms)

        # Gera o script de submissão (.job_file) com base no queue
        set_queue(self)

        # Executa remotamente se houver runner
        if self.remote_runner:
            self.remote_runner.transfer_inputs(self.directory, self.remote_subdir)
            self.remote_runner.submit_remote_job(self.remote_subdir)
            self.remote_runner.retrieve_results(self.remote_subdir, self.directory)

        # Lê os resultados do cálculo
        self.read_results()
        return self.results.get("energy", 0.0)

    def test_local_submission_setup(self, verbose=True):
        """
        Testa se a função set_queue(self) está funcionando corretamente.
        Gera os arquivos de entrada e o .job_file no diretório local.
        Não realiza submissão remota nem leitura de resultados.
        """
        os.makedirs(self.test_dir, exist_ok=True)

        # Salva o diretório original
        original_dir = getattr(self, "directory", None)

        # Redireciona temporariamente para o diretório de teste
        self.directory = self.test_dir

        # Gera o .job_file
        set_queue(self)


        # Restaura o diretório original
        if original_dir is not None:
            self.directory = original_dir

        job_path = os.path.join(self.test_dir, ".job_file")
        if os.path.exists(job_path):
            if verbose:
                print("✅ .job_file gerado com sucesso em:", job_path)
                with open(job_path) as f:
                    print(f.read())
            return True
        else:
            if verbose:
                print("❌ .job_file não foi encontrado. Verifique se set_queue(self) foi chamado corretamente.")
            return False
