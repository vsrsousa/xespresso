from xespresso import Espresso
from ase.build import bulk
import os

atoms = bulk("Si", "diamond", a=5.43)

queue = {
    "scheduler": "direct",
    "config": ".xespressorc-snake6"
}

calc = Espresso(label="test_direct", queue=queue, parallel="mpirun -np 32")
calc.write_input(atoms)

# Verifica se .job_file foi gerado corretamente
job_path = os.path.join(calc.directory, "job_file")
with open(job_path) as f:
    content = f.read()
    assert "#SBATCH" not in content
    assert "bash" in calc.command
    print("✅ Job direto gerado com sucesso.")

