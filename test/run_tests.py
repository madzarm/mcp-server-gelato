#!/usr/bin/env python3
"""Test runner script for Gelato MCP Server tests."""

import sys
import subprocess
from pathlib import Path


def run_tests():
    """Run all tests with coverage."""
    print("🧪 Running Gelato MCP Server Test Suite\n")
    
    # Change to project root
    project_root = Path(__file__).parent.parent
    
    try:
        # Install test dependencies
        print("📦 Installing test dependencies...")
        subprocess.run([
            "uv", "add", "--group", "test", 
            "pytest>=8.0.0",
            "pytest-asyncio>=0.23.0", 
            "pytest-cov>=4.0.0",
            "pytest-mock>=3.12.0"
        ], cwd=project_root, check=True)
        
        # Run unit tests
        print("\n🔬 Running unit tests...")
        result = subprocess.run([
            "uv", "run", "pytest", "test/unit/", 
            "-v", "--tb=short", 
            "--cov=src", "--cov-report=term-missing"
        ], cwd=project_root)
        
        unit_success = result.returncode == 0
        
        # Run integration tests (may be slower)
        print("\n🔧 Running integration tests...")
        result = subprocess.run([
            "uv", "run", "pytest", "test/integration/", 
            "-v", "--tb=short", "-m", "not slow"
        ], cwd=project_root)
        
        integration_success = result.returncode == 0
        
        # Summary
        print("\n" + "="*60)
        print("📊 TEST RESULTS SUMMARY")
        print("="*60)
        print(f"Unit tests: {'✅ PASSED' if unit_success else '❌ FAILED'}")
        print(f"Integration tests: {'✅ PASSED' if integration_success else '❌ FAILED'}")
        
        if unit_success and integration_success:
            print("\n🎉 All tests passed!")
            return 0
        else:
            print("\n💥 Some tests failed. See output above for details.")
            return 1
            
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error running tests: {e}")
        return 1
    except KeyboardInterrupt:
        print("\n⏹️  Tests interrupted by user")
        return 1


if __name__ == "__main__":
    sys.exit(run_tests())