# Elastic Constants Calculation Workflow

## Overview

The elastic constants calculation workflow provides a comprehensive tool for computing elastic constants of crystalline materials using the energy-strain method. This workflow is particularly useful for materials science research involving mechanical properties of crystals.

## Features

- **Automatic strain generation**: Creates strained structures for different deformation modes
- **Energy-strain fitting**: Automatically fits quadratic curves to extract elastic constants
- **Multiple crystal systems**: Supports cubic and general crystal systems
- **Parallel execution**: Can run multiple calculations in parallel
- **Visualization**: Built-in plotting of energy vs strain curves
- **Flexible configuration**: Customizable strain magnitudes and calculation parameters

## Theory

Elastic constants relate stress and strain in a linear elastic material. For small strains, the energy-strain relationship is:

```
E(ε) = E₀ + V₀ * Σᵢⱼ Cᵢⱼ * εᵢ * εⱼ
```

where:
- E(ε) is the total energy at strain ε
- E₀ is the equilibrium energy
- V₀ is the equilibrium volume
- Cᵢⱼ are the elastic constants
- εᵢ, εⱼ are strain components

### Cubic Crystals

For cubic crystals, there are three independent elastic constants:

1. **C11**: Longitudinal elastic constant (resistance to uniaxial strain)
2. **C12**: Transverse elastic constant (Poisson effect)
3. **C44**: Shear elastic constant (resistance to shear)

The workflow extracts these by applying different strain modes:

- **Volumetric strain**: ε = (ε, ε, ε, 0, 0, 0) → Bulk modulus B = (C11 + 2*C12)/3
- **Uniaxial strain**: ε = (ε, 0, 0, 0, 0, 0) → C11
- **Orthorhombic strain**: ε = (ε, -ε, 0, 0, 0, 0) → C11 - C12
- **Monoclinic shear**: ε = (0, 0, 0, 0, 0, ε) → C44

## Usage

### Basic Example

```python
from ase.build import bulk
from xespresso.workflow.elastic import Elastic

# Create crystal structure
atoms = bulk('Si', 'diamond', a=5.43)

# Define calculator parameters
calculator = {
    'pseudopotentials': {'Si': 'Si.pbe-n-rrkjus_psl.1.0.0.UPF'},
    'ecutwfc': 40.0,
    'ecutrho': 320.0,
    'kpts': (8, 8, 8),
    'occupations': 'smearing',
    'degauss': 0.02,
    'calculation': 'scf',
    'conv_thr': 1e-8,
}

# Create and run elastic workflow
elastic = Elastic(
    atoms,
    label='elastic/si',
    calculator=calculator,
    crystal_system='cubic',
)

elastic.run()

# Access results
print(elastic.results['elastic_constants'])
```

### Custom Strain Magnitudes

You can customize the strain magnitudes used in the calculations:

```python
elastic = Elastic(
    atoms,
    label='elastic/si',
    calculator=calculator,
    crystal_system='cubic',
    strain_magnitudes=[-0.02, -0.01, 0.0, 0.01, 0.02],  # Custom strains
)
```

### With Queue/Cluster Submission

For cluster calculations, add queue parameters:

```python
queue = {
    'nodes': 2,
    'ntasks-per-node': 20,
    'partition': 'compute',
    'time': '02:00:00'
}

calculator['queue'] = queue

elastic = Elastic(
    atoms,
    label='elastic/si',
    calculator=calculator,
    crystal_system='cubic',
)

elastic.run()
```

### Visualization

Plot energy vs strain curves:

```python
elastic.run()
elastic.plot_energy_strain(output='elastic/si/energy_strain.png')
```

## Output

### Results Dictionary

The workflow stores results in `elastic.results['elastic_constants']`:

For cubic systems:
```python
{
    'C11': 165.7,      # GPa
    'C12': 63.9,       # GPa
    'C44': 79.6,       # GPa
    'bulk_modulus': 97.8  # GPa
}
```

### Log File

