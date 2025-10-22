"""
Tests for the elastic constants workflow.
"""

import pytest
import numpy as np
from ase.build import bulk
from xespresso.workflow.elastic import Elastic


def test_elastic_initialization():
    """Test basic elastic workflow initialization."""
    atoms = bulk("Si", cubic=True)
    calculator = {
        'pseudopotentials': {'Si': 'Si.pbe.UPF'},
        'ecutwfc': 40.0,
        'kpts': (4, 4, 4),
    }
    
    elastic = Elastic(
        atoms,
        label='test_elastic',
        calculator=calculator,
    )
    
    assert elastic.atoms is not None
    assert elastic.crystal_system == 'cubic'
    assert len(elastic.strain_magnitudes) == 5
    assert elastic.strain_magnitudes == [-0.01, -0.005, 0.0, 0.005, 0.01]


def test_elastic_custom_strains():
    """Test elastic workflow with custom strain magnitudes."""
    atoms = bulk("Si", cubic=True)
    calculator = {'pseudopotentials': {'Si': 'Si.pbe.UPF'}}
    
    custom_strains = [-0.02, -0.01, 0.0, 0.01, 0.02]
    elastic = Elastic(
        atoms,
        label='test_elastic',
        calculator=calculator,
        strain_magnitudes=custom_strains,
    )
    
    assert elastic.strain_magnitudes == custom_strains


def test_elastic_crystal_systems():
    """Test different crystal systems."""
    atoms = bulk("Si", cubic=True)
    calculator = {'pseudopotentials': {'Si': 'Si.pbe.UPF'}}
    
    # Test cubic
    elastic_cubic = Elastic(
        atoms,
        label='test_elastic_cubic',
        calculator=calculator,
        crystal_system='cubic',
    )
    assert elastic_cubic.crystal_system == 'cubic'
    
    # Test general
    elastic_general = Elastic(
        atoms,
        label='test_elastic_general',
        calculator=calculator,
        crystal_system='hexagonal',
    )
    assert elastic_general.crystal_system == 'hexagonal'


def test_generate_strained_structures_cubic():
    """Test generation of strained structures for cubic system."""
    atoms = bulk("Si", cubic=True)
    calculator = {'pseudopotentials': {'Si': 'Si.pbe.UPF'}}
    
    elastic = Elastic(
        atoms,
        label='test_elastic',
        calculator=calculator,
        crystal_system='cubic',
        strain_magnitudes=[-0.01, 0.0, 0.01],
    )
    
    elastic.generate_strained_structures()
    
    # For cubic with 3 strains, we should have 4 strain types × 3 magnitudes = 12 structures
    assert len(elastic.strained_structures) == 12
    
    # Check that different strain types exist
    strain_types = set()
    for key in elastic.strained_structures.keys():
        strain_type = '_'.join(key.split('_')[:-1])
        strain_types.add(strain_type)
    
    expected_types = {'volumetric', 'uniaxial_100', 'orthorhombic', 'monoclinic'}
    assert strain_types == expected_types


def test_generate_strained_structures_general():
    """Test generation of strained structures for general system."""
    atoms = bulk("Si", cubic=True)
    calculator = {'pseudopotentials': {'Si': 'Si.pbe.UPF'}}
    
    elastic = Elastic(
        atoms,
        label='test_elastic',
        calculator=calculator,
        crystal_system='hexagonal',
        strain_magnitudes=[-0.01, 0.0, 0.01],
    )
    
    elastic.generate_strained_structures()
    
    # For general system with 3 strains, we should have 1 strain type × 3 magnitudes = 3 structures
    assert len(elastic.strained_structures) == 3
    
    # Check that only volumetric strain exists
    for key in elastic.strained_structures.keys():
        assert 'volumetric' in key


def test_volumetric_strain():
    """Test volumetric strain application."""
    atoms = bulk("Si", cubic=True)
    calculator = {'pseudopotentials': {'Si': 'Si.pbe.UPF'}}
    
    elastic = Elastic(
        atoms,
        label='test_elastic',
        calculator=calculator,
    )
    
    original_cell = atoms.get_cell()
    original_volume = atoms.get_volume()
    
    # Apply +1% volumetric strain
    strained = elastic._volumetric_strain(original_cell, 0.01)
    new_volume = strained.get_volume()
    
    # Volume should increase by (1.01)^3 ≈ 1.0303
    expected_volume = original_volume * (1.01 ** 3)
    assert np.isclose(new_volume, expected_volume, rtol=1e-6)


