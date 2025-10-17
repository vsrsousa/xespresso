import os
from ase.geometry import get_layers
from ase.constraints import FixAtoms
from ase.io.espresso import construct_namelist
from xespresso import Espresso
from xespresso.xio import build_atomic_species_str
from ase.dft.bandgap import bandgap
import pickle
import multiprocessing
import numpy as np

# ====================================================
# Magnetic configuration helpers
# ====================================================


def set_magnetic_moments(atoms, magnetic_moments, pseudopotentials=None):
    """
    Simplified way to set up magnetic moments for spin-polarized calculations.
    
    Automatically creates species labels and input_ntyp dictionary for 
    starting_magnetization based on the provided magnetic moments.
    
    Parameters
    ----------
    atoms : ase.Atoms
        The atomic structure
    magnetic_moments : list, dict, or array
        Magnetic moments for each atom. Can be:
        - list/array: magnetic moment for each atom in order
        - dict: {atom_index: magnetic_moment} for specific atoms
    pseudopotentials : dict, optional
        Existing pseudopotentials dict. If provided, it will be updated
        with new species labels. Otherwise, returns the species mapping.
    
    Returns
    -------
    dict
        A dictionary containing:
        - 'input_ntyp': dict with starting_magnetization
        - 'pseudopotentials': dict mapping species to pseudopotential files
        - 'species_map': dict mapping species labels to their base element symbols
                         (e.g., {'Fe': 'Fe', 'Fe1': 'Fe'})
    
    Examples
    --------
    # Example 1: Simple antiferromagnetic Fe
    >>> from ase.build import bulk
    >>> from xespresso import Espresso
    >>> atoms = bulk('Fe', cubic=True)
    >>> mag_config = set_magnetic_moments(atoms, [1.0, -1.0])
    >>> calc = Espresso(
    ...     pseudopotentials=mag_config['pseudopotentials'],
    ...     input_data={'input_ntyp': mag_config['input_ntyp']},
    ...     nspin=2
    ... )
    
    # Example 2: Specific atoms with magnetic moments
    >>> atoms = bulk('Fe', cubic=True) * (2, 2, 1)
    >>> mag_config = set_magnetic_moments(atoms, {0: 1.0, 1: -1.0, 2: -1.0, 3: 1.0})
    """
    # Ensure species array exists
    if 'species' not in atoms.arrays:
        atoms.new_array('species', np.array(atoms.get_chemical_symbols(), dtype='U20'))
    
    # Convert magnetic_moments to dict format
    if isinstance(magnetic_moments, (list, np.ndarray)):
        mag_dict = {i: mag for i, mag in enumerate(magnetic_moments)}
    else:
        mag_dict = magnetic_moments
    
    # Group atoms by (symbol, magnetic_moment)
    species_groups = {}
    species_counter = {}
    
    for i in range(len(atoms)):
        symbol = atoms[i].symbol
        mag = mag_dict.get(i, 0.0)
        
        key = (symbol, mag)
        if key not in species_groups:
            # Count how many species of this element we already have
            if symbol not in species_counter:
                species_counter[symbol] = 0
                species_label = symbol
            else:
                species_counter[symbol] += 1
                species_label = f"{symbol}{species_counter[symbol]}"
            species_groups[key] = species_label
        
        # Assign species label to atom
        atoms.arrays['species'][i] = species_groups[key]
    
    # Create input_ntyp dictionary for starting_magnetization
    input_ntyp = {'starting_magnetization': {}}
    species_map = {}
    
    for (symbol, mag), species_label in species_groups.items():
        if mag != 0.0:
            input_ntyp['starting_magnetization'][species_label] = mag
        # Map species_label back to base element symbol
        species_map[species_label] = symbol
    
    # Handle pseudopotentials
    if pseudopotentials is None:
        # Return template that user should fill
        pseudo_dict = {}
        for species_label in species_groups.values():
            # Get the base element symbol
            base_symbol = ''.join([c for c in species_label if not c.isdigit()])
            pseudo_dict[species_label] = f"{base_symbol}.UPF"
    else:
        # Update existing pseudopotentials
        pseudo_dict = pseudopotentials.copy()
        for (symbol, mag), species_label in species_groups.items():
            if species_label not in pseudo_dict:
                # Try to find pseudopotential for base element
                base_pseudo = pseudopotentials.get(symbol)
                if base_pseudo:
                    pseudo_dict[species_label] = base_pseudo
                else:
                    pseudo_dict[species_label] = f"{symbol}.UPF"
    
    return {
        'input_ntyp': input_ntyp,
        'pseudopotentials': pseudo_dict,
        'species_map': species_map
    }


