"""Payload cache for fetched government data — avoid re-fetching what doesn't change.

Two layers, checked in order:

  BUNDLED  (skills/tw-data/cache/)  — ships with the repo. Holds *frozen* history:
           data for a closed period that will never change (a past month's 月報,
           a published survey year). Committed, shared across machines, always
           valid on hit — no network, no TTL.
  LOCAL    (~/.claude/tw-data-cache/) — this machine's working cache. Everything
           fetched lands here. Frozen entries are permanent; the rest honour a
           TTL so current-period data still refreshes.

A cache entry is `{url, fetched, bytes, frozen}` in that layer's manifest.json;
the body is `{sha1(url)}.bin` beside it. `promote()` copies LOCAL frozen entries
into BUNDLED — that's how a machine's frozen pulls become the repo's shared set.

Set TW_DATA_CACHE to relocate LOCAL; set TW_DATA_NOCACHE=1 to bypass entirely.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import time
from pathlib import Path

_HERE = Path(__file__).resolve()
BUNDLED = _HERE.parents[2] / "cache"                       # tw-data/cache
LOCAL = Path(os.environ.get("TW_DATA_CACHE")
             or (Path.home() / ".claude" / "tw-data-cache"))
DEFAULT_TTL = 8 * 3600  # seconds a non-frozen entry stays fresh
DISABLED = os.environ.get("TW_DATA_NOCACHE") == "1"


def _key(url: str) -> str:
    return hashlib.sha1(url.encode("utf-8")).hexdigest()


def _manifest(base: Path) -> dict:
    p = base / "manifest.json"
    if p.exists():
        try:
            return json.loads(p.read_text("utf-8"))
        except (ValueError, OSError):
            return {}
    return {}


def _write_manifest(base: Path, m: dict) -> None:
    base.mkdir(parents=True, exist_ok=True)
    (base / "manifest.json").write_text(
        json.dumps(m, ensure_ascii=False, indent=1, sort_keys=True), "utf-8")


def get(url: str, *, ttl: int = DEFAULT_TTL, now: float | None = None) -> bytes | None:
    """Return a cached body, or None. BUNDLED frozen always hits; LOCAL frozen
    always hits; LOCAL non-frozen hits only within `ttl`."""
    if DISABLED:
        return None
    now = time.time() if now is None else now
    k = _key(url)
    for base, honour_ttl in ((BUNDLED, False), (LOCAL, True)):
        entry = _manifest(base).get(k)
        if not entry:
            continue
        blob = base / f"{k}.bin"
        if not blob.exists():
            continue
        if entry.get("frozen"):
            return blob.read_bytes()
        if honour_ttl and (now - entry.get("fetched", 0)) < ttl:
            return blob.read_bytes()
    return None


def put(url: str, body: bytes, *, freeze: bool = False, now: float | None = None) -> None:
    if DISABLED:
        return
    now = time.time() if now is None else now
    k = _key(url)
    LOCAL.mkdir(parents=True, exist_ok=True)
    (LOCAL / f"{k}.bin").write_bytes(body)
    m = _manifest(LOCAL)
    m[k] = {"url": url, "fetched": round(now), "bytes": len(body), "frozen": bool(freeze)}
    _write_manifest(LOCAL, m)


def promote() -> int:
    """Copy every frozen LOCAL entry into BUNDLED (skips ones already there).
    Returns the count promoted. Run this, then commit tw-data/cache/, to share a
    machine's frozen history with everyone who pulls the repo."""
    lm, bm = _manifest(LOCAL), _manifest(BUNDLED)
    BUNDLED.mkdir(parents=True, exist_ok=True)
    n = 0
    for k, entry in lm.items():
        if not entry.get("frozen") or k in bm:
            continue
        src = LOCAL / f"{k}.bin"
        if not src.exists():
            continue
        shutil.copy2(src, BUNDLED / f"{k}.bin")
        bm[k] = entry
        n += 1
    if n:
        _write_manifest(BUNDLED, bm)
    return n


def stats() -> dict:
    def summ(base: Path) -> dict:
        m = _manifest(base)
        return {"entries": len(m),
                "frozen": sum(1 for e in m.values() if e.get("frozen")),
                "bytes": sum(e.get("bytes", 0) for e in m.values())}
    return {"bundled": summ(BUNDLED), "local": summ(LOCAL),
            "bundled_dir": str(BUNDLED), "local_dir": str(LOCAL)}


__all__ = ["get", "put", "promote", "stats", "DEFAULT_TTL", "BUNDLED", "LOCAL"]
