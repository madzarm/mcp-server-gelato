"""Unit tests for configuration management."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from src.config import Settings, get_settings


class TestSettings:
    """Test cases for Settings class."""
    
    def test_default_values(self):
        """Test Settings with default values."""
        with patch.dict(os.environ, {"GELATO_API_KEY": "test_key_minimum_10_chars"}, clear=True):
            settings = Settings()
            
            assert settings.gelato_api_key == "test_key_minimum_10_chars"
            assert settings.gelato_base_url == "https://order.gelatoapis.com"
            assert settings.gelato_product_url == "https://product.gelatoapis.com"
            assert settings.timeout == 30.0
            assert settings.max_retries == 3
    
    def test_custom_values_from_env(self):
        """Test Settings with custom environment variables."""
        env_vars = {
            "GELATO_API_KEY": "custom_test_key_minimum_10_chars",
            "GELATO_BASE_URL": "https://custom-order.gelatoapis.com",
            "GELATO_PRODUCT_URL": "https://custom-product.gelatoapis.com",
            "TIMEOUT": "60.0",
            "MAX_RETRIES": "5"
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            settings = Settings()
            
            assert settings.gelato_api_key == "custom_test_key_minimum_10_chars"
            assert settings.gelato_base_url == "https://custom-order.gelatoapis.com"
            assert settings.gelato_product_url == "https://custom-product.gelatoapis.com"
            assert settings.timeout == 60.0
            assert settings.max_retries == 5
    
    def test_missing_api_key_raises_error(self):
        """Test that missing API key raises validation error."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="GELATO_API_KEY"):
                Settings()
    
    def test_empty_api_key_raises_error(self):
        """Test that empty API key raises validation error."""
        with patch.dict(os.environ, {"GELATO_API_KEY": ""}, clear=True):
            with pytest.raises(ValueError, match="GELATO_API_KEY"):
                Settings()
    
    def test_invalid_timeout_type(self):
        """Test that invalid timeout type raises validation error."""
        env_vars = {
            "GELATO_API_KEY": "test_key_minimum_10_chars",
            "TIMEOUT": "not_a_number"
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            with pytest.raises(ValueError):
                Settings()
    
    def test_invalid_max_retries_type(self):
        """Test that invalid max_retries type raises validation error."""
        env_vars = {
            "GELATO_API_KEY": "test_key_minimum_10_chars",
            "MAX_RETRIES": "not_a_number"
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            with pytest.raises(ValueError):
                Settings()
    
    def test_negative_timeout(self):
        """Test that negative timeout raises validation error."""
        env_vars = {
            "GELATO_API_KEY": "test_key_minimum_10_chars",
            "TIMEOUT": "-10"
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            with pytest.raises(ValueError, match="Timeout must be positive"):
                Settings()
    
    def test_negative_max_retries(self):
        """Test that negative max_retries raises validation error."""
        env_vars = {
            "GELATO_API_KEY": "test_key_minimum_10_chars",
            "MAX_RETRIES": "-1"
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            with pytest.raises(ValueError, match="Max retries must be non-negative"):
                Settings()
    
    def test_zero_max_retries_allowed(self):
        """Test that zero max_retries is allowed."""
        env_vars = {
            "GELATO_API_KEY": "test_key_minimum_10_chars",
            "MAX_RETRIES": "0"
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            settings = Settings()
            assert settings.max_retries == 0


class TestDotEnvLoading:
    """Test cases for .env file loading."""
    
    def test_dotenv_file_loading(self):
        """Test that .env file is loaded correctly."""
        # Create temporary .env file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write("GELATO_API_KEY=dotenv_test_key_minimum_10_chars\n")
            f.write("TIMEOUT=45.0\n")
            f.write("MAX_RETRIES=2\n")
            dotenv_path = f.name
        
        try:
            # Clear environment
            with patch.dict(os.environ, {}, clear=True):
                # Mock the .env file path
                with patch('src.config.Path.cwd') as mock_cwd:
                    mock_cwd.return_value = Path(dotenv_path).parent
                    with patch('src.config.Path.exists') as mock_exists:
                        mock_exists.return_value = True
                        with patch('dotenv.load_dotenv') as mock_load_dotenv:
                            # Simulate loading the .env file
                            def load_env(path):
                                os.environ["GELATO_API_KEY"] = "dotenv_test_key_minimum_10_chars"
                                os.environ["TIMEOUT"] = "45.0"
                                os.environ["MAX_RETRIES"] = "2"
                            
                            mock_load_dotenv.side_effect = load_env
                            
                            settings = Settings()
                            
                            assert settings.gelato_api_key == "dotenv_test_key_minimum_10_chars"
                            assert settings.timeout == 45.0
                            assert settings.max_retries == 2
        finally:
            # Clean up temp file
            os.unlink(dotenv_path)
    
    def test_env_vars_override_dotenv(self):
        """Test that environment variables override .env file."""
        # Set environment variable
        env_vars = {
            "GELATO_API_KEY": "env_override_key_minimum_10_chars",
            "TIMEOUT": "90.0"
        }
        
        with patch.dict(os.environ, env_vars, clear=False):
            # Mock .env file loading (would set different values)
            with patch('dotenv.load_dotenv') as mock_load_dotenv:
                def load_env(path):
                    # This would normally set different values, but env vars should override
                    if "GELATO_API_KEY" not in os.environ:
                        os.environ["GELATO_API_KEY"] = "dotenv_test_key_minimum_10_chars"
                    if "TIMEOUT" not in os.environ:
                        os.environ["TIMEOUT"] = "45.0"
                
                mock_load_dotenv.side_effect = load_env
                
                settings = Settings()
                
                # Environment variables should take precedence
                assert settings.gelato_api_key == "env_override_key_minimum_10_chars"
                assert settings.timeout == 90.0


class TestGetSettings:
    """Test cases for get_settings function."""
    
    def test_get_settings_returns_settings_instance(self):
        """Test that get_settings returns a Settings instance."""
        with patch.dict(os.environ, {"GELATO_API_KEY": "test_key_minimum_10_chars"}, clear=True):
            settings = get_settings()
            
            assert isinstance(settings, Settings)
            assert settings.gelato_api_key == "test_key_minimum_10_chars"
    
    def test_get_settings_with_custom_env(self):
        """Test get_settings with custom environment variables."""
        env_vars = {
            "GELATO_API_KEY": "function_test_key_minimum_10_chars",
            "GELATO_BASE_URL": "https://function-test.gelatoapis.com"
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            settings = get_settings()
            
            assert settings.gelato_api_key == "function_test_key_minimum_10_chars"
            assert settings.gelato_base_url == "https://function-test.gelatoapis.com"
    
    def test_get_settings_validation_error(self):
        """Test that get_settings propagates validation errors."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError):
                get_settings()


class TestSettingsEdgeCases:
    """Test cases for edge cases in Settings."""
    
    def test_very_long_api_key(self):
        """Test Settings with very long API key."""
        long_api_key = "a" * 1000  # 1000 character API key
        
        with patch.dict(os.environ, {"GELATO_API_KEY": long_api_key}, clear=True):
            settings = Settings()
            assert settings.gelato_api_key == long_api_key
    
    def test_whitespace_in_api_key(self):
        """Test Settings with API key containing whitespace."""
        api_key_with_spaces = "  test_key_minimum_10_chars  "
        
        with patch.dict(os.environ, {"GELATO_API_KEY": api_key_with_spaces}, clear=True):
            settings = Settings()
            # Should preserve whitespace (validation happens in auth utils)
            assert settings.gelato_api_key == api_key_with_spaces
    
    def test_float_values_as_strings(self):
        """Test that float values can be provided as strings."""
        env_vars = {
            "GELATO_API_KEY": "test_key_minimum_10_chars",
            "TIMEOUT": "30.5"  # String representation of float
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            settings = Settings()
            assert settings.timeout == 30.5
            assert isinstance(settings.timeout, float)
    
    def test_max_retries_boundary_values(self):
        """Test max_retries with boundary values."""
        # Test with maximum reasonable value
        env_vars = {
            "GELATO_API_KEY": "test_key_minimum_10_chars",
            "MAX_RETRIES": "100"
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            settings = Settings()
            assert settings.max_retries == 100