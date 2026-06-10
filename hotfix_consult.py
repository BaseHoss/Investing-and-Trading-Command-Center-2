#!/usr/bin/env python3
"""Patch 2.6.1: (A) Explorer add-dropdown shows each position's price + day change on the
same line; (B) Position Consultant picks scale with the amount (3 small -> up to 5 larger)
for diversification. Idempotent + self-verifying (pure ASCII)."""
import json, sys
t = open('dashboard_template_beta.html').read()
def rep(o, n, tag):
    global t
    if o in t: t = t.replace(o, n); print('ok', tag)
    elif n in t: print('already', tag)
    else: print('FAIL anchor', tag); sys.exit(1)

# A) dropdown option: append price + signed day% (plain text; refs show '(ref)')
rep("opts.push('<option value=\"'+p.id+'\">'+p.id+(p.name?' &#183; '+p.name:'')+'</option>');",
    "opts.push('<option value=\"'+p.id+'\">'+p.id+(p.name?' &#183; '+p.name:'')+(p.ref?'  (ref)':('  '+(p.cur||'$')+fmt(p.px)+'  '+(p.day>=0?'+':'')+Number(p.day).toFixed(2)+'%'))+'</option>');",
    "dropdown-pxchg")

# B) adaptive pick count by amount
rep(' const picks=cands.slice(0,3);',
    ' var nPick=amt<1000?3:(amt<3000?4:5);const picks=cands.slice(0,nPick);',
    'adaptive-picks')

# B2) explain it in the limitations text
rep("not stock-picking alpha.';",
    "not stock-picking alpha. The number of suggested positions scales with the amount (3 for small accounts, up to 5 for larger) to aid diversification, not to add alpha.';",
    'limits-note')

assert all(ord(c) < 128 for c in t), 'non-ascii introduced'
open('dashboard_template_beta.html', 'w').write(t)
d = json.load(open('dashboard_data_beta.json')); d['build_meta']['build_version'] = '2.6.1'
json.dump(d, open('dashboard_data_beta.json', 'w'), separators=(',', ':'))
print('consult patch applied; version 2.6.1')
