# GUI Calculation Button Implementation

## Summary

Implemented a "Run Calculation" button in the xespresso GUI that properly wraps xespresso functionality, allowing users to run Quantum ESPRESSO calculations directly from the GUI without needing pre-existing input files.

## Problem Statement Addressed

The user requested:
1. ✅ A button to run calculations
2. ✅ The button should activate `calc.get_potential_energy()` and not depend on input files
3. ✅ The GUI should create an Espresso instance and store information
4. ✅ The GUI should create an ASE atom object from the structure
5. ✅ All parameters should be passed to the calculator
6. ✅ Keep the dry run functionality for those who want to create input files first
7. ✅ The GUI must act as a wrapper for xespresso functions

## Implementation Details

### Files Modified

1. **`xespresso/gui/pages/calculation_setup.py`** (NEW: 640 lines)
   - Comprehensive calculation setup page with two tabs:
     - **Configuration Tab**: Configure all calculation parameters
     - **Run Calculation Tab**: Execute calculations or generate files

2. **`xespresso/gui/streamlit_app.py`** (MODIFIED: -366 lines)
   - Replaced 370+ lines of inline calculation setup code
   - Now calls modular `render_calculation_setup_page()`

### Key Features Implemented

#### 1. Configuration Tab
Users can configure:
- Calculation type (SCF, Relax, VC-Relax, Bands, DOS, NSCF)
- Pseudopotentials (manual entry or load from config)
- Energy cutoffs (ecutwfc, ecutrho, dual parameter)
- Convergence threshold
- Electronic occupations (smearing type, degauss)
- K-point sampling (k-spacing or Monkhorst-Pack grid)
- Spin polarization (nspin)

All configuration is stored in `st.session_state.workflow_config` and persists across page visits.

#### 2. Run Calculation Tab

Two buttons are provided:

**🚀 Run Calculation Button**:
```python
def run_calculation(atoms, config, label):
    """
    Executes calculation using xespresso's standard workflow:
    1. Creates Espresso calculator with all parameters from GUI
    2. Sets calculator on atoms object
    3. Calls atoms.get_potential_energy() to run calculation
    """
    # Build input_data and calc_params from config
    calc = Espresso(**calc_params)
    atoms.calc = calc
    energy = atoms.get_potential_energy()  # Automatically generates files and runs!
```

**🧪 Generate Files (Dry Run) Button**:
```python
def generate_input_files(atoms, config, label):
    """
    Generates input files without running:
    1. Creates Espresso calculator with parameters from GUI
    2. Calls calc.write_input(atoms) to generate files
    """
    calc = Espresso(**calc_params)
    calc.write_input(atoms)  # Only generates files, doesn't run
```

### Workflow Comparison

**Before (Problematic)**:
1. User configures parameters in GUI
2. User generates input files (dry run)
3. User goes to Job Submission page
4. User selects input files from folder
5. Job Submission reads files and creates calculator from them
6. Runs calculation

**After (Correct)**:
1. User configures parameters in GUI
2. User clicks "Run Calculation" button
3. GUI creates calculator directly from configuration
4. Runs with `atoms.get_potential_energy()`
5. Done!

OR (if user wants to review files):
1. User configures parameters in GUI
2. User clicks "Generate Files (Dry Run)"
3. Files are created for review
4. User can manually run later if desired

### Example Usage Flow

#### Example 1: Direct Calculation

```
Structure Viewer Page:
  → Load structure (creates ASE Atoms object)

Calculation Setup Page:
  → Configuration Tab:
    - Select calculation type: SCF
    - Set pseudopotentials: Fe.pbe-spn-rrkjus_psl.1.0.0.UPF
    - Set ecutwfc: 40 Ry
    - Set kpts: 6×6×6
    - Configure other parameters
  
  → Run Calculation Tab:
    - Click "Run Calculation"
    - Calculator created from GUI parameters
    - Calculation runs with get_potential_energy()
    - Results displayed
```

#### Example 2: Dry Run First

```
Structure Viewer Page:
  → Load structure

Calculation Setup Page:
  → Configuration Tab:
    - Configure all parameters
  
  → Run Calculation Tab:
    - Click "Generate Files (Dry Run)"
    - Input files created in specified directory
    - User can review/edit files
    - Later: Click "Run Calculation" to execute
```

### Code Structure

```python
render_calculation_setup_page()
    ├── render_configuration_section()
    │   ├── Calculation type selector
    │   ├── Pseudopotential configuration
    │   ├── Calculation parameters
    │   ├── Electronic occupations
    │   ├── K-point sampling
    │   └── Spin polarization
    │
    └── render_run_calculation_section()
        ├── Configuration summary display
        ├── Working directory selection
        ├── Label/path configuration
        ├── run_calculation() button
        └── generate_input_files() button
```

### Security Features

- Path validation prevents directory traversal attacks
- Only allows directories under home or /tmp
- Input sanitization on all user inputs
- Safe file path handling with `os.path.realpath()`

### Compatibility

The implementation maintains backward compatibility:
- Job Submission page still works for running existing input files
- Dry run functionality preserved for users who prefer it
- Session state used for configuration persistence
- No breaking changes to existing workflows

## Testing

Created test scripts demonstrating:
1. ✅ Module imports work correctly
2. ✅ Workflow matches xespresso examples (ex01-scf.py)
3. ✅ Calculator can be created from GUI parameters
4. ✅ No dependency on pre-existing input files

## Conclusion

The GUI now properly wraps xespresso functionality:
- Creates Espresso calculator from GUI parameters (not from files)
- Creates ASE Atoms object from GUI structure
- Runs calculations with `get_potential_energy()` (xespresso handles file generation)
- Provides optional dry run for those who want to review files first
- Follows the same workflow as xespresso command-line examples

This makes the GUI a true wrapper for xespresso functions, as requested.
