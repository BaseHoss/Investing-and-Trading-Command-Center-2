#!/usr/bin/env python3
"""One-shot server-side patch: fix the news-card field swap (publisher=s, paragraph=p)
and harden the publisher band so it always shows. Idempotent + self-verifying."""
import json, sys

t = open('dashboard_template_beta.html').read()

old_story = "function story(n,cross){return '<div class=\"story\"><div class=\"thumb\" style=\"background:linear-gradient(135deg,'+n.c1+','+n.c2+')\">'+publogo(n.p)+'<span class=\"tsrc\">'+n.p+'</span></div><div class=\"body\"><span class=\"kicker\">'+(cross?'From the '+cross+' desk':'')+'<span class=\"date\">'+n.dt+'</span></span><h4>'+n.h+'</h4><p>'+n.s+'</p><a class=\"btn\" href=\"'+n.u+'\" target=\"_blank\" rel=\"noopener\">Read full article \\u2192</a><span class=\"src\">Source: '+n.p+'</span></div></div>';}"
new_story = "function story(n,cross){var pub=(n.s||n.p||'Newswire');var para=(n.p||n.s||'');var kick=(cross?'From the '+cross+' desk ':'');return '<div class=\"story\"><div class=\"thumb\" style=\"background:linear-gradient(135deg,'+(n.c1||'#1d49c4')+','+(n.c2||'#22d3ee')+')\">'+publogo(pub)+'<span class=\"tsrc\" title=\"'+pub+'\">'+pub+'</span></div><div class=\"body\"><span class=\"kicker\">'+kick+'<span class=\"date\">'+(n.dt||'')+'</span></span><h4>'+(n.h||'Market update')+'</h4><p>'+para+'</p><a class=\"btn\" href=\"'+(n.u||'#')+'\" target=\"_blank\" rel=\"noopener\">Read full article \\u2192</a><span class=\"src\">Source: '+pub+'</span></div></div>';}"

old_css = ".story .thumb .tsrc{color:rgba(255,255,255,.96);font-weight:800;font-size:13.5px;text-shadow:0 1px 3px rgba(0,0,0,.25)}"
new_css = ".story .thumb{min-width:0}.story .thumb .tsrc{color:rgba(255,255,255,.98);font-weight:800;font-size:13.5px;text-shadow:0 1px 4px rgba(0,0,0,.55);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;min-width:0;flex:1}"

changed = False
if old_story in t:
    t = t.replace(old_story, new_story); changed = True
elif new_story not in t:
    print('ERROR: story() neither old nor new found'); sys.exit(1)
if old_css in t:
    t = t.replace(old_css, new_css); changed = True
elif new_css not in t:
    print('ERROR: tsrc css neither old nor new found'); sys.exit(1)

if not all(ord(c) < 128 for c in t):
    print('ERROR: non-ascii introduced'); sys.exit(1)
open('dashboard_template_beta.html', 'w').write(t)

d = json.load(open('dashboard_data_beta.json'))
d['build_meta']['build_version'] = '2.5.4'
json.dump(d, open('dashboard_data_beta.json', 'w'), separators=(',', ':'))
print('news hotfix applied (changed=%s), version -> 2.5.4' % changed)
