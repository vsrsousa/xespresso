# Quantum ESPRESSO Codes Configuration

## Overview

The `xespresso.codes` module provides utilities for managing Quantum ESPRESSO code configurations across different machines. This allows you to:

- Define available QE executables and their paths
- Store QE version information per machine
- Automatically detect QE codes on a machine
- Configure code settings per machine
- Integrate with the machines configuration system
- **Support multiple QE versions on the same machine**

## Quick Start

### Manual Configuration

```python
from xespresso.codes import CodesConfig, Code, CodesManager

# Create a configuration for a machine
config = CodesConfig(
    machine_name="cluster1",
    qe_prefix="/opt/qe-7.2/bin",
    qe_version="7.2"
)

# Add individual codes
config.add_code(Code(
    name="pw",
    path="/opt/qe-7.2/bin/pw.x",
    version="7.2"
))

config.add_code(Code(
    name="hp",
    path="/opt/qe-7.2/bin/hp.x",
    version="7.2"
))

# Save configuration
filepath = CodesManager.save_config(config)
print(f"Saved to: {filepath}")
```

### Multiple Versions on Same Machine

A common scenario in HPC environments is having multiple QE versions installed. XEspresso now supports this seamlessly:

```python
from xespresso.codes import CodesConfig, Code

# Create configuration with default version
config = CodesConfig(
    machine_name="cluster1",
    qe_version="7.2"  # Default version
)

# Add QE 7.2 codes
config.add_code(
    Code(name="pw", path="/opt/qe-7.2/bin/pw.x", version="7.2"),
    version="7.2"
)

# Add QE 6.8 codes (same machine!)
config.add_code(
    Code(name="pw", path="/opt/qe-6.8/bin/pw.x", version="6.8"),
    version="6.8"
)

# Save - now supports both versions
CodesManager.save_config(config)
```

### Using Different Versions

```python
from xespresso.codes import load_codes_config

# Load configuration
codes = load_codes_config("cluster1")

# Use QE 7.2 (default)
pw_72 = codes.get_code("pw", version="7.2")
print(f"QE 7.2 pw.x: {pw_72.path}")

# Use QE 6.8
pw_68 = codes.get_code("pw", version="6.8")
print(f"QE 6.8 pw.x: {pw_68.path}")

# List all versions
versions = codes.list_versions()
print(f"Available versions: {versions}")
```

### Automatic Detection

```python
from xespresso.codes import detect_qe_codes

# Detect codes on local machine
config = detect_qe_codes(
    machine_name="local",
    qe_prefix="/opt/qe-7.2/bin"
)

# Detect codes on remote machine via SSH
config = detect_qe_codes(
    machine_name="cluster",
    ssh_connection={'host': 'cluster.edu', 'username': 'user'},
    modules=['quantum-espresso/7.2']
)

# Configuration is automatically saved
```

### Loading Configuration

```python
from xespresso.codes import load_codes_config

# Load codes configuration
config = load_codes_config("cluster1")

if config:
    print(f"Available codes: {', '.join(config.list_codes())}")
    
    # Get specific code
    pw_code = config.get_code("pw")
    print(f"pw.x path: {pw_code.path}")
    print(f"version: {pw_code.version}")
```

## Configuration File Format

Codes configurations are stored as JSON files in `~/.xespresso/codes/`:

### Single Version Format (Backward Compatible)

```json
{
  "machine_name": "cluster1",
  "qe_prefix": "/opt/qe-7.2/bin",
  "qe_version": "7.2",
  "modules": ["quantum-espresso/7.2"],
  "codes": {
    "pw": {
      "name": "pw",
      "path": "/opt/qe-7.2/bin/pw.x",
      "version": "7.2"
    },
    "hp": {
      "name": "hp",
      "path": "/opt/qe-7.2/bin/hp.x",
      "version": "7.2"
    }
  }
}
```

### Multi-Version Format

```json
{
  "machine_name": "cluster1",
  "qe_version": "7.2",
  "codes": {},
  "versions": {
    "7.2": {
      "qe_prefix": "/opt/qe-7.2/bin",
      "modules": ["quantum-espresso/7.2"],
      "codes": {
        "pw": {
          "name": "pw",
          "path": "/opt/qe-7.2/bin/pw.x",
          "version": "7.2"
        },
        "hp": {
          "name": "hp",
          "path": "/opt/qe-7.2/bin/hp.x",
          "version": "7.2"
        }
      }
    },
    "6.8": {
      "qe_prefix": "/opt/qe-6.8/bin",
      "modules": ["quantum-espresso/6.8"],
      "codes": {
        "pw": {
          "name": "pw",
          "path": "/opt/qe-6.8/bin/pw.x",
          "version": "6.8"
        },
        "hp": {
          "name": "hp",
          "path": "/opt/qe-6.8/bin/hp.x",
          "version": "6.8"
        }
      }
    }
  }
}
```