def set_antiferromagnetic(atoms, sublattice_indices, magnetic_moment=1.0, pseudopotentials=None):
    """
    Simplified way to set up antiferromagnetic configurations.
    
    Divides atoms into two sublattices with opposite magnetic moments.
    
    Parameters
    ----------
    atoms : ase.Atoms
        The atomic structure
    sublattice_indices : list of lists
        Two sublattices: [sublattice_A_indices, sublattice_B_indices]
        Example: [[0, 2], [1, 3]] for 4 atoms in checkerboard AFM
    magnetic_moment : float, default=1.0
        Magnitude of magnetic moment (absolute value)
    pseudopotentials : dict, optional
        Existing pseudopotentials dict
    
    Returns
    -------
    dict
        Same as set_magnetic_moments: input_ntyp, pseudopotentials, species_map
    
    Examples
    --------
    # Simple AFM with alternating spins
    >>> from ase.build import bulk
    >>> from xespresso import Espresso
    >>> atoms = bulk('Fe', cubic=True)
    >>> afm_config = set_antiferromagnetic(atoms, [[0], [1]])
    >>> calc = Espresso(
    ...     pseudopotentials=afm_config['pseudopotentials'],
    ...     input_data={'input_ntyp': afm_config['input_ntyp']},
    ...     nspin=2
    ... )
    """
    if len(sublattice_indices) != 2:
        raise ValueError("sublattice_indices must contain exactly 2 sublattices")
    
    # Create magnetic moments array
    mag_dict = {}
    for idx in sublattice_indices[0]:
        mag_dict[idx] = magnetic_moment
    for idx in sublattice_indices[1]:
        mag_dict[idx] = -magnetic_moment
    
    return set_magnetic_moments(atoms, mag_dict, pseudopotentials)


def set_ferromagnetic(atoms, magnetic_moment=1.0, element=None, pseudopotentials=None):
    """
    Simplified way to set up ferromagnetic configurations.
    
    Sets all atoms (or all atoms of a specific element) to the same magnetic moment.
    
    Parameters
    ----------
    atoms : ase.Atoms
        The atomic structure
    magnetic_moment : float, default=1.0
        Magnetic moment for all atoms
    element : str, optional
        If specified, only set magnetic moment for atoms of this element
    pseudopotentials : dict, optional
        Existing pseudopotentials dict
    
    Returns
    -------
    dict
        Same as set_magnetic_moments: input_ntyp, pseudopotentials, species_map
    
    Examples
    --------
    # Ferromagnetic Fe
    >>> from ase.build import bulk
    >>> from xespresso import Espresso
    >>> atoms = bulk('Fe', cubic=True)
    >>> fm_config = set_ferromagnetic(atoms, magnetic_moment=2.0)
    >>> calc = Espresso(
    ...     pseudopotentials=fm_config['pseudopotentials'],
    ...     input_data={'input_ntyp': fm_config['input_ntyp']},
    ...     nspin=2
    ... )
    """
    mag_dict = {}
    for i, atom in enumerate(atoms):
        if element is None or atom.symbol == element:
            mag_dict[i] = magnetic_moment
    
    return set_magnetic_moments(atoms, mag_dict, pseudopotentials)


# ====================================================


def get_nbnd(atoms=None, scale=1.2, pseudopotentials={}, nspin=1, input_data={}):
    input_parameters = construct_namelist(input_data)
    atomic_species_str, species_info, total_valence = build_atomic_species_str(
        atoms, input_parameters, pseudopotentials
    )
    nbnd = int(total_valence / (2.0 / nspin))
    nbnd_scale = int(nbnd * scale)
    print(
        " total valence: %s\n nbnd: %s\n scaled nbnd: %s"
        % (total_valence, nbnd, nbnd_scale)
    )
    return nbnd


def merge_slab(slab1, slab2, index=2):
    """ """
    slab2.cell[index] = slab1.cell[index]
    slab2.set_cell(slab1.cell, scale_atoms=True)
    slab1 = slab1 + slab2
    slab1.cell[2][2] = max(slab1.positions[:, 2] + 15)
    slab1.wrap()
    return slab1


def qeinp(
    calculation,
    ecutwfc=30,
    mixing_beta=0.5,
    conv_thr=1.0e-8,
    edir=False,
    input_ntyp={},
    atoms=None,
):
    #
    inp = {
        # control
        "calculation": calculation,
        "max_seconds": 78000,
        "verbosity": "high",
        "tprnfor": True,
        # system
        "ecutwfc": ecutwfc,
        "ecutrho": ecutwfc * 8,
        "occupations": "smearing",
        "degauss": 0.01,
        "input_ntyp": input_ntyp,
        # electrons
        "mixing_beta": mixing_beta,
        "conv_thr": conv_thr,
        "electron_maxstep": 400,
    }
    #
    if edir:
        inp.update(dipole_correction(atoms, edir))

    return inp


def dipole_correction(atoms, edir=3):
    inp = {
        "dipfield": True,
        "tefield": True,
        "edir": edir,
        "eamp": 0.001,
        "eopreg": 0.05,
    }
    emaxpos = (
        max(atoms.positions[:, edir - 1] + atoms.cell[edir - 1][edir - 1])
        / 2.0
        / atoms.cell[edir - 1][edir - 1]
    )
    inp["emaxpos"] = round(emaxpos, 2)
    return inp


