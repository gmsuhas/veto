"""veto on the command line, and as an MCP server.

    python3 -m veto check examples/oversold.txt
    python3 -m veto serve

`serve` speaks MCP over stdin and stdout. It is the same `decide` the
command calls. A client that already has an MCP session can call the tool
instead of shelling out.
"""

from __future__ import annotations

import json
import sys

from veto.decide import decide
from veto.read import ReadError, parse
from veto.server import serve


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    try:
        if not args or args[0] in ("-h", "--help"):
            sys.stderr.write(
                "usage: veto check FILE\n"
                "       veto serve\n"
            )
            return 1
        if args[0] == "check" and len(args) == 2:
            decision = decide(parse(_read(args[1])))
            sys.stdout.write(_render(decision))
            return 0
        if args[0] == "serve" and len(args) == 1:
            serve(sys.stdin, sys.stdout)
            return 0
        raise ReadError("unknown command")
    except (ReadError, OSError, json.JSONDecodeError) as error:
        sys.stderr.write("veto: %s\n" % error)
        return 1


def _read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def _render(decision):
    lines = ["%s  %s" % (decision["outcome"], decision["reason"])]
    for check in decision["checks"]:
        mark = "pass" if check["pass"] else "FAIL"
        lines.append("  %-20s %s  %s" % (check["rule"], mark, check["detail"]))
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    sys.exit(main())
