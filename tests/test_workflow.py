"""
Tests for the simplified workflow functionality.
"""

import pytest
import tempfile
import shutil
import numpy as np
from pathlib import Path
from ase.build import bulk
from xespresso.workflow import CalculationWorkflow, quick_scf, quick_relax, PRESETS


def test_presets_exist():
    """Test that all expected presets exist."""
    assert 'fast' in PRESETS
    assert 'moderate' in PRESETS
    assert 'accurate' in PRESETS


def test_preset_values():
    """Test that presets have expected structure and values."""
    for quality, preset in PRESETS.items():
        # Check required keys
        assert 'ecutwfc' in preset
        assert 'ecutrho' in preset
        assert 'conv_thr' in preset
        assert 'kspacing' in preset
        
        # Check types
        assert isinstance(preset['ecutwfc'], float)
        assert isinstance(preset['ecutrho'], float)
        assert isinstance(preset['conv_thr'], float)
        assert isinstance(preset['kspacing'], float)
        
        # Check reasonable values
        assert preset['ecutwfc'] > 0
        assert preset['ecutrho'] > preset['ecutwfc']
        assert preset['kspacing'] > 0


def test_workflow_initialization():
    """Test basic workflow initialization."""
    atoms = bulk("Si", cubic=True)
    pseudopotentials = {"Si": "Si.pbe-n-rrkjus_psl.1.0.0.UPF"}
    
    workflow = CalculationWorkflow(
        atoms=atoms,
        pseudopotentials=pseudopotentials,
        quality='moderate'
    )
    
    assert workflow.atoms is not None
    assert workflow.pseudopotentials == pseudopotentials
    assert workflow.quality == 'moderate'


def test_workflow_invalid_quality():
    """Test that invalid quality raises an error."""
    atoms = bulk("Si", cubic=True)
    pseudopotentials = {"Si": "Si.pbe-n-rrkjus_psl.1.0.0.UPF"}
    
    with pytest.raises(ValueError, match="Quality must be one of"):
        CalculationWorkflow(
            atoms=atoms,
            pseudopotentials=pseudopotentials,
            quality='invalid'
        )


def test_workflow_kspacing():
    """Test k-spacing functionality."""
    atoms = bulk("Si", cubic=True)
    pseudopotentials = {"Si": "Si.pbe-n-rrkjus_psl.1.0.0.UPF"}
    
    # Test with default kspacing from preset
    workflow1 = CalculationWorkflow(
        atoms=atoms,
        pseudopotentials=pseudopotentials,
        quality='moderate'
    )
    kpts1 = workflow1._get_kpts()
    assert isinstance(kpts1, tuple)
    assert len(kpts1) == 3
    assert all(isinstance(k, (int, np.int64, np.int32)) for k in kpts1)
    
    # Test with custom kspacing
    workflow2 = CalculationWorkflow(
        atoms=atoms,
        pseudopotentials=pseudopotentials,
        quality='moderate',
        kspacing=0.5  # Larger spacing = fewer k-points
    )
    kpts2 = workflow2._get_kpts()
    assert isinstance(kpts2, tuple)
    assert len(kpts2) == 3
    
    # Larger k-spacing should give fewer k-points (approximately)
    # Note: This is approximate due to grid rounding
    assert sum(kpts2) <= sum(kpts1)


def test_workflow_get_preset_info():
    """Test get_preset_info method."""
    atoms = bulk("Si", cubic=True)
    pseudopotentials = {"Si": "Si.pbe-n-rrkjus_psl.1.0.0.UPF"}
    
    workflow = CalculationWorkflow(
        atoms=atoms,
        pseudopotentials=pseudopotentials,
        quality='fast',
        kspacing=0.4
    )
    
    info = workflow.get_preset_info()
    
    assert 'quality' in info
    assert 'preset' in info
    assert 'kpts' in info
    assert 'kspacing' in info
    
    assert info['quality'] == 'fast'
    assert info['kspacing'] == 0.4


def test_workflow_input_data_merge():
    """Test that custom input_data is merged with presets."""
    atoms = bulk("Si", cubic=True)
    pseudopotentials = {"Si": "Si.pbe-n-rrkjus_psl.1.0.0.UPF"}
    
    custom_input = {
        'mixing_beta': 0.9,
        'custom_param': 'test'
    }
    
    workflow = CalculationWorkflow(
        atoms=atoms,
        pseudopotentials=pseudopotentials,
        quality='moderate',
        input_data=custom_input
    )
    
    # Check that preset values are present
    assert 'ecutwfc' in workflow.input_data
    assert 'conv_thr' in workflow.input_data
    
    # Check that custom values override preset
    assert workflow.input_data['mixing_beta'] == 0.9
    
    # Check that custom params are added
    assert workflow.input_data['custom_param'] == 'test'


