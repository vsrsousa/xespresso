from _common_helpers import set_envs
import numpy as np


def test_graphene_structure():
    """Test graphene structure creation from ase.build.graphene"""
    from ase.build import graphene
    
    # Create graphene monolayer
    atoms = graphene()
    
    # Verify basic structure
    assert len(atoms) == 2, "Graphene unit cell should have 2 atoms"
    assert all(atoms.get_chemical_symbols() == np.array(["C", "C"])), "Both atoms should be Carbon"
    assert atoms.pbc[0] and atoms.pbc[1], "Graphene should be periodic in x and y"
    assert not atoms.pbc[2], "Graphene should not be periodic in z initially"
    
    # Add vacuum in z-direction
    atoms.cell[2, 2] = 15.0
    atoms.center(axis=2)
    
    # Verify cell setup
    assert atoms.cell[2, 2] == 15.0, "Cell should have 15 Angstrom vacuum"
    assert np.allclose(atoms.positions[:, 2], 7.5), "Atoms should be centered at z=7.5"


def test_graphene_scf(graphene_monolayer):
    """Test graphene monolayer SCF calculation using ase.build.graphene"""
    from xespresso import Espresso

    set_envs()
    
    # Use fixture
    atoms = graphene_monolayer
    
    # Define pseudopotentials
    pseudopotentials = {
        "C": "C.pbe-n-rrkjus_psl.1.0.0.UPF",
    }
    
    # Create calculator with basic settings
    calc = Espresso(
        pseudopotentials=pseudopotentials,
        label="calculations/scf/graphene",
        ecutwfc=30,
        occupations="smearing",
        degauss=0.03,
        kpts=(4, 4, 1),
        debug=True,
    )
    
    atoms.calc = calc
    e = atoms.get_potential_energy()
    print("Energy: {0:1.4f}".format(e))
    
    # Check that energy is reasonable (negative for stable structure)
    assert e < 0, "Energy should be negative for stable structure"
    assert np.isfinite(e), "Energy should be finite"


def test_graphene_relax(graphene_monolayer):
    """Test graphene monolayer relaxation"""
    from xespresso import Espresso

    set_envs()
    
    # Use fixture
    atoms = graphene_monolayer
    
    pseudopotentials = {"C": "C.pbe-n-rrkjus_psl.1.0.0.UPF"}
    
    calc = Espresso(
        label="calculations/relax/graphene",
        pseudopotentials=pseudopotentials,
        calculation="relax",
        ecutwfc=30,
        kpts=(4, 4, 1),
        debug=True,
    )
    
    atoms.calc = calc
    e = atoms.get_potential_energy()
    print("Energy = {0:1.4f} eV".format(e))
    
    # Verify structure properties
    assert len(atoms) == 2, "Graphene unit cell should have 2 atoms"
    assert all(atoms.get_chemical_symbols() == np.array(["C", "C"])), "Both atoms should be Carbon"
    assert e < 0, "Energy should be negative"
    assert np.isfinite(e), "Energy should be finite"
