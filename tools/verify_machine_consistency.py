#!/usr/bin/env python3
"""
Machine Configuration Consistency Verification Tool

This utility analyzes all machine configuration files in the xespresso project
and reports any inconsistencies between them. It can be used during development
to ensure that changes maintain consistency across all loaders.

Usage:
    python tools/verify_machine_consistency.py

The script will analyze all machine configuration loaders and report:
- Scheduler default value consistency
- Authentication method support consistency  
- Required field availability
- Functional testing with sample configurations

Exit codes:
- 0: All checks passed, no inconsistencies found
- 1: Inconsistencies detected or analysis failed
"""

import os
import ast
import json
import tempfile
import sys
from pathlib import Path

def extract_function_defaults(file_path, function_name="load_machine"):
    """Extract default values from a function definition."""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        tree = ast.parse(content)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == function_name:
                defaults = {}
                
                # Look for dictionary definitions in the function
                for stmt in ast.walk(node):
                    if isinstance(stmt, ast.Assign):
                        for target in stmt.targets:
                            if isinstance(target, ast.Name) and target.id == "queue":
                                if isinstance(stmt.value, ast.Dict):
                                    for key, value in zip(stmt.value.keys, stmt.value.values):
                                        if isinstance(key, ast.Constant):
                                            key_name = key.value
                                            if isinstance(value, ast.Call) and isinstance(value.func, ast.Attribute):
                                                if value.func.attr == "get" and len(value.args) >= 2:
                                                    if isinstance(value.args[1], ast.Constant):
                                                        defaults[key_name] = value.args[1].value
                return defaults
        return {}
    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
        return {}

def check_auth_methods(file_path):
    """Check what authentication methods are supported in the code."""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        supports_password = 'method == "password"' in content
        supports_key = 'method == "key"' in content or 'method != "key"' in content
        
        return {
            "supports_password": supports_password,
            "supports_key": supports_key
        }
    except Exception as e:
        print(f"Error checking auth methods in {file_path}: {e}")
        return {"supports_password": False, "supports_key": False}

def check_docstring_consistency(file_path):
    """Extract and check docstring information."""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        tree = ast.parse(content)
        
        # Module docstring
        docstring = ast.get_docstring(tree)
        if docstring:
            # Check for password support (but not deprecation mentions)
            password_mentions = "password" in docstring.lower() and "authentication" in docstring.lower()
            password_deprecated = "no longer supported" in docstring.lower() and "password" in docstring.lower()
            supports_password = password_mentions and not password_deprecated
            supports_key = "key" in docstring.lower() and "authentication" in docstring.lower()
            return {
                "has_docstring": True,
                "supports_password": supports_password,
                "supports_key": supports_key,
                "docstring": docstring[:200] + "..." if len(docstring) > 200 else docstring
            }
        
        return {"has_docstring": False}
    except Exception as e:
        print(f"Error checking docstring in {file_path}: {e}")
        return {"has_docstring": False}

def analyze_machine_files():
    """Main analysis function."""
    
    # Find project root (directory containing this script's parent)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    machine_files = [
        "xespresso/utils/machines/machine_config.py",
        "xespresso/utils/machines/config/loader.py", 
        "xespresso/utils/machines/config/old/loader.py"
    ]
    
    results = {}
    
    for file_rel_path in machine_files:
        file_path = project_root / file_rel_path
        if not file_path.exists():
            print(f"❌ File not found: {file_path}")
            continue
        
        print(f"\n🔍 Analyzing: {file_rel_path}")
        
        # Extract function defaults
        defaults = extract_function_defaults(str(file_path))
        
        # Check docstring
        docstring_info = check_docstring_consistency(str(file_path))
        
        # Check auth methods
        auth_info = check_auth_methods(str(file_path))
        
        results[file_rel_path] = {
            "defaults": defaults,
            "docstring": docstring_info,
            "auth": auth_info
        }
        
        print(f"  ✅ Scheduler default: {defaults.get('scheduler', 'N/A')}")
        print(f"  ✅ Auth support - Key: {auth_info['supports_key']}, Password: {auth_info['supports_password']}")
        print(f"  ✅ Docstring mentions password auth: {docstring_info.get('supports_password', False)}")
    
    return results

def find_inconsistencies(results):
    """Find and report inconsistencies."""
    print("\n🔎 INCONSISTENCY ANALYSIS")
    print("=" * 50)
    
    inconsistencies = []
    
    # Check scheduler defaults
    scheduler_defaults = {}
    for file_path, data in results.items():
        scheduler_default = data["defaults"].get("scheduler")
        if scheduler_default:
            scheduler_defaults[file_path] = scheduler_default
    
    if len(set(scheduler_defaults.values())) > 1:
        inconsistencies.append({
            "type": "scheduler_defaults",
            "description": "Different default scheduler values across files",
            "details": scheduler_defaults
        })
        print("❌ INCONSISTENCY: Scheduler defaults differ")
        for file_path, default in scheduler_defaults.items():
            print(f"  - {file_path}: '{default}'")
    else:
        print("✅ Scheduler defaults are consistent")
    
    # Check authentication support
    auth_support = {}
    for file_path, data in results.items():
        auth_info = data["auth"]
        auth_support[file_path] = {
            "key": auth_info["supports_key"],
            "password": auth_info["supports_password"]
        }
    
    password_support_files = [f for f, auth in auth_support.items() if auth["password"]]
    if password_support_files:
        inconsistencies.append({
            "type": "auth_support",
            "description": "Some files still support password authentication",
            "details": password_support_files
        })
        print("❌ INCONSISTENCY: Password authentication support")
        for file_path in password_support_files:
            print(f"  - {file_path}: supports password auth")
    else:
        print("✅ Authentication support is consistent (key-only)")
    
    # Check docstring consistency
    docstring_mentions_password = []
    for file_path, data in results.items():
        if data["docstring"].get("supports_password", False):
            docstring_mentions_password.append(file_path)
    
    if docstring_mentions_password:
        inconsistencies.append({
            "type": "docstring_auth",
            "description": "Docstrings mention password authentication",
            "details": docstring_mentions_password
        })
        print("❌ INCONSISTENCY: Docstring mentions password auth")
        for file_path in docstring_mentions_password:
            print(f"  - {file_path}: docstring mentions password")
    else:
        print("✅ Docstrings are consistent regarding authentication")
    
    return inconsistencies

