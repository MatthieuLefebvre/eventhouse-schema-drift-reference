import json
import tempfile
import unittest
from pathlib import Path

from scripts.emit_promotion_kql import emit_command


class PromotionCommandTests(unittest.TestCase):
    def test_emits_reviewable_ddl(self) -> None:
        request = {"table": "ControllerTelemetry", "column": "ServiceCountdownHours", "type": "real"}
        self.assertEqual(
            emit_command(request),
            ".alter-merge table ControllerTelemetry (ServiceCountdownHours:real)",
        )

    def test_rejects_identifier_injection(self) -> None:
        with self.assertRaises(ValueError):
            emit_command({"table": "T; .drop table T", "column": "Field", "type": "string"})

    def test_rejects_unknown_type(self) -> None:
        with self.assertRaises(ValueError):
            emit_command({"table": "T", "column": "Field", "type": "varchar"})


if __name__ == "__main__":
    unittest.main()
