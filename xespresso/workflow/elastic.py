"""
Elastic constants calculation workflow.

This module provides functionality to calculate elastic constants of crystals
using the energy-strain method. It applies small strains to the crystal structure,
calculates the energy, and fits the data to extract elastic constants.

The elastic constants are calculated using the energy vs strain relationship:
    E(ε) = E₀ + V₀ * Σᵢⱼ Cᵢⱼ * εᵢ * εⱼ
    
For cubic crystals, three independent elastic constants are needed:
    - C11: longitudinal elastic constant
    - C12: transverse elastic constant  
    - C44: shear elastic constant

For other crystal systems, more elastic constants may be needed.
"""

import os
import numpy as np
from copy import deepcopy
from ase import Atoms
from xespresso import Espresso
from xespresso.workflow.base import Base
from xespresso.xlog import XLogger
import matplotlib.pyplot as plt
from concurrent.futures import ThreadPoolExecutor, as_completed


class ELogger(XLogger):
    """Logger for elastic constants calculations."""

    def __init__(self):
        XLogger.__init__(self)

    def logo(self):
        self()
        self(" ====================================")
        self(" Elastic Constants Calculation")
        self(" ====================================")
        self()


class Elastic(Base):
    """
    Workflow for calculating elastic constants.
    
    This class handles the calculation of elastic constants by:
    1. Generating strained structures
    2. Calculating energies for each strained structure
    3. Fitting energy vs strain to extract elastic constants
    
    Examples:
        >>> from ase.build import bulk
        >>> atoms = bulk('Si', cubic=True)
        >>> calculator = {
        ...     'pseudopotentials': {'Si': 'Si.pbe.UPF'},
        ...     'ecutwfc': 40.0,
        ...     'ecutrho': 320.0,
        ...     'kpts': (8, 8, 8),
        ... }
        >>> elastic = Elastic(
        ...     atoms,
        ...     label='elastic/si',
        ...     calculator=calculator,
        ... )
        >>> elastic.run()
        >>> print(elastic.results['elastic_constants'])
    """

    def __init__(
        self,
        atoms,
        label="elastic",
        prefix=None,
        calculator=None,
        view=False,
        debug=False,
        strain_magnitudes=None,
        crystal_system='cubic',
    ):
        """
        Initialize elastic constants workflow.
        
        Args:
            atoms: ASE Atoms object
            label: Label for the calculation directory
            prefix: Prefix for calculation files
            calculator: Calculator parameters dict
            view: Whether to visualize structures
            debug: Debug mode flag
            strain_magnitudes: List of strain values to apply (default: [-0.01, -0.005, 0, 0.005, 0.01])
            crystal_system: Crystal system ('cubic', 'hexagonal', etc.)
        """
        Base.__init__(
            self, atoms, label=label, prefix=prefix, calculator=calculator, 
            view=view, debug=debug
        )
        self.name = 'elastic'
        self.set_logger(ELogger)
        self.strained_structures = {}
        
        if strain_magnitudes is None:
            self.strain_magnitudes = [-0.01, -0.005, 0.0, 0.005, 0.01]
        else:
            self.strain_magnitudes = strain_magnitudes
            
        self.crystal_system = crystal_system
        self.elastic_constants = {}
        self.energies = {}
        
        self.log("Elastic constants calculation workflow initialized")
        self.log(f"Crystal system: {crystal_system}")
        self.log(f"Strain magnitudes: {self.strain_magnitudes}")

    def run(self):
        """Run the elastic constants calculation workflow."""
        self.log("="*60)
        self.log("Starting elastic constants calculation")
        self.log("="*60)
        
        # Generate strained structures
        self.generate_strained_structures()
        
        # Calculate energies
        self.calculate_energies()
        
        # Extract elastic constants
        self.extract_elastic_constants()
        
        # Generate report
        self.print_results()
        
        self.log("="*60)
        self.log("Elastic constants calculation completed")
        self.log("="*60)

    def generate_strained_structures(self):
        """
        Generate strained structures for elastic constant calculations.
        
        For cubic crystals, we need:
        - Volumetric strain (for bulk modulus)
        - Uniaxial strain along [100] (for C11)
        - Orthorhombic strain (for C11-C12)
        - Monoclinic shear strain (for C44)
        """
        self.log("")
        self.log("Generating strained structures...")
        
        original_cell = self.atoms.get_cell()
        
        if self.crystal_system == 'cubic':
            # For cubic crystals, generate different strain types
            strain_types = {
                'volumetric': self._volumetric_strain,
                'uniaxial_100': self._uniaxial_strain_100,
                'orthorhombic': self._orthorhombic_strain,
                'monoclinic': self._monoclinic_strain,
            }
        else:
            # For general case, just use volumetric strain
            strain_types = {
                'volumetric': self._volumetric_strain,
            }
        
        count = 0
        for strain_type, strain_func in strain_types.items():
            for magnitude in self.strain_magnitudes:
                job_name = f"{strain_type}_{magnitude:+.4f}"
                strained_atoms = strain_func(original_cell, magnitude)
                self.strained_structures[job_name] = strained_atoms
                count += 1
        
        self.log(f"Generated {count} strained structures")

    def _volumetric_strain(self, cell, magnitude):
        """Apply volumetric (hydrostatic) strain."""
        strain_matrix = np.eye(3) * (1.0 + magnitude)
        strained_cell = cell @ strain_matrix.T
        strained_atoms = self.atoms.copy()
        strained_atoms.set_cell(strained_cell, scale_atoms=True)
        return strained_atoms

    def _uniaxial_strain_100(self, cell, magnitude):
        """Apply uniaxial strain along [100] direction."""
        strain_matrix = np.eye(3)
        strain_matrix[0, 0] = 1.0 + magnitude
        strained_cell = cell @ strain_matrix.T
        strained_atoms = self.atoms.copy()
        strained_atoms.set_cell(strained_cell, scale_atoms=True)
        return strained_atoms

    def _orthorhombic_strain(self, cell, magnitude):
        """Apply orthorhombic strain (ε_xx = -ε_yy)."""
        strain_matrix = np.eye(3)
        strain_matrix[0, 0] = 1.0 + magnitude
        strain_matrix[1, 1] = 1.0 - magnitude
        strained_cell = cell @ strain_matrix.T
        strained_atoms = self.atoms.copy()
        strained_atoms.set_cell(strained_cell, scale_atoms=True)
        return strained_atoms

    def _monoclinic_strain(self, cell, magnitude):
        """Apply monoclinic shear strain (ε_yz = ε_zy = magnitude/2)."""
        strain_matrix = np.eye(3)
        strain_matrix[1, 2] = magnitude / 2.0
        strain_matrix[2, 1] = magnitude / 2.0
        # Use deformation gradient F = I + ε
        F = np.eye(3) + strain_matrix
        strained_cell = cell @ F.T
        strained_atoms = self.atoms.copy()
        strained_atoms.set_cell(strained_cell, scale_atoms=True)
        return strained_atoms

    def calculate_energies(self):
        """Calculate energies for all strained structures."""
        self.log("")
        self.log("Calculating energies for strained structures...")
        
        # Use base class pool_atoms method for parallel execution
        self.pool_atoms(self.strained_structures, self.run_single_calculation)
        
        self.log(f"Completed energy calculations for {len(self.energies)} structures")

    def run_single_calculation(self, job, atoms):
        """
        Run a single energy calculation for a strained structure.
        
        Args:
            job: Job name/identifier
            atoms: Strained atoms object
            
        Returns:
            Tuple of (job, energy)
        """
        self.log("-" * 60)
        self.log(f"Running calculation: {job}")
        self.log.print_atoms(atoms)
        
        calculator = deepcopy(self.calculator)
        calculator.update({
            'calculation': 'scf',
            'prefix': job,
        })
        
        calc = Espresso(
            label=os.path.join(self.label, job),
            **calculator,
        )
        
        atoms.calc = calc
        calc.run(atoms=atoms)
        calc.read_results()
        
        energy = calc.results['energy']
        self.results[job] = deepcopy(calc.results)
        self.energies[job] = energy
        
        self.log(f"Energy for {job}: {energy:.6f} eV")
        
        return job, energy

    def extract_elastic_constants(self):
        """
        Extract elastic constants from energy-strain data.
        
        For cubic crystals:
        - Bulk modulus B = (C11 + 2*C12) / 3
        - Shear modulus from C44
        - C11 from uniaxial strain
        - C12 from orthorhombic strain
        """
        self.log("")
        self.log("Extracting elastic constants...")
        
        if self.crystal_system == 'cubic':
            self._extract_cubic_constants()
        else:
            self._extract_bulk_modulus()
        
        self.log("Elastic constants extraction completed")

    def _extract_cubic_constants(self):
        """Extract elastic constants for cubic crystal system."""
        # Get equilibrium volume and energy
        eq_energy = self.energies.get('volumetric_+0.0000', None)
        if eq_energy is None:
            # Try to find the zero strain case
            for key in self.energies.keys():
                if 'volumetric' in key and '0.00' in key:
                    eq_energy = self.energies[key]
                    break
        
        eq_atoms = self.strained_structures.get('volumetric_+0.0000', self.atoms)
        V0 = eq_atoms.get_volume()
        
        # Extract bulk modulus from volumetric strain
        vol_strains = []
        vol_energies = []
        for key, energy in self.energies.items():
            if 'volumetric' in key:
                # Extract strain magnitude from key
                parts = key.split('_')
                strain = float(parts[-1])
                vol_strains.append(strain)
                vol_energies.append(energy)
        
        if len(vol_strains) > 2:
            # Fit parabola: E = E0 + V0 * B/2 * ε^2
            vol_strains = np.array(vol_strains)
            vol_energies = np.array(vol_energies)
            coeffs = np.polyfit(vol_strains, vol_energies, 2)
            # B = 2 * a2 / V0, where E = a0 + a1*ε + a2*ε^2
            # Convert to GPa: 1 eV/Å³ = 160.21766208 GPa
            B = 2 * coeffs[0] / V0 * 160.21766208
            self.elastic_constants['bulk_modulus'] = B
            self.log(f"Bulk modulus B: {B:.2f} GPa")
        
        # Extract C11 from uniaxial strain
        uni_strains = []
        uni_energies = []
        for key, energy in self.energies.items():
            if 'uniaxial_100' in key:
                parts = key.split('_')
                strain = float(parts[-1])
                uni_strains.append(strain)
                uni_energies.append(energy)
        
        if len(uni_strains) > 2:
            uni_strains = np.array(uni_strains)
            uni_energies = np.array(uni_energies)
            coeffs = np.polyfit(uni_strains, uni_energies, 2)
            # For uniaxial strain: E = E0 + V0 * C11/2 * ε^2
            C11 = 2 * coeffs[0] / V0 * 160.21766208
            self.elastic_constants['C11'] = C11
            self.log(f"C11: {C11:.2f} GPa")
        
        # Extract C12 from orthorhombic strain
        orth_strains = []
        orth_energies = []
        for key, energy in self.energies.items():
            if 'orthorhombic' in key:
                parts = key.split('_')
                strain = float(parts[-1])
                orth_strains.append(strain)
                orth_energies.append(energy)
        
        if len(orth_strains) > 2:
            orth_strains = np.array(orth_strains)
            orth_energies = np.array(orth_energies)
            coeffs = np.polyfit(orth_strains, orth_energies, 2)
            # For orthorhombic strain: E = E0 + V0 * (C11-C12) * ε^2
            C11_minus_C12 = 2 * coeffs[0] / V0 * 160.21766208
            if 'C11' in self.elastic_constants:
                C12 = self.elastic_constants['C11'] - C11_minus_C12
                self.elastic_constants['C12'] = C12
                self.log(f"C12: {C12:.2f} GPa")
        
        # Extract C44 from monoclinic strain
        mono_strains = []
        mono_energies = []
        for key, energy in self.energies.items():
            if 'monoclinic' in key:
                parts = key.split('_')
                strain = float(parts[-1])
                mono_strains.append(strain)
                mono_energies.append(energy)
        
        if len(mono_strains) > 2:
            mono_strains = np.array(mono_strains)
            mono_energies = np.array(mono_energies)
            coeffs = np.polyfit(mono_strains, mono_energies, 2)
            # For monoclinic shear: E = E0 + V0 * C44 * ε^2
            C44 = 2 * coeffs[0] / V0 * 160.21766208
            self.elastic_constants['C44'] = C44
            self.log(f"C44: {C44:.2f} GPa")

    def _extract_bulk_modulus(self):
        """Extract bulk modulus for general crystal systems."""
        # Get equilibrium volume
        eq_atoms = self.strained_structures.get('volumetric_+0.0000', self.atoms)
        V0 = eq_atoms.get_volume()
        
        # Extract bulk modulus from volumetric strain
        vol_strains = []
        vol_energies = []
        for key, energy in self.energies.items():
            if 'volumetric' in key:
                parts = key.split('_')
                strain = float(parts[-1])
                vol_strains.append(strain)
                vol_energies.append(energy)
        
        if len(vol_strains) > 2:
            vol_strains = np.array(vol_strains)
            vol_energies = np.array(vol_energies)
            coeffs = np.polyfit(vol_strains, vol_energies, 2)
            # Convert to GPa
            B = 2 * coeffs[0] / V0 * 160.21766208
            self.elastic_constants['bulk_modulus'] = B
            self.log(f"Bulk modulus B: {B:.2f} GPa")

    def print_results(self):
        """Print summary of elastic constants."""
        self.log("")
        self.log("="*60)
        self.log("ELASTIC CONSTANTS RESULTS")
        self.log("="*60)
        
        if self.crystal_system == 'cubic':
            if 'C11' in self.elastic_constants:
                self.log(f"C11: {self.elastic_constants['C11']:.2f} GPa")
            if 'C12' in self.elastic_constants:
                self.log(f"C12: {self.elastic_constants['C12']:.2f} GPa")
            if 'C44' in self.elastic_constants:
                self.log(f"C44: {self.elastic_constants['C44']:.2f} GPa")
            if 'bulk_modulus' in self.elastic_constants:
                self.log(f"Bulk modulus B: {self.elastic_constants['bulk_modulus']:.2f} GPa")
        else:
            if 'bulk_modulus' in self.elastic_constants:
                self.log(f"Bulk modulus B: {self.elastic_constants['bulk_modulus']:.2f} GPa")
        
        self.log("="*60)
        
        # Store in results dictionary
        self.results['elastic_constants'] = self.elastic_constants

    def plot_energy_strain(self, output=None):
        """
        Plot energy vs strain curves.
        
        Args:
            output: Output filename for the plot (optional)
        """
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        axes = axes.flatten()
        
        strain_types = ['volumetric', 'uniaxial_100', 'orthorhombic', 'monoclinic']
        titles = ['Volumetric Strain', 'Uniaxial [100] Strain', 
                  'Orthorhombic Strain', 'Monoclinic Shear']
        
        for idx, (strain_type, title) in enumerate(zip(strain_types, titles)):
            ax = axes[idx]
            
            strains = []
            energies = []
            for key, energy in self.energies.items():
                if strain_type in key:
                    parts = key.split('_')
                    strain = float(parts[-1])
                    strains.append(strain)
                    energies.append(energy)
            
            if strains:
                strains = np.array(strains)
                energies = np.array(energies)
                
                # Sort by strain
                sort_idx = np.argsort(strains)
                strains = strains[sort_idx]
                energies = energies[sort_idx]
                
                # Normalize energies
                energies = energies - energies.min()
                
                ax.plot(strains, energies, 'o-', linewidth=2, markersize=8)
                ax.set_xlabel('Strain', fontsize=12)
                ax.set_ylabel('Energy (eV)', fontsize=12)
                ax.set_title(title, fontsize=14)
                ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if output:
            plt.savefig(output, dpi=300, bbox_inches='tight')
            self.log(f"Energy-strain plot saved to {output}")
        
        return fig
