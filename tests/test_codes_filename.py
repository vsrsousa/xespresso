"""
Tests for codes configuration filename generation with labels.

These tests verify that the codes configuration saves with appropriate
filenames based on label and version, preventing accidental overwriting.
"""

import pytest
import os
import tempfile
from pathlib import Path


def test_save_config_with_label():
    """Test that save_config uses label in filename."""
    from xespresso.codes.config import Code, CodesConfig
    from xespresso.codes.manager import CodesManager
    
    codes = {
        'pw': Code(name='pw', path='/usr/bin/pw.x', version='7.2'),
    }
    
    config = CodesConfig(
        machine_name='test_machine',
        codes=codes,
        label='production'
    )
    
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = CodesManager.save_config(
            config,
            output_dir=tmpdir,
            interactive=False
        )
        
        # Should save as test_machine-production.json
        expected_filename = 'test_machine-production.json'
        assert os.path.basename(filepath) == expected_filename
        assert os.path.exists(filepath)


def test_save_config_with_version_no_label():
    """Test that save_config uses default filename when no label provided."""
    from xespresso.codes.config import Code, CodesConfig
    from xespresso.codes.manager import CodesManager
    
    codes = {
        'pw': Code(name='pw', path='/usr/bin/pw.x', version='7.2'),
    }
    
    config = CodesConfig(
        machine_name='test_machine',
        codes=codes,
        qe_version='7.2'
    )
    
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = CodesManager.save_config(
            config,
            output_dir=tmpdir,
            interactive=False
        )
        
        # Should save as test_machine.json (default, backward compatible)
        expected_filename = 'test_machine.json'
        assert os.path.basename(filepath) == expected_filename
        assert os.path.exists(filepath)


def test_save_config_without_label_or_version():
    """Test that save_config uses default filename without label or version."""
    from xespresso.codes.config import Code, CodesConfig
    from xespresso.codes.manager import CodesManager
    
    codes = {
        'pw': Code(name='pw', path='/usr/bin/pw.x'),
    }
    
    config = CodesConfig(
        machine_name='test_machine',
        codes=codes
    )
    
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = CodesManager.save_config(
            config,
            output_dir=tmpdir,
            interactive=False
        )
        
        # Should save as test_machine.json
        expected_filename = 'test_machine.json'
        assert os.path.basename(filepath) == expected_filename
        assert os.path.exists(filepath)


def test_save_multiple_configs_different_labels():
    """Test that multiple configs with different labels create separate files."""
    from xespresso.codes.config import Code, CodesConfig
    from xespresso.codes.manager import CodesManager
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Save production config
        config1 = CodesConfig(
            machine_name='cluster',
            codes={'pw': Code(name='pw', path='/opt/qe-prod/pw.x')},
            label='production'
        )
        filepath1 = CodesManager.save_config(config1, output_dir=tmpdir, interactive=False)
        
        # Save dev config
        config2 = CodesConfig(
            machine_name='cluster',
            codes={'pw': Code(name='pw', path='/opt/qe-dev/pw.x')},
            label='dev'
        )
        filepath2 = CodesManager.save_config(config2, output_dir=tmpdir, interactive=False)
        
        # Both files should exist
        assert os.path.exists(filepath1)
        assert os.path.exists(filepath2)
        
        # Filenames should be different
        assert os.path.basename(filepath1) == 'cluster-production.json'
        assert os.path.basename(filepath2) == 'cluster-dev.json'


def test_load_config_with_label():
    """Test that load_config can load by label."""
    from xespresso.codes.config import Code, CodesConfig
    from xespresso.codes.manager import CodesManager
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Save config with label
        original_config = CodesConfig(
            machine_name='test_machine',
            codes={'pw': Code(name='pw', path='/usr/bin/pw.x')},
            label='test_label'
        )
        CodesManager.save_config(original_config, output_dir=tmpdir, interactive=False)
        
        # Load by label
        loaded_config = CodesManager.load_config(
            'test_machine',
            codes_dir=tmpdir,
            label='test_label'
        )
        
        assert loaded_config is not None
        assert loaded_config.label == 'test_label'
        assert 'pw' in loaded_config.codes


def test_load_config_label_fallback_to_default():
    """Test that load_config falls back to default when label not found."""
    from xespresso.codes.config import Code, CodesConfig
    from xespresso.codes.manager import CodesManager
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Save default config (no label)
        default_config = CodesConfig(
            machine_name='test_machine',
            codes={'pw': Code(name='pw', path='/usr/bin/pw.x')},
        )
        CodesManager.save_config(default_config, output_dir=tmpdir, interactive=False)
        
        # Try to load with non-existent label - should fall back to default
        loaded_config = CodesManager.load_config(
            'test_machine',
            codes_dir=tmpdir,
            label='nonexistent'
        )
        
        assert loaded_config is not None
        assert 'pw' in loaded_config.codes


def test_list_machine_configs():
    """Test that list_machine_configs lists all configurations for a machine."""
    from xespresso.codes.config import Code, CodesConfig
    from xespresso.codes.manager import CodesManager, list_machine_configs
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Save default config
        config1 = CodesConfig(
            machine_name='cluster',
            codes={'pw': Code(name='pw', path='/opt/qe/pw.x')},
        )
        CodesManager.save_config(config1, output_dir=tmpdir, interactive=False)
        
        # Save production config
        config2 = CodesConfig(
            machine_name='cluster',
            codes={'pw': Code(name='pw', path='/opt/qe-prod/pw.x')},
            label='production'
        )
        CodesManager.save_config(config2, output_dir=tmpdir, interactive=False)
        
        # Save dev config
        config3 = CodesConfig(
            machine_name='cluster',
            codes={'pw': Code(name='pw', path='/opt/qe-dev/pw.x')},
            label='dev'
        )
        CodesManager.save_config(config3, output_dir=tmpdir, interactive=False)
        
        # List configs
        configs = list_machine_configs('cluster', tmpdir)
        
        assert len(configs) == 3
        assert '' in configs  # Default config
        assert 'production' in configs
        assert 'dev' in configs


def test_list_machine_configs_empty():
    """Test that list_machine_configs returns empty list when no configs exist."""
    from xespresso.codes.manager import list_machine_configs
    
    with tempfile.TemporaryDirectory() as tmpdir:
        configs = list_machine_configs('nonexistent', tmpdir)
        assert configs == []


def test_label_priority_over_version():
    """Test that only label is used in filename, not version."""
    from xespresso.codes.config import Code, CodesConfig
    from xespresso.codes.manager import CodesManager
    
    codes = {
        'pw': Code(name='pw', path='/usr/bin/pw.x', version='7.2'),
    }
    
    config = CodesConfig(
        machine_name='test_machine',
        codes=codes,
        qe_version='7.2',
        label='production'  # Both label and version set
    )
    
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = CodesManager.save_config(
            config,
            output_dir=tmpdir,
            interactive=False
        )
        
        # Should use label, not version (version info is stored inside the file)
        expected_filename = 'test_machine-production.json'
        assert os.path.basename(filepath) == expected_filename


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
