"""Read the numbers from a small text block.

One `name: value` per line. A blank line or a line starting with `#` is
skipped. `yes` and `no` become booleans. Numbers become numbers. Anything
else stays text. A missing name is left missing, and the rule that needs it
fails rather than guessing.
"""

from __future__ import annotations

FIELDS = (
    "price", "analyst_target", "rsi", "macd_histogram", "catalyst_days",
    "iv_rank", "hours_to_fomc", "gap_percent", "earnings_days", "earnings_plan",
    "spread", "long_dte", "long_strike_steps", "short_dte", "short_strike_steps",
    "short_expires_before_earnings",
)


class ReadError(ValueError):
    pass


def parse(text):
    found = {}
    for line_no, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        name, colon, value = line.partition(":")
        name = name.strip()
        if not colon or name not in FIELDS:
            raise ReadError("line %d: expected one of %s" % (line_no, ", ".join(FIELDS)))
        if name in found:
            raise ReadError("line %d: %s is repeated" % (line_no, name))
        found[name] = _value(value.strip(), line_no)
    return {name: found.get(name) for name in FIELDS}


def _value(text, line_no):
    if text == "":
        raise ReadError("line %d has no value" % line_no)
    lowered = text.lower()
    if lowered in ("yes", "true"):
        return True
    if lowered in ("no", "false"):
        return False
    try:
        if "." in text:
            return float(text)
        return int(text)
    except ValueError:
        return text
