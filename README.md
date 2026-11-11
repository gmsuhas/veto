# veto

A review that gives the same answer on Thursday as it did on Monday.

**TLDR.** I checked the same names twice in one week and the second check
disagreed with the first. A value that was "near" the line counted as a
pass, and a missing number got the benefit of the doubt. veto writes the
refusals down: you bring the figures, and it answers `pass`, `fail`, or
`watchlist`. Nothing to install beyond Python 3.9.

Read this if a decision you care about changes depending on who applies the
rules and how tired they are. The worked example is a long investment call.
The lesson is any review where the inputs are numbers you could round in
your favor without noticing. It does not fetch a price and it does not
recommend a trade.

## Try it

```sh
pip install veto-check
veto check examples/se.txt
python3 -m veto check examples/se.txt
python3 -m veto check examples/clear.txt
python3 -m veto check examples/spread.txt
```

A reading is one `name: value` per line. A missing value fails the rule that
needs it. There is no "close enough": RSI of 30.01 does not pass a rule
written as 30.

`examples/se.txt` fails both entry modes, so the result is `watchlist`. Not a
smaller trade. `examples/bmy.txt` fails the analyst check first, at 8.3%
against a rule that wants 20%. `examples/spread.txt` passes an entry mode and
then fails because the short leg is too short, too far from the money, and
expires after earnings.

## The rules

Applied in this order. The first one is first because it removes a name
before the rest of the numbers are worth collecting.

| Rule | Passes when |
|---|---|
| analyst upside | target is at least 20% above the price |
| mode A | RSI is 30 or below, and the MACD histogram is positive |
| mode B | RSI is from 45 to 65, and a catalyst falls inside 30 days |
| iv rank | below 30 |
| FOMC | the decision is more than 48 hours away, or already past |
| gap | the open is not more than 5% |
| earnings | a hold-or-exit decision is already written down |
| diagonal | only when the reading is a spread: each leg 60 to 120 days, at the money or one strike out, and the short leg expires before earnings |

One of the two modes has to pass. The other rules all have to pass. Both
modes failing is `watchlist`. A mode passing while another rule fails is
`fail`.

## As an MCP server

```sh
python3 -m veto serve
```

This speaks [MCP](https://modelcontextprotocol.io/specification/2025-06-18/basic/transports)
over stdin and stdout: one JSON-RPC message per line, logs on stderr, nothing
else on stdout. It implements `initialize`, `tools/list`, `tools/call`, and
`ping`. The one tool is `check`, and its arguments are the same fields as the
text file.

A host that already runs other servers adds this beside them. The decision
does not change because it arrived over the protocol: `serve` calls the same
function `check` does. A client that would rather not speak MCP can shell out
to `python3 -m veto check` and read the text.

```json
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"example","version":"0"}}}
```

## What it will not do

It does not fetch a price, an analyst target, or an option chain. Those
numbers go stale, and a tool that fetches them starts pretending the fetch
cannot be wrong. You bring the figures. It also does not size a position,
pick a strike, or tell you to buy anything. The output is whether the reading
cleared rules you can read in `veto/rules.py`.

## Tests

```sh
python3 -m unittest discover -s tests
```
