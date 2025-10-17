"""
Tests for magnetic configuration helper functions.

These tests verify the new simplified API for setting up magnetic moments
for spin-polarized and antiferromagnetic calculations.
"""

import pytest
import numpy as np
from ase.build import bulk
from xespresso.tools import (
    set_magnetic_moments,
    set_antiferromagnetic,
    set_ferromagnetic
)


class TestSetMagneticMoments:
    """Tests for set_magnetic_moments function."""
    
    def test_simple_afm_list(self):
        """Test simple AFM configuration with list of magnetic moments."""
        atoms = bulk('Fe', cubic=True)
        
        mag_config = set_magnetic_moments(atoms, [1.0, -1.0])
        
        # Check that species were created
        assert 'species' in atoms.arrays
        assert len(set(atoms.arrays['species'])) == 2  # Two different species
        
        # Check input_ntyp structure
        assert 'input_ntyp' in mag_config
        assert 'starting_magnetization' in mag_config['input_ntyp']
        
        # Check that we have two species with opposite magnetization
        mag_dict = mag_config['input_ntyp']['starting_magnetization']
        assert len(mag_dict) == 2
        values = list(mag_dict.values())
        assert 1.0 in values
        assert -1.0 in values
        
        # Check pseudopotentials
        assert 'pseudopotentials' in mag_config
        assert len(mag_config['pseudopotentials']) == 2
    
    def test_afm_with_dict(self):
        """Test AFM configuration with dictionary of magnetic moments."""
        atoms = bulk('Fe', cubic=True)
        
        mag_config = set_magnetic_moments(atoms, {0: 1.0, 1: -1.0})
        
        # Check input_ntyp
        mag_dict = mag_config['input_ntyp']['starting_magnetization']
        assert len(mag_dict) == 2
        assert 1.0 in mag_dict.values()
        assert -1.0 in mag_dict.values()
    
    def test_mixed_elements(self):
        """Test with multiple elements."""
        from ase import Atoms
        atoms = Atoms('Fe2O', positions=[[0, 0, 0], [1.5, 0, 0], [0, 1.5, 0]])
        atoms.cell = [5, 5, 5]
        
        # Set magnetic moments only on Fe atoms
        mag_config = set_magnetic_moments(atoms, {0: 1.0, 1: -1.0, 2: 0.0})
        
        # Check that we have Fe and Fe1 species with magnetization
        mag_dict = mag_config['input_ntyp']['starting_magnetization']
        assert len(mag_dict) == 2  # Only Fe atoms with non-zero magnetization
    
    def test_with_pseudopotentials(self):
        """Test with existing pseudopotentials."""
        atoms = bulk('Fe', cubic=True)
        existing_pseudo = {'Fe': 'Fe.pbe-spn-rrkjus_psl.1.0.0.UPF'}
        
        mag_config = set_magnetic_moments(
            atoms, 
            [1.0, -1.0],
            pseudopotentials=existing_pseudo
        )
        
        # Check that pseudopotentials are updated correctly
        pseudo = mag_config['pseudopotentials']
        assert 'Fe' in pseudo
        assert 'Fe1' in pseudo
        # Both should use the same pseudopotential file
        assert pseudo['Fe'] == 'Fe.pbe-spn-rrkjus_psl.1.0.0.UPF'
        assert pseudo['Fe1'] == 'Fe.pbe-spn-rrkjus_psl.1.0.0.UPF'
    
    def test_zero_magnetic_moments(self):
        """Test atoms with zero magnetic moments are not included."""
        atoms = bulk('Fe', cubic=True) * (2, 1, 1)
        
        # Only first two atoms have magnetic moments
        mag_config = set_magnetic_moments(atoms, {0: 1.0, 1: -1.0, 2: 0.0, 3: 0.0})
        
        # Only non-zero magnetic moments should be in starting_magnetization
        mag_dict = mag_config['input_ntyp']['starting_magnetization']
        assert len(mag_dict) == 2


