#!/usr/bin/env python3
"""Apply daily_update.json (small delta) to the price DB + dashboard_data_beta.json.
Runs IDENTICALLY on GitHub Actions (server rebuild) and locally (Cowork mirror).

DATA-INTEGRITY RULES (v3, 2026-06-09):
- CANDLE FINALITY (B1): never store a row dated today (UTC) or later. Only fully
  closed prior sessions enter the database, so a mid-day or random intraday run can
  never freeze a partial close as final.
- PROVISIONAL SELF-HEAL: incoming rows whose date already exists are UPSERTED
  (overwritten) only if within REFRESH_WINDOW_DAYS of today; this lets a later run
  replace any earlier provisional close with the final one. Rows older than the
  window are immutable (history is never rewritten).
- FUSE-SAFE: the DB filename rotates as end_date advances; os.remove of the old file
  can fail on a OneDrive/FUSE mount (lock). That is caught and downgraded to a warning
  (the newest file always wins via sorted glob); the run is NOT failed for it.
- TOLERANT SYMBOLS: a symbol present in the delta but not in this DB is skipped with a
  warning (not fatal), so a lagging local mirror does not fail when the authoritative
  repo DB already carries more symbols.
- TYPE COERCION: vix.px / vix.day coerced to float (strips %, +). Non-numeric -> fail.

Delta schema: {rows:{SYM:[[date,close],...]}, vix:{}, asof:"", macro:"", action:"",
notes:{SYM}, rec:{SYM}, risk:{SYM}, earnings:{SYM}, fund:{SYM}, news:{}, active_situations:[],
build_meta:{}}. Validates: >=9 assets, required keys, ASCII-only, em/en dash ban.
"""
import json, glob, sys, os, datetime

REFRESH_WINDOW_DAYS = 16
TODAY_UTC = datetime.datetime.utcnow().date()
TODAY = TODAY_UTC.isoformat()
WINDOW_CUT = (TODAY_UTC - datetime.timedelta(days=REFRESH_WINDOW_DAYS)).isoformat()

def num(x):
    """Coerce '+5.0%' / '21.51' / 21.51 -> float; raise on garbage."""
    if isinstance(x, (int, float)):
        return float(x)
    return float(str(x).replace('%', '').replace('+', '').strip())

u = json.load(open('daily_update.json'))
dbf = sorted(glob.glob('stock_price_db_*_to_*.json'))[-1]
db = json.load(open(dbf))

rejected_future, upserts, appends = [], 0, 0
for sym, rows in (u.get('rows') or {}).items():
    if sym not in db['prices']:
        print('WARN: symbol not in this DB (skipped; authoritative copy may have it):', sym); continue
    existing = {str(d)[:10]: round(float(p), 2) for d, p in db['prices'][sym]}
    for d, p in rows:
        d = str(d)[:10]; p = round(float(p), 2)
        if p <= 0:
            print('ERROR: bad price', sym, d, p); sys.exit(1)
        if d >= TODAY:                      # B1: candle not final yet
            rejected_future.append('%s %s' % (sym, d)); continue
        if d in existing:
            if d >= WINDOW_CUT and existing[d] != p:
                existing[d] = p; upserts += 1   # finalize a provisional close
            continue                            # else immutable history
        existing[d] = p; appends += 1
    merged = sorted(existing.items())
    db['prices'][sym] = [[d, p] for d, p in merged]
    m = db['meta']['symbols'][sym]
    m['last_date'] = merged[-1][0]; m['points'] = len(merged)
    db['meta']['end_date'] = max(db['meta']['end_date'], merged[-1][0])

if rejected_future:
    print('candle-finality: skipped not-yet-final rows:', ', '.join(rejected_future))
print('rows upserted (provisional->final):', upserts, '| appended:', appends)

db['meta']['last_updated'] = datetime.datetime.now().isoformat(timespec='seconds')
target = 'stock_price_db_%s_to_%s.json' % (db['meta']['start_date'], db['meta']['end_date'])
json.dump(db, open(target, 'w'), separators=(',', ':'))
if target != dbf:
    try:
        os.remove(dbf); print('rotated DB file:', dbf, '->', target)
    except OSError as e:
        print('WARN: could not remove old DB file (FUSE lock, non-fatal):', dbf, '|', e)
        print('      newest file', target, 'is authoritative via sorted glob.')

d = json.load(open('dashboard_data_beta.json'))
for sym, rows in db['prices'].items():
    if sym not in d['assets']: continue
    a = d['assets'][sym]
    a['dates'] = [r[0] for r in rows]; a['prices'] = [r[1] for r in rows]
    a['px'] = rows[-1][1]; a['day'] = round((rows[-1][1] / rows[-2][1] - 1) * 100, 2)
for k in ['vix', 'macro', 'asof', 'news', 'active_situations', 'build_meta', 'action']:
    if k in u: d[k] = u[k]
if isinstance(d.get('vix'), dict):
    try:
        d['vix']['px'] = round(num(d['vix'].get('px')), 2)
        d['vix']['day'] = round(num(d['vix'].get('day')), 2)
    except (TypeError, ValueError):
        print('ERROR: vix px/day not numeric:', d.get('vix')); sys.exit(1)
d.setdefault('build_meta', {})['price_db'] = target
for field in ['notes', 'rec', 'risk', 'earnings', 'fund']:
    for sym, val in (u.get(field) or {}).items():
        if sym in d['assets']:
            d['assets'][sym]['note' if field == 'notes' else field] = val

required = ['asof', 'assets', 'quoteOnly', 'news', 'macro', 'vix', 'active_situations', 'build_meta']
missing = [k for k in required if k not in d]
if missing: print('ERROR: missing keys', missing); sys.exit(1)
if len(d['assets']) < 9: print('ERROR: fewer than 9 assets, got', len(d['assets'])); sys.exit(1)
if len(d.get('active_situations', [])) > 5:
    print('ERROR: more than 5 active_situations:', d['active_situations']); sys.exit(1)
out = json.dumps(d, separators=(',', ':'))
if '\\u2014' in out or '\\u2013' in out:
    print('ERROR: em/en dash found in data'); sys.exit(1)
if any(ord(c) > 127 for c in out):
    print('ERROR: non-ascii in serialized data'); sys.exit(1)
open('dashboard_data_beta.json', 'w').write(out)
print('OK applied delta | asof', d.get('asof'), '| build', d['build_meta'].get('build_version', '?'),
      '| assets', len(d['assets']), '| situations', len(d.get('active_situations', [])), '| db', target)
