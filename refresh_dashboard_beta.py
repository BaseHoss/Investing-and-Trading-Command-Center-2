#!/usr/bin/env python3
"""Beta assembler: dashboard_template_beta.html + dashboard_data_beta.json -> investing-dashboard-beta.html.
Same contract as production refresh_dashboard.py. Validates JSON first. Never hand-edit the output."""
import json
t=open('dashboard_template_beta.html').read()
d=open('dashboard_data_beta.json').read()
json.loads(d)
assert '__DATA__' in t, 'template missing __DATA__ token'
out=t.replace('__DATA__',d)
open('investing-dashboard-beta.html','w').write(out)
print('OK beta assembled:',len(t),'template +',len(d),'data ->',len(out),'bytes')