class TestSetAntiferromagnetic:
    """Tests for set_antiferromagnetic function."""
    
    def test_simple_afm(self):
        """Test simple antiferromagnetic configuration."""
        atoms = bulk('Fe', cubic=True)
        
        afm_config = set_antiferromagnetic(atoms, [[0], [1]])
        
        # Check magnetization
        mag_dict = afm_config['input_ntyp']['starting_magnetization']
        assert len(mag_dict) == 2
        values = list(mag_dict.values())
        assert 1.0 in values
        assert -1.0 in values
    
    def test_custom_magnetic_moment(self):
        """Test AFM with custom magnetic moment magnitude."""
        atoms = bulk('Fe', cubic=True)
        
        afm_config = set_antiferromagnetic(atoms, [[0], [1]], magnetic_moment=2.5)
        
        # Check magnetization magnitude
        mag_dict = afm_config['input_ntyp']['starting_magnetization']
        values = list(mag_dict.values())
        assert 2.5 in values
        assert -2.5 in values
    
    def test_larger_system(self):
        """Test AFM in larger system with multiple sublattices."""
        atoms = bulk('Fe', cubic=True) * (2, 2, 1)
        
        # Checkerboard AFM pattern
        afm_config = set_antiferromagnetic(
            atoms, 
            [[0, 3], [1, 2]],
            magnetic_moment=1.0
        )
        
        # Should have two species
        mag_dict = afm_config['input_ntyp']['starting_magnetization']
        assert len(mag_dict) == 2
    
    def test_invalid_sublattices(self):
        """Test that error is raised for invalid sublattice count."""
        atoms = bulk('Fe', cubic=True)
        
        with pytest.raises(ValueError, match="exactly 2 sublattices"):
            set_antiferromagnetic(atoms, [[0]])
        
        with pytest.raises(ValueError, match="exactly 2 sublattices"):
            set_antiferromagnetic(atoms, [[0], [1], [2]])


class TestSetFerromagnetic:
    """Tests for set_ferromagnetic function."""
    
    def test_simple_fm(self):
        """Test simple ferromagnetic configuration."""
        atoms = bulk('Fe', cubic=True)
        
        fm_config = set_ferromagnetic(atoms, magnetic_moment=2.0)
        
        # All atoms should have same magnetization
        mag_dict = fm_config['input_ntyp']['starting_magnetization']
        assert len(mag_dict) == 1  # Only one species
        assert list(mag_dict.values())[0] == 2.0
    
    def test_element_specific(self):
        """Test ferromagnetic configuration for specific element."""
        from ase import Atoms
        atoms = Atoms('Fe2O', positions=[[0, 0, 0], [1.5, 0, 0], [0, 1.5, 0]])
        atoms.cell = [5, 5, 5]
        
        # Only set magnetization for Fe
        fm_config = set_ferromagnetic(atoms, magnetic_moment=2.0, element='Fe')
        
        # Only Fe atoms should have magnetization
        mag_dict = fm_config['input_ntyp']['starting_magnetization']
        assert len(mag_dict) == 1
        assert list(mag_dict.values())[0] == 2.0
        
        # O should not have magnetization in input_ntyp
        species_with_mag = list(mag_dict.keys())
        assert all('Fe' in sp for sp in species_with_mag)


class TestIntegrationWithEspresso:
    """Integration tests to ensure helpers work with Espresso calculator."""
    
    def test_afm_fe_integration(self):
        """Test that AFM configuration works with Espresso calculator setup."""
        atoms = bulk('Fe', cubic=True)
        
        # Use helper function
        mag_config = set_antiferromagnetic(atoms, [[0], [1]], magnetic_moment=1.0)
        
        # Add actual pseudopotential names
        mag_config['pseudopotentials']['Fe'] = 'Fe.pbe-spn-rrkjus_psl.1.0.0.UPF'
        mag_config['pseudopotentials']['Fe1'] = 'Fe.pbe-spn-rrkjus_psl.1.0.0.UPF'
        
        # Check that the configuration is correct
        assert 'input_ntyp' in mag_config
        assert 'starting_magnetization' in mag_config['input_ntyp']
        assert 'Fe' in mag_config['pseudopotentials']
        assert 'Fe1' in mag_config['pseudopotentials']
        
        # Check magnetization values
        mag_dict = mag_config['input_ntyp']['starting_magnetization']
        assert len(mag_dict) == 2
        values = list(mag_dict.values())
        assert 1.0 in values
        assert -1.0 in values
    
    def test_comparison_with_old_method(self):
        """Compare new helper with old manual method."""
        atoms_old = bulk('Fe', cubic=True)
        atoms_new = bulk('Fe', cubic=True)
        
        # Old method (manual)
        atoms_old.new_array('species', np.array(atoms_old.get_chemical_symbols(), dtype='U20'))
        atoms_old.arrays['species'][0] = 'Fe'
        atoms_old.arrays['species'][1] = 'Fe1'
        input_ntyp_old = {
            'starting_magnetization': {
                'Fe': 1.0,
                'Fe1': -1.0,
            }
        }
        
        # New method (helper)
        mag_config = set_magnetic_moments(atoms_new, [1.0, -1.0])
        
        # Both should have same number of species
        assert len(set(atoms_old.arrays['species'])) == len(set(atoms_new.arrays['species']))
        
        # Both should have same magnetization values
        old_mags = set(input_ntyp_old['starting_magnetization'].values())
        new_mags = set(mag_config['input_ntyp']['starting_magnetization'].values())
        assert old_mags == new_mags


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
