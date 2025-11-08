#!/usr/bin/env python3
"""
Example: Listing Available Modules and Specifying QE Versions

This example demonstrates the new features for:
1. Listing available modules on remote systems
2. Specifying Quantum ESPRESSO version explicitly
3. Using different QE versions for different calculations

These features address common issues where:
- Users don't know which QE modules are available
- Auto-detection picks up compiler versions instead of QE versions
- Different calculations need different QE versions
"""

from xespresso.codes import detect_qe_codes, create_codes_config, CodesManager


def example_list_modules():
    """Example 1: List available modules on a remote system"""
    print("=" * 70)
    print("Example 1: List available Quantum ESPRESSO modules")
    print("=" * 70)
    
    # List all modules containing "espresso" on a remote cluster
    try:
        modules = CodesManager.list_available_modules(
            ssh_connection={
                'host': 'cluster.example.edu',
                'username': 'myuser',
                'port': 22
            },
            env_setup="source /etc/profile",
            search_pattern="espresso"
        )
        
        print(f"Found {len(modules)} Quantum ESPRESSO modules:")
        for module in modules:
            print(f"  - {module}")
        
        # User can then choose which module to use
        if modules:
            print(f"\n💡 You can now use one of these modules:")
            print(f"   modules=['{modules[0]}']")
    except Exception as e:
        print(f"Note: This is a demonstration. Actual execution requires remote access.")
        print(f"Error (expected): {type(e).__name__}")


def example_list_modules_local():
    """Example 2: List modules on local system"""
    print("\n" + "=" * 70)
    print("Example 2: List modules on local system")
    print("=" * 70)
    
    # For local systems
    try:
        modules = CodesManager.list_available_modules(
            search_pattern="quantum"
        )
        
        if modules:
            print(f"Found {len(modules)} modules with 'quantum' in the name:")
            for module in modules:
                print(f"  - {module}")
        else:
            print("No modules found (or module system not available locally)")
    except Exception as e:
        print(f"Note: Module system may not be available on this machine")


def example_specify_version():
    """Example 3: Explicitly specify QE version instead of auto-detection"""
    print("\n" + "=" * 70)
    print("Example 3: Specify QE version explicitly")
    print("=" * 70)
    
    # Problem: Auto-detection might return compiler version like "2021.4"
    # Solution: Specify the version explicitly
    
    try:
        config = detect_qe_codes(
            machine_name="my_cluster",
            modules=["quantum-espresso/7.2"],
            ssh_connection={
                'host': 'cluster.example.edu',
                'username': 'myuser'
            },
            env_setup="source /etc/profile",
            qe_version="7.2",  # Explicitly set the version
            auto_load_machine=False
        )
        
        print(f"✅ Configuration created with version: {config.qe_version}")
        print(f"   Codes detected: {list(config.codes.keys())}")
    except Exception as e:
        print(f"Note: This is a demonstration. Actual execution requires remote access.")
        print(f"Error (expected): {type(e).__name__}")


def example_version_comparison():
    """Example 4: Why explicit version matters"""
    print("\n" + "=" * 70)
    print("Example 4: Auto-detection vs Explicit version")
    print("=" * 70)
    
    print("🔍 Auto-detection might return:")
    print("   Version: 2021.4  ← This is the Intel compiler version!")
    print("   or")
    print("   Version: 11.2    ← This could be GCC version!")
    
    print("\n✅ With explicit version:")
    print("   Version: 7.2     ← This is the actual QE version!")
    
    print("\n💡 Recommendation:")
    print("   Always verify auto-detected versions and use qe_version parameter")
    print("   if the detected version doesn't match your Quantum ESPRESSO version.")