A detailed log file is created at `{label}/{prefix}.elastico` containing:
- Strain magnitudes used
- Structure information for each strained configuration
- Energy calculations
- Fitted elastic constants
- Summary of results

## Parameters

### Elastic Class Parameters

- **atoms** (Atoms): ASE Atoms object representing the crystal structure
- **label** (str): Directory for calculations (default: 'elastic')
- **prefix** (str, optional): Prefix for calculation files
- **calculator** (dict): Dictionary of calculator parameters
- **view** (bool): Whether to visualize structures (default: False)
- **debug** (bool): Debug mode for sequential execution (default: False)
- **strain_magnitudes** (list): List of strain values (default: [-0.01, -0.005, 0, 0.005, 0.01])
- **crystal_system** (str): Crystal system type (default: 'cubic')

### Calculator Parameters

The calculator dictionary should include:
- **pseudopotentials**: Dict mapping elements to pseudopotential files
- **ecutwfc**: Kinetic energy cutoff (Ry)
- **ecutrho**: Charge density cutoff (Ry)
- **kpts**: k-point grid (tuple)
- **calculation**: Calculation type (typically 'scf')
- **conv_thr**: Energy convergence threshold
- **queue** (optional): Queue parameters for cluster submission

## Supported Crystal Systems

### Cubic
Full elastic tensor with C11, C12, C44, and bulk modulus.

### General
Currently supports bulk modulus calculation only. Full elastic tensor support for other crystal systems (hexagonal, tetragonal, orthorhombic, etc.) can be added in future versions.

## Tips and Best Practices

1. **Convergence**: Ensure your calculator parameters (ecutwfc, kpts) are well-converged before running elastic constant calculations.

2. **Strain Range**: The default strain range (±1%) is suitable for most materials. Reduce for soft materials, increase for very hard materials.

3. **Number of Points**: At least 5 strain points (including zero) are recommended for good quadratic fits.

4. **Equilibrium Structure**: Start with a well-relaxed equilibrium structure for accurate results.

5. **Symmetry**: Ensure your structure has the expected symmetry before running calculations.

6. **Units**: All elastic constants are reported in GPa (GigaPascals).

## Example Results

### Silicon (Diamond Structure)

Experimental values:
- C11: 166 GPa
- C12: 64 GPa
- C44: 80 GPa

Typical DFT-PBE results:
- C11: 165-168 GPa
- C12: 63-65 GPa
- C44: 78-82 GPa

## Troubleshooting

### Issue: Energy not converging

**Solution**: Increase `conv_thr` in calculator parameters or increase k-point density.

### Issue: Irregular energy-strain curve

**Solution**: Check if structure is properly relaxed. Consider using smaller strain magnitudes.

### Issue: Negative elastic constants

**Solution**: This indicates structural instability. Check:
- Is the structure stable at 0K?
- Are symmetries correctly defined?
- Is the calculation properly converged?

## Advanced Usage

### Manual Workflow Control

For more control, you can run individual steps:

```python
elastic = Elastic(atoms, label='elastic/si', calculator=calculator)

# Generate strained structures
elastic.generate_strained_structures()

# Calculate energies
elastic.calculate_energies()

# Extract elastic constants
elastic.extract_elastic_constants()

# Print results
elastic.print_results()
```

### Accessing Individual Calculations

```python
# After running the workflow
for job_name, result in elastic.results.items():
    if job_name != 'elastic_constants':
        print(f"{job_name}: {result['energy']} eV")
```

## References

1. Nielsen, O. H., & Martin, R. M. (1985). Quantum-mechanical theory of stress and force. Physical Review B, 32(6), 3780.

2. Mehl, M. J., et al. (2009). Structural properties of ordered high-melting-temperature intermetallic alloys from first-principles total-energy calculations. Physical Review B, 41(15), 10311.

3. Hill, R. (1952). The elastic behaviour of a crystalline aggregate. Proceedings of the Physical Society. Section A, 65(5), 349.

## See Also

- [Phonon workflow](phonon.py) for vibrational properties
- [OER workflow](oer.py) for electrochemistry
- [Base workflow](base.py) for creating custom workflows
