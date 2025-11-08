# GUI Visual Structure - Calculation Setup Page

## Page Layout

```
┌─────────────────────────────────────────────────────────────────────┐
│                    📊 Calculation Setup                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  Configure your calculation parameters and run calculations using    │
│  xespresso.                                                          │
│                                                                       │
│  Workflow:                                                           │
│  1. Configure calculation parameters below                           │
│  2. Choose to either:                                                │
│     - Run Calculation: Creates calculator and runs with              │
│       calc.get_potential_energy()                                    │
│     - Generate Files (Dry Run): Creates calculator and generates     │
│       input files with calc.write_input()                            │
│                                                                       │
├─────────────────────────────────────────────────────────────────────┤
│  ✅ Working with: Fe (1 atoms)                                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌──────────────────────┬────────────────────────────────────────┐  │
│  │  ⚙️ Configuration    │  🚀 Run Calculation                    │  │
│  └──────────────────────┴────────────────────────────────────────┘  │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

## Configuration Tab

```
┌─────────────────────────────────────────────────────────────────────┐
│  Calculation Type                                                     │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │ SCF (Self-Consistent Field)                                  ▼│    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                       │
├─────────────────────────────────────────────────────────────────────┤
│  Pseudopotentials                                                     │
│  Elements in structure: Fe                                            │
│                                                                       │
│  Pseudopotential Selection:                                          │
│  ○ Manual Entry    ● Load Configuration                              │
│                                                                       │
│  Fe: ┌──────────────────────────────────────────────────────────┐   │
│      │ Fe.pbe-n-kjpaw_psl.1.0.0.UPF                              │   │
│      └──────────────────────────────────────────────────────────┘   │
│                                                                       │
├─────────────────────────────────────────────────────────────────────┤
│  Calculation Parameters                                               │
│                                                                       │
│  ┌──────────────────────────────┬──────────────────────────────┐    │
│  │ Kinetic Energy Cutoff        │ Charge Density Cutoff        │    │
│  │ (ecutwfc) [Ry]               │ (ecutrho) [Ry]               │    │
│  │ ┌────────────────┐           │ ┌────────────────┐           │    │
│  │ │ 50.0          ││           │ │ 200.0         ││ (disabled) │    │
│  │ └────────────────┘           │ └────────────────┘           │    │
│  │                               │                               │    │
│  │ Dual Parameter                │                               │    │
│  │ ┌────────────────┐           │                               │    │
│  │ │ 4.0           ││           │                               │    │
│  │ └────────────────┘           │                               │    │
│  │                               │                               │    │
│  │ Convergence Threshold         │                               │    │
│  │ ┌────────────────┐           │                               │    │
│  │ │ 1.0e-06       ││           │                               │    │
│  │ └────────────────┘           │                               │    │
│  └──────────────────────────────┴──────────────────────────────┘    │
│                                                                       │
├─────────────────────────────────────────────────────────────────────┤
│  Electronic Occupations                                               │
│                                                                       │
│  ┌──────────────────────────────┬──────────────────────────────┐    │
│  │ Occupation Type              │ Smearing Type                │    │
│  │ ┌────────────────┐           │ ┌────────────────┐           │    │
│  │ │ smearing      ▼│           │ │ gaussian      ▼│           │    │
│  │ └────────────────┘           │ └────────────────┘           │    │
│  │                               │                               │    │
│  │                               │ Smearing Width (degauss)     │    │
│  │                               │ ┌────────────────┐           │    │
│  │                               │ │ 0.020         ││           │    │
│  │                               │ └────────────────┘           │    │
│  └──────────────────────────────┴──────────────────────────────┘    │
│                                                                       │
├─────────────────────────────────────────────────────────────────────┤
│  K-point Sampling                                                     │
│                                                                       │
│  K-point Method:                                                     │
│  ○ K-spacing    ● Monkhorst-Pack Grid                                │
│                                                                       │
│  ┌──────────┬──────────┬──────────┐                                 │
│  │ k₁       │ k₂       │ k₃       │                                 │
│  │ ┌──────┐ │ ┌──────┐ │ ┌──────┐ │                                 │
│  │ │  4   │ │ │  4   │ │ │  4   │ │                                 │
│  │ └──────┘ │ └──────┘ │ └──────┘ │                                 │
│  └──────────┴──────────┴──────────┘                                 │
│                                                                       │
├─────────────────────────────────────────────────────────────────────┤
│  Spin Polarization                                                    │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │ Non-spin-polarized                                           ▼│    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                       │
├─────────────────────────────────────────────────────────────────────┤
│  ✅ Configuration saved! Go to the 'Run Calculation' tab to execute. │
└─────────────────────────────────────────────────────────────────────┘
```

## Run Calculation Tab

```
┌─────────────────────────────────────────────────────────────────────┐
│  Run Calculation                                                      │
│                                                                       │
│  You can either:                                                     │
│  1. Run Calculation: Creates Espresso calculator and runs with       │
│     calc.get_potential_energy()                                      │
│  2. Generate Files (Dry Run): Creates calculator and generates       │
│     input files with calc.write_input()                              │
│                                                                       │
├─────────────────────────────────────────────────────────────────────┤
│  📋 Configuration Summary                                             │
│                                                                       │
│  ┌──────────────────────────────┬──────────────────────────────┐    │
│  │ Calculation Type: SCF        │ Pseudopotentials:            │    │
│  │ Energy Cutoff: 50 Ry         │   Fe: Fe.pbe-...UPF          │    │
│  │ K-points: 4×4×4              │                               │    │
│  └──────────────────────────────┴──────────────────────────────┘    │
│                                                                       │
├─────────────────────────────────────────────────────────────────────┤
│  📁 Working Directory                                                 │
│                                                                       │
│  Working Directory:                                                  │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │ /home/user/calculations                                      │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                       │
│  Calculation Label:                                                  │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │ scf/Fe                                                        │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                       │
│  ℹ️ Calculation will run in: `/home/user/calculations/scf/Fe`        │
│                                                                       │
├─────────────────────────────────────────────────────────────────────┤
│  🚀 Execute                                                           │
│                                                                       │
│  ┌────────────────────────────┬─────────────────────────────────┐   │
│  │  🚀 Run Calculation        │  🧪 Generate Files (Dry Run)    │   │
│  └────────────────────────────┴─────────────────────────────────┘   │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

