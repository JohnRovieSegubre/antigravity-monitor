"""
Sovereign MCP Server
=====================
MCP server for Sovereign API — expose AI inference as MCP tools.

Usage:
    python -m sovereign_mcp
"""

from .server import main, SovereignMCPServer

__version__ = "1.0.0"
__all__ = ["main", "SovereignMCPServer"]
