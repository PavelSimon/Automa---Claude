#!/usr/bin/env python3
"""Development scripts for Automa platform."""

import subprocess
import sys
import os
from pathlib import Path


def run_backend():
    """Run the backend development server."""
    print("🚀 Starting Automa backend with uv...")
    subprocess.run([
        "uv", "run", "uvicorn",
        "backend.app.main:app",
        "--reload",
        "--host", "0.0.0.0",
        "--port", "8000"
    ])


def run_frontend():
    """Run the frontend development server."""
    print("🎨 Starting frontend development server...")
    os.chdir("frontend")
    subprocess.run(["npm", "run", "dev"])


def install_deps():
    """Install all dependencies."""
    print("📦 Installing Python dependencies with uv...")
    subprocess.run(["uv", "sync"])

    print("📦 Installing frontend dependencies...")
    os.chdir("frontend")
    subprocess.run(["npm", "install"])
    os.chdir("..")


def run_tests():
    """Run all tests."""
    print("🧪 Running backend tests...")
    subprocess.run(["uv", "run", "pytest", "backend/tests/"])


def lint():
    """Run linting."""
    print("🔍 Running linting...")
    subprocess.run(["uv", "run", "ruff", "check", "backend/"])


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: uv run scripts/dev.py [backend|frontend|install|test|lint]")
        sys.exit(1)

    command = sys.argv[1]

    if command == "backend":
        run_backend()
    elif command == "frontend":
        run_frontend()
    elif command == "install":
        install_deps()
    elif command == "test":
        run_tests()
    elif command == "lint":
        lint()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)