# tools


def build_oer(atoms):
    """ """
    from ase.atoms import Atoms

    # ----------------------------------
    ooh = Atoms("O2H", positions=[[0, 0, 0], [1.4, 0, 0], [1.4, 0, 1.0]])
    ooh.rotate("z", np.pi / 4)
    mols = {
        "o": Atoms("O"),
        "oh": Atoms("OH", positions=[[0, 0, 0], [0, 0, 1.0]]),
        "ooh": ooh,
    }
    #
    jobs = {}
    maxz = max(atoms.positions[:, 2])
    indm = [atom.index for atom in atoms if atom.z > maxz - 1.0 and atom.symbol != "O"][
        0
    ]
    for job, mol in mols.items():
        # print(job, mol)
        ads = mol.copy()
        natoms = atoms.copy()
        ads.translate(atoms[indm].position - ads[0].position + [0, 0, 1.9])
        natoms = natoms + ads
        jobs[job] = natoms
    return jobs


def fix_layers(atoms, miller=(0, 0, 1), tol=1.0, n=[0, 4]):
    """ """
    layers = get_layers(atoms, miller, tol)[0]
    index = [j for j in range(len(atoms)) if layers[j] in range(n[0], n[1])]
    constraint = FixAtoms(indices=index)
    atoms.set_constraint(constraint)
    return atoms


def mypool(jobs, func, showInfo=False):
    """ """
    from random import random
    from time import sleep

    pool = multiprocessing.Pool(len(jobs))
    results = []
    images = []
    for job, atoms in jobs.items():
        if showInfo:
            print(job, len(atoms), atoms)
        sleep(random() * 2)
        results.append(pool.apply_async(func, (job, atoms)))
    for r in results:
        r.get()
    pool.close()
    pool.join()


def dwubelix(updates=[]):
    file = "pw err out dos pdos projwfc int xyz path a.xml txt png"
    print("Downloading.....")
    cwd = os.getcwd()
    for update in updates:
        os.chdir(update)
        os.system("dwubelix-sc.py %s" % file)
        os.chdir(cwd)
    print("Finished")


def ana(dire, calc):
    atoms = calc.results["atoms"]
    results = [dire, atoms, atoms.cell, atoms.positions]
    for prop in ["energy", "forces", "stress", "magmoms"]:
        if prop in calc.results:
            prop = calc.results[prop]
        else:
            prop = None
        results.append(prop)
    return results


# tools


def summary(updates=[], prefix="datas"):
    import pandas as pd

    columns = ["label", "atoms", "cell", "positions", "energy", "forces", "stress"]
    file = "%s.pickle" % prefix
    db = "%s.db" % prefix
    if os.path.exists(file):
        with open(file, "rb") as f:
            datas, df = pickle.load(f)
    else:
        datas = {}
        df = pd.DataFrame(columns=columns)
    calc = Espresso()
    print("Reading.....")
    for update in updates:
        cwd = os.getcwd()
        for i, j, y in os.walk(update):
            output = is_espresso(i)
            if output:
                os.chdir(i)
                print("=" * 30)
                print("Reading dire:", i)
                calc.directory = cwd + "/" + i
                calc.prefix = output[0:-4]
                try:
                    calc.results = {}
                    calc.read_results()
                    datas[i] = calc.results
                    atoms = calc.results["atoms"]
                    atoms.write(os.path.join(calc.directory, "%s.cif" % calc.prefix))
                except Exception as e:
                    print("error: %s \n" % e)
            os.chdir(cwd)
    with open(file, "wb") as f:
        pickle.dump([datas, df], f)
    print("Finished")


def is_espresso(path):
    """
    check espresso
    """
    dirs = os.listdir(path)
    # print(dirs)
    # flag = True

    for qefile in [".pwi"]:
        flag = False
        for file in dirs:
            if qefile in file:
                return file
        if not flag:
            return False
    # return flag


def grep_valence_configuration(pseudopotential):
    """
    Given a UPF pseudopotential file, find the valence configuration.

    Valence configuration:
    nl pn  l   occ       Rcut    Rcut US       E pseu
    3S  1  0  2.00      0.700      1.200    -6.910117

    """
    orbitals = ["S", "P", "D", "F"]
    valence = {}
    with open(pseudopotential) as psfile:
        lines = psfile.readlines()
        for i in range(len(lines)):
            if "valence configuration:" in lines[i].lower():
                j = i + 2
                ob = lines[j].split()[0]
                while ob[1] in orbitals:
                    valence[ob] = lines[j].split()[3]
                    j += 1
                    ob = lines[j].split()[0]
                return valence
    if not valence:
        raise ValueError("Valence configuration missing in {}".format(pseudopotential))
