"""Hard rule (CLAUDE.md s2): no bet-placing code at all.

Fails if any code file mentions an order/offer submission endpoint, or issues a non-GET
HTTP request anywhere except the single allowed Matchbook session login.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
THIS = Path(__file__).resolve()
CODE_SUFFIXES = {".py", ".sh", ".js", ".ts", ".service", ".timer", ".toml", ".cfg", ".ini", ".yml", ".yaml"}
SKIP_DIRS = {".git", "data", "docs", "__pycache__", ".pytest_cache"}

# The only file allowed a non-GET request, and the only URL it may send one to.
LOGIN_FILE = ROOT / "recorder" / "matchbook_login.py"
LOGIN_URL = "https://api.matchbook.com/bpapi/rest/security/session"

FORBIDDEN_ENDPOINTS = [
    r"/offers?\b", r"/bets?\b", r"/orders?\b", r"placeOrders", r"place_?bet", r"submit_?offer",
    r"/v\d/offers", r"cashout", r"cash-out", r"/positions\b",
]
NON_GET = [
    r"\.(post|put|patch|delete)\s*\(",
    r"method\s*=\s*['\"](POST|PUT|PATCH|DELETE)['\"]",
    r"-X\s*(POST|PUT|PATCH|DELETE)",
    r"--request\s+(POST|PUT|PATCH|DELETE)",
    r"(--data|-d)\s",
    r"Request\([^)]*data\s*=",
    r"\burlopen\([^)]*data\s*=",
]


def code_files():
    for p in ROOT.rglob("*"):
        if p.is_file() and p.suffix in CODE_SUFFIXES and p.resolve() != THIS \
                and not (set(p.relative_to(ROOT).parts) & SKIP_DIRS):
            yield p


def test_scanner_sees_code():
    files = list(code_files())
    assert any(p.name == "odds.py" for p in files)


def test_no_order_or_offer_endpoints():
    bad = []
    for p in code_files():
        for i, line in enumerate(p.read_text(errors="ignore").splitlines(), 1):
            for pat in FORBIDDEN_ENDPOINTS:
                if re.search(pat, line, re.I):
                    bad.append(f"{p.relative_to(ROOT)}:{i}: {line.strip()}")
    assert not bad, "bet-placing endpoints found:\n" + "\n".join(bad)


def test_only_login_may_use_non_get():
    bad = []
    for p in code_files():
        text = p.read_text(errors="ignore")
        for i, line in enumerate(text.splitlines(), 1):
            if any(re.search(pat, line) for pat in NON_GET) and p.resolve() != LOGIN_FILE.resolve():
                bad.append(f"{p.relative_to(ROOT)}:{i}: {line.strip()}")
    assert not bad, "non-GET requests outside the login file:\n" + "\n".join(bad)


def test_login_file_only_talks_to_login_url():
    if not LOGIN_FILE.exists():
        return
    urls = set(re.findall(r"https?://[^\s'\"]+", LOGIN_FILE.read_text()))
    assert urls <= {LOGIN_URL}, urls


def test_scanner_catches_planted_violations(tmp_path):
    samples = ['requests.post("https://api.matchbook.com/edge/rest/v2/offers", json=x)',
               "s.put(url)", 'urllib.request.Request(u, data=b"{}")', "curl -X POST https://x"]
    for s in samples:
        assert any(re.search(p, s, re.I) for p in FORBIDDEN_ENDPOINTS + NON_GET), s
