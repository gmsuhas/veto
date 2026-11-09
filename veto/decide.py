"""Turn a reading into a decision.

The decision is `pass` only when one entry mode passes and every other
applicable rule passes. Both modes failing is a watchlist, not a smaller
trade. There is no third answer.
"""

from __future__ import annotations

from veto.rules import RULES


def decide(reading):
    checks = [check for rule in RULES if (check := rule(reading)) is not None]
    by_name = {check.rule: check for check in checks}
    mode_a = by_name["mode_a"]
    mode_b = by_name["mode_b"]
    others = [check for check in checks if check.rule not in ("mode_a", "mode_b")]
    others_pass = all(check.passed for check in others)

    if mode_a.passed and others_pass:
        outcome = "pass"
        reason = "mode A passes and every other rule passes"
    elif mode_b.passed and others_pass:
        outcome = "pass"
        reason = "mode B passes and every other rule passes"
    elif not mode_a.passed and not mode_b.passed:
        outcome = "watchlist"
        reason = "neither entry mode passes, so there is no entry"
    else:
        outcome = "fail"
        failed = [check.rule for check in others if not check.passed]
        reason = "an entry mode passes, but %s does not" % ", ".join(failed)

    return {
        "outcome": outcome,
        "reason": reason,
        "checks": [check.as_dict() for check in checks],
    }
