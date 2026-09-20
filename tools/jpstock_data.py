#!/usr/bin/env python3
"""日本株データツール — EDINET を財務の正本、yfinance を価格補助にする。

使い方:
  python tools/jpstock_data.py quote 7203
  python tools/jpstock_data.py prices 7203 --period 5y --adjusted
  python tools/jpstock_data.py financials 7203
  python tools/jpstock_data.py filings 7203 --years 5

EDINET を使う financials / filings には EDINET_API_KEY が必要です。
キーは URL や出力には表示しません。EDINET 応答は local/edinet_cache/ にだけ
キャッシュされ、Git には追加されません。
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
from io import BytesIO
from pathlib import Path

try:
    import yfinance as yf
except ImportError:  # pragma: no cover - exercised by command-line users only
    yf = None


ROOT = Path(__file__).resolve().parents[1]
CACHE_DIR = ROOT / "local" / "edinet_cache"
YFINANCE_CACHE_DIR = ROOT / "local" / "yfinance_cache"
EDINET_BASE = "https://api.edinet-fsa.go.jp/api/v2"
ANNUAL_SECURITIES_REPORT = "120"
_TIMEOUT = 30


def _force_utf8_stdio() -> None:
    """Keep Japanese help and error messages usable in a Windows console."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def normalize_code(code: str) -> str:
    """Convert a four-character TSE security code to a Yahoo Finance symbol."""
    base = code.strip().upper().removesuffix(".T")
    if not re.fullmatch(r"(?=.*\d)[0-9A-Z]{4}", base):
        raise ValueError("証券コードは4文字（例: 7203 / 130A）で指定してください")
    return f"{base}.T"


def _edinet_key() -> str:
    key = os.environ.get("EDINET_API_KEY", "").strip()
    if not key:
        raise RuntimeError(
            "EDINET_API_KEY が未設定です。scripts/set-edinet-api-key.ps1 を実行するか、"
            "環境変数にEDINET APIキーを設定してください。"
        )
    return key


def _request_edinet(path: str, params: dict[str, str], cache_name: str | None = None) -> bytes:
    """Call EDINET v2 without logging its subscription key."""
    cache_path = CACHE_DIR / cache_name if cache_name else None
    if cache_path and cache_path.exists():
        return cache_path.read_bytes()

    query = dict(params)
    query["Subscription-Key"] = _edinet_key()
    url = f"{EDINET_BASE}{path}?{urllib.parse.urlencode(query)}"
    request = urllib.request.Request(url, headers={"User-Agent": "ai-berkshire-jp/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=_TIMEOUT) as response:
            payload = response.read()
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"EDINET API request failed (HTTP {exc.code})") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"EDINET API network error: {exc.reason}") from exc

    if cache_path:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_bytes(payload)
    # Only pace actual API calls. Cache hits return before this point.
    time.sleep(0.1)
    return payload


def _documents_for_day(day: date) -> list[dict]:
    # The list endpoint is scanned once per business day. Reuse that day's
    # response even when several commands run on the same day.
    cache_name = f"documents/{day.isoformat()}.json"
    payload = _request_edinet(
        "/documents.json", {"date": day.isoformat(), "type": "2"}, cache_name
    )
    try:
        return json.loads(payload).get("results", [])
    except json.JSONDecodeError as exc:
        raise RuntimeError("EDINET returned an invalid document list") from exc


def _filings(
    code: str,
    years: int | None = None,
    annual_only: bool = False,
    days: int | None = None,
) -> list[dict]:
    """Find an issuer's filings. EDINET's list API is deliberately date-based."""
    if days is None:
        if years is None or years < 1 or years > 10:
            raise ValueError("--years は1から10で指定してください")
        days = 366 * years
    start = date.today() - timedelta(days=days)
    rows: list[dict] = []
    day = date.today()
    while day >= start:
        if day.weekday() < 5:
            for row in _documents_for_day(day):
                sec_code = str(row.get("secCode") or "").upper()
                if not sec_code.startswith(code.upper()):
                    continue
                if annual_only and str(row.get("docTypeCode")) != ANNUAL_SECURITIES_REPORT:
                    continue
                rows.append(row)
        day -= timedelta(days=1)
    return sorted(rows, key=lambda row: row.get("submitDateTime", ""), reverse=True)


