"""The rules, written as data so a change to one is a diff you can read.

A rule looks at a reading and returns a check. It never returns a trade.
Missing numbers fail the rule that needs them: an unknown figure is not a pass.
"""

from __future__ import annotations


class Check:
    def __init__(self, rule, passed, detail):
        self.rule = rule
        self.passed = passed
        self.detail = detail

    def as_dict(self):
        return {"rule": self.rule, "pass": self.passed, "detail": self.detail}


def _need(reading, *names):
    missing = [name for name in names if reading.get(name) is None]
    return missing


def analyst_upside(reading):
    missing = _need(reading, "price", "analyst_target")
    if missing:
        return Check("analyst_upside", False, "missing %s" % ", ".join(missing))
    price = reading["price"]
    if price <= 0:
        return Check("analyst_upside", False, "price must be positive")
    upside = (reading["analyst_target"] - price) / price
    detail = "upside %.1f%%" % (upside * 100)
    return Check("analyst_upside", upside >= 0.20, detail)


def mode_a(reading):
    missing = _need(reading, "rsi", "macd_histogram")
    if missing:
        return Check("mode_a", False, "missing %s" % ", ".join(missing))
    rsi_ok = reading["rsi"] <= 30
    macd_ok = reading["macd_histogram"] > 0
    detail = "rsi %.2f, macd histogram %.4f" % (reading["rsi"], reading["macd_histogram"])
    return Check("mode_a", rsi_ok and macd_ok, detail)


def mode_b(reading):
    missing = _need(reading, "rsi", "catalyst_days")
    if missing:
        return Check("mode_b", False, "missing %s" % ", ".join(missing))
    rsi_ok = 45 <= reading["rsi"] <= 65
    catalyst_ok = 0 <= reading["catalyst_days"] <= 30
    detail = "rsi %.2f, catalyst in %s days" % (reading["rsi"], reading["catalyst_days"])
    return Check("mode_b", rsi_ok and catalyst_ok, detail)


def iv_rank(reading):
    missing = _need(reading, "iv_rank")
    if missing:
        return Check("iv_rank", False, "missing iv_rank")
    rank = reading["iv_rank"]
    return Check("iv_rank", rank < 30, "iv rank %.1f" % rank)


def fomc_blackout(reading):
    missing = _need(reading, "hours_to_fomc")
    if missing:
        return Check("fomc_blackout", False, "missing hours_to_fomc")
    hours = reading["hours_to_fomc"]
    clear = hours < 0 or hours > 48
    return Check("fomc_blackout", clear, "%.1f hours to the decision" % hours)


def gap(reading):
    missing = _need(reading, "gap_percent")
    if missing:
        return Check("gap", False, "missing gap_percent")
    move = reading["gap_percent"]
    return Check("gap", move <= 5, "gap %.2f%%" % move)


def earnings_decision(reading):
    """A binary that has to be made before entry, not during it."""
    missing = _need(reading, "earnings_days", "earnings_plan")
    if missing:
        return Check("earnings_decision", False, "missing %s" % ", ".join(missing))
    days = reading["earnings_days"]
    plan = reading["earnings_plan"]
    if days is None or days > 90:
        return Check("earnings_decision", True, "no earnings inside the window")
    known = plan in ("hold", "exit_day_before")
    return Check("earnings_decision", known, "plan %r, earnings in %s days" % (plan, days))


def diagonal(reading):
    """Both legs, checked on their own. Absent when the reading is not a spread."""
    if not reading.get("spread"):
        return None
    missing = _need(
        reading,
        "long_dte", "long_strike_steps",
        "short_dte", "short_strike_steps",
        "short_expires_before_earnings",
    )
    if missing:
        return Check("diagonal", False, "missing %s" % ", ".join(missing))
    problems = []
    for leg, dte, steps in (
        ("long", reading["long_dte"], reading["long_strike_steps"]),
        ("short", reading["short_dte"], reading["short_strike_steps"]),
    ):
        if not 60 <= dte <= 120:
            problems.append("%s dte %s outside 60-120" % (leg, dte))
        if steps not in (0, 1):
            problems.append("%s is %s strikes from the money" % (leg, steps))
    if not reading["short_expires_before_earnings"]:
        problems.append("short leg expires after earnings")
    detail = "; ".join(problems) if problems else "both legs inside the rules"
    return Check("diagonal", not problems, detail)


# Order is the order a person should apply them. The upside filter is first
# because it removes a name before any other number is worth fetching.
RULES = (
    analyst_upside,
    mode_a,
    mode_b,
    iv_rank,
    fomc_blackout,
    gap,
    earnings_decision,
    diagonal,
)
