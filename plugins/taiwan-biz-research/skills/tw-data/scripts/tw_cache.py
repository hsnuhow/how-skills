#!/usr/bin/env python3
"""Inspect and share the tw-data fetch cache.

  python3 scripts/tw_cache.py stats     # what's cached, where, how big
  python3 scripts/tw_cache.py promote   # copy this machine's frozen entries
                                        # into the repo's bundled cache, then
                                        # `git add cache/ && git commit` to share

Two layers (see twdata/_cache.py): LOCAL (~/.claude/tw-data-cache, this machine's
working cache) and BUNDLED (tw-data/cache, committed and shared). `promote` moves
frozen — closed-period, never-changing — entries from LOCAL into BUNDLED so anyone
who pulls the repo skips re-fetching that history. Set TW_DATA_CACHE to relocate
LOCAL; TW_DATA_NOCACHE=1 to disable caching entirely.
"""

import json
import sys

from twdata import _cache


def main() -> None:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "stats"
    if cmd == "stats":
        s = _cache.stats()
        print(json.dumps(s, ensure_ascii=False, indent=2))
        b, l = s["bundled"], s["local"]
        print(f"\n  bundled: {b['entries']} entries ({b['frozen']} frozen), "
              f"{b['bytes'] / 1e6:.1f} MB — {s['bundled_dir']}")
        print(f"  local:   {l['entries']} entries ({l['frozen']} frozen), "
              f"{l['bytes'] / 1e6:.1f} MB — {s['local_dir']}")
    elif cmd == "promote":
        n = _cache.promote()
        print(f"promoted {n} frozen entr{'y' if n == 1 else 'ies'} into {_cache.BUNDLED}")
        if n:
            print("now: git add cache/ && git commit  (to share the frozen history)")
    else:
        print(__doc__)
        sys.exit(2)


if __name__ == "__main__":
    main()
