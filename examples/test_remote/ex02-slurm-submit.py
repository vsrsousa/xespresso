from xespresso import Espresso
from ase.build import bulk
import os

atoms = bulk("Si", "diamond", a=5.43)

queue = {
    "scheduler": "slurm",
    "config": ".xespressorc-medusa",
    "nodes": 1,
    "ntasks-per-node": 16,
    "time": "00:10:00"
}

calc = Espresso(label="test_slurm", queue=queue, parallel="srun --mpi=pmi2")
calc.write_input(atoms)

# Verifica se .job_file foi gerado corretamente
job_path = os.path.join(calc.directory, "job_file")
with open(job_path) as f:
    content = f.read()
    assert "#SBATCH" in content
    assert "sbatch" in calc.command
    print("✅ Slurm job file gerado com sucesso.")

