#!/usr/bin/env python3
"""
Single command to run NextMeal app.
Handles backend and frontend concurrently.

Usage:
    python scripts/run.py
"""

import subprocess
import sys
import os
import signal
from pathlib import Path

def run():
    """Run both backend and frontend servers."""
    project_root = Path(__file__).parent.parent
    backend_dir = project_root / "backend"
    frontend_dir = project_root / "frontend"

    print("🍽️  Starting NextMeal...")
    print("")

    # Check if dependencies are installed
    if not (backend_dir / "nextmeal.db").exists():
        print("⚠️  Database not found. Please run setup first:")
        print("   cd backend")
        print("   pip install -r requirements.txt")
        print("   alembic upgrade head")
        print("   python -m app.seed_data")
        print("")
        sys.exit(1)

    if not (frontend_dir / "node_modules").exists():
        print("⚠️  Frontend dependencies not installed. Please run:")
        print("   cd frontend")
        print("   npm install")
        print("")
        sys.exit(1)

    # Start backend
    backend_cmd = [
        sys.executable, "-m", "uvicorn",
        "app.main:app",
        "--reload",
        "--host", "127.0.0.1",
        "--port", "8000"
    ]

    # Start frontend (different commands for Windows vs Unix)
    if sys.platform == "win32":
        frontend_cmd = ["npm.cmd", "run", "dev"]
    else:
        frontend_cmd = ["npm", "run", "dev"]

    backend_proc = None
    frontend_proc = None

    try:
        print("Starting backend server...")
        backend_proc = subprocess.Popen(
            backend_cmd,
            cwd=backend_dir,
        )

        print("Starting frontend server...")
        frontend_proc = subprocess.Popen(
            frontend_cmd,
            cwd=frontend_dir,
        )

        print("")
        print("✅ Backend running on http://localhost:8000")
        print("✅ Frontend running on http://localhost:5173")
        print("")
        print("📱 Open http://localhost:5173 in your browser")
        print("📖 API docs available at http://localhost:8000/docs")
        print("")
        print("Press Ctrl+C to stop")
        print("")

        # Wait for processes
        backend_proc.wait()
        frontend_proc.wait()

    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down...")
        if backend_proc:
            backend_proc.terminate()
            backend_proc.wait()
        if frontend_proc:
            frontend_proc.terminate()
            frontend_proc.wait()
        print("👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        if backend_proc:
            backend_proc.terminate()
        if frontend_proc:
            frontend_proc.terminate()
        sys.exit(1)


if __name__ == "__main__":
    run()
