import re
from typing import Dict, Any

def parse_slurm_output(output: str) -> Dict[str, Any]:
    """
    Parse Slurm submission output to extract job ID
    """
    # Typical output: "Submitted batch job 123456"
    match = re.search(r"Submitted batch job (\d+)", output)
    if match:
        return {"job_id": match.group(1), "success": True}
    return {"success": False, "raw_output": output}

def validate_slurm_time(time_str: str) -> bool:
    """
    Validate Slurm time format (DD-HH:MM:SS or HH:MM:SS)
    """
    pattern = r"^(\d+-)?\d{1,2}:\d{2}:\d{2}$"
    return bool(re.match(pattern, time_str))