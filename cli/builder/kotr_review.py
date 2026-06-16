#!/usr/bin/env python3
"""kotr_review.py — build a clickable HTML slide deck reviewing recent autonomous activity.

Reads #kotr-ai-builders (the performance record), categorizes each actor's posts into wins vs
problems, flags routines that keep failing, folds in service health + the latest kotr-ai pulse,
and writes a self-contained deck to the Windows desktop. Re-run any morning.

Usage: python3 kotr_review.py
"""
import re, subprocess, os, html, datetime

VSS = os.path.expanduser("~/Visual_Studio_Settings")
READ = os.path.join(VSS, "cli/discord/read_channel.py")
BLOG = os.path.join(VSS, "cli/builder/BLOCKED_ROUTINES_LOG.md")
OUT = "/mnt/c/Users/ureth/Desktop/KOTR_Review.html"
CH = "1515624584815181905"

WIN = re.compile(r"✅|SWEEP GREEN|\bDONE\b|shipped|verified|online|GREEN", re.I)
BAD = re.compile(r"\bFAIL|RED\b|blocked|❌|error|stuck|timed? out|could ?n.t|unable|stalled|partial", re.I)

def channel(limit=100):
    out = subprocess.run(["python3", READ, "--channel", CH, "--limit", str(limit)],
                         capture_output=True, text=True).stdout
    msgs, cur = [], None
    for line in out.splitlines():
        m = re.match(r"^\[(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d)\]\s+(.*?):\s?(.*)$", line)
        if m:
            if cur: msgs.append(cur)
            cur = {"ts": m.group(1), "who": m.group(2), "text": m.group(3)}
        elif cur is not None:
            cur["text"] += " " + line.strip()
    if cur: msgs.append(cur)
    return msgs

def classify(t):
    bad = bool(BAD.search(t)); win = bool(WIN.search(t))
    return "problem" if (bad and not win) else ("win" if win else "info")

def svc():
    rows = []
    for u in ("gir-listener", "kotr-listener", "kotr-ai-pulse"):
        s = subprocess.run(["systemctl", "--user", "is-active", u], capture_output=True, text=True).stdout.strip()
        rows.append((u, s))
    return rows

def pulse_latest():
    try:
        blocks = open(BLOG).read().split("## ")
        return ("## " + blocks[-1]).strip()[:1200] if len(blocks) > 1 else "(no pulse output yet)"
    except Exception:
        return "(no pulse log)"

msgs = channel(100)
actors = {}
for m in msgs:
    a = actors.setdefault(m["who"], {"win": 0, "problem": 0, "info": 0, "last": "", "lastbad": ""})
    c = classify(m["text"]); a[c] += 1; a["last"] = m["text"][:140]
    if c == "problem": a["lastbad"] = m["text"][:160]
problems = [m for m in msgs if classify(m["text"]) == "problem"]
repeat = {a: d for a, d in actors.items() if d["problem"] >= 2}
now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%MZ")
span = f'{msgs[-1]["ts"]} → {msgs[0]["ts"]}' if msgs else "no data"

def esc(s): return html.escape(s)
def bar(w, p, i):
    tot = max(w + p + i, 1)
    return (f'<span class=seg style="width:{w/tot*100:.0f}%;background:#3fb950"></span>'
            f'<span class=seg style="width:{p/tot*100:.0f}%;background:#f85149"></span>'
            f'<span class=seg style="width:{i/tot*100:.0f}%;background:#444"></span>')

slides = []
# 1 title
slides.append(f"""<section><h1>KOTR — Nightly Review</h1>
<p class=sub>generated {now} · window {esc(span)} · {len(msgs)} posts · {len(actors)} actors</p>
<p class=big>{sum(a['win'] for a in actors.values())} ✅ wins · {len(problems)} ⚠️ problems</p>
<p class=hint>← → or scroll to navigate</p></section>""")
# 2 per-actor
rows = "".join(f"<tr><td>{esc(a)}</td><td class=n>{d['win']}</td><td class=n>{d['problem']}</td>"
               f"<td class=bar>{bar(d['win'],d['problem'],d['info'])}</td></tr>"
               for a, d in sorted(actors.items(), key=lambda x:-x[1]['win']-x[1]['problem']))
