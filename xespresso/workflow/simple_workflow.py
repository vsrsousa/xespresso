"""
Simplified workflow for common Quantum ESPRESSO calculations.

This module provides an easy-to-use interface for running common calculations
like SCF and structure relaxation from CIF files or ASE Atoms objects.
"""

import numpy as np
from typing import Dict, Optional, Union, Tuple
from pathlib import Path
from ase import Atoms
from ase.io import read
from ase.io.espresso import kspacing_to_grid
from xespresso import Espresso


# Preset configurations for different calculation qualities
PRESETS = {
    'fast': {
        'ecutwfc': 30.0,
        'ecutrho': 240.0,
        'conv_thr': 1.0e-6,
        'kspacing': 0.5,  # Angstrom^-1
        'mixing_beta': 0.7,
        'electron_maxstep': 100,
    },
    'moderate': {
        'ecutwfc': 50.0,
        'ecutrho': 400.0,
        'conv_thr': 1.0e-8,
        'kspacing': 0.3,  # Angstrom^-1
        'mixing_beta': 0.5,
        'electron_maxstep': 200,
    },
    'accurate': {
        'ecutwfc': 80.0,
        'ecutrho': 640.0,
        'conv_thr': 1.0e-10,
        'kspacing': 0.15,  # Angstrom^-1
        'mixing_beta': 0.3,
        'electron_maxstep': 300,
    }
}


class CalculationWorkflow:
    """
    Simplified workflow for running Quantum ESPRESSO calculations.
    
    This class provides an easy interface for:
    - Reading structures from CIF files
    - Setting up calculations with quality presets
    - Running SCF or relaxation calculations
    - Using k-spacing instead of explicit k-points
    
    Examples:
        >>> # SCF calculation from CIF file
        >>> workflow = CalculationWorkflow.from_cif(
        ...     'structure.cif',
        ...     pseudopotentials={'Si': 'Si.pbe.UPF'},
        ...     quality='moderate'
        ... )
        >>> workflow.run_scf(label='scf/silicon')
        
        >>> # Relax calculation with custom k-spacing
        >>> workflow = CalculationWorkflow.from_cif(
        ...     'structure.cif',
        ...     pseudopotentials={'Si': 'Si.pbe.UPF'},
        ...     quality='fast',
        ...     kspacing=0.4
        ... )
        >>> workflow.run_relax(label='relax/silicon')
    """
    
    def __init__(
        self,
        atoms: Atoms,
        pseudopotentials: Dict[str, str],
        quality: str = 'moderate',
        kspacing: Optional[float] = None,
        input_data: Optional[Dict] = None,
        **kwargs
    ):
        """
        Initialize a calculation workflow.
        
        Args:
            atoms: ASE Atoms object representing the structure
            pseudopotentials: Dictionary mapping element symbols to pseudopotential files
            quality: Quality preset: 'fast', 'moderate', or 'accurate'
            kspacing: K-point spacing in Angstrom^-1. If None, uses preset value.
                     This is converted to k-points using ase.io.espresso.kspacing_to_grid
            input_data: Additional input parameters (merged with preset)
            **kwargs: Additional parameters passed to Espresso calculator
        """
        self.atoms = atoms
        self.pseudopotentials = pseudopotentials
        self.quality = quality
        self.extra_kwargs = kwargs
        
        # Get preset configuration
        if quality not in PRESETS:
            raise ValueError(
                f"Quality must be one of {list(PRESETS.keys())}, got '{quality}'"
            )
        
        self.preset = PRESETS[quality].copy()
        
        # Override k-spacing if provided
        if kspacing is not None:
            self.preset['kspacing'] = kspacing
        
        # Merge input_data with preset
        self.input_data = self.preset.copy()
        if input_data:
            self.input_data.update(input_data)
        
        # Remove kspacing from input_data as it will be converted to kpts
        self.kspacing = self.input_data.pop('kspacing', None)
    
    @classmethod
    def from_cif(
        cls,
        cif_file: Union[str, Path],
        pseudopotentials: Dict[str, str],
        quality: str = 'moderate',
        kspacing: Optional[float] = None,
        input_data: Optional[Dict] = None,
        **kwargs
    ) -> 'CalculationWorkflow':
        """
        Create a workflow from a CIF file.
        
        Args:
            cif_file: Path to CIF file
            pseudopotentials: Dictionary mapping element symbols to pseudopotential files
            quality: Quality preset: 'fast', 'moderate', or 'accurate'
            kspacing: K-point spacing in Angstrom^-1
            input_data: Additional input parameters
            **kwargs: Additional parameters passed to Espresso calculator
            
        Returns:
            CalculationWorkflow: Initialized workflow object
        """
        atoms = read(str(cif_file))
        return cls(atoms, pseudopotentials, quality, kspacing, input_data, **kwargs)
    
    def _get_kpts(self) -> Union[Tuple[int, int, int], str]:
        """
        Calculate k-points from k-spacing using ase.io.espresso.kspacing_to_grid.
        
        Returns:
            Tuple of k-points or 'gamma'
        """
        if self.kspacing is not None:
            # Convert kspacing to k-point grid
            # Note: kspacing_to_grid expects spacing in units of 2*pi/Angstrom
            # So we need to convert from Angstrom^-1
            kpts = kspacing_to_grid(self.atoms, self.kspacing / (2 * np.pi))
            return tuple(kpts)
        else:
            # Default to gamma point if no k-spacing specified
            return (1, 1, 1)
    
    def run_scf(
        self,
        label: str = 'scf',
        **calc_kwargs
    ) -> Espresso:
        """
        Run a self-consistent field (SCF) calculation.
        
        Args:
            label: Directory/label for the calculation
            **calc_kwargs: Additional parameters for the Espresso calculator
            
        Returns:
            Espresso: Calculator object with results
        """
        # Prepare parameters
        params = {
            'pseudopotentials': self.pseudopotentials,
            'label': label,
            'calculation': 'scf',
            'input_data': self.input_data.copy(),
            'kpts': self._get_kpts(),
        }
        
        # Add ecutwfc and ecutrho at top level
        params['ecutwfc'] = self.input_data.get('ecutwfc', 50.0)
        params['ecutrho'] = self.input_data.get('ecutrho', 400.0)
        
        # Merge with extra kwargs
        params.update(self.extra_kwargs)
        params.update(calc_kwargs)
        
        # Create and run calculator
        calc = Espresso(**params)
        self.atoms.calc = calc
        calc.run(atoms=self.atoms)
        
        return calc
    
    def run_relax(
        self,
        label: str = 'relax',
        relax_type: str = 'relax',
        **calc_kwargs
    ) -> Espresso:
        """
        Run a structure relaxation calculation.
        
        Args:
            label: Directory/label for the calculation
            relax_type: Type of relaxation: 'relax' (ions only) or 'vc-relax' (ions + cell)
            **calc_kwargs: Additional parameters for the Espresso calculator
            
        Returns:
            Espresso: Calculator object with results
        """
        if relax_type not in ['relax', 'vc-relax']:
            raise ValueError(
                f"relax_type must be 'relax' or 'vc-relax', got '{relax_type}'"
            )
        
        # Prepare parameters
        params = {
            'pseudopotentials': self.pseudopotentials,
            'label': label,
            'calculation': relax_type,
            'input_data': self.input_data.copy(),
            'kpts': self._get_kpts(),
        }
        
        # Add ecutwfc and ecutrho at top level
        params['ecutwfc'] = self.input_data.get('ecutwfc', 50.0)
        params['ecutrho'] = self.input_data.get('ecutrho', 400.0)
        
        # Merge with extra kwargs
        params.update(self.extra_kwargs)
        params.update(calc_kwargs)
        
        # Create and run calculator
        calc = Espresso(**params)
        self.atoms.calc = calc
        calc.run(atoms=self.atoms)
        
        return calc
    
    def get_atoms(self) -> Atoms:
        """Get the current atoms object."""
        return self.atoms
    
    def get_preset_info(self) -> Dict:
        """Get information about the current quality preset."""
        return {
            'quality': self.quality,
            'preset': self.preset,
            'kpts': self._get_kpts(),
            'kspacing': self.kspacing,
        }


