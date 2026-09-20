"""jpstock_data.py のネットワーク不要な回帰テスト。"""

import sys
import os
import subprocess
import tempfile
import unittest
import zipfile
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock, patch
from urllib.parse import parse_qs, urlparse

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import jpstock_data as J  # noqa: E402


def xbrl_zip() -> bytes:
    xml = '''<?xml version="1.0" encoding="UTF-8"?>
<xbrl xmlns="http://www.xbrl.org/2003/instance" xmlns:j="urn:test">
  <context id="CurrentYearDuration_ConsolidatedMember" />
  <context id="CurrentYearInstant_ConsolidatedMember" />
  <j:NetSales contextRef="CurrentYearDuration_ConsolidatedMember">100000000</j:NetSales>
  <j:OperatingIncome contextRef="CurrentYearDuration_ConsolidatedMember">20000000</j:OperatingIncome>
  <j:ProfitLossAttributableToOwnersOfParent contextRef="CurrentYearDuration_ConsolidatedMember">15000000</j:ProfitLossAttributableToOwnersOfParent>
  <j:BasicEarningsPerShare contextRef="CurrentYearDuration_ConsolidatedMember">150</j:BasicEarningsPerShare>
  <j:NetCashProvidedByUsedInOperatingActivities contextRef="CurrentYearDuration_ConsolidatedMember">25000000</j:NetCashProvidedByUsedInOperatingActivities>
  <j:Assets contextRef="CurrentYearInstant_ConsolidatedMember">500000000</j:Assets>
  <j:NetAssets contextRef="CurrentYearInstant_ConsolidatedMember">300000000</j:NetAssets>
  <j:NumberOfIssuedSharesAtTheEndOfFiscalYearIncludingTreasuryStock contextRef="CurrentYearInstant_ConsolidatedMember">100000000</j:NumberOfIssuedSharesAtTheEndOfFiscalYearIncludingTreasuryStock>
</xbrl>'''
    out = BytesIO()
    with zipfile.ZipFile(out, "w") as archive:
        archive.writestr("XBRL/PublicDoc/sample.xbrl", xml)
    return out.getvalue()


class JapanStockDataTests(unittest.TestCase):
    def test_normalize_code(self):
        self.assertEqual(J.normalize_code("7203"), "7203.T")
        self.assertEqual(J.normalize_code("7203.T"), "7203.T")
        self.assertEqual(J.normalize_code("130a"), "130A.T")
        with self.assertRaises(ValueError):
            J.normalize_code("TOYOTA")

    def test_extract_standard_consolidated_facts(self):
        values = J._xbrl_financials(xbrl_zip())
        self.assertEqual(str(values["revenue"]), "100000000")
        self.assertEqual(str(values["operating_income"]), "20000000")
        self.assertEqual(str(values["eps"]), "150")
        self.assertEqual(str(values["shares_outstanding"]), "100000000")

    def test_edinet_key_is_required(self):
        old = J.os.environ.pop("EDINET_API_KEY", None)
        try:
            with self.assertRaisesRegex(RuntimeError, "EDINET_API_KEY"):
                J._edinet_key()
        finally:
            if old is not None:
                J.os.environ["EDINET_API_KEY"] = old

    def test_edinet_request_uses_environment_key(self):
        response = MagicMock()
        response.read.return_value = b'{"results": []}'
        response.__enter__.return_value = response
        with patch.dict(J.os.environ, {"EDINET_API_KEY": "test-key"}, clear=False), patch(
            "jpstock_data.urllib.request.urlopen", return_value=response
        ) as urlopen:
            J._request_edinet("/documents.json", {"date": "2026-09-20", "type": "2"})
        query = parse_qs(urlparse(urlopen.call_args.args[0].full_url).query)
        self.assertEqual(query["Subscription-Key"], ["test-key"])

    def test_edinet_daily_cache_skips_network_and_wait(self):
        response = MagicMock()
        response.read.return_value = b'{"results": []}'
        response.__enter__.return_value = response
        with tempfile.TemporaryDirectory() as cache_dir, patch.object(
            J, "CACHE_DIR", Path(cache_dir)
        ), patch.dict(J.os.environ, {"EDINET_API_KEY": "test-key"}, clear=False), patch(
            "jpstock_data.urllib.request.urlopen", return_value=response
        ) as urlopen, patch("jpstock_data.time.sleep") as sleep:
            J._documents_for_day(J.date.today())
            J._documents_for_day(J.date.today())
        self.assertEqual(urlopen.call_count, 1)
        self.assertEqual(sleep.call_count, 1)

    def test_financials_searches_latest_eighteen_months(self):
        with patch("jpstock_data._filings", return_value=[]) as filings:
            with self.assertRaisesRegex(RuntimeError, "18か月"):
                J.cmd_financials("7203")
        filings.assert_called_once_with("7203", annual_only=True, days=550)

    def test_japanese_error_survives_cp932_console(self):
        env = dict(os.environ)
        env["PYTHONIOENCODING"] = "cp932"
        env.pop("PYTHONUTF8", None)
        proc = subprocess.run(
            [sys.executable, str(Path(J.__file__)), "quote", "INVALID"],
            capture_output=True,
            env=env,
        )
        self.assertEqual(proc.returncode, 1)
        self.assertNotIn(b"UnicodeEncodeError", proc.stderr)
        self.assertIn("証券コード", proc.stderr.decode("utf-8", "replace"))


if __name__ == "__main__":
    unittest.main()
