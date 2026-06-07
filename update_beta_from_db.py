#!/usr/bin/env python3
"""DB -> dashboard bridge (beta pipeline step).
Rebuilds the six live assets' series/px/day in dashboard_data_beta.json from the
latest stock_price_db_*.json (after db_append.py delta pulls), preserving all
editorial fields (notes, rec, risk, macro, news, active_situations, vix).
Run order each refresh: 1) delta-pull rows per symbol -> db_append.py
2) update VIX + editorial fields in dashboard_data_beta.json
3) python3 update_beta_from_db.py   4) python3 refresh_dashboard_beta.py"""
import json, glob
db=json.load(open(sorted(glob.glob('stock_price_db_*.json'))[-1]))
d=json.load(open('dashboard_data_beta.json'))
for sym,rows in db['prices'].items():
    if sym not in d['assets']: continue
    a=d['assets'][sym]
    a['dates']=[r[0] for r in rows]
    a['prices']=[r[1] for r in rows]
    a['px']=rows[-1][1]
    a['day']=round((rows[-1][1]/rows[-2][1]-1)*100,2)
d['build_meta']['price_db']=sorted(glob.glob('stock_price_db_*.json'))[-1]
json.dump(d,open('dashboard_data_beta.json','w'),separators=(',',':'))
print('OK beta data rebuilt from',d['build_meta']['price_db'])