def create_test_config():
    """Create a test machine configuration file."""
    test_config = {
        "machines": {
            "test_local": {
                "execution": "local",
                "scheduler": "direct",
                "workdir": "./test_dir",
                "modules": [],
                "use_modules": False,
                "prepend": ["echo 'Starting job'"],
                "postpend": ["echo 'Job finished'"],
                "resources": {},
                "launcher": "mpirun -np {nprocs}",
                "nprocs": 2
            },
            "test_remote": {
                "execution": "remote",
                "scheduler": "slurm", 
                "host": "test.example.com",
                "username": "testuser",
                "workdir": "/home/testuser/jobs",
                "auth": {
                    "method": "key",
                    "ssh_key": "~/.ssh/test_key",
                    "port": 22
                },
                "modules": ["module1", "module2"],
                "use_modules": True,
                "prepend": "module load gcc",
                "postpend": "module unload gcc",
                "resources": {
                    "nodes": 1,
                    "ntasks-per-node": 4,
                    "time": "01:00:00",
                    "partition": "test"
                },
                "launcher": "srun -n {nprocs}",
                "nprocs": 4
            }
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(test_config, f, indent=2)
        return f.name

def test_loaders():
    """Test all loaders with a sample configuration."""
    print("\n🧪 TESTING LOADERS")
    print("=" * 30)
    
    test_config_path = create_test_config()
    print(f"Created test config: {test_config_path}")
    
    try:
        # Add project root to path for imports
        script_dir = Path(__file__).parent
        project_root = script_dir.parent
        sys.path.insert(0, str(project_root))
        
        from xespresso.utils.machines.machine_config import load_machine as load_machine_main
        from xespresso.utils.machines.config.loader import load_machine as load_machine_new
        from xespresso.utils.machines.config.old.loader import load_machine as load_machine_old
        
        loaders = [
            ("machine_config.py", load_machine_main),
            ("config/loader.py", load_machine_new),
            ("config/old/loader.py", load_machine_old)
        ]
        
        test_machines = ["test_local", "test_remote"]
        
        all_passed = True
        
        for machine_name in test_machines:
            print(f"\n  Testing with machine: {machine_name}")
            for loader_name, loader_func in loaders:
                try:
                    result = loader_func(test_config_path, machine_name)
                    if result:
                        scheduler = result.get("scheduler", "N/A")
                        execution = result.get("execution", "N/A")
                        print(f"    ✅ {loader_name}: scheduler='{scheduler}', execution='{execution}'")
                        
                        # Check for specific fields
                        has_launcher = "launcher" in result
                        has_nprocs = "nprocs" in result
                        if machine_name == "test_remote":
                            has_port = result.get("remote_auth", {}).get("port") is not None
                            print(f"        - launcher: {has_launcher}, nprocs: {has_nprocs}, port: {has_port}")
                            if not (has_launcher and has_nprocs and has_port):
                                all_passed = False
                        else:
                            print(f"        - launcher: {has_launcher}, nprocs: {has_nprocs}")
                            if not (has_launcher and has_nprocs):
                                all_passed = False
                    else:
                        print(f"    ❌ {loader_name}: returned None")
                        all_passed = False
                except Exception as e:
                    print(f"    ❌ {loader_name}: Error - {e}")
                    all_passed = False
        
        return all_passed
        
    finally:
        # Clean up
        os.unlink(test_config_path)

def main():
    """Main entry point."""
    print("🔧 XESPRESSO MACHINE CONFIGURATION VERIFICATION")
    print("=" * 60)
    
    try:
        # Analyze files
        results = analyze_machine_files()
        
        # Find inconsistencies
        inconsistencies = find_inconsistencies(results)
        
        # Test loaders
        loader_tests_passed = test_loaders()
        
        # Summary
        print(f"\n📊 SUMMARY")
        print("=" * 20)
        
        success = True
        
        if inconsistencies:
            print(f"❌ Found {len(inconsistencies)} inconsistency types")
            for inc in inconsistencies:
                print(f"  - {inc['type']}: {inc['description']}")
            success = False
        else:
            print("✅ No inconsistencies found!")
        
        if not loader_tests_passed:
            print("❌ Some loader tests failed!")
            success = False
        else:
            print("✅ All loader tests passed!")
        
        print("\n🎯 Verification completed!")
        
        return 0 if success else 1
        
    except Exception as e:
        print(f"\n💥 Verification failed with error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())