slides.append(f"""<section><h2>Per-actor activity</h2>
<table><tr><th>actor</th><th>✅</th><th>⚠️</th><th>mix (green/red/info)</th></tr>{rows}</table>
<p class=hint>green = wins · red = problems · gray = info</p></section>""")
# 3 wins
wins = [m for m in msgs if classify(m["text"]) == "win"][:8]
wl = "".join(f"<li><b>{esc(m['who'])}</b> · {esc(m['text'][:150])}</li>" for m in wins) or "<li>none</li>"
slides.append(f"<section><h2>✅ Recent wins</h2><ul class=feed>{wl}</ul></section>")
# 4 problems / repeat failures
rep = "".join(f"<li><b>{esc(a)}</b> — {d['problem']} problem posts · last: {esc(d['lastbad'])}</li>"
              for a, d in repeat.items()) or "<li>No actor has ≥2 problem posts in this window. 🎉</li>"
pl = "".join(f"<li><b>{esc(m['who'])}</b> · {esc(m['text'][:160])}</li>" for m in problems[:8]) or "<li>none</li>"
slides.append(f"""<section><h2>⚠️ Problems &amp; repeated failures</h2>
<h3>Continuously failing (≥2):</h3><ul class=feed>{rep}</ul>
<h3>Recent problem posts:</h3><ul class=feed>{pl}</ul></section>""")
# 5 health + pulse
sv = "".join(f"<li>{'🟢' if s=='active' else '🔴'} {u} — {s}</li>" for u, s in svc())
slides.append(f"""<section><h2>Backend health &amp; kotr-ai pulse</h2>
<ul class=feed>{sv}</ul><h3>Latest pulse (blocked-routine analysis):</h3>
<pre>{esc(pulse_latest())}</pre></section>""")
# 6 verdict
direction = ("trending UP — wins dominate" if sum(a['win'] for a in actors.values()) > 3*len(problems)
             else "MIXED — review the problems slide")
slides.append(f"""<section><h2>Verdict</h2>
<p class=big>{direction}</p>
<ul class=feed>
<li>Most active: {esc(max(actors, key=lambda a:actors[a]['win']+actors[a]['problem'])) if actors else '—'}</li>
<li>{len(repeat)} actor(s) with repeated problems — see slide 4</li>
<li>Re-run this deck anytime: <code>python3 ~/Visual_Studio_Settings/cli/builder/kotr_review.py</code></li>
</ul></section>""")

DOC = """<!doctype html><meta charset=utf-8><title>KOTR Nightly Review</title><style>
html,body{margin:0;background:#0d1117;color:#c9d1d9;font:16px/1.5 'Segoe UI',sans-serif;scroll-snap-type:y mandatory;overflow-y:scroll;height:100vh}
section{min-height:100vh;scroll-snap-align:start;padding:6vh 8vw;box-sizing:border-box;border-bottom:1px solid #21262d}
h1{font-size:3em;margin:.2em 0;color:#58a6ff}h2{font-size:2em;color:#58a6ff}h3{color:#8b949e;margin:.8em 0 .3em}
.sub,.hint{color:#6e7681}.big{font-size:1.6em;color:#3fb950}.hint{font-size:.85em}
table{width:100%;border-collapse:collapse;margin-top:1em}td,th{padding:6px 10px;border-bottom:1px solid #21262d;text-align:left}
.n{text-align:center;width:50px}.bar{width:40%}.seg{display:inline-block;height:14px;border-radius:2px}
ul.feed{list-style:none;padding:0}ul.feed li{padding:7px 10px;border-bottom:1px solid #21262d}
pre{background:#161b22;padding:12px;border-radius:6px;white-space:pre-wrap;font-size:.85em;max-height:38vh;overflow:auto}
code{background:#161b22;padding:2px 6px;border-radius:4px}
</style>
<body>__SLIDES__
<script>addEventListener('keydown',e=>{let s=[...document.querySelectorAll('section')],y=scrollY,
i=s.findIndex(el=>el.offsetTop>y+10);if(e.key=='ArrowRight'||e.key=='ArrowDown')(s[i]||s[s.length-1]).scrollIntoView();
if(e.key=='ArrowLeft'||e.key=='ArrowUp')(s[Math.max(0,(i<0?s.length:i)-2)]||s[0]).scrollIntoView();});</script>
""".replace("__SLIDES__", "\n".join(slides))

open(OUT, "w", encoding="utf-8").write(DOC)
print(f"wrote deck: {OUT}  ({len(msgs)} posts, {len(problems)} problems, {len(repeat)} repeat-fail actors)")
