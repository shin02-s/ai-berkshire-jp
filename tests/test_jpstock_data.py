"""jpstock_data.py のネットワーク不要な回帰テスト。"""

import sys
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


if __name__ == "__main__":
    unittest.main()