def test_uniaxial_strain():
    """Test uniaxial strain application."""
    atoms = bulk("Si", cubic=True)
    calculator = {'pseudopotentials': {'Si': 'Si.pbe.UPF'}}
    
    elastic = Elastic(
        atoms,
        label='test_elastic',
        calculator=calculator,
    )
    
    original_cell = atoms.get_cell()
    a0 = original_cell[0, 0]
    
    # Apply +1% uniaxial strain along [100]
    strained = elastic._uniaxial_strain_100(original_cell, 0.01)
    new_cell = strained.get_cell()
    
    # First lattice parameter should increase by 1%
    assert np.isclose(new_cell[0, 0], a0 * 1.01, rtol=1e-6)
    # Other parameters should remain unchanged
    assert np.isclose(new_cell[1, 1], original_cell[1, 1], rtol=1e-6)
    assert np.isclose(new_cell[2, 2], original_cell[2, 2], rtol=1e-6)


def test_orthorhombic_strain():
    """Test orthorhombic strain application."""
    atoms = bulk("Si", cubic=True)
    calculator = {'pseudopotentials': {'Si': 'Si.pbe.UPF'}}
    
    elastic = Elastic(
        atoms,
        label='test_elastic',
        calculator=calculator,
    )
    
    original_cell = atoms.get_cell()
    a0 = original_cell[0, 0]
    
    # Apply orthorhombic strain
    strained = elastic._orthorhombic_strain(original_cell, 0.01)
    new_cell = strained.get_cell()
    
    # First parameter increases, second decreases
    assert np.isclose(new_cell[0, 0], a0 * 1.01, rtol=1e-6)
    assert np.isclose(new_cell[1, 1], a0 * 0.99, rtol=1e-6)
    assert np.isclose(new_cell[2, 2], original_cell[2, 2], rtol=1e-6)


def test_monoclinic_strain():
    """Test monoclinic shear strain application."""
    atoms = bulk("Si", cubic=True)
    calculator = {'pseudopotentials': {'Si': 'Si.pbe.UPF'}}
    
    elastic = Elastic(
        atoms,
        label='test_elastic',
        calculator=calculator,
    )
    
    original_cell = atoms.get_cell()
    
    # Apply monoclinic shear strain
    strained = elastic._monoclinic_strain(original_cell, 0.01)
    new_cell = strained.get_cell()
    
    # Check that shear components are introduced
    # The cell should be modified but we check it doesn't crash
    assert strained.get_volume() > 0


def test_elastic_constants_extraction_mock():
    """Test elastic constants extraction with mock data."""
    atoms = bulk("Si", cubic=True)
    calculator = {'pseudopotentials': {'Si': 'Si.pbe.UPF'}}
    
    elastic = Elastic(
        atoms,
        label='test_elastic',
        calculator=calculator,
        crystal_system='cubic',
        strain_magnitudes=[-0.01, -0.005, 0.0, 0.005, 0.01],
    )
    
    # Generate strained structures
    elastic.generate_strained_structures()
    
    # Mock energy data (parabolic: E = E0 + a*strain^2)
    V0 = atoms.get_volume()
    E0 = -100.0  # eV
    
    # Create mock energies for different strain types
    for key in elastic.strained_structures.keys():
        parts = key.split('_')
        strain = float(parts[-1])
        
        # Different curvature for different strain types
        if 'volumetric' in key:
            a = 10.0  # eV
        elif 'uniaxial' in key:
            a = 8.0
        elif 'orthorhombic' in key:
            a = 5.0
        elif 'monoclinic' in key:
            a = 3.0
        else:
            a = 1.0
        
        energy = E0 + a * strain ** 2
        elastic.energies[key] = energy
    
    # Extract elastic constants
    elastic._extract_cubic_constants()
    
    # Check that some constants were extracted
    assert 'bulk_modulus' in elastic.elastic_constants
    assert elastic.elastic_constants['bulk_modulus'] > 0
    
    if 'C11' in elastic.elastic_constants:
        assert elastic.elastic_constants['C11'] > 0
    if 'C44' in elastic.elastic_constants:
        assert elastic.elastic_constants['C44'] > 0


def test_elastic_logger():
    """Test that the elastic workflow logger works."""
    atoms = bulk("Si", cubic=True)
    calculator = {'pseudopotentials': {'Si': 'Si.pbe.UPF'}}
    
    elastic = Elastic(
        atoms,
        label='test_elastic',
        calculator=calculator,
    )
    
    # Check that logger exists and has the logo method
    assert hasattr(elastic, 'log')
    assert hasattr(elastic.log.__class__, 'logo')


def test_elastic_workflow_import():
    """Test that Elastic can be imported from workflow module."""
    from xespresso.workflow import Elastic as ElasticImport
    
    atoms = bulk("Si", cubic=True)
    calculator = {'pseudopotentials': {'Si': 'Si.pbe.UPF'}}
    
    elastic = ElasticImport(
        atoms,
        label='test_elastic',
        calculator=calculator,
    )
    
    assert elastic is not None
    assert elastic.__class__.__name__ == 'Elastic'


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
