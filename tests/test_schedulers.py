import os
import tempfile
import pytest
from xespresso.schedulers import get_scheduler

class DummyCalc:
    def __init__(self, prefix, directory, package="pw.x", parallel="mpirun -np 4"):
        self.prefix = prefix
        self.directory = directory
        self.package = package
        self.parallel = parallel
        self.queue = {}

@pytest.mark.parametrize("scheduler_type,expected_file,expected_command", [
    ("slurm", ".job_file", "sbatch .job_file"),
    ("direct", "run.sh", "bash run.sh")
])
def test_scheduler_script_generation(scheduler_type, expected_file, expected_command):
    with tempfile.TemporaryDirectory() as tmpdir:
        calc = DummyCalc(prefix="testjob", directory=tmpdir)
        raw_command = "PARALLEL PACKAGE -inp PREFIX.pwi > PREFIX.pwo"

        # Simulate placeholder substitution like set_queue() does
        command = raw_command.replace("PACKAGE", calc.package)
        command = command.replace("PREFIX", calc.prefix)
        command = command.replace("PARALLEL", calc.parallel)

        queue = {
            "scheduler": scheduler_type,
            "partition": "cpu",
            "time": "01:00:00",
            "prepend_text": "module load qe/7.2",
            "append_text": "echo Done"
        }

        scheduler = get_scheduler(calc, command, queue)
        scheduler.generate_script()
        submission_cmd = scheduler.get_submission_command()

        script_path = os.path.join(tmpdir, expected_file)
        assert os.path.exists(script_path), f"{expected_file} was not created"
        assert submission_cmd == expected_command

        with open(script_path, "r") as f:
            content = f.read()
            assert "module load qe/7.2" in content
            assert f"{calc.package} -inp {calc.prefix}.pwi > {calc.prefix}.pwo" in content
            assert "echo Done" in content
            if scheduler_type == "slurm":
                assert "#SBATCH --partition=cpu" in content
                assert "#SBATCH --time=01:00:00" in content

