#!/usr/bin/env python3
"""Deterministic fallback report builder for biz-case-workflow.

The report agent is the workflow's fragile last step: a single mid-response API
drop or a credit lapse leaves a 60-minute run with everything computed but no
report.html. This rebuilds a self-contained HTML report from the workflow's
result JSON — no agent, no network, so it cannot fail the way the agent can.

Usage:
    python3 build_report.py --result <result.json | task-output.json> \
                            --out <path/to/report.html>

The --result file may be either the raw workflow result object, or the harness
task-output wrapper ({"result": <object-or-json-string>, ...}) — both are
handled. Charts are rendered as tables (an honest representation of the same
numbers); the point of the fallback is guaranteed delivery, not pixels.
"""
import argparse
import html
import json
import sys


def load_result(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    # Unwrap the harness task-output shape if present.
    res = data.get("result", data) if isinstance(data, dict) else data
    if isinstance(res, str):
        res = json.loads(res)
    return res


def esc(x):
    return html.escape("" if x is None else str(x))


def tag(name, text, cls=None):
    c = f' class="{cls}"' if cls else ""
    return f"<{name}{c}>{esc(text)}</{name}>"


VERDICT_CLASS = {
    "pass": "v-pass", "fail": "v-fail",
    "insufficient": "v-warn", "untestable": "v-warn",
    "untested": "v-mute", None: "v-mute",
}


def rows(headers, body_rows):
    """body_rows: list of lists of already-escaped/HTML-safe cells."""
    thead = "".join(f"<th>{esc(h)}</th>" for h in headers)
    trs = ""
    for r in body_rows:
        trs += "<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>"
    return (
        '<div class="tbl-scroll"><table><thead><tr>'
        + thead + "</tr></thead><tbody>" + trs + "</tbody></table></div>"
    )


def build(res):
    P = []  # page parts
    decision = res.get("decision", "")
    opts = res.get("options", {}) or {}
    framed = opts.get("framed", []) or []
    excluded = opts.get("excluded", []) or []
    killed = {k.get("id"): k.get("cause") for k in (opts.get("killed", []) or [])}
    alive = set(opts.get("alive", []) or [])
    debates = res.get("debates", []) or []
    conditions = res.get("conditions", []) or []
    tests = res.get("test_results", []) or []
    model = res.get("model", {}) or {}
    comp = res.get("competitors", {}) or {}
    choice = res.get("choice", {}) or {}
    critique = res.get("critique", "")

    chosen = choice.get("chosen_option", "")

    # ---- header + recommendation ----
    n_alive, n_killed = len(alive), len(killed)
    badges = (
        f'<span class="badge">選項 <b>{len(framed)}</b></span>'
        f'<span class="badge good">存活 <b>{n_alive}</b></span>'
        f'<span class="badge bad">斬殺 <b>{n_killed}</b></span>'
        f'<span class="badge">辯論 <b>{len(debates)}</b></span>'
        f'<span class="badge">測試 <b>{len(tests)}</b></span>'
    )
    P.append(
        '<header class="mast">'
        '<div class="eyebrow"><span class="dot"></span> Taiwan Business Case '
        "· 假設驅動策略研究 · biz-case-workflow</div>"
        f"<h1>{esc(decision.split(' — ')[0] if decision else 'Business Case')}</h1>"
        f'<p class="sub">{esc(decision)}</p>'
        f'<div class="badges">{badges}</div></header>'
    )

    rationale = choice.get("rationale", "")
    cheapest = choice.get("cheapest_decisive_action", "")
    chosen_name = next((o.get("name") for o in framed if o.get("id") == chosen), chosen or "未定")
    P.append(
        '<div class="rec"><span class="tag">行動摘要 · 建議</span>'
        f"<p>{esc(chosen_name)}</p>"
        + (f'<p class="why">{esc(rationale)}</p>' if rationale else "")
        + (f'<p class="why"><b>最便宜的裁決動作：</b>{esc(cheapest)}</p>' if cheapest else "")
        + "</div>"
    )

    # ---- options map ----
    if framed:
        body = []
        for o in framed:
            oid = o.get("id")
            if oid in killed:
                status = '<span class="v-fail">斬殺</span>'
            elif oid == chosen:
                status = '<span class="v-pass">存活 · 選定</span>'
            elif oid in alive:
                status = '<span class="v-pass">存活</span>'
            else:
                status = '<span class="v-mute">—</span>'
            name = esc(o.get("name"))
            if o.get("is_status_quo"):
                name += ' <span class="mute">（現狀）</span>'
            body.append([name, esc(o.get("happy_story", "")), status])
        P.append(section("選項地圖", "options",
                          rows(["選項", "贏的故事", "狀態"], body)))
        # killed causes
        if killed:
            kc = "".join(
                f"<p><b>{esc(next((o.get('name') for o in framed if o.get('id')==kid), kid))}</b> "
                f"— {esc(cause)}</p>" for kid, cause in killed.items())
            P.append('<div class="box limit"><h3><span class="lbl">死因</span> '
                     f"must-have 條件失敗</h3>{kc}</div>")
        if excluded:
            ex = "".join(f"<li><b>{esc(e.get('name'))}</b> — {esc(e.get('why'))}</li>"
                         for e in excluded)
            P.append(f'<div class="box"><h3>framing 階段即否決</h3><ul>{ex}</ul></div>')

    # ---- debates ----
    if debates:
        body = [[esc(d.get("question")), esc(d.get("bull")), esc(d.get("bear")),
                 esc(d.get("value_at_stake"))] for d in debates]
        P.append(section("關鍵辯論紀錄（bull / bear 各推到滿）", "debates",
                          rows(["辯論", "Bull（正方）", "Bear（反方）", "值多少"], body)))

    # ---- model ----
    if model:
        parts = []
        if model.get("boundary"):
            parts.append(f'<p><b>邊界：</b>{esc(model["boundary"])}</p>')
        rng = model.get("range") or {}
        if rng:
            parts.append(
                f'<p><b>範圍（{esc(rng.get("unit",""))}）：</b>'
                f'{esc(rng.get("low",""))} — {esc(rng.get("high",""))}'
                + (f' · {esc(rng.get("horizon"))}' if rng.get("horizon") else "") + "</p>")
        drivers = model.get("drivers", []) or []
        if drivers:
            body = [[esc(d.get("name")), esc(d.get("low")), esc(d.get("high")),
                     esc(d.get("analog_used") or d.get("basis") or "")] for d in drivers]
            parts.append(rows(["Driver", "低", "高", "基礎/類比"], body))
        if model.get("sensitivity"):
            parts.append(f'<p><b>敏感度：</b>{esc(model["sensitivity"])}</p>')
        if model.get("reconciliation"):
            parts.append(f'<p><b>Top-down / bottom-up 對帳：</b>{esc(model["reconciliation"])}</p>')
        cannot = model.get("what_model_cannot_see", []) or []
        if cannot:
            parts.append("<p><b>模型看不到：</b></p><ul>"
                         + "".join(f"<li>{esc(x)}</li>" for x in cannot) + "</ul>")
        P.append(section("市場模型（driver tree · 兩端範圍）", "model", "".join(parts)))

    # ---- competitors ----
    if comp:
        parts = []
        dims = comp.get("dimensions", []) or []
        if dims:
            parts.append("<p><b>維度：</b></p><ul>"
                         + "".join(f"<li>{esc(d)}</li>" for d in dims) + "</ul>")
        players = comp.get("players", []) or []
        if players:
            body = [[esc(p.get("name")), esc(p.get("archetype")),
                     esc(p.get("binding_constraint"))] for p in players]
            parts.append(rows(["玩家", "原型", "約束條件"], body))
        if comp.get("share_dynamics"):
            parts.append(f'<p><b>份額動態：</b>{esc(comp["share_dynamics"])}</p>')
        blind = comp.get("blind_spots", []) or []
        if blind:
            parts.append("<p><b>盲區：</b></p><ul>"
                         + "".join(f"<li>{esc(x)}</li>" for x in blind) + "</ul>")
        P.append(section("競爭者分析（同一套維度對稱量所有玩家）", "competitors", "".join(parts)))

    # ---- what you need to believe ----
    wynb = choice.get("what_you_need_to_believe", []) or []
    if wynb:
        P.append(section("What You Need To Believe（存活假設）", "wynb",
                         "<ol>" + "".join(f"<li>{esc(x)}</li>" for x in wynb) + "</ol>"))

    # ---- scenarios ----
    sc = choice.get("scenarios") or {}
    if sc:
        body = [[esc(k), esc(v)] for k, v in
                (("Bull", sc.get("bull")), ("Base", sc.get("base")), ("Bear", sc.get("bear")))
                if v]
        P.append(section("情境：Bull / Base / Bear", "scenarios",
                          rows(["情境", "內容"], body)))

    # ---- signposts ----
    sp = choice.get("signposts", []) or []
    if sp:
        body = [[esc(s.get("indicator")), esc(s.get("threshold")), esc(s.get("moves_toward"))]
                for s in sp]
        P.append(section("Signposts 監測計畫", "signposts",
                          rows(["指標", "門檻", "推向"], body)))

    # ---- conditions + tests appendix ----
    if conditions:
        body = []
        for c in conditions:
            v = c.get("verdict")
            vc = VERDICT_CLASS.get(v, "v-mute")
            body.append([esc(c.get("option_id")), esc(c.get("area")),
                         esc(c.get("statement")),
                         "★" if c.get("must_have") else "",
                         esc(c.get("confidence")),
                         f'<span class="{vc}">{esc(v or "untested")}</span>'])
        P.append(section("條件與判決", "conditions",
                          rows(["選項", "領域", "條件（what would have to be true）",
                                "must", "信心", "判決"], body)))

    if tests:
        det = []
        for t in tests:
            findings = t.get("findings", []) or []
            fl = "".join(
                f'<li>{esc(f.get("statement",""))} = '
                f'<span class="val">{esc(f.get("value",""))}</span> '
                f'<span class="per">[{esc(f.get("period",""))}] ({esc(f.get("source",""))})</span></li>'
                for f in findings)
            v = t.get("verdict")
            vc = VERDICT_CLASS.get(v, "v-mute")
            det.append(
                f'<details><summary><span class="lp">{esc(t.get("test_id"))}</span>'
                f'<span class="{vc}">{esc(v)}</span></summary>'
                f'<div class="ev-body">'
                + (f"<p>{esc(t.get('reasoning'))}</p>" if t.get("reasoning") else "")
                + (f"<ul>{fl}</ul>" if fl else "")
                + "</div></details>")
        P.append(section("方法論與證據附錄", "appendix",
                         "".join(det)
                         + '<p class="mute">所有來源免費、免金鑰、公開，重跑指令即是驗證。'
                           "此報告由 build_report.py 從 workflow 結果 JSON 確定性重建"
                           "（report agent 失敗時的 fallback）。</p>"))

    if critique:
        P.append('<div class="box limit"><h3><span class="lbl">已知限制</span> '
                 f"completeness critic</h3><p>{esc(critique)}</p></div>")

    return HTML_SHELL.replace("{{TITLE}}", esc((decision.split(" — ")[0] if decision else "商業案例")))\
                     .replace("{{BODY}}", "".join(P))


def section(title, anchor, inner):
    return (f'<section id="{anchor}"><div class="sec-h"><h2>{esc(title)}</h2></div>'
            f"{inner}</section>")


HTML_SHELL = """<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{TITLE}} — 商業案例</title><style>
:root{--paper:#F7F5F0;--surface:#fff;--ink:#1A1A1C;--soft:#524F49;--line:#DED9CF;
--accent:#31527A;--good:#2F6F5E;--bad:#B23A3A;--warn:#9A6B2E;
--serif:"Songti TC","Noto Serif TC",Georgia,serif;
--sans:"PingFang TC","Noto Sans TC","Microsoft JhengHei",-apple-system,system-ui,sans-serif;
--mono:ui-monospace,"SF Mono",Menlo,monospace;}
@media(prefers-color-scheme:dark){:root{--paper:#161719;--surface:#1D1E21;--ink:#E9E6DF;
--soft:#A9A59B;--line:#2E2F33;--accent:#84A9D6;--good:#74BBA1;--bad:#E0908C;--warn:#D6A961;}}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);
font-family:var(--sans);line-height:1.7;font-size:16px}
.wrap{max-width:900px;margin:0 auto;padding:clamp(20px,5vw,56px) clamp(16px,5vw,36px)}
h1,h2{font-family:var(--serif);text-wrap:balance}
.mast{border-bottom:2px solid var(--ink);padding-bottom:16px}
.eyebrow{font-family:var(--mono);font-size:12px;letter-spacing:.12em;text-transform:uppercase;color:var(--soft)}
.eyebrow .dot{display:inline-block;width:5px;height:5px;border-radius:50%;background:var(--accent)}
h1{font-size:clamp(26px,5vw,40px);margin:12px 0 6px}
.sub{color:var(--soft);font-size:15px;max-width:64ch}
.badges{display:flex;flex-wrap:wrap;gap:8px;margin-top:14px}
.badge{font-family:var(--mono);font-size:12px;padding:3px 10px;border-radius:999px;
border:1px solid var(--line);background:var(--surface);color:var(--soft)}
.badge b{color:var(--ink)}.badge.good b{color:var(--good)}.badge.bad b{color:var(--bad)}
.rec{background:var(--surface);border:1px solid var(--line);border-left:4px solid var(--accent);
border-radius:6px;padding:clamp(16px,4vw,28px);margin:24px 0}
.rec .tag{font-family:var(--mono);font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:var(--accent)}
.rec p{font-family:var(--serif);font-size:clamp(17px,2.4vw,22px);line-height:1.5;margin:10px 0 0}
.rec .why{font-family:var(--sans);font-size:15px;color:var(--soft);line-height:1.65}
.rec .why b{color:var(--ink)}
section{margin:36px 0}.sec-h{border-bottom:1px solid var(--line);padding-bottom:8px;margin-bottom:16px}
.sec-h h2{font-size:clamp(18px,3vw,24px);margin:0}
.tbl-scroll{overflow-x:auto}table{border-collapse:collapse;width:100%;font-size:14px;min-width:560px}
th,td{text-align:left;padding:10px 12px;border-bottom:1px solid var(--line);vertical-align:top}
th{font-family:var(--mono);font-size:11px;letter-spacing:.05em;text-transform:uppercase;color:var(--soft)}
.v-pass{color:var(--good);font-weight:600;white-space:nowrap}
.v-fail{color:var(--bad);font-weight:600;white-space:nowrap}
.v-warn{color:var(--warn);font-weight:600;white-space:nowrap}
.v-mute,.mute{color:var(--soft)}
.box{border:1px solid var(--line);border-radius:6px;padding:16px 20px;margin:16px 0;background:var(--surface)}
.box.limit{border-left:4px solid var(--bad)}
.box h3{font-size:15px;margin:0 0 8px}
.box h3 .lbl{font-family:var(--mono);font-size:11px;letter-spacing:.1em;text-transform:uppercase;
color:var(--bad);border:1px solid currentColor;padding:1px 7px;border-radius:4px;margin-right:6px}
.box ul,.box ol{margin:0;padding-left:20px}.box li{margin:8px 0;font-size:14.5px}
ol,ul{padding-left:22px}li{margin:7px 0}
details{border:1px solid var(--line);border-radius:6px;margin:8px 0;background:var(--surface)}
summary{cursor:pointer;padding:11px 14px;font-family:var(--mono);font-size:13px;
display:flex;justify-content:space-between;gap:10px}summary::-webkit-details-marker{display:none}
.ev-body{padding:12px 14px;border-top:1px solid var(--line)}
.ev-body li{font-size:13px}.ev-body .val{font-family:var(--mono);color:var(--accent);font-weight:600}
.ev-body .per{font-family:var(--mono);color:var(--soft);font-size:11px}
footer{margin-top:44px;padding-top:18px;border-top:2px solid var(--ink);
font-family:var(--mono);font-size:12px;color:var(--soft)}
@media print{body{background:#fff;color:#000}.rec,.box,table,details,section{break-inside:avoid}}
</style></head><body><div class="wrap">{{BODY}}
<footer>由 build_report.py 從 workflow 結果 JSON 確定性重建 · taiwan-biz-research biz-case-workflow</footer>
</div></body></html>"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--result", required=True, help="path to result JSON (raw result object or harness task-output wrapper)")
    ap.add_argument("--out", required=True, help="path to write report.html")
    a = ap.parse_args()
    try:
        res = load_result(a.result)
    except Exception as e:
        print(f"error: could not load result JSON from {a.result}: {e}", file=sys.stderr)
        return 1
    if not isinstance(res, dict) or "options" not in res and "choice" not in res:
        print("error: JSON does not look like a biz-case-workflow result "
              "(no 'options'/'choice' keys)", file=sys.stderr)
        return 1
    with open(a.out, "w", encoding="utf-8") as f:
        f.write(build(res))
    print(f"wrote {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
