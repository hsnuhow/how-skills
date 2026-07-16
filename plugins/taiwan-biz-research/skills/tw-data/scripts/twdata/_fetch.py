"""Shared fetch layer for Taiwan government open data.

Every quirk below was hit for real while testing these endpoints. The point of
this module is that no other script has to rediscover them.

The big one: **HTTP 200 does not mean you got data.** Taiwan government hosts
routinely answer 200 with an HTML error page, a bot challenge, an SPA shell, an
empty body, or a header-only file for a month that isn't published yet. Every
fetch here is validated on the payload, never on the status code.
"""

from __future__ import annotations

import csv
import io
import json
import re
import shutil
import ssl
import subprocess
import urllib.error
import urllib.parse
import urllib.request
import zipfile

# data.gov.tw and several agency hosts 403 the default Python UA. curl gets 200
# for the same URL, so this is UA filtering, not blocking.
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"

TIMEOUT = 60


class FetchError(RuntimeError):
    """Raised when a response is not usable data, whatever the status code said."""


# Signatures of "200 but not data". Checked against the head of the body.
_NOT_DATA = (
    (b"<!DOCTYPE html", "HTML page instead of data"),
    (b"<html", "HTML page instead of data"),
    (b"<HTML", "HTML page instead of data"),
    (b"Pardon Our Interruption", "Akamai bot challenge"),
    (b"_abck", "Akamai bot challenge"),
    (b"Just a moment", "Cloudflare challenge"),
)


def encode_url(url: str) -> str:
    """Percent-encode non-ASCII characters in a URL.

    DGBAS serves its files under literal Chinese filenames
    (.../011-平均每戶消費支出按區域別分.csv). urllib requires an ASCII request
    line and raises UnicodeEncodeError on those, so every URL is normalised here
    rather than at each call site. Already-encoded URLs pass through unchanged
    because '%' stays in the safe set.
    """
    parts = urllib.parse.urlsplit(url)
    return urllib.parse.urlunsplit((
        parts.scheme,
        parts.netloc,
        urllib.parse.quote(parts.path, safe="/%"),
        urllib.parse.quote(parts.query, safe="=&%?+,"),
        parts.fragment,
    ))


def _fetch_via_curl(url: str) -> bytes:
    """Retry a fetch through curl, which trusts the platform certificate store.

    ws.dgbas.gov.tw serves a broken chain: the leaf is issued by "TWCA Secure
    SSL Certification Authority", but the server never sends that intermediate —
    it sends unrelated ePKI/GRCA certificates instead. Python builds its trust
    path from certifi and cannot complete the chain, so it rejects the host.
    curl uses the OS trust store, which carries the Taiwan government CAs, and
    verifies the same host successfully.

    Verification stays ON here — this swaps trust stores, it does not disable
    the check. If curl also refuses the certificate, the fetch fails, which is
    the correct outcome.
    """
    if not shutil.which("curl"):
        raise FetchError(
            f"SSL verification failed for {url} and curl is unavailable to retry. "
            "This host serves an incomplete certificate chain."
        )
    try:
        proc = subprocess.run(
            ["curl", "-sSL", "--fail", "-A", UA, "--max-time", str(TIMEOUT), url],
            capture_output=True, timeout=TIMEOUT + 10,
        )
    except subprocess.TimeoutExpired as e:
        raise FetchError(f"curl timed out for {url}") from e
    if proc.returncode != 0:
        raise FetchError(
            f"curl failed for {url} (exit {proc.returncode}): "
            f"{proc.stderr.decode('utf-8', 'replace')[:200]}"
        )
    return proc.stdout


def fetch(url: str, *, min_bytes: int = 512, allow_html: bool = False) -> bytes:
    """GET a URL and return the body, or raise FetchError.

    min_bytes guards the header-only case: several endpoints serve a valid file
    containing nothing but column headers when the period isn't published yet
    (MOPS returns 916 bytes for an unpublished month). Size is the only signal
    that distinguishes it from a real response.
    """
    url = encode_url(url)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            body = resp.read()
            status = resp.status
    except urllib.error.HTTPError as e:
        raise FetchError(f"HTTP {e.code} for {url}") from e
    except urllib.error.URLError as e:
        if isinstance(e.reason, ssl.SSLCertVerificationError):
            body = _fetch_via_curl(url)
            status = 200
        else:
            raise FetchError(f"network error for {url}: {e.reason}") from e

    if not body:
        raise FetchError(f"HTTP {status} but empty body for {url} (cbc's OpenAPI does this)")

    if not allow_html:
        head = body[:2048]
        for sig, why in _NOT_DATA:
            if sig in head:
                raise FetchError(f"HTTP {status} but {why} for {url}")

    if len(body) < min_bytes:
        raise FetchError(
            f"HTTP {status} but only {len(body)}B for {url} — "
            f"likely headers with no rows (period not published yet?)"
        )
    return body


