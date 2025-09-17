# Distribution Guide for MCP Server Gelato

This guide explains how to package, distribute, and deploy your FastMCP Gelato server for others to use.

## 📦 Package Structure

Your server is now properly packaged with:

- ✅ **fastmcp.json** - FastMCP configuration for standardized deployment
- ✅ **pyproject.toml** - Python package metadata and build configuration
- ✅ **LICENSE** - MIT license for open source distribution
- ✅ **src/__init__.py** - Package initialization with version info
- ✅ **Console script** - `mcp-server-gelato` command line entry point

## 🚀 Distribution Options

### Option 1: PyPI Distribution (Recommended)

Upload to PyPI for global pip installation:

```bash
# 1. Build packages (already done)
uv build

# 2. Install twine for uploading
uv add --dev twine

# 3. Upload to TestPyPI first (recommended)
uv run twine upload --repository testpypi dist/*

# 4. Test installation from TestPyPI
pip install --index-url https://test.pypi.org/simple/ mcp-server-gelato

# 5. Upload to production PyPI
uv run twine upload dist/*
```

After PyPI upload, users can install with:
```bash
pip install mcp-server-gelato
```

### Option 2: GitHub Distribution

Push to GitHub and let users install directly:

```bash
# Users install with:
pip install git+https://github.com/yourusername/mcp-server-gelato.git

# Or specific version:
pip install git+https://github.com/yourusername/mcp-server-gelato.git@v0.1.0
```

### Option 3: FastMCP Cloud Deployment

Deploy to fastmcp.cloud for hosted solution:

1. Push your code to GitHub
2. Visit [fastmcp.cloud](https://fastmcp.cloud)
3. Connect your GitHub account
4. Select your repository
5. Configure deployment settings
6. Get a unique server URL

### Option 4: Local Distribution

Share the built wheel file directly:

```bash
# Users install the .whl file:
pip install mcp_server_gelato-0.1.0-py3-none-any.whl
```

## 🔧 Using the Server

### Command Line Usage

After installation, users can run:

```bash
# Set API key
export GELATO_API_KEY="your-gelato-api-key"

# Run the server
mcp-server-gelato
```

### FastMCP Configuration

Users can use the included `fastmcp.json` for standardized deployment:

```bash
# Run with FastMCP CLI
fastmcp run fastmcp.json

# Deploy to cloud
fastmcp deploy fastmcp.json
```

### Environment Variables

Required:
- `GELATO_API_KEY` - Gelato API key

Optional:
- `GELATO_BASE_URL` - Order API URL (default: https://order.gelatoapis.com)
- `GELATO_PRODUCT_URL` - Product API URL (default: https://product.gelatoapis.com)
- `GELATO_SHIPMENT_URL` - Shipment API URL (default: https://shipment.gelatoapis.com)
- `TIMEOUT` - Request timeout (default: 30)
- `DEBUG` - Enable debug logging (default: false)

## 📋 Pre-Release Checklist

Before distributing:

- [ ] Update version in `pyproject.toml` and `src/__init__.py`
- [ ] Update author information in configuration files
- [ ] Update GitHub URLs to your actual repository
- [ ] Run full test suite: `uv run pytest`
- [ ] Test local installation: `uv pip install -e .`
- [ ] Build packages: `uv build`
- [ ] Create git tag for version: `git tag v0.1.0`

## 🔄 Release Process

1. **Version Bump**: Update version numbers in files
2. **Test**: Run comprehensive tests
3. **Build**: Create distribution packages
4. **Tag**: Create git tag for release
5. **Upload**: Deploy to PyPI/GitHub
6. **Document**: Update README with installation instructions

## 🧪 Testing Installation

Test your package before distribution:

```bash
# Test in clean environment
python -m venv test_env
source test_env/bin/activate
pip install dist/mcp_server_gelato-0.1.0-py3-none-any.whl

# Test command works
GELATO_API_KEY=test-key-1234567890 mcp-server-gelato

# Clean up
deactivate
rm -rf test_env
```

## 📚 Documentation

Ensure your README.md includes:
- Clear installation instructions
- Usage examples
- Configuration options
- API key setup
- Troubleshooting guide

## 🎯 Next Steps

Your FastMCP Gelato server is ready for distribution! Choose your preferred distribution method and update the configuration files with your actual details before publishing.