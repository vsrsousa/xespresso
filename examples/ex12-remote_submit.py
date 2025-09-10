from xespresso import Espresso
from xespresso.remote_job_manager import RemoteJobManager
from ase.build import bulk

atoms = bulk("Si", "diamond", a=5.43)

queue = {
    "nodes": 1,
    "ntasks-per-node": 16,
    "partition": "parallel",
    "time": "01:00:00",
    "config": ".xespressorc-medusa"
}

calc = Espresso(label="scf/test", parallel="srun --mpi=pmi2", queue=queue)
calc.write_input(atoms)

ssh_config = {
    "host": "medusa.fis.uerj.br",
#    "port": 222,
    "user": "vinicius",
    "key_path": "/home/vinicius/.ssh/aiida",
    "remote_base": "/home/{user}/scratch/xespresso"
}

manager = RemoteJobManager(**ssh_config)
#manager.submit(local_dir=calc.directory, prefix="test.pwi")
manager.submit(local_dir=calc.directory, label=calc.label)