def _format_yen(value: Decimal | None) -> str:
    if value is None:
        return "-"
    absolute = abs(value)
    if absolute >= Decimal("1e12"):
        return f"{value / Decimal('1e12'):,.2f}兆円"
    if absolute >= Decimal("1e8"):
        return f"{value / Decimal('1e8'):,.2f}億円"
    return f"{value:,.0f}円"


def _number(text: str | None) -> Decimal | None:
    if text is None or text.strip() in {"", "-"}:
        return None
    try:
        return Decimal(text.strip().replace(",", ""))
    except InvalidOperation:
        return None


def _xbrl_financials(payload: bytes) -> dict[str, Decimal | None]:
    """Extract standard consolidated annual facts from an EDINET XBRL ZIP.

    Custom issuer tags are intentionally not guessed: absent standard tags stay
    blank so a report never presents a made-up number as an EDINET fact.
    """
    with zipfile.ZipFile(BytesIO(payload)) as archive:
        names = [
            name for name in archive.namelist()
            if "/XBRL/PublicDoc/" in f"/{name}" and name.lower().endswith(".xbrl")
        ]
        if not names:
            raise RuntimeError("EDINET document did not include a PublicDoc XBRL file")
        root = ET.fromstring(archive.read(names[0]))

    contexts = {element.attrib.get("id", ""): element for element in root if element.tag.endswith("context")}

    def pick_context(kind: str) -> str | None:
        candidates = [key for key in contexts if kind in key]
        consolidated = [key for key in candidates if "ConsolidatedMember" in key]
        return (consolidated or candidates or [None])[0]

    duration = pick_context("CurrentYearDuration")
    instant = pick_context("CurrentYearInstant")
    names = {
        "revenue": ("NetSales", "OperatingRevenue1", "OperatingRevenue2"),
        "operating_income": ("OperatingIncome",),
        "profit_attributable_to_owners": ("ProfitLossAttributableToOwnersOfParent",),
        "eps": ("BasicEarningsPerShare",),
        "operating_cash_flow": ("NetCashProvidedByUsedInOperatingActivities",),
        "total_assets": ("Assets",),
        "net_assets": ("NetAssets",),
        "shares_outstanding": ("NumberOfIssuedSharesAtTheEndOfFiscalYearIncludingTreasuryStock",),
    }
    out: dict[str, Decimal | None] = {key: None for key in names}
    for element in root.iter():
        local = element.tag.rsplit("}", 1)[-1]
        context = element.attrib.get("contextRef")
        for key, accepted in names.items():
            expected_context = instant if key in {"total_assets", "net_assets", "shares_outstanding"} else duration
            if out[key] is None and local in accepted and context == expected_context:
                out[key] = _number(element.text)
    return out


def _ticker(symbol: str):
    """Keep yfinance's SQLite cache in the repository's ignored local area."""
    YFINANCE_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    yf.set_tz_cache_location(str(YFINANCE_CACHE_DIR))
    return yf.Ticker(symbol)


def cmd_quote(code: str) -> None:
    if yf is None:
        raise RuntimeError("yfinance が未インストールです: python -m pip install yfinance")
    symbol = normalize_code(code)
    try:
        history = _ticker(symbol).history(period="5d", auto_adjust=False)
    except Exception as exc:
        raise RuntimeError(f"yfinance から価格を取得できませんでした: {exc}") from exc
    if history.empty:
        raise RuntimeError(f"価格を取得できませんでした: {symbol}")
    latest = history.iloc[-1]
    previous = history.iloc[-2] if len(history) > 1 else None
    change = ((latest["Close"] / previous["Close"] - 1) * 100) if previous is not None else None
    print(f"日本株株価: {symbol}  データ源: Yahoo Finance (yfinance、補助)")
    print(f"  日付:       {history.index[-1].date()}")
    print(f"  終値:       {latest['Close']:,.2f} 円")
    if change is not None:
        print(f"  前日比:     {change:+.2f}%")
    print(f"  始値/高値/安値: {latest['Open']:,.2f} / {latest['High']:,.2f} / {latest['Low']:,.2f} 円")
    print(f"  出来高:     {latest['Volume']:,.0f} 株")