def decode(body: bytes) -> str:
    """Decode agency text. Nearly everything is UTF-8 with BOM these days.

    The widespread "Taiwan gov data is Big5" advice is mostly stale: MOEA CSVs,
    DGBAS XML and NDC CSVs are all utf-8-sig. Big5 survives in MOPS HTML and in
    NDC's *zip filenames* (not their contents) — those are handled separately.
    """
    for enc in ("utf-8-sig", "utf-8", "big5", "cp950"):
        try:
            return body.decode(enc)
        except UnicodeDecodeError:
            continue
    return body.decode("utf-8", errors="replace")


def read_csv(body: bytes) -> list[dict]:
    return list(csv.DictReader(io.StringIO(decode(body))))


def read_csv_rows(body: bytes) -> list[list[str]]:
    return list(csv.reader(io.StringIO(decode(body))))


# --- dates -----------------------------------------------------------------
# There is no single convention. TWSE/MOPS/MOEA/MOI use ROC (民國) years; CBC,
# NDC and the DGBAS household surveys use AD. TPEx mixes both *within one API*,
# so detect per value rather than per source.

def roc_to_ad(value: str) -> str:
    """Convert a ROC date to AD, preserving the shape.

    1150715 -> 20260715   (packed date)
    11506   -> 202606     (packed year-month)
    115     -> 2026       (year only)
    Values already in AD are returned unchanged.
    """
    v = str(value).strip()
    if not v.isdigit():
        return v
    if len(v) == 7:   # YYYMMDD
        return f"{int(v[:3]) + 1911}{v[3:]}"
    if len(v) == 5:   # YYYMM
        return f"{int(v[:3]) + 1911}{v[3:]}"
    if len(v) == 3:   # YYY
        return str(int(v) + 1911)
    return v  # 8 or 6 digits: already AD


def looks_roc(value: str) -> bool:
    """TPEx serves ROC and AD in the same API; length is the discriminator."""
    v = str(value).strip()
    return v.isdigit() and len(v) in (3, 5, 7)


# DGBAS marks revised/preliminary figures with a suffix on the period itself
# (202604Ⓡ, 202605Ⓟ). Left in place they silently break period joins.
_STATUS = re.compile(r"[ⓇⓅⓄ\*]+$")


def strip_status(period: str) -> str:
    return _STATUS.sub("", str(period).strip())


def clean_cell(value: str) -> str | None:
    """Agency 'no data' markers are a literal dash, not an empty cell.

    Also strips trailing whitespace, which matters more than it should: NDC's
    light column contains '黃藍 ' with a trailing space, and grouping on the raw
    value silently splits one category into two.
    """
    v = str(value).strip()
    return None if v in ("-", "－", "…", "") else v


# --- data.gov.tw -----------------------------------------------------------

def resolve_dataset(dataset_id: str | int) -> dict:
    """Resolve a data.gov.tw dataset id to its current download URLs.

    Always resolve rather than hardcoding: the underlying paths rotate (NDC's
    embed an opaque base64 blob that changes on every re-upload).

    Note the platform's keyword *search* API needs an API key; this per-id
    lookup does not. Metadata dates lie — several datasets report a 2024
    modifiedDate while serving 2026 data. Trust the file, not the metadata.
    """
    url = f"https://data.gov.tw/api/v2/rest/dataset/{dataset_id}"
    body = fetch(url, min_bytes=32)
    result = json.loads(decode(body)).get("result") or {}
    if not result:
        raise FetchError(f"dataset {dataset_id} returned no result")
    return {
        "id": str(dataset_id),
        "title": result.get("title"),
        "distribution": [
            {
                "description": d.get("resourceDescription"),
                "format": (d.get("resourceFormat") or "").upper(),
                "url": d.get("resourceDownloadUrl"),
            }
            for d in (result.get("distribution") or [])
            if d.get("resourceDownloadUrl")
        ],
    }


def dataset_file(dataset_id: str | int, *, fmt: str = "CSV", contains: str = "") -> bytes:
    """Fetch one file from a dataset, picked by format and an optional name match."""
    meta = resolve_dataset(dataset_id)
    for d in meta["distribution"]:
        if d["format"] == fmt.upper() and contains in (d["description"] or ""):
            return fetch(d["url"])
    have = [(d["format"], d["description"]) for d in meta["distribution"]]
    raise FetchError(f"dataset {dataset_id}: no {fmt} matching {contains!r}; has {have}")


def unzip(body: bytes) -> dict[str, bytes]:
    """Unzip, repairing Big5 filenames.

    NDC ships its zips with Big5-encoded entry names. Python (and `unzip`) read
    them as cp437, producing mojibake. The contents are plain utf-8-sig — it is
    only the filenames that need rescuing.
    """
    out: dict[str, bytes] = {}
    with zipfile.ZipFile(io.BytesIO(body)) as zf:
        for info in zf.infolist():
            name = info.filename
            if not info.flag_bits & 0x800:  # no UTF-8 flag => cp437-decoded Big5
                try:
                    name = name.encode("cp437").decode("big5")
                except (UnicodeEncodeError, UnicodeDecodeError):
                    pass
            out[name] = zf.read(info)
    return out


__all__ = [
    "FetchError", "fetch", "encode_url", "decode", "read_csv", "read_csv_rows",
    "roc_to_ad", "looks_roc", "strip_status", "clean_cell",
    "resolve_dataset", "dataset_file", "unzip",
]
