"""Minimal zero-dependency .xlsx reader.

tw-data deliberately ships with no third-party dependencies — every other
script uses only the stdlib through `_fetch.py`. Some sources (財政統計月報 on
service.mof.gov.tw) serve .xlsx rather than CSV, so this reads the sheet grid
without pulling in openpyxl.

An .xlsx is a zip of XML. Cell text lives either inline or, more often, as an
index into a shared-strings table. Empty cells are omitted from the row, so a
cell reference (A1 -> row 1, col 1) is the only reliable way to place values;
naive positional parsing silently shifts every column after the first gap.

Scope is deliberately small: read a worksheet into a dense list-of-rows of
strings. No styles, no formulas-as-written, no dates-as-serials handling beyond
returning the raw number. That is all the MOF monthly tables need.
"""

from __future__ import annotations

import io
import re
import xml.etree.ElementTree as ET
import zipfile

_NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
_R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
_CELL_RE = re.compile(r"^([A-Z]+)(\d+)$")


def _col_to_idx(col: str) -> int:
    """'A' -> 0, 'Z' -> 25, 'AA' -> 26."""
    n = 0
    for ch in col:
        n = n * 26 + (ord(ch) - ord("A") + 1)
    return n - 1


def _shared_strings(zf: zipfile.ZipFile) -> list[str]:
    try:
        raw = zf.read("xl/sharedStrings.xml")
    except KeyError:
        return []
    out: list[str] = []
    for si in ET.fromstring(raw).findall(f"{_NS}si"):
        # a shared string is either one <t> or a run of <r><t> pieces
        parts = [t.text or "" for t in si.iter(f"{_NS}t")]
        out.append("".join(parts))
    return out


def _sheet_targets(zf: zipfile.ZipFile) -> list[tuple[str, str]]:
    """-> [(sheet name, worksheet path)] in workbook order."""
    wb = ET.fromstring(zf.read("xl/workbook.xml"))
    rels_raw = zf.read("xl/_rels/workbook.xml.rels")
    rid_to_target = {
        rel.get("Id"): rel.get("Target")
        for rel in ET.fromstring(rels_raw)
    }
    out = []
    for sh in wb.find(f"{_NS}sheets") or []:
        rid = sh.get(f"{_R}id")
        target = rid_to_target.get(rid, "")
        if target and not target.startswith("/"):
            target = "xl/" + target.lstrip("/")
        out.append((sh.get("name") or "", target))
    return out


def _read_sheet(zf: zipfile.ZipFile, path: str, strings: list[str]) -> list[list[str]]:
    root = ET.fromstring(zf.read(path))
    rows: list[list[str]] = []
    for row in root.iter(f"{_NS}row"):
        cells: dict[int, str] = {}
        maxc = -1
        for c in row.findall(f"{_NS}c"):
            ref = c.get("r") or ""
            m = _CELL_RE.match(ref)
            ci = _col_to_idx(m.group(1)) if m else len(cells)
            t = c.get("t")
            if t == "s":  # shared-string index
                v = c.find(f"{_NS}v")
                text = strings[int(v.text)] if v is not None and v.text else ""
            elif t == "inlineStr":
                text = "".join(x.text or "" for x in c.iter(f"{_NS}t"))
            else:  # number, or formula string in <v>
                v = c.find(f"{_NS}v")
                text = v.text if v is not None and v.text is not None else ""
            cells[ci] = text
            maxc = max(maxc, ci)
        rows.append([cells.get(i, "") for i in range(maxc + 1)])
    return rows


def read_xlsx(body: bytes) -> dict[str, list[list[str]]]:
    """Parse .xlsx bytes into {sheet name: [[cell, ...], ...]}.

    Cells are strings (numbers as their raw text). Empty cells are ''. Rows are
    padded to the last non-empty cell in that row only, so different rows may
    have different lengths — index defensively.
    """
    with zipfile.ZipFile(io.BytesIO(body)) as zf:
        strings = _shared_strings(zf)
        return {
            name: _read_sheet(zf, path, strings)
            for name, path in _sheet_targets(zf)
            if path
        }


__all__ = ["read_xlsx"]
