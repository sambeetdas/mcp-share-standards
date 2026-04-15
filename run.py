#!/usr/bin/env python3
"""
Entry point for the Enterprise MCP Standards Server.

Usage:
    # stdio transport (default — for Cursor/VS Code)
    python run.py

    # SSE transport (for network deployment)
    python run.py --transport sse --port 8080

    # Custom standards directory
    python run.py --standards-dir /path/to/standards

    # With audit persistence
    python run.py --audit-file ./data/audit.json

    # Debug logging
    python run.py --log-level DEBUG
"""

import sys
from pathlib import Path

# Add src to path so the package is importable without installation
sys.path.insert(0, str(Path(__file__).parent / "src"))

from standards_server.server import main

if __name__ == "__main__":
    main()
