# tw-data bundled cache

Frozen fetch payloads that ship with the plugin so a fresh clone skips
re-downloading history that will never change (past-month 財政統計月報, published
survey years, closed tax years).

- `manifest.json` maps `sha1(url)` → `{url, fetched, bytes, frozen:true}`.
- `{sha1}.bin` is the raw body.

Populated by `python3 scripts/tw_cache.py promote`, which copies frozen entries
from the local working cache (`~/.claude/tw-data-cache`) here. Then commit this
directory. See `twdata/_cache.py`.
