"""A single-tool MCP server over stdio.

The framing is newline-delimited JSON-RPC, which is the stdio transport.
Logging goes to stderr because stdout is the protocol. The only tool is
`check`: it takes the same fields the text format does and returns the
decision. A host that already runs other servers adds this one beside them.
"""

from __future__ import annotations

import json

from veto import __version__
from veto.decide import decide
from veto.read import FIELDS

PROTOCOL = "2025-06-18"

TOOL = {
    "name": "check",
    "description": (
        "Decide whether a long-call reading passes a fixed set of rules. "
        "Returns pass, fail, or watchlist. It does not recommend a trade, "
        "and a missing number fails the rule that needs it."
    ),
    "inputSchema": {
        "type": "object",
        "properties": {name: {"description": name} for name in FIELDS},
        "additionalProperties": False,
    },
}


def serve(stdin, stdout):
    for line in stdin:
        line = line.strip()
        if not line:
            continue
        message = json.loads(line)
        response = handle(message)
        if response is not None:
            stdout.write(json.dumps(response) + "\n")
            stdout.flush()


def handle(message):
    if message.get("jsonrpc") != "2.0" or "method" not in message:
        return _error(message.get("id"), -32600, "not a JSON-RPC request")
    method = message["method"]
    request_id = message.get("id")
    if request_id is None:
        return None
    if method == "initialize":
        return _result(request_id, {
            "protocolVersion": PROTOCOL,
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "veto", "version": __version__},
        })
    if method == "tools/list":
        return _result(request_id, {"tools": [TOOL]})
    if method == "tools/call":
        return _call(request_id, message.get("params") or {})
    if method == "ping":
        return _result(request_id, {})
    return _error(request_id, -32601, "unknown method %s" % method)


def _call(request_id, params):
    if params.get("name") != "check":
        return _error(request_id, -32602, "unknown tool")
    arguments = params.get("arguments") or {}
    unknown = [name for name in arguments if name not in FIELDS]
    if unknown:
        return _error(request_id, -32602, "unknown field %s" % ", ".join(unknown))
    reading = {name: arguments.get(name) for name in FIELDS}
    decision = decide(reading)
    return _result(request_id, {
        "content": [{"type": "text", "text": json.dumps(decision)}],
        "isError": False,
    })


def _result(request_id, result):
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def _error(request_id, code, message):
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}
