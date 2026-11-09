import json
import unittest

from veto.decide import decide
from veto.read import ReadError, parse
from veto.server import handle


def load(name):
    with open("examples/%s.txt" % name, encoding="utf-8") as handle:
        return parse(handle.read())


class DecideTests(unittest.TestCase):
    def test_both_modes_failing_is_a_watchlist(self):
        decision = decide(load("se"))
        self.assertEqual(decision["outcome"], "watchlist")
        checks = {item["rule"]: item for item in decision["checks"]}
        self.assertFalse(checks["mode_a"]["pass"])
        self.assertFalse(checks["mode_b"]["pass"])

    def test_the_analyst_filter_fails_a_name_before_the_setup_matters(self):
        decision = decide(load("bmy"))
        self.assertEqual(decision["outcome"], "fail")
        upside = next(item for item in decision["checks"] if item["rule"] == "analyst_upside")
        self.assertFalse(upside["pass"])
        self.assertIn("8.3%", upside["detail"])

    def test_a_clean_reading_passes(self):
        decision = decide(load("clear"))
        self.assertEqual(decision["outcome"], "pass")

    def test_a_mode_that_is_one_point_off_does_not_pass(self):
        reading = load("clear")
        reading["rsi"] = 30.01
        decision = decide(reading)
        self.assertNotEqual(decision["outcome"], "pass")

    def test_the_diagonal_is_checked_per_leg(self):
        decision = decide(load("spread"))
        diagonal = next(item for item in decision["checks"] if item["rule"] == "diagonal")
        self.assertFalse(diagonal["pass"])
        self.assertIn("short dte", diagonal["detail"])
        self.assertIn("earnings", diagonal["detail"])

    def test_a_missing_number_fails_its_rule(self):
        reading = load("clear")
        reading["iv_rank"] = None
        decision = decide(reading)
        iv = next(item for item in decision["checks"] if item["rule"] == "iv_rank")
        self.assertFalse(iv["pass"])
        self.assertEqual(decision["outcome"], "fail")

    def test_fomc_blackout_is_the_48_hours_before(self):
        reading = load("clear")
        reading["hours_to_fomc"] = 48
        self.assertEqual(decide(reading)["outcome"], "fail")
        reading["hours_to_fomc"] = 48.1
        self.assertEqual(decide(reading)["outcome"], "pass")

    def test_a_repeated_field_is_an_error(self):
        with self.assertRaises(ReadError):
            parse("price: 1\nprice: 2\n")


class ServerTests(unittest.TestCase):
    def test_initialize_names_the_protocol(self):
        reply = handle({"jsonrpc": "2.0", "id": 1, "method": "initialize"})
        self.assertEqual(reply["result"]["protocolVersion"], "2025-06-18")
        self.assertEqual(reply["result"]["serverInfo"]["name"], "veto")

    def test_the_tool_returns_the_same_decision(self):
        reading = load("se")
        reply = handle({
            "jsonrpc": "2.0", "id": 2, "method": "tools/call",
            "params": {"name": "check", "arguments": reading},
        })
        body = json.loads(reply["result"]["content"][0]["text"])
        self.assertEqual(body["outcome"], "watchlist")

    def test_an_unknown_field_is_rejected(self):
        reply = handle({
            "jsonrpc": "2.0", "id": 3, "method": "tools/call",
            "params": {"name": "check", "arguments": {"ticker": "SE"}},
        })
        self.assertEqual(reply["error"]["code"], -32602)

    def test_a_notification_gets_no_reply(self):
        self.assertIsNone(handle({
            "jsonrpc": "2.0", "method": "notifications/initialized",
        }))


if __name__ == "__main__":
    unittest.main()
