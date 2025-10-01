"""
Example: Detecting and configuring Quantum ESPRESSO codes

This example shows how to:
1. Detect available QE codes on a machine
2. Create a codes configuration
3. Save and load configurations
"""

from xespresso.codes import (
    detect_qe_codes,
    create_codes_config,
    load_codes_config,
    CodesManager,
    Code,
    CodesConfig
)

print("="*60)
print("Example 1: Manually create a codes configuration")
print("="*60)

# Create a manual configuration for a local machine
config = CodesConfig(
    machine_name="local_desktop",
    qe_prefix="/usr/local/qe-7.2/bin",
    qe_version="7.2"
)

# Add codes manually
config.add_code(Code(
    name="pw",
    path="/usr/local/qe-7.2/bin/pw.x",
    version="7.2"
))

config.add_code(Code(
    name="hp",
    path="/usr/local/qe-7.2/bin/hp.x",
    version="7.2"
))

config.add_code(Code(
    name="dos",
    path="/usr/local/qe-7.2/bin/dos.x",
    version="7.2"
))

print(f"Machine: {config.machine_name}")
print(f"QE Version: {config.qe_version}")
print(f"Available codes: {', '.join(config.list_codes())}")

# Save configuration
import tempfile
import os
tmpdir = tempfile.mkdtemp()
filepath = CodesManager.save_config(config, output_dir=tmpdir)
print(f"\n✅ Configuration saved to: {filepath}")

print("\n" + "="*60)
print("Example 2: Load a saved configuration")
print("="*60)

# Load the configuration back
loaded_config = CodesManager.load_config("local_desktop", codes_dir=tmpdir)
if loaded_config:
    print(f"Loaded machine: {loaded_config.machine_name}")
    print(f"QE version: {loaded_config.qe_version}")
    print(f"Codes: {', '.join(loaded_config.list_codes())}")
    
    # Get a specific code
    pw_code = loaded_config.get_code("pw")
    if pw_code:
        print(f"\npw.x details:")
        print(f"  Path: {pw_code.path}")
        print(f"  Version: {pw_code.version}")

print("\n" + "="*60)
print("Example 3: Auto-detect codes (requires QE installation)")
print("="*60)

print("\nNote: Auto-detection requires QE to be installed and in PATH")
print("Uncomment the following code to try auto-detection:")
print("""
# For local machine with QE in PATH
config = detect_qe_codes(
    machine_name="local",
    qe_prefix="/path/to/qe/bin"  # Optional: specify QE installation path
)

# For remote machine via SSH
config = detect_qe_codes(
    machine_name="cluster",
    ssh_connection={'host': 'cluster.edu', 'username': 'user'},
    modules=['quantum-espresso/7.2']  # Load modules before detection
)

# Save detected configuration
if config.codes:
    filepath = CodesManager.save_config(config)
    print(f"Saved to: {filepath}")
""")

print("\n" + "="*60)
print("Example 4: Using codes config with machines")
print("="*60)

print("""
# You can integrate codes with machine configuration:
from xespresso.machines import load_machine
from xespresso.codes import load_codes_config

machine = load_machine('cluster')
codes = load_codes_config('cluster')

if codes and codes.has_code('pw'):
    pw_code = codes.get_code('pw')
    print(f"pw.x path: {pw_code.path}")
    print(f"QE version: {pw_code.version}")
""")

# Cleanup
import shutil
shutil.rmtree(tmpdir, ignore_errors=True)

print("\n✅ Examples completed!")