## Integration with Machines

The codes module integrates with the machines configuration system:

```python
from xespresso.machines import load_machine
from xespresso.codes import load_codes_config

# Load machine and codes configuration
machine = load_machine('cluster1')
codes = load_codes_config('cluster1')

# Use in calculations
if codes and codes.has_code('pw'):
    pw_code = codes.get_code('pw')
    # Use pw_code.path in your calculations
```

## Connection Persistence Across Versions

**Important:** When using multiple QE versions on the same remote machine, SSH connections are automatically maintained!

```python
from xespresso.machines import load_machine
from xespresso.codes import load_codes_config

# Load once
machine = load_machine('cluster1')
codes = load_codes_config('cluster1')

# First calculation with QE 7.2
pw_code_72 = codes.get_code('pw', version='7.2')
# ... run calculation ...
# Connection to cluster1 established

# Second calculation with QE 6.8
pw_code_68 = codes.get_code('pw', version='6.8')
# ... run calculation ...
# REUSES same connection! No reconnection needed!

# Third calculation back to QE 7.2
pw_code_72_again = codes.get_code('pw', version='7.2')
# ... run calculation ...
# STILL using same connection!
```

**Key Points:**
- Connection is identified by `(host, username)`, not by QE version
- RemoteExecutionMixin handles connection caching automatically
- Switching versions only changes the executable path and modules
- No connection overhead when switching between versions
- Improves performance and reduces server load

## API Reference

### Classes

#### `Code`
Represents a single QE executable.

**Attributes:**
- `name` (str): Code name (e.g., 'pw', 'hp', 'dos')
- `path` (str): Full path to executable
- `version` (str, optional): QE version
- `parallel_command` (str, optional): MPI command prefix
- `default_parallel` (str, optional): Default parallelization options

#### `CodesConfig`
Configuration for all QE codes on a machine.

**Attributes:**
- `machine_name` (str): Name of the machine
- `codes` (Dict[str, Code]): Dictionary of codes
- `qe_prefix` (str, optional): Common prefix for QE executables
- `qe_version` (str, optional): Default QE version
- `modules` (List[str], optional): Modules to load
- `environment` (Dict[str, str], optional): Environment variables

**Methods:**
- `add_code(code: Code, version: Optional[str] = None)`: Add a code (optionally to a specific version)
- `get_code(name: str, version: Optional[str] = None) -> Code`: Get a code by name (optionally from a specific version)
- `has_code(name: str, version: Optional[str] = None) -> bool`: Check if code exists (optionally in a specific version)
- `list_codes(version: Optional[str] = None) -> List[str]`: List all code names (optionally for a specific version)
- `list_versions() -> List[str]`: List all available QE versions
- `get_version_config(version: str) -> Dict`: Get version-specific configuration
- `to_json(filepath: str)`: Save to JSON file
- `from_json(filepath: str) -> CodesConfig`: Load from JSON file

#### `CodesManager`
Manager for code configurations.

**Methods:**
- `detect_codes(...)`: Detect available QE codes
- `create_config(...)`: Create a CodesConfig from detected codes
- `save_config(config, output_dir)`: Save configuration to file
- `load_config(machine_name, codes_dir)`: Load configuration from file

### Functions

#### `detect_qe_codes`
```python
detect_qe_codes(
    machine_name: str = "local",
    qe_prefix: Optional[str] = None,
    search_paths: Optional[List[str]] = None,
    modules: Optional[List[str]] = None,
    ssh_connection: Optional[Dict] = None
) -> CodesConfig
```

Detect and create a codes configuration.

#### `create_codes_config`
```python
create_codes_config(
    machine_name: str = "local",
    qe_prefix: Optional[str] = None,
    search_paths: Optional[List[str]] = None,
    modules: Optional[List[str]] = None,
    ssh_connection: Optional[Dict] = None,
    save: bool = True,
    output_dir: str = DEFAULT_CODES_DIR
) -> CodesConfig
```

Create a codes configuration with optional auto-save.

#### `load_codes_config`
```python
load_codes_config(
    machine_name: str,
    codes_dir: str = DEFAULT_CODES_DIR,
    version: Optional[str] = None
) -> Optional[CodesConfig]
```

Load a codes configuration from file.

**New Parameter:**
- `version`: Optional QE version to display. If None, uses default or main codes.

#### `add_version_to_config`
```python
add_version_to_config(
    machine_name: str,
    version: str,
    qe_prefix: Optional[str] = None,
    search_paths: Optional[List[str]] = None,
    modules: Optional[List[str]] = None,
    ssh_connection: Optional[Dict] = None,
    codes_dir: str = DEFAULT_CODES_DIR
) -> Optional[CodesConfig]
```

