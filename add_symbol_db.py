#!/usr/bin/env python3
"""Add a NEW symbol to the stock price DB with tier-matched sampling + validation.
Usage: python3 add_symbol_db.py SYM "Display Name" "source desc" rows1.json [rows2.json ...]
Rows files: JSON list of [date, price]. The script:
  - dedupes + sorts ascending, validates prices > 0
  - tier1 (<= 2025-06-05): dates must match NVDA's tier-1 weekly calendar (reports diffs)
  - tier2/3 (>= 2025-06-06): cross-checks date set vs NVDA sessions (reports diffs)
  - inserts into prices + meta.symbols, refreshes meta counts. Refuses existing symbols.
"""
import json, sys, glob

def main():
    if len(sys.argv) < 5:
        print(__doc__); sys.exit(1)
    sym, name, source = sys.argv[1].upper(), sys.argv[2], sys.argv[3]
    db_file = sorted(glob.glob('stock_price_db_*_to_*.json'))[-1]
    db = json.load(open(db_file))
    if sym in db['prices']:
        print('ERROR: symbol exists, use db_append.py'); sys.exit(2)
    rows = {}
    for f in sys.argv[4:]:
        for r in json.load(open(f)):
            d, p = str(r[0])[:10], round(float(r[1]), 2)
            assert p > 0, 'bad price %s %s' % (d, p)
            if d in rows and rows[d] != p:
                print('WARN dup date conflicting price', d, rows[d], p)
            rows[d] = p
    rows = sorted(rows.items())
    nvda = db['prices']['NVDA']
    nv1 = set(r[0] for r in nvda if r[0] <= '2025-06-05')
    nv2 = set(r[0] for r in nvda if r[0] >= '2025-06-06')
    s1 = set(d for d, _ in rows if d <= '2025-06-05')
    s2 = set(d for d, _ in rows if d >= '2025-06-06')
    print('tier1: %d rows (NVDA %d) | missing-vs-NVDA: %s | extra: %s' % (
        len(s1), len(nv1), sorted(nv1 - s1) or 'none', sorted(s1 - nv1) or 'none'))
    print('tier2/3: %d rows (NVDA %d) | missing-vs-NVDA: %s | extra: %s' % (
        len(s2), len(nv2), sorted(nv2 - s2) or 'none', sorted(s2 - nv2) or 'none'))
    db['prices'][sym] = [[d, p] for d, p in rows]
    db['meta']['symbols'][sym] = {
        'name': name, 'source': source,
        'first_date': rows[0][0], 'last_date': rows[-1][0], 'points': len(rows)}
    import datetime
    db['meta']['last_updated'] = datetime.datetime.now().isoformat(timespec='seconds')
    json.dump(db, open(db_file, 'w'), separators=(',', ':'))
    print('ADDED %s: %d points %s -> %s | file: %s' % (sym, len(rows), rows[0][0], rows[-1][0], db_file))

if __name__ == '__main__':
    main()
