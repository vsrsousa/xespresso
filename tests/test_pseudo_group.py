"""Test pseudo_group parameter handling"""
import pytest
import os
import tempfile
from pathlib import Path
from ase.build import bulk
from xespresso import Espresso


class TestPseudoGroupHandling:
    """Test that pseudo_group parameter respects xespresso patterns"""
    
    def test_pseudo_group_does_not_set_pseudo_dir(self):
        """Test that using pseudo_group does NOT set pseudo_dir in parameters"""
        # Set up environment
        os.environ['ESPRESSO_PSEUDO'] = '/tmp/pseudos'
        
        atoms = bulk('Fe', 'bcc', a=2.87)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            calc = Espresso(
                label=os.path.join(tmpdir, 'test'),
                atoms=atoms,
                pseudo_group='SSSP_1.1.2_PBE_efficiency',
                input_data={'ecutwfc': 50.0}
            )
            
            # Check that pseudo_dir is NOT set in CONTROL
            pseudo_dir = calc.parameters.get('input_data', {}).get('CONTROL', {}).get('pseudo_dir')
            assert pseudo_dir is None, f"pseudo_dir should not be set, but got: {pseudo_dir}"
            
            # Check that pseudopotentials dictionary is set
            assert 'pseudopotentials' in calc.parameters
            assert 'Fe' in calc.parameters['pseudopotentials']
            assert calc.parameters['pseudopotentials']['Fe'] == 'Fe.pbe-spn-kjpaw_psl.0.2.1.UPF'
            
            # Check that pseudo_group is stored internally
            assert hasattr(calc, 'pseudo_group')
            assert calc.pseudo_group == 'SSSP_1.1.2_PBE_efficiency'
    
    def test_manual_pseudopotentials_also_no_pseudo_dir(self):
        """Test that manual pseudopotentials also don't set pseudo_dir by default"""
        os.environ['ESPRESSO_PSEUDO'] = '/tmp/pseudos'
        
        atoms = bulk('Fe', 'bcc', a=2.87)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            calc = Espresso(
                label=os.path.join(tmpdir, 'test'),
                atoms=atoms,
                pseudopotentials={'Fe': 'Fe.pbe-spn.UPF'},
                input_data={'ecutwfc': 50.0}
            )
            
            # Check that pseudo_dir is NOT set in CONTROL
            pseudo_dir = calc.parameters.get('input_data', {}).get('CONTROL', {}).get('pseudo_dir')
            assert pseudo_dir is None, f"pseudo_dir should not be set, but got: {pseudo_dir}"
    
    def test_explicit_pseudo_dir_is_respected(self):
        """Test that explicitly setting pseudo_dir still works"""
        os.environ['ESPRESSO_PSEUDO'] = '/tmp/pseudos'
        
        atoms = bulk('Fe', 'bcc', a=2.87)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            explicit_dir = '/explicit/path/to/pseudos'
            calc = Espresso(
                label=os.path.join(tmpdir, 'test'),
                atoms=atoms,
                pseudopotentials={'Fe': 'Fe.pbe-spn.UPF'},
                pseudo_dir=explicit_dir,
                input_data={'ecutwfc': 50.0}
            )
            
            # Check that explicit pseudo_dir IS set in CONTROL
            pseudo_dir = calc.parameters.get('input_data', {}).get('CONTROL', {}).get('pseudo_dir')
            assert pseudo_dir == explicit_dir, f"Expected {explicit_dir}, but got: {pseudo_dir}"
    
    def test_subdirectory_search_finds_files(self):
        """Test that pseudopotentials in subdirectories can be found"""
        from xespresso.xio import build_atomic_species_str
        from ase.io.espresso import construct_namelist
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create subdirectory structure
            pseudo_subdir = Path(tmpdir) / 'SSSP_1.1.2_PBE_efficiency'
            pseudo_subdir.mkdir(parents=True)
            
            # Create a fake pseudopotential file
            pseudo_file = pseudo_subdir / 'Fe.pbe-spn-kjpaw_psl.0.2.1.UPF'
            pseudo_file.write_text('''<UPF version="2.0.1">
<PP_HEADER
   z_valence="8.00000000000E+00"
/>
</UPF>''')
            
            # Set environment to point to parent directory
            os.environ['ESPRESSO_PSEUDO'] = str(tmpdir)
            
            # Create atoms and input parameters
            atoms = bulk('Fe', 'bcc', a=2.87)
            pseudopotentials = {'Fe': 'Fe.pbe-spn-kjpaw_psl.0.2.1.UPF'}
            input_parameters = construct_namelist(
                {'ecutwfc': 50.0},
                ecutwfc=50.0,
                ecutrho=400.0
            )
            
            # This should find the file in the subdirectory
            try:
                atomic_species_str, species_info, total_valence = build_atomic_species_str(
                    atoms, input_parameters, pseudopotentials
                )
                
                # Check that valence was extracted (meaning file was found)
                assert 'Fe' in species_info
                assert species_info['Fe']['valence'] == 8.0
                
                print("✓ Subdirectory search successfully found pseudopotential file")
            except Exception as e:
                pytest.fail(f"Failed to find pseudopotential in subdirectory: {e}")
    
    def test_comparison_with_and_without_pseudo_group(self):
        """Compare behavior with and without pseudo_group to ensure consistency"""
        os.environ['ESPRESSO_PSEUDO'] = '/tmp/pseudos'
        
        atoms = bulk('Fe', 'bcc', a=2.87)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # With pseudo_group
            calc1 = Espresso(
                label=os.path.join(tmpdir, 'test1'),
                atoms=atoms,
                pseudo_group='SSSP_1.1.2_PBE_efficiency',
                input_data={'ecutwfc': 50.0}
            )
            
            # Manual (xespresso way)
            calc2 = Espresso(
                label=os.path.join(tmpdir, 'test2'),
                atoms=atoms,
                pseudopotentials={'Fe': 'Fe.pbe-spn-kjpaw_psl.0.2.1.UPF'},
                input_data={'ecutwfc': 50.0}
            )
            
            # Both should have pseudo_dir NOT SET
            pseudo_dir1 = calc1.parameters.get('input_data', {}).get('CONTROL', {}).get('pseudo_dir')
            pseudo_dir2 = calc2.parameters.get('input_data', {}).get('CONTROL', {}).get('pseudo_dir')
            
            assert pseudo_dir1 is None, "pseudo_group should not set pseudo_dir"
            assert pseudo_dir2 is None, "manual should not set pseudo_dir"
            assert pseudo_dir1 == pseudo_dir2, "Both approaches should behave the same"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
