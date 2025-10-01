"""
Tests for the codes module
"""

import os
import json
import tempfile
import shutil
import pytest
from xespresso.codes import (
    Code, CodesConfig, CodesManager,
    create_codes_config, load_codes_config, detect_qe_codes
)


class TestCode:
    """Tests for Code dataclass"""
    
    def test_code_creation(self):
        """Test creating a Code object"""
        code = Code(
            name="pw",
            path="/usr/bin/pw.x",
            version="7.2"
        )
        assert code.name == "pw"
        assert code.path == "/usr/bin/pw.x"
        assert code.version == "7.2"
    
    def test_code_to_dict(self):
        """Test Code serialization to dict"""
        code = Code(
            name="pw",
            path="/usr/bin/pw.x",
            version="7.2"
        )
        data = code.to_dict()
        assert data["name"] == "pw"
        assert data["path"] == "/usr/bin/pw.x"
        assert data["version"] == "7.2"
    
    def test_code_from_dict(self):
        """Test Code deserialization from dict"""
        data = {
            "name": "pw",
            "path": "/usr/bin/pw.x",
            "version": "7.2"
        }
        code = Code.from_dict(data)
        assert code.name == "pw"
        assert code.path == "/usr/bin/pw.x"
        assert code.version == "7.2"


class TestCodesConfig:
    """Tests for CodesConfig class"""
    
    def test_config_creation(self):
        """Test creating a CodesConfig object"""
        config = CodesConfig(
            machine_name="test_machine",
            qe_version="7.2"
        )
        assert config.machine_name == "test_machine"
        assert config.qe_version == "7.2"
    
    def test_add_code(self):
        """Test adding a code to config"""
        config = CodesConfig(machine_name="test")
        code = Code(name="pw", path="/usr/bin/pw.x")
        config.add_code(code)
        assert "pw" in config.codes
        assert config.get_code("pw") == code
    
    def test_list_codes(self):
        """Test listing codes"""
        config = CodesConfig(machine_name="test")
        config.add_code(Code(name="pw", path="/usr/bin/pw.x"))
        config.add_code(Code(name="hp", path="/usr/bin/hp.x"))
        codes = config.list_codes()
        assert "pw" in codes
        assert "hp" in codes
        assert len(codes) == 2
    
    def test_has_code(self):
        """Test checking code availability"""
        config = CodesConfig(machine_name="test")
        config.add_code(Code(name="pw", path="/usr/bin/pw.x"))
        assert config.has_code("pw")
        assert not config.has_code("nonexistent")
    
    def test_to_dict(self):
        """Test config serialization"""
        config = CodesConfig(machine_name="test", qe_version="7.2")
        config.add_code(Code(name="pw", path="/usr/bin/pw.x", version="7.2"))
        data = config.to_dict()
        assert data["machine_name"] == "test"
        assert data["qe_version"] == "7.2"
        assert "pw" in data["codes"]
    
    def test_from_dict(self):
        """Test config deserialization"""
        data = {
            "machine_name": "test",
            "qe_version": "7.2",
            "codes": {
                "pw": {
                    "name": "pw",
                    "path": "/usr/bin/pw.x",
                    "version": "7.2"
                }
            }
        }
        config = CodesConfig.from_dict(data)
        assert config.machine_name == "test"
        assert config.qe_version == "7.2"
        assert config.has_code("pw")
    
    def test_json_roundtrip(self):
        """Test saving and loading from JSON"""
        config = CodesConfig(machine_name="test", qe_version="7.2")
        config.add_code(Code(name="pw", path="/usr/bin/pw.x", version="7.2"))
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            filepath = f.name
        
        try:
            config.to_json(filepath)
            loaded = CodesConfig.from_json(filepath)
            assert loaded.machine_name == config.machine_name
            assert loaded.qe_version == config.qe_version
            assert loaded.has_code("pw")
        finally:
            os.unlink(filepath)


class TestCodesManager:
    """Tests for CodesManager class"""
    
    def test_create_config(self):
        """Test creating config from detected codes"""
        detected_codes = {
            "pw": "/usr/bin/pw.x",
            "hp": "/usr/bin/hp.x"
        }
        config = CodesManager.create_config(
            machine_name="test",
            detected_codes=detected_codes,
            qe_version="7.2"
        )
        assert config.machine_name == "test"
        assert config.qe_version == "7.2"
        assert config.has_code("pw")
        assert config.has_code("hp")
    
    def test_save_and_load_config(self):
        """Test saving and loading config"""
        config = CodesConfig(machine_name="test", qe_version="7.2")
        config.add_code(Code(name="pw", path="/usr/bin/pw.x", version="7.2"))
        
        tmpdir = tempfile.mkdtemp()
        try:
            filepath = CodesManager.save_config(config, output_dir=tmpdir)
            assert os.path.exists(filepath)
            
            loaded = CodesManager.load_config("test", codes_dir=tmpdir)
            assert loaded is not None
            assert loaded.machine_name == "test"
            assert loaded.has_code("pw")
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)
    
    def test_load_nonexistent_config(self):
        """Test loading a config that doesn't exist"""
        tmpdir = tempfile.mkdtemp()
        try:
            loaded = CodesManager.load_config("nonexistent", codes_dir=tmpdir)
            assert loaded is None
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)


class TestConvenienceFunctions:
    """Tests for convenience functions"""
    
    def test_detect_qe_codes_no_installation(self):
        """Test detect_qe_codes when no QE is installed"""
        # This should return an empty config when no QE is found
        config = detect_qe_codes(
            machine_name="test",
            search_paths=["/nonexistent/path"]
        )
        assert config.machine_name == "test"
        assert len(config.codes) == 0
    
    def test_create_codes_config_no_save(self):
        """Test creating config without saving"""
        config = create_codes_config(
            machine_name="test",
            search_paths=["/nonexistent/path"],
            save=False
        )
        assert config.machine_name == "test"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
