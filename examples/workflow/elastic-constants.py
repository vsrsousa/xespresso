"""
Example: Calculate elastic constants for a cubic crystal (Silicon).

This example demonstrates how to use the Elastic workflow to calculate
elastic constants (C11, C12, C44, bulk modulus) for a cubic crystal.

The workflow:
1. Creates strained structures (volumetric, uniaxial, orthorhombic, monoclinic)
2. Calculates energies for each strained structure
3. Fits energy-strain data to extract elastic constants
4. Plots energy vs strain curves
"""

from ase.build import bulk
from xespresso.workflow.elastic import Elastic

# Create silicon cubic structure
atoms = bulk('Si', 'diamond', a=5.43)

# Define pseudopotentials (adjust path as needed)
pseudopotentials = {
    'Si': 'Si.pbe-n-rrkjus_psl.1.0.0.UPF'
}

# Calculator parameters
calculator = {
    'pseudopotentials': pseudopotentials,
    'ecutwfc': 40.0,
    'ecutrho': 320.0,
    'kpts': (8, 8, 8),
    'occupations': 'smearing',
    'degauss': 0.02,
    'calculation': 'scf',
    'conv_thr': 1e-8,
}

# Optional: Set queue parameters for cluster submission
# queue = {
#     'nodes': 2,
#     'ntasks-per-node': 20,
#     'partition': 'debug',
#     'time': '01:00:00'
# }
# calculator['queue'] = queue

# Create elastic constants workflow
elastic = Elastic(
    atoms,
    label='elastic/si',
    calculator=calculator,
    crystal_system='cubic',
    strain_magnitudes=[-0.01, -0.005, 0.0, 0.005, 0.01],
    debug=False,  # Set to True for sequential execution
)

# Run the workflow
elastic.run()

# Access results
print("\n" + "="*60)
print("RESULTS")
print("="*60)
elastic_constants = elastic.results['elastic_constants']
for key, value in elastic_constants.items():
    print(f"{key}: {value:.2f} GPa")

# Plot energy vs strain curves
elastic.plot_energy_strain(output='elastic/si/energy_strain.png')

print("\nElastic constants calculation completed!")
print("Results saved in: elastic/si/")
