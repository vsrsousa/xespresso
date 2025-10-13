# Graphene Monolayer Tests

This test file demonstrates how to use `ase.build.graphene` to create graphene monolayer structures for DFT calculations with Quantum ESPRESSO through xespresso.

## Tests

### `test_graphene_structure()`
Tests the creation and setup of a graphene monolayer structure:
- Creates graphene unit cell with 2 carbon atoms
- Adds 15 Angstrom vacuum in z-direction
- Centers atoms in the cell
- Validates structure properties

This test **does not require Quantum ESPRESSO** and can be run standalone.

### `test_graphene_scf(graphene_monolayer)`
Performs a self-consistent field (SCF) calculation on graphene monolayer:
- Uses 4×4×1 k-point mesh (appropriate for 2D materials)
- Applies smearing for metallic systems
- Uses C.pbe-n-rrkjus_psl.1.0.0.UPF pseudopotential

This test **requires Quantum ESPRESSO** to be installed.

### `test_graphene_relax(graphene_monolayer)`
Performs structural relaxation on graphene monolayer:
- Optimizes atomic positions
- Uses 4×4×1 k-point mesh
- Validates final structure properties

This test **requires Quantum ESPRESSO** to be installed.

## Fixture: `graphene_monolayer`

The `graphene_monolayer` fixture in `conftest.py` provides a pre-configured graphene structure:
- 2 carbon atoms in unit cell
- 15 Angstrom vacuum in z-direction
- Atoms centered at z=7.5 Angstrom
- Periodic boundary conditions in all directions

## Usage

Run all graphene tests:
```bash
pytest tests/test_graphene.py -v
```

Run only structure test (no QE required):
```bash
pytest tests/test_graphene.py::test_graphene_structure -v
```

Run SCF test:
```bash
pytest tests/test_graphene.py::test_graphene_scf -v
```

## Expected Behavior

### Without Quantum ESPRESSO
- `test_graphene_structure()` will **PASS**
- `test_graphene_scf()` and `test_graphene_relax()` will **FAIL** with exit code 127 (command not found)

### With Quantum ESPRESSO
All tests should pass and produce reasonable energies for graphene.

## Input File Example

The test generates a Quantum ESPRESSO input file like:

```
&CONTROL
   prefix = 'graphene'
/
&SYSTEM
   ecutwfc = 30
   occupations = 'smearing'
   degauss = 0.03
   ntyp = 1
   nat = 2
/
...
ATOMIC_SPECIES
C 12.011 C.pbe-n-rrkjus_psl.1.0.0.UPF

K_POINTS automatic
4 4 1  0 0 0

CELL_PARAMETERS angstrom
2.46000000000000 0.00000000000000 0.00000000000000
-1.23000000000000 2.13042249330972 0.00000000000000
0.00000000000000 0.00000000000000 15.00000000000000

ATOMIC_POSITIONS angstrom
C 0.0000000000 0.0000000000 7.5000000000 
C 1.2300000000 0.7101408311 7.5000000000
```

## Common Issues

### Issue: Missing graphene function
**Error**: `ImportError: cannot import name 'graphene' from 'ase.build'`

**Solution**: Upgrade ASE to version 3.20+ where `graphene()` was added:
```bash
pip install --upgrade ase
```

### Issue: Missing pseudopotential
**Error**: File not found for pseudopotential

**Solution**: Ensure `C.pbe-n-rrkjus_psl.1.0.0.UPF` is in the `ESPRESSO_PSEUDO` directory.

### Issue: QE not found
**Error**: `CalledProcessError: Command 'bash job_file' returned non-zero exit status 127`

**Solution**: This is expected if Quantum ESPRESSO is not installed. The structure test will still pass. To run full tests, install QE and set the `ASE_ESPRESSO_COMMAND` environment variable.