Add a new QE version to an existing codes configuration. This allows managing multiple QE versions on the same machine.

**Example:**
```python
# Add QE 7.2
config = add_version_to_config(
    machine_name="cluster1",
    version="7.2",
    qe_prefix="/opt/qe-7.2/bin",
    modules=["quantum-espresso/7.2"]
)

# Add QE 6.8
config = add_version_to_config(
    machine_name="cluster1",
    version="6.8",
    qe_prefix="/opt/qe-6.8/bin",
    modules=["quantum-espresso/6.8"]
)
```

## Examples

See `examples/codes_example.py` for complete examples.

## Supported QE Codes

The module automatically detects the following QE codes:
- `pw` - PWscf (plane-wave self-consistent field)
- `ph` - PHonon
- `pp` - PostProc
- `projwfc` - Projection of wavefunction
- `dos` - Density of states
- `bands` - Band structure
- `neb` - Nudged elastic band
- `hp` - Hubbard parameters (DFPT)
- `dynmat` - Dynamical matrix
- `matdyn` - Matdyn
- `q2r` - q2r
- And others...

## Advanced Usage

### Multiple Versions on Same Machine

Managing multiple QE versions is straightforward:

```python
from xespresso.codes import add_version_to_config

# Start with one version
config = add_version_to_config(
    machine_name="cluster1",
    version="7.2",
    qe_prefix="/opt/qe-7.2/bin",
    modules=["quantum-espresso/7.2"]
)

# Add another version to the same machine
config = add_version_to_config(
    machine_name="cluster1",
    version="6.8",
    qe_prefix="/opt/qe-6.8/bin",
    modules=["quantum-espresso/6.8"]
)

# Now you can use either version:
codes = load_codes_config("cluster1")
pw_72 = codes.get_code("pw", version="7.2")
pw_68 = codes.get_code("pw", version="6.8")
```

### Using Different Versions in Same Script

```python
from xespresso.codes import load_codes_config
from xespresso.machines import load_machine

# Load configuration once
machine = load_machine("cluster1")
codes = load_codes_config("cluster1")

# Task 1: SCF calculation with QE 7.2
print("Running SCF with QE 7.2...")
pw_code = codes.get_code("pw", version="7.2")
# ... set up and run calculation with pw_code.path ...

# Task 2: DOS calculation with QE 6.8
print("Running DOS with QE 6.8...")
dos_code = codes.get_code("dos", version="6.8")
# ... set up and run calculation with dos_code.path ...

# Task 3: Back to QE 7.2 for bands
print("Running bands with QE 7.2...")
bands_code = codes.get_code("bands", version="7.2")
# ... set up and run calculation with bands_code.path ...

# Connection to cluster1 is maintained throughout!
```

### Listing Available Versions and Codes

```python
from xespresso.codes import load_codes_config

codes = load_codes_config("cluster1")

# List all versions
versions = codes.list_versions()
print(f"Available QE versions: {versions}")

# List codes for each version
for version in versions:
    code_list = codes.list_codes(version=version)
    print(f"\nQE {version} codes: {', '.join(code_list)}")
    
    # Show details for each code
    for code_name in code_list:
        code = codes.get_code(code_name, version=version)
        print(f"  {code_name}: {code.path}")
```

### Custom Code Detection

```python
from xespresso.codes import CodesManager

# Custom search paths
detected = CodesManager.detect_codes(
    search_paths=['/custom/path/bin', '/another/path'],
    modules=['custom-qe-module']
)

# Remote detection with SSH
detected = CodesManager.detect_codes(
    ssh_connection={
        'host': 'cluster.example.edu',
        'username': 'myuser'
    },
    search_paths=['/opt/qe/bin']
)
```

### Version Detection

```python
from xespresso.codes import CodesManager

# Detect QE version from pw.x
version = CodesManager.detect_qe_version('/path/to/pw.x')
print(f"QE version: {version}")
```

## Notes

- Codes configurations are stored separately from machine configurations
- Auto-detection requires SSH access for remote machines
- Module loading is supported via the `modules` parameter
- Configurations are stored in `~/.xespresso/codes/` by default
- **Multiple QE versions can coexist on the same machine**
- **SSH connections persist when switching between versions**
- **Version selection happens at the code loading level, not connection level**
- Backward compatible with single-version configurations

## See Also

- `examples/multi_version_example.py` - Complete example of multi-version usage
- `examples/codes_example.py` - Basic codes configuration examples
- `docs/REMOTE_CONNECTION_PERSISTENCE.md` - Details on connection management