def cmd_prices(code: str, period: str, adjusted: bool) -> None:
    if yf is None:
        raise RuntimeError("yfinance が未インストールです: python -m pip install yfinance")
    symbol = normalize_code(code)
    try:
        history = _ticker(symbol).history(period=period, auto_adjust=adjusted)
    except Exception as exc:
        raise RuntimeError(f"yfinance から価格を取得できませんでした: {exc}") from exc
    if history.empty:
        raise RuntimeError(f"価格を取得できませんでした: {symbol}")
    print(f"# {symbol} | {'調整済み' if adjusted else '未調整'}価格 | Yahoo Finance (yfinance)")
    history.to_csv(sys.stdout)


def cmd_filings(code: str, years: int) -> None:
    rows = _filings(code, years)
    print(f"EDINET提出書類: {code} 直近{years}年（正本）")
    if not rows:
        print("  該当書類なし")
        return
    for row in rows:
        print(
            f"  {row.get('submitDateTime', '')[:10]}  {row.get('docTypeCode', ''):<4} "
            f"{row.get('docDescription', '')}  {row.get('docID', '')}"
        )


def cmd_financials(code: str) -> None:
    # Annual reports should exist within 18 months; avoid a five-year first-run scan.
    rows = _filings(code, annual_only=True, days=550)
    if not rows:
        raise RuntimeError(f"直近18か月に {code} の有価証券報告書（docTypeCode 120）が見つかりません")
    filing = rows[0]
    doc_id = filing.get("docID")
    if not doc_id:
        raise RuntimeError("EDINET filing did not have a document ID")
    payload = _request_edinet(f"/documents/{doc_id}", {"type": "1"})
    values = _xbrl_financials(payload)
    print(f"EDINET財務: {code}（正本）")
    print(f"  提出日:     {filing.get('submitDateTime', '')[:10]}")
    print(f"  書類:       {filing.get('docDescription', '')}")
    print(f"  売上高:     {_format_yen(values['revenue'])}")
    print(f"  営業利益:   {_format_yen(values['operating_income'])}")
    print(f"  親会社株主利益: {_format_yen(values['profit_attributable_to_owners'])}")
    print(f"  EPS:        {values['eps'] if values['eps'] is not None else '-'} 円")
    print(f"  営業CF:     {_format_yen(values['operating_cash_flow'])}")
    print(f"  総資産:     {_format_yen(values['total_assets'])}")
    print(f"  純資産:     {_format_yen(values['net_assets'])}")
    print(f"  発行済株式数: {values['shares_outstanding'] if values['shares_outstanding'] is not None else '-'} 株")


def main() -> int:
    _force_utf8_stdio()
    parser = argparse.ArgumentParser(description="日本株データ — EDINET財務 + yfinance価格")
    sub = parser.add_subparsers(dest="command", required=True)
    quote = sub.add_parser("quote", help="最新終値・出来高（yfinance）")
    quote.add_argument("code")
    prices = sub.add_parser("prices", help="日足CSV（yfinance）")
    prices.add_argument("code")
    prices.add_argument("--period", default="1y", help="yfinance period、例: 5y")
    prices.add_argument("--adjusted", action="store_true", help="分割・配当調整済み価格")
    financials = sub.add_parser("financials", help="最新有価証券報告書の主要財務（EDINET）")
    financials.add_argument("code")
    filings = sub.add_parser("filings", help="提出書類一覧（EDINET）")
    filings.add_argument("code")
    filings.add_argument("--years", type=int, default=5)
    args = parser.parse_args()
    try:
        if args.command == "quote":
            cmd_quote(args.code)
        elif args.command == "prices":
            cmd_prices(args.code, args.period, args.adjusted)
        elif args.command == "financials":
            cmd_financials(args.code)
        else:
            cmd_filings(args.code, args.years)
    except (RuntimeError, ValueError) as exc:
        print(f"❌ {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
