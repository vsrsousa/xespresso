# Quantum ESPRESSO Codes Configuration

## Overview

The `xespresso.codes` module provides utilities for managing Quantum ESPRESSO code configurations across different machines. This allows you to:

- Define available QE executables and their paths
- Store QE version information per machine
- Automatically detect QE codes on a machine
- Configure code settings per machine
- Integrate with the machines configuration system

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
    },
    "dos": {
      "name": "dos",
      "path": "/opt/qe-7.2/bin/dos.x",
      "version": "7.2"
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
- `add_code(code: Code)`: Add a code
- `get_code(name: str) -> Code`: Get a code by name
- `has_code(name: str) -> bool`: Check if code exists
- `list_codes() -> List[str]`: List all code names
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
    codes_dir: str = DEFAULT_CODES_DIR
) -> Optional[CodesConfig]
```

Load a codes configuration from file.

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
