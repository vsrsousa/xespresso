from _common_helpers import set_envs
import numpy as np


def test_graphene_scf():
    """Test graphene monolayer using ase.build.graphene"""
    from ase.build import graphene
    from xespresso import Espresso

    set_envs()
    
    # Create graphene monolayer
    atoms = graphene()
    
    # Add vacuum in z-direction for 2D material (15 Angstrom)
    atoms.cell[2, 2] = 15.0
    atoms.center(axis=2)
    
    # Set all directions as periodic (standard for plane wave calculations)
    atoms.pbc = [True, True, True]
    
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


def test_graphene_relax():
    """Test graphene monolayer relaxation"""
    from ase.build import graphene
    from xespresso import Espresso

    set_envs()
    
    # Create graphene monolayer
    atoms = graphene()
    
    # Add vacuum in z-direction for 2D material
    atoms.cell[2, 2] = 15.0
    atoms.center(axis=2)
    atoms.pbc = [True, True, True]
    
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
