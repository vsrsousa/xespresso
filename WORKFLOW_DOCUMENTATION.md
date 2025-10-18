# Simplified Workflow for Quantum ESPRESSO Calculations

This document describes the new simplified workflow system in xespresso that makes it easy to run common calculations with quality presets and k-spacing support.

## Features

- **Quality Presets**: Choose between `fast`, `moderate`, and `accurate` calculations
- **K-spacing Support**: Use k-point spacing instead of explicit k-meshes
- **CIF File Support**: Create workflows directly from CIF files
- **Pseudopotential Management**: Store and manage pseudopotential configurations in JSON format
- **Simple API**: Quick functions for common calculation types

## Installation

The workflow functionality is included in xespresso. No additional installation is required.

```bash
pip install xespresso
```

## Quick Start

### Basic SCF Calculation

```python
from xespresso import quick_scf

# Quick SCF calculation from CIF file
calc = quick_scf(
    'structure.cif',
    {'Fe': 'Fe.pbe-spn.UPF'},
    quality='moderate',
    label='scf/fe'
)

energy = calc.results['energy']
print(f"Energy: {energy} eV")
```

### Structure Relaxation

```python
from xespresso import quick_relax

# Quick relaxation
calc = quick_relax(
    'structure.cif',
    {'Fe': 'Fe.pbe-spn.UPF'},
    quality='moderate',
    relax_type='vc-relax',  # relax both cell and ions
    label='relax/fe'
)

relaxed_atoms = calc.results['atoms']
```

## Quality Presets

Three quality presets are available:

### Fast
- **ecutwfc**: 30.0 Ry
- **ecutrho**: 240.0 Ry
- **conv_thr**: 1.0e-6
- **kspacing**: 0.5 Å⁻¹
- Best for: Quick tests, structure screening

### Moderate
- **ecutwfc**: 50.0 Ry
- **ecutrho**: 400.0 Ry
- **conv_thr**: 1.0e-8
- **kspacing**: 0.3 Å⁻¹
- Best for: Standard calculations, most production runs

### Accurate
- **ecutwfc**: 80.0 Ry
- **ecutrho**: 640.0 Ry
- **conv_thr**: 1.0e-10
- **kspacing**: 0.15 Å⁻¹
- Best for: High-accuracy results, publication-quality data

## Using the Workflow Class

For more control, use the `CalculationWorkflow` class:

```python
from xespresso import CalculationWorkflow
from ase.io import read

# Load structure
atoms = read('structure.cif')

# Create workflow
workflow = CalculationWorkflow(
    atoms=atoms,
    pseudopotentials={'Si': 'Si.pbe.UPF'},
    quality='moderate',
    kspacing=0.3  # Optional: override preset k-spacing
)

# Run SCF
calc = workflow.run_scf(label='scf/silicon')

# Run relaxation
calc = workflow.run_relax(label='relax/silicon', relax_type='relax')
```

## K-spacing Support

Instead of specifying explicit k-points, you can use k-spacing (in Å⁻¹):

```python
from xespresso import CalculationWorkflow
import numpy as np

# Using k-spacing as mentioned in the problem statement
workflow = CalculationWorkflow(
    atoms=atoms,
    pseudopotentials=pseudopotentials,
    quality='moderate',
    kspacing=0.20/(2*np.pi)  # This gets converted to k-points
)

# See what k-points this corresponds to
kpts = workflow._get_kpts()
print(f"K-points: {kpts}")
```

The workflow uses ASE's `kspacing_to_grid` function internally to convert k-spacing to k-points.

## Pseudopotential Configuration Management

Store and manage pseudopotential configurations in `~/.xespresso`:

### Saving a Configuration