def example_multiple_versions():
    """Example 5: Using multiple QE versions for different calculations"""
    print("\n" + "=" * 70)
    print("Example 5: Multiple QE versions for different calculations")
    print("=" * 70)
    
    print("You can create separate configurations for different QE versions:")
    
    # Configuration for QE 7.2
    print("\n📦 Configuration 1: Quantum ESPRESSO 7.2 (for production)")
    code_example_72 = """
config_72 = create_codes_config(
    machine_name="cluster",
    modules=["quantum-espresso/7.2"],
    qe_version="7.2",
    ssh_connection={'host': 'cluster.edu', 'username': 'user'},
    save=True,
    output_dir="~/.xespresso/codes"
)
"""
    print(code_example_72)
    
    # Configuration for QE 7.1
    print("📦 Configuration 2: Quantum ESPRESSO 7.1 (for compatibility)")
    code_example_71 = """
config_71 = create_codes_config(
    machine_name="cluster",
    modules=["quantum-espresso/7.1"],
    qe_version="7.1",
    ssh_connection={'host': 'cluster.edu', 'username': 'user'},
    save=True,
    output_dir="~/.xespresso/codes"
)
"""
    print(code_example_71)
    
    print("💡 Then use different versions for different calculations:")
    usage_example = """
from xespresso.codes import load_codes_config

# Use QE 7.2 for production runs
codes_72 = load_codes_config("cluster", version="7.2")

# Use QE 7.1 for legacy calculations
codes_71 = load_codes_config("cluster", version="7.1")
"""
    print(usage_example)


def example_workflow_with_modules():
    """Example 6: Complete workflow with module listing and version control"""
    print("\n" + "=" * 70)
    print("Example 6: Complete workflow")
    print("=" * 70)
    
    workflow = """
# Step 1: Discover available modules
modules = CodesManager.list_available_modules(
    ssh_connection={'host': 'cluster.edu', 'username': 'user'},
    env_setup="source /etc/profile",
    search_pattern="espresso"
)
print(f"Available modules: {modules}")
# Output: ['quantum-espresso/7.2', 'quantum-espresso/7.1', 'espresso/6.8']

# Step 2: Choose the module and specify version explicitly
chosen_module = "quantum-espresso/7.2"
actual_version = "7.2"  # Don't rely on auto-detection!

# Step 3: Create configuration with explicit version
config = create_codes_config(
    machine_name="my_cluster",
    modules=[chosen_module],
    qe_version=actual_version,  # Explicitly set version
    ssh_connection={'host': 'cluster.edu', 'username': 'user'},
    env_setup="source /etc/profile",
    save=True
)

# Step 4: Use the configuration in your calculations
from xespresso import Espresso
calc = Espresso(
    # ... your calculation parameters ...
)
"""
    print(workflow)


def example_troubleshooting():
    """Example 7: Troubleshooting version detection issues"""
    print("\n" + "=" * 70)
    print("Example 7: Troubleshooting guide")
    print("=" * 70)
    
    print("\n❌ Problem: Auto-detected version is wrong")
    print("   Detected: 2021.4")
    print("   Expected: 7.2")
    
    print("\n✅ Solution: Use qe_version parameter")
    solution = """
config = detect_qe_codes(
    machine_name="cluster",
    modules=["quantum-espresso/7.2"],
    qe_version="7.2",  # Explicit version
)
"""
    print(solution)
    
    print("\n❌ Problem: Don't know which modules are available")
    print("\n✅ Solution: List available modules first")
    solution2 = """
modules = CodesManager.list_available_modules(
    ssh_connection={'host': 'cluster.edu', 'username': 'user'},
    search_pattern="espresso"
)
print(modules)
"""
    print(solution2)
    
    print("\n❌ Problem: Need different QE versions for different calculations")
    print("\n✅ Solution: Create separate configs with explicit versions")
    solution3 = """
# Create config for QE 7.2
config_72 = create_codes_config(
    machine_name="cluster",
    modules=["quantum-espresso/7.2"],
    qe_version="7.2"
)

# Create config for QE 7.1
config_71 = create_codes_config(
    machine_name="cluster",
    modules=["quantum-espresso/7.1"],
    qe_version="7.1"
)

# Load specific version when needed
from xespresso.codes import load_codes_config
codes = load_codes_config("cluster", version="7.2")
"""
    print(solution3)


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("Module Listing and Version Control Examples")
    print("=" * 70)
    print("\nThese examples demonstrate new features for:")
    print("- Discovering available Quantum ESPRESSO modules")
    print("- Explicitly specifying QE version (avoiding compiler version confusion)")
    print("- Using different QE versions for different calculations")
    print("=" * 70)
    
    # Run examples
    example_list_modules()
    example_list_modules_local()
    example_specify_version()
    example_version_comparison()
    example_multiple_versions()
    example_workflow_with_modules()
    example_troubleshooting()
    
    print("\n" + "=" * 70)
    print("For more information, see:")
    print("- xespresso/codes/manager.py (CodesManager class)")
    print("- xespresso/codes/__init__.py (exported functions)")
    print("=" * 70)