def test_workflow_different_presets():
    """Test that different presets have different parameters."""
    atoms = bulk("Si", cubic=True)
    pseudopotentials = {"Si": "Si.pbe-n-rrkjus_psl.1.0.0.UPF"}
    
    fast = CalculationWorkflow(atoms, pseudopotentials, 'fast')
    moderate = CalculationWorkflow(atoms, pseudopotentials, 'moderate')
    accurate = CalculationWorkflow(atoms, pseudopotentials, 'accurate')
    
    # Check that accuracy increases with preset level
    assert fast.input_data['ecutwfc'] < moderate.input_data['ecutwfc'] < accurate.input_data['ecutwfc']
    assert fast.input_data['conv_thr'] > moderate.input_data['conv_thr'] > accurate.input_data['conv_thr']
    assert fast.kspacing > moderate.kspacing > accurate.kspacing


def test_workflow_from_atoms_object():
    """Test creating workflow from ASE Atoms object."""
    atoms = bulk("Si", cubic=True)
    pseudopotentials = {"Si": "Si.pbe-n-rrkjus_psl.1.0.0.UPF"}
    
    workflow = CalculationWorkflow(
        atoms=atoms,
        pseudopotentials=pseudopotentials,
        quality='moderate'
    )
    
    # Workflow makes a copy to avoid modifying the original
    assert workflow.get_atoms() is not atoms
    assert len(workflow.get_atoms()) == len(atoms)
    assert workflow.get_atoms().get_chemical_symbols() == atoms.get_chemical_symbols()


def test_workflow_magnetic_ferro():
    """Test ferromagnetic configuration."""
    atoms = bulk("Fe", cubic=True)
    pseudopotentials = {"Fe": "Fe.pbe-spn.UPF"}
    
    workflow = CalculationWorkflow(
        atoms=atoms,
        pseudopotentials=pseudopotentials,
        quality='moderate',
        magnetic_config='ferro'
    )
    
    assert 'input_ntyp' in workflow.input_data
    assert 'starting_magnetization' in workflow.input_data['input_ntyp']


def test_workflow_magnetic_antiferro():
    """Test antiferromagnetic configuration."""
    atoms = bulk("Fe", cubic=True)
    pseudopotentials = {"Fe": "Fe.pbe-spn.UPF"}
    
    workflow = CalculationWorkflow(
        atoms=atoms,
        pseudopotentials=pseudopotentials,
        quality='moderate',
        magnetic_config='antiferro'
    )
    
    # Should create different species
    assert 'species' in workflow.atoms.arrays
    assert len(set(workflow.atoms.arrays['species'])) > 1
    assert 'input_ntyp' in workflow.input_data
    assert 'starting_magnetization' in workflow.input_data['input_ntyp']


def test_workflow_magnetic_element_based():
    """Test element-based magnetic configuration."""
    atoms = bulk("Fe", cubic=True)
    pseudopotentials = {"Fe": "Fe.pbe-spn.UPF"}
    
    workflow = CalculationWorkflow(
        atoms=atoms,
        pseudopotentials=pseudopotentials,
        quality='moderate',
        magnetic_config={'Fe': [1, -1]}
    )
    
    # Should create different species
    assert 'species' in workflow.atoms.arrays
    species = workflow.atoms.arrays['species']
    assert 'Fe1' in species
    assert 'Fe2' in species


def test_workflow_magnetic_with_hubbard():
    """Test magnetic configuration with Hubbard U."""
    atoms = bulk("Fe", cubic=True)
    pseudopotentials = {"Fe": "Fe.pbe-spn.UPF"}
    
    workflow = CalculationWorkflow(
        atoms=atoms,
        pseudopotentials=pseudopotentials,
        quality='accurate',
        magnetic_config={'Fe': {'mag': [1, -1], 'U': 4.3}}
    )
    
    # Should have Hubbard parameters
    assert 'input_ntyp' in workflow.input_data
    assert 'Hubbard_U' in workflow.input_data['input_ntyp']
    
    # Check that U values are set
    hubbard_u = workflow.input_data['input_ntyp']['Hubbard_U']
    assert 'Fe1' in hubbard_u
    assert 'Fe2' in hubbard_u
    assert hubbard_u['Fe1'] == 4.3
    assert hubbard_u['Fe2'] == 4.3


# Note: We don't test actual calculation runs here as they require
# Quantum ESPRESSO to be installed and configured. These tests focus
# on the workflow setup and parameter handling.


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