## After Clicking "Run Calculation"

```
┌─────────────────────────────────────────────────────────────────────┐
│  ℹ️ Creating Espresso calculator with configured parameters...       │
│  ℹ️ Calculator parameters:                                            │
│     {                                                                 │
│       "pseudopotentials": {"Fe": "Fe.pbe-spn-rrkjus_psl..."},       │
│       "label": "/home/user/calculations/scf/Fe",                     │
│       "ecutwfc": 50,                                                 │
│       "ecutrho": 200,                                                │
│       "kpts": (4, 4, 4),                                             │
│       ...                                                            │
│     }                                                                 │
│                                                                       │
│  ℹ️ Running calculation with calc.get_potential_energy()...          │
│  ℹ️ This will automatically generate input files and run the         │
│     calculation.                                                     │
│                                                                       │
│  ⏳ Running calculation... This may take a while.                     │
│                                                                       │
├─────────────────────────────────────────────────────────────────────┤
│  ✅ Calculation completed successfully!                               │
│                                                                       │
│  📊 Results                                                           │
│                                                                       │
│  ┌────────────────────────────┬─────────────────────────────────┐   │
│  │ Total Energy               │ Structure                       │   │
│  │ -3368.401000 eV            │ Fe                              │   │
│  └────────────────────────────┴─────────────────────────────────┘   │
│                                                                       │
│  📁 Output Files                                                      │
│  Calculation directory: `/home/user/calculations/scf/Fe`             │
│                                                                       │
│  Files generated:                                                    │
│    - espresso.pwi                                                    │
│    - espresso.pwo                                                    │
│    - espresso.save/                                                  │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

## Key UI Elements

### Buttons
- 🚀 **Run Calculation** (Primary, Blue): Runs calculation directly
- 🧪 **Generate Files (Dry Run)** (Secondary): Only generates files

### Status Messages
- ✅ Success messages (Green)
- ℹ️ Info messages (Blue)
- ⚠️ Warning messages (Yellow)
- ❌ Error messages (Red)

### Input Fields
- Text inputs for parameters
- Number inputs with min/max validation
- Dropdowns for selections
- Radio buttons for choices
- Sliders for ranges

### Layout
- Two-column layout for related parameters
- Expandable sections for configuration summary
- Tabs for configuration vs execution
- Clear visual hierarchy