def quick_scf(
    structure: Union[str, Path, Atoms],
    pseudopotentials: Dict[str, str],
    label: str = 'scf',
    quality: str = 'moderate',
    kspacing: Optional[float] = None,
    **kwargs
) -> Espresso:
    """
    Quick SCF calculation helper function.
    
    Args:
        structure: CIF file path or ASE Atoms object
        pseudopotentials: Dictionary mapping element symbols to pseudopotential files
        label: Directory/label for the calculation
        quality: Quality preset: 'fast', 'moderate', or 'accurate'
        kspacing: K-point spacing in Angstrom^-1
        **kwargs: Additional parameters for the calculator
        
    Returns:
        Espresso: Calculator object with results
        
    Example:
        >>> calc = quick_scf(
        ...     'structure.cif',
        ...     {'Si': 'Si.pbe.UPF'},
        ...     quality='fast'
        ... )
    """
    if isinstance(structure, (str, Path)):
        workflow = CalculationWorkflow.from_cif(
            structure, pseudopotentials, quality, kspacing, **kwargs
        )
    else:
        workflow = CalculationWorkflow(
            structure, pseudopotentials, quality, kspacing, **kwargs
        )
    
    return workflow.run_scf(label=label)


def quick_relax(
    structure: Union[str, Path, Atoms],
    pseudopotentials: Dict[str, str],
    label: str = 'relax',
    quality: str = 'moderate',
    kspacing: Optional[float] = None,
    relax_type: str = 'relax',
    **kwargs
) -> Espresso:
    """
    Quick structure relaxation helper function.
    
    Args:
        structure: CIF file path or ASE Atoms object
        pseudopotentials: Dictionary mapping element symbols to pseudopotential files
        label: Directory/label for the calculation
        quality: Quality preset: 'fast', 'moderate', or 'accurate'
        kspacing: K-point spacing in Angstrom^-1
        relax_type: Type of relaxation: 'relax' or 'vc-relax'
        **kwargs: Additional parameters for the calculator
        
    Returns:
        Espresso: Calculator object with results
        
    Example:
        >>> calc = quick_relax(
        ...     'structure.cif',
        ...     {'Si': 'Si.pbe.UPF'},
        ...     quality='moderate',
        ...     relax_type='vc-relax'
        ... )
    """
    if isinstance(structure, (str, Path)):
        workflow = CalculationWorkflow.from_cif(
            structure, pseudopotentials, quality, kspacing, **kwargs
        )
    else:
        workflow = CalculationWorkflow(
            structure, pseudopotentials, quality, kspacing, **kwargs
        )
    
    return workflow.run_relax(label=label, relax_type=relax_type)