```python
from xespresso.utils import save_pseudo_config

config = {
    "name": "PBE_efficiency",
    "description": "Efficient PBE pseudopotentials",
    "functional": "PBE",
    "pseudopotentials": {
        "H": "H.pbe-rrkjus_psl.1.0.0.UPF",
        "C": "C.pbe-n-kjpaw_psl.1.0.0.UPF",
        "O": "O.pbe-n-kjpaw_psl.0.1.UPF",
        "Fe": "Fe.pbe-spn-kjpaw_psl.0.2.1.UPF",
    }
}

save_pseudo_config("pbe_efficiency", config)
```

### Loading and Using a Configuration

```python
from xespresso.utils import load_pseudo_config
from xespresso import quick_scf

# Load configuration
config = load_pseudo_config("pbe_efficiency")

# Use in calculation
calc = quick_scf(
    'structure.cif',
    config['pseudopotentials'],
    quality='moderate'
)
```

### Managing Configurations

```python
from xespresso.utils import (
    list_pseudo_configs,
    delete_pseudo_config,
    get_pseudo_info
)

# List all configurations
configs = list_pseudo_configs()
print(f"Available: {configs}")

# Get pseudopotential for a specific element
pseudo = get_pseudo_info("pbe_efficiency", "Fe")
print(f"Fe pseudopotential: {pseudo}")

# Delete a configuration
delete_pseudo_config("old_config")
```

## Advanced Usage

### Custom Input Parameters

You can override any preset parameter or add custom ones:

```python
workflow = CalculationWorkflow(
    atoms=atoms,
    pseudopotentials=pseudopotentials,
    quality='moderate',
    input_data={
        'mixing_beta': 0.9,  # Override preset
        'nspin': 2,          # Add magnetic calculation
    }
)
```

### Working with Different Calculation Types

```python
# SCF calculation
calc = workflow.run_scf(label='scf/fe')

# Ion relaxation only
calc = workflow.run_relax(label='relax/fe', relax_type='relax')

# Full cell relaxation
calc = workflow.run_relax(label='relax/fe-vc', relax_type='vc-relax')
```

## Examples

Complete working examples are available in the `examples/` directory:

- `workflow_simple_example.py`: Basic workflow usage
- `pseudo_config_example.py`: Pseudopotential configuration management
- `complete_workflow_example.py`: Complete integration example from CIF to results

## API Reference

### CalculationWorkflow

Main class for managing calculations.

**Constructor Parameters:**
- `atoms`: ASE Atoms object
- `pseudopotentials`: Dict mapping elements to pseudopotential files
- `quality`: Quality preset ('fast', 'moderate', 'accurate')
- `kspacing`: K-point spacing in Å⁻¹ (optional)
- `input_data`: Additional input parameters (optional)
- `**kwargs`: Additional parameters for Espresso calculator

**Methods:**
- `run_scf(label, **kwargs)`: Run SCF calculation
- `run_relax(label, relax_type='relax', **kwargs)`: Run relaxation
- `get_atoms()`: Get the atoms object
- `get_preset_info()`: Get preset information

**Class Methods:**
- `from_cif(cif_file, ...)`: Create workflow from CIF file

### Quick Functions

- `quick_scf(structure, pseudopotentials, quality='moderate', ...)`: Quick SCF calculation
- `quick_relax(structure, pseudopotentials, quality='moderate', ...)`: Quick relaxation

### Pseudo Configuration Functions

- `save_pseudo_config(name, config, overwrite=False)`: Save configuration
- `load_pseudo_config(name)`: Load configuration
- `list_pseudo_configs()`: List all configurations
- `delete_pseudo_config(name)`: Delete configuration
- `get_pseudo_info(config_name, element)`: Get pseudopotential for element

## Notes

- K-spacing is converted to k-points using `ase.io.espresso.kspacing_to_grid`
- Pseudopotential configurations are stored as JSON in `~/.xespresso/`
- All presets use sensible defaults that can be overridden
- The workflow integrates seamlessly with existing xespresso functionality

## See Also

- [ASE Espresso Calculator](https://wiki.fysik.dtu.dk/ase/ase/calculators/espresso.html)
- [Quantum ESPRESSO Documentation](https://www.quantum-espresso.org/)
