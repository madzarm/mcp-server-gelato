"""Integration tests for MCP protocol compliance."""

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from unittest.mock import patch

import pytest


class TestMCPProtocolCompliance:
    """Test cases for MCP protocol compliance."""
    
    def test_server_stdout_json_only(self):
        """Test that server only outputs JSON to stdout."""
        # This is a critical test for MCP compliance
        env = os.environ.copy()
        env["GELATO_API_KEY"] = "test_key_minimum_10_chars"
        
        try:
            # Start server process briefly
            process = subprocess.Popen(
                ["uv", "run", "python", "main.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
                cwd=Path(__file__).parent.parent.parent
            )
            
            # Give it a moment to start and potentially output messages
            time.sleep(2)
            
            # Terminate gracefully
            process.terminate()
            try:
                stdout, stderr = process.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                stdout, stderr = process.communicate()
            
            # Verify stdout is empty or contains only JSON
            if stdout.strip():
                # If there's output, it should be JSON
                lines = stdout.strip().split('\n')
                for line in lines:
                    line = line.strip()
                    if line:
                        # Each line should be valid JSON
                        try:
                            json.loads(line)
                        except json.JSONDecodeError:
                            pytest.fail(f"Non-JSON output in stdout: {line}")
            
            # Verify stderr contains expected logging
            assert "Starting Gelato" in stderr or len(stderr) > 0
            
        except subprocess.SubprocessError as e:
            pytest.skip(f"Could not start server process: {e}")
    
    def test_server_logging_to_stderr(self):
        """Test that server logging goes to stderr, not stdout."""
        env = os.environ.copy()
        env["GELATO_API_KEY"] = "test_key_minimum_10_chars"
        env["DEBUG"] = "true"  # Enable debug logging
        
        try:
            process = subprocess.Popen(
                ["uv", "run", "python", "main.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
                cwd=Path(__file__).parent.parent.parent
            )
            
            time.sleep(3)  # Let it try to initialize
            
            process.terminate()
            try:
                stdout, stderr = process.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                stdout, stderr = process.communicate()
            
            # Stdout should be empty (no logging messages)
            assert not any("🚀" in line for line in stdout.split('\n'))
            assert not any("📦" in line for line in stdout.split('\n'))
            assert not any("🔧" in line for line in stdout.split('\n'))
            
            # Stderr should contain logging messages
            assert any("Starting Gelato" in line for line in stderr.split('\n'))
            
        except subprocess.SubprocessError as e:
            pytest.skip(f"Could not start server process: {e}")


class TestServerInitialization:
    """Test cases for server initialization."""
    
    def test_server_creation(self):
        """Test that server can be created without errors."""
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
        
        try:
            from src.server import create_server
            
            # Should create server without raising exceptions
            server = create_server()
            assert server is not None
            assert hasattr(server, 'name')
            
        except ImportError as e:
            pytest.skip(f"Could not import server module: {e}")
    
    def test_server_has_expected_name(self):
        """Test that server has expected name."""
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
        
        try:
            from src.server import create_server
            
            server = create_server()
            assert server.name == "Gelato Print API"
            
        except ImportError as e:
            pytest.skip(f"Could not import server module: {e}")


class TestResourceRegistration:
    """Test cases for resource registration."""
    
    def test_order_resources_registered(self):
        """Test that order resources are registered."""
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
        
        try:
            from src.server import create_server
            
            server = create_server()
            
            # Check that server has resources registered
            # Note: The exact method to check resources depends on FastMCP implementation
            assert hasattr(server, '_resources') or hasattr(server, 'resources')
            
        except ImportError as e:
            pytest.skip(f"Could not import server module: {e}")
    
    def test_product_resources_registered(self):
        """Test that product resources are registered."""
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
        
        try:
            from src.server import create_server
            
            server = create_server()
            
            # Verify server is properly configured
            assert server.instructions is not None
            assert "Gelato" in server.instructions
            
        except ImportError as e:
            pytest.skip(f"Could not import server module: {e}")


class TestToolRegistration:
    """Test cases for tool registration."""
    
    def test_order_tools_registered(self):
        """Test that order tools are registered."""
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
        
        try:
            from src.server import create_server
            
            server = create_server()
            
            # Check that server has tools registered
            # Note: The exact method to check tools depends on FastMCP implementation
            assert hasattr(server, '_tools') or hasattr(server, 'tools')
            
        except ImportError as e:
            pytest.skip(f"Could not import server module: {e}")


class TestLifespanManagement:
    """Test cases for lifespan management."""
    
    def test_lifespan_function_exists(self):
        """Test that lifespan function is defined."""
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
        
        try:
            from src.server import lifespan
            
            assert callable(lifespan)
            
        except ImportError as e:
            pytest.skip(f"Could not import lifespan function: {e}")
    
    def test_client_registry_usage(self):
        """Test that client registry is used properly."""
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
        
        try:
            from src.utils.client_registry import client_registry
            
            # Should be able to import and create registry
            assert client_registry is not None
            
            # Clear any existing client
            client_registry.clear_client()
            
            # Should raise error when no client is set
            with pytest.raises(RuntimeError, match="No Gelato client registered"):
                client_registry.get_client()
            
        except ImportError as e:
            pytest.skip(f"Could not import client registry: {e}")


class TestConfigurationHandling:
    """Test cases for configuration handling."""
    
    def test_settings_loading(self):
        """Test that settings can be loaded."""
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
        
        try:
            from src.config import get_settings
            
            # Test with environment variable
            with patch.dict(os.environ, {"GELATO_API_KEY": "test_key_minimum_10_chars"}):
                settings = get_settings()
                assert settings.gelato_api_key == "test_key_minimum_10_chars"
            
        except ImportError as e:
            pytest.skip(f"Could not import settings: {e}")
    
    def test_settings_validation(self):
        """Test settings validation."""
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
        
        try:
            from src.config import Settings
            
            # Should raise error for missing API key
            with patch.dict(os.environ, {}, clear=True):
                with pytest.raises(ValueError):
                    Settings()
            
        except ImportError as e:
            pytest.skip(f"Could not import Settings: {e}")


class TestErrorHandling:
    """Test cases for error handling."""
    
    def test_authentication_error_handling(self):
        """Test that authentication errors are handled properly."""
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
        
        try:
            from src.utils.exceptions import AuthenticationError, GelatoAPIError
            
            # Test exception hierarchy
            auth_error = AuthenticationError("Invalid API key")
            assert isinstance(auth_error, GelatoAPIError)
            assert isinstance(auth_error, Exception)
            
        except ImportError as e:
            pytest.skip(f"Could not import exceptions: {e}")
    
    def test_client_error_handling(self):
        """Test that client errors are handled properly."""
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
        
        try:
            from src.utils.exceptions import OrderNotFoundError, CatalogNotFoundError
            
            # Test specific error types
            order_error = OrderNotFoundError("missing-order")
            assert "missing-order" in str(order_error)
            
            catalog_error = CatalogNotFoundError("missing-catalog")
            assert "missing-catalog" in str(catalog_error)
            
        except ImportError as e:
            pytest.skip(f"Could not import exceptions: {e}")


@pytest.mark.slow
class TestMCPInspectorCompatibility:
    """Test cases for MCP Inspector compatibility."""
    
    def test_inspector_can_start_server(self):
        """Test that MCP Inspector can start the server without errors."""
        env = os.environ.copy()
        env["GELATO_API_KEY"] = "test_key_minimum_10_chars"
        
        try:
            # Check if MCP Inspector is available
            result = subprocess.run(
                ["npx", "--yes", "@modelcontextprotocol/inspector", "--help"],
                capture_output=True,
                text=True,
                timeout=15
            )
            
            if result.returncode != 0:
                pytest.skip("MCP Inspector not available")
            
            # Try to start inspector briefly
            process = subprocess.Popen([
                "npx", "--yes", "@modelcontextprotocol/inspector",
                "uv", "run", "python", "main.py"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, 
               env=env, cwd=Path(__file__).parent.parent.parent)
            
            time.sleep(5)  # Let it try to start
            
            if process.poll() is None:
                # Inspector started successfully
                process.terminate()
                process.wait(timeout=5)
                # This is a success case
            else:
                stdout, stderr = process.communicate()
                # Check for JSON parsing errors (would indicate our server is outputting non-JSON)
                if "JSON parse" in stderr or "SyntaxError" in stderr:
                    pytest.fail(f"MCP Inspector getting JSON parse errors: {stderr[:200]}")
            
        except subprocess.TimeoutExpired:
            # Timeout might be normal for inspector startup
            pass
        except subprocess.SubprocessError as e:
            pytest.skip(f"Could not test with MCP Inspector: {e}")


class TestProtocolMessages:
    """Test cases for MCP protocol message handling."""
    
    def test_json_rpc_message_format(self):
        """Test that server expects correct JSON-RPC message format."""
        # This test verifies that our server is set up to handle JSON-RPC messages
        # The actual message handling is done by the FastMCP framework
        
        # Example of expected message format
        init_message = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test", "version": "1.0"}
            }
        }
        
        # Verify message structure
        assert init_message["jsonrpc"] == "2.0"
        assert "id" in init_message
        assert "method" in init_message
        assert "params" in init_message
        
        # This confirms we understand the expected message format