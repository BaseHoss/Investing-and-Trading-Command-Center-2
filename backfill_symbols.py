#!/usr/bin/env python3
"""Server-side 3Y backfill for new tracked symbols (runs in GitHub Actions only).
Fetches daily history from FMP REST (FMP_API_KEY repo secret), aligns each symbol to
NVDA's canonical calendar (forward-fill any gaps), appends to the price DB, and adds
the asset to dashboard_data_beta.json with default editorial. Idempotent: symbols
already in the DB are skipped. Resilient: a symbol that fails to fetch is skipped, not
fatal. The next daily run enriches notes/rec/fundamentals/earnings for the new names."""
import os, json, glob, sys, bisect, datetime, urllib.request, urllib.parse

KEY = os.environ.get('FMP_API_KEY', '').strip()
if not KEY:
    print('ERROR: FMP_API_KEY not set'); sys.exit(1)
BASE = 'https://financialmodelingprep.com/stable/historical-price-eod/light'

# (id, fmp_symbol, display_name, default_risk)
NEW = [
    ('AAPL', 'AAPL', 'Apple', 'Med'),
    ('AMZN', 'AMZN', 'Amazon', 'Med'),
    ('META', 'META', 'Meta Platforms', 'High'),
    ('GOOGL', 'GOOGL', 'Alphabet', 'Med'),
    ('TSLA', 'TSLA', 'Tesla', 'High'),
    ('NFLX', 'NFLX', 'Netflix', 'High'),
    ('DIS', 'DIS', 'Disney', 'Med'),
    ('BRKB', 'BRK-B', 'Berkshire Hathaway', 'Low'),
    ('DIA', 'DIA', 'Dow Jones (DIA)', 'Med'),
    ('SILVER', 'SIUSD', 'Silver (oz)', 'High'),
    ('OIL', 'USO', 'Oil (USO)', 'High'),
]
NOTE = ('Newly added to the tracked universe (server backfill). Editorial review pending; '
        'default Monitor call until the next analyst pass.')

def fetch(sym, frm, to):
    url = '%s?symbol=%s&from=%s&to=%s&apikey=%s' % (BASE, urllib.parse.quote(sym), frm, to, KEY)
    req = urllib.request.Request(url, headers={'User-Agent': 'gh-action'})
    with urllib.request.urlopen(req, timeout=60) as r:
        data = json.loads(r.read().decode())
    if isinstance(data, dict):
        data = data.get('historical') or data.get('results') or []
    out = {}
    for row in data:
        d = str(row.get('date', ''))[:10]
        p = row.get('price', row.get('close', row.get('adjClose')))
        if d and p is not None and float(p) > 0:
            out[d] = round(float(p), 2)
    return out

db_file = sorted(glob.glob('stock_price_db_*_to_*.json'))[-1]
db = json.load(open(db_file))
nvda_dates = [r[0] for r in db['prices']['NVDA']]
start, end = nvda_dates[0], db['meta']['end_date']
data = json.load(open('dashboard_data_beta.json'))

added, skipped = [], []
for cid, fsym, name, risk in NEW:
    if cid in db['prices']:
        skipped.append(cid + ' (already present)'); continue
    try:
        hist = fetch(fsym, start, end)
    except Exception as e:
        skipped.append('%s (fetch error: %s)' % (cid, e)); continue
    if len(hist) < 100:
        skipped.append('%s (insufficient data: %d pts)' % (cid, len(hist))); continue
    keys = sorted(hist)
    aligned, last = [], None
    for nd in nvda_dates:
        if nd in hist:
            last = hist[nd]
        else:
            i = bisect.bisect_right(keys, nd) - 1
            if i >= 0:
                last = hist[keys[i]]
        if last is not None:
            aligned.append([nd, last])
    if len(aligned) < len(nvda_dates) * 0.8:
        skipped.append('%s (alignment too sparse: %d/%d)' % (cid, len(aligned), len(nvda_dates))); continue
    db['prices'][cid] = aligned
    db['meta']['symbols'][cid] = {
        'name': name, 'source': 'FMP stable historical-price-eod/light symbol=%s (server backfill)' % fsym,
        'first_date': aligned[0][0], 'last_date': aligned[-1][0], 'points': len(aligned)}
    px = aligned[-1][1]; prev = aligned[-2][1] if len(aligned) > 1 else px
    data['assets'][cid] = {'id': cid, 'name': name, 'cur': '$', 'rec': 'monitor', 'risk': risk,
        'note': NOTE, 'px': px, 'day': round((px / prev - 1) * 100, 2),
        'dates': [r[0] for r in aligned], 'prices': [r[1] for r in aligned], 'live': True}
    added.append('%s %d pts last %s=%s' % (cid, len(aligned), aligned[-1][0], px))

db['meta']['last_updated'] = datetime.datetime.now().isoformat(timespec='seconds')
json.dump(db, open(db_file, 'w'), separators=(',', ':'))
data.setdefault('build_meta', {})['build_version'] = '2.6.0'
data['build_meta']['price_db'] = db_file
json.dump(data, open('dashboard_data_beta.json', 'w'), separators=(',', ':'))
print('ADDED:', added)
print('SKIPPED:', skipped)
print('universe now:', len(data['assets']), 'assets')
