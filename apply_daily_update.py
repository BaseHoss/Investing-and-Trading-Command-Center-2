#!/usr/bin/env python3
"""Apply daily_update.json (small delta) to the price DB + dashboard_data_beta.json.
Runs IDENTICALLY on GitHub Actions (server rebuild) and locally (Cowork mirror).
Delta schema: {rows:{SYM:[[date,close],...]}, vix:{}, asof:"", macro:"", notes:{SYM:""},
rec:{SYM:""}, risk:{SYM:""}, earnings:{SYM:{}}, fund:{SYM:{}}, news:{}, active_situations:[],
build_meta:{}}. Idempotent: rows on or before each symbol's last_date are skipped.
Validates: 9 assets, required keys, ASCII-only, em/en dash ban. Exits non-zero on any failure."""
import json, glob, sys, os, datetime

u = json.load(open('daily_update.json'))
dbf = sorted(glob.glob('stock_price_db_*_to_*.json'))[-1]
db = json.load(open(dbf))

for sym, rows in (u.get('rows') or {}).items():
    if sym not in db['prices']:
        print('ERROR: unknown symbol', sym); sys.exit(1)
    last = db['meta']['symbols'][sym]['last_date']
    new = sorted({str(r[0])[:10]: round(float(r[1]), 2) for r in rows if str(r[0])[:10] > last}.items())
    if not new:
        print(sym, 'no new rows after', last); continue
    assert all(p > 0 for _, p in new), 'bad price in ' + sym
    db['prices'][sym].extend([[d, p] for d, p in new])
    m = db['meta']['symbols'][sym]
    m['last_date'] = new[-1][0]; m['points'] = len(db['prices'][sym])
    db['meta']['end_date'] = max(db['meta']['end_date'], new[-1][0])
    print('appended', len(new), 'rows to', sym)
db['meta']['last_updated'] = datetime.datetime.now().isoformat(timespec='seconds')
target = 'stock_price_db_%s_to_%s.json' % (db['meta']['start_date'], db['meta']['end_date'])
json.dump(db, open(target, 'w'), separators=(',', ':'))
if target != dbf:
    os.remove(dbf); print('renamed:', dbf, '->', target)

d = json.load(open('dashboard_data_beta.json'))
for sym, rows in db['prices'].items():
    if sym not in d['assets']: continue
    a = d['assets'][sym]
    a['dates'] = [r[0] for r in rows]; a['prices'] = [r[1] for r in rows]
    a['px'] = rows[-1][1]; a['day'] = round((rows[-1][1] / rows[-2][1] - 1) * 100, 2)
for k in ['vix', 'macro', 'asof', 'news', 'active_situations', 'build_meta']:
    if k in u: d[k] = u[k]
d.setdefault('build_meta', {})['price_db'] = target
for field in ['notes', 'rec', 'risk', 'earnings', 'fund']:
    for sym, val in (u.get(field) or {}).items():
        if sym in d['assets']:
            d['assets'][sym]['note' if field == 'notes' else field] = val

required = ['asof', 'assets', 'quoteOnly', 'news', 'macro', 'vix', 'active_situations', 'build_meta']
missing = [k for k in required if k not in d]
if missing: print('ERROR: missing keys', missing); sys.exit(1)
if len(d['assets']) != 9: print('ERROR: expected 9 assets, got', len(d['assets'])); sys.exit(1)
out = json.dumps(d, separators=(',', ':'))
if '\\u2014' in out or '\\u2013' in out:
    print('ERROR: em/en dash found in data'); sys.exit(1)
if any(ord(c) > 127 for c in out):
    print('ERROR: non-ascii in serialized data'); sys.exit(1)
open('dashboard_data_beta.json', 'w').write(out)
print('OK applied delta | asof', d.get('asof'), '| build', d['build_meta'].get('build_version', '?'), '| db', target)
