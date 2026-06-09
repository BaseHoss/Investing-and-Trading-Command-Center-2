#!/usr/bin/env python3
"""One-shot UI patch (2.5.5): fix Price Explorer card sizing (fixed height, decoupled
from the left label) + shorten row labels + mobile layout (period selector wrap,
status-bar build-version inline, header/section width). Idempotent + self-verifying."""
import json, sys

t = open('dashboard_template_beta.html').read()
edits = []

def rep(old, new, tag):
    global t
    if old in t:
        t = t.replace(old, new); edits.append(tag + ':applied')
    elif new in t:
        edits.append(tag + ':already')
    else:
        print('ERROR: anchor not found for', tag); sys.exit(1)

# 1) Cards always equal size: fixed min-height + vertically centered content
rep(".aset{border:1px solid var(--line);background:var(--card2);border-radius:10px;padding:7px 9px;cursor:pointer;text-align:left;transition:.12s;min-width:0}",
    ".aset{border:1px solid var(--line);background:var(--card2);border-radius:10px;padding:7px 9px;cursor:pointer;text-align:left;transition:.12s;min-width:0;min-height:56px;display:flex;flex-direction:column;justify-content:center}",
    "aset-fixed-height")

# 2) Row no longer stretches cards to label height; slightly wider, label centered
rep(".exprow{display:grid;grid-template-columns:60px 1fr;gap:8px;margin-top:8px;align-items:stretch}",
    ".exprow{display:grid;grid-template-columns:64px 1fr;gap:8px;margin-top:8px;align-items:center}",
    "exprow-decouple")

# 3) Short, code-name row labels so they never wrap into many rows
rep('<div class="rowlab"><b>Live &#xB7; stocks &amp; semis</b><span>full price history</span></div>',
    '<div class="rowlab"><b>STOCKS</b><span>&amp; semis</span></div>',
    "label-row1")
rep('<div class="rowlab"><b>Live &#xB7; index, gold, crypto</b><span>+ GCC reference theses</span></div>',
    '<div class="rowlab"><b>MARKETS</b><span>index, gold, crypto</span></div>',
    "label-row2")

# 4) Mobile: replace the media block tail with extra rules (selector wrap, status inline, widths)
rep(" .pgbtn{width:auto;flex:1;padding:9px 6px;font-size:12px}\n}",
    " .pgbtn{width:auto;flex:1;padding:9px 6px;font-size:12px}\n"
    " .modhead{flex-direction:column;align-items:flex-start;gap:7px}\n"
    " .modhead h2{font-size:15px}\n"
    " .dur{display:flex;flex-wrap:wrap;width:100%;justify-content:center;gap:2px}\n"
    " .dur button{flex:1 0 auto;min-width:38px;padding:7px 4px;font-size:11px}\n"
    " .runstatus{gap:5px 12px;padding:10px 12px;font-size:10px}\n"
    " .runstatus span[style]{margin-left:0 !important}\n"
    " .topnav .in{padding:9px 12px}\n"
    "}",
    "mobile-rules")

if not all(ord(c) < 128 for c in t):
    print('ERROR: non-ascii introduced'); sys.exit(1)
open('dashboard_template_beta.html', 'w').write(t)

d = json.load(open('dashboard_data_beta.json'))
d['build_meta']['build_version'] = '2.5.5'
json.dump(d, open('dashboard_data_beta.json', 'w'), separators=(',', ':'))
print('UI hotfix applied:', ' | '.join(edits), '| version -> 2.5.5')
