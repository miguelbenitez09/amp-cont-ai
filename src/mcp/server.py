"""
Model Context Protocol (MCP) Server for Panama Maritime PortOps AI.
Implements the JSON-RPC 2.0 protocol over stdio for Claude Desktop, Cursor, Antigravity,
and other agentic AI orchestrators.

Author: Desarrollado v1.0 Miguel Benítez
License: GNU GPL-3.0 with Section 7 Mandatory Attribution
"""

import sys
import json
import logging
from typing import Any, Dict, Optional
from src.mcp.tools import get_available_tools_schema, execute_tool

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("mcp_server")


class MCPServer:
    """
    Standard Model Context Protocol Server implementation.
    Complies with MCP 2024-11-05 spec for tools discovery and execution.
    """

    PROTOCOL_VERSION = "2024-11-05"
    SERVER_NAME = "panama-portops-mcp-server"
    SERVER_VERSION = "1.0.0"

    def __init__(self):
        self.tools = get_available_tools_schema()

    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handles an incoming JSON-RPC 2.0 message."""
        msg_id = request.get("id")
        method = request.get("method")
        params = request.get("params", {})

        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "protocolVersion": self.PROTOCOL_VERSION,
                    "serverInfo": {
                        "name": self.SERVER_NAME,
                        "version": self.SERVER_VERSION,
                        "author": "Desarrollado v1.0 Miguel Benítez"
                    },
                    "capabilities": {
                        "tools": {"listChanged": False}
                    }
                }
            }

        elif method == "notifications/initialized":
            return {}  # No-op notification response

        elif method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "tools": self.tools
                }
            }

        elif method == "tools/call":
            tool_name = params.get("name")
            tool_args = params.get("arguments", {})
            try:
                result = execute_tool(tool_name, tool_args)
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(result, indent=2, ensure_ascii=False)
                            }
                        ],
                        "isError": False
                    }
                }
            except Exception as e:
                logger.error(f"Error executing tool {tool_name}: {e}")
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "error": {
                        "code": -32603,
                        "message": str(e)
                    }
                }

        elif method == "ping":
            return {"jsonrpc": "2.0", "id": msg_id, "result": {}}

        else:
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {
                    "code": -32601,
                    "message": f"Method '{method}' not found."
                }
            }

    def run_stdio(self) -> None:
        """Runs the server reading JSON-RPC lines from standard input."""
        logger.info(f"Starting {self.SERVER_NAME} v{self.SERVER_VERSION} (Desarrollado v1.0 Miguel Benítez) on stdio...")
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                req = json.loads(line)
                resp = self.handle_request(req)
                if resp:
                    sys.stdout.write(json.dumps(resp) + "\n")
                    sys.stdout.flush()
            except json.JSONDecodeError as err:
                err_resp = {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Parse error"}}
                sys.stdout.write(json.dumps(err_resp) + "\n")
                sys.stdout.flush()


if __name__ == "__main__":
    server = MCPServer()
    server.run_stdio()
