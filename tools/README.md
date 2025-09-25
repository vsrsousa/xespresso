# Development Tools

This directory contains utilities for development and maintenance of the xespresso codebase.

## Machine Configuration Verification

### verify_machine_consistency.py

A tool to verify consistency across all machine configuration loaders in the project.

**Usage:**
```bash
python tools/verify_machine_consistency.py
```

**What it checks:**
- Scheduler default values are consistent across all loaders
- Authentication method support is consistent (key-only, no password)
- All loaders support the same required fields (launcher, nprocs, port, etc.)
- Docstrings accurately reflect the current authentication support
- Functional testing with sample configurations

**Exit codes:**
- `0`: All checks passed, no inconsistencies found
- `1`: Inconsistencies detected or analysis failed

**When to use:**
- After making changes to any machine configuration loader
- Before committing changes to machine-related code
- As part of CI/CD pipeline to catch inconsistencies early
- When debugging machine configuration issues

This tool helped identify and fix several inconsistencies that existed across the machine configuration modules, ensuring a consistent user experience regardless of which loader is used.