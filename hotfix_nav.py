#!/usr/bin/env python3
"""One-shot nav patch (2.5.6): mobile top bar no longer overflows the dashboard width.
The two page buttons drop to their own full-width row; the theme toggle stays top-right
and its text may wrap. Desktop nav unchanged. Idempotent + self-verifying."""
import json, sys

t = open('dashboard_template_beta.html').read()

old = " .topnav .in{padding:9px 12px}\n}"
new = (" .topnav .in{flex-wrap:wrap;gap:8px;padding:9px 14px}\n"
       " .thbtn{order:2;margin-left:auto;white-space:normal;line-height:1.15;text-align:center;padding:7px 10px}\n"
       " .pagebtns{order:3;flex-basis:100%;margin-top:2px}\n"
       "}")
if old in t:
    t = t.replace(old, new)
elif new in t:
    pass
else:
    print('ERROR: mobile nav anchor not found'); sys.exit(1)

if not all(ord(c) < 128 for c in t):
    print('ERROR: non-ascii introduced'); sys.exit(1)
open('dashboard_template_beta.html', 'w').write(t)

d = json.load(open('dashboard_data_beta.json'))
d['build_meta']['build_version'] = '2.5.6'
json.dump(d, open('dashboard_data_beta.json', 'w'), separators=(',', ':'))
print('nav hotfix applied | version -> 2.5.6')
