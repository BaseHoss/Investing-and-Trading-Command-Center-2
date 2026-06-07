#!/usr/bin/env python3
"""Safely append delta price rows to the stock price database.
Usage: python3 db_append.py SYMBOL rows.json [db_file]
rows.json = JSON list of [date, close] or [{"date":...,"price":...}] (any order).
Rules enforced: only rows AFTER the symbol's last_date are appended (delta pulls only),
dates deduped + sorted, meta (last_date, points, end_date, last_updated) refreshed.
If end_date changes, the file is renamed to stock_price_db_<start>_to_<newend>.json.
"""
import json, sys, glob, os, datetime

def main():
    if len(sys.argv) < 3:
        print(__doc__); sys.exit(1)
    sym = sys.argv[1].upper()
    rows_file = sys.argv[2]
    db_file = sys.argv[3] if len(sys.argv) > 3 else None
    if not db_file:
        cands = sorted(glob.glob('stock_price_db_*_to_*.json'))
        if not cands:
            print('ERROR: no stock_price_db file found'); sys.exit(2)
        db_file = cands[-1]
    db = json.load(open(db_file))
    if sym not in db['prices']:
        print('ERROR: unknown symbol', sym, '- known:', list(db['prices'])); sys.exit(2)
    raw = json.load(open(rows_file))
    rows = []
    for r in raw:
        if isinstance(r, dict):
            d = r.get('date') or r.get('d'); p = r.get('price') or r.get('p') or r.get('close')
        else:
            d, p = r[0], r[1]
        rows.append((str(d)[:10], round(float(p), 2)))
    last = db['meta']['symbols'][sym]['last_date']
    new = sorted({d: p for d, p in rows if d > last}.items())
    if not new:
        print('No new rows after', last, '- nothing to do (delta rule).'); return
    db['prices'][sym].extend([[d, p] for d, p in new])
    m = db['meta']['symbols'][sym]
    m['last_date'] = new[-1][0]
    m['points'] = len(db['prices'][sym])
    old_end = db['meta']['end_date']
    db['meta']['end_date'] = max(db['meta']['end_date'], new[-1][0])
    db['meta']['last_updated'] = datetime.datetime.now().isoformat(timespec='seconds')
    target = db_file
    if db['meta']['end_date'] != old_end:
        target = 'stock_price_db_%s_to_%s.json' % (db['meta']['start_date'], db['meta']['end_date'])
    json.dump(db, open(target, 'w'), separators=(',', ':'))
    if target != db_file:
        os.remove(db_file)
        print('Renamed:', db_file, '->', target)
    print('Appended', len(new), 'rows to', sym, '| last_date:', m['last_date'], '| file:', target)

if __name__ == '__main__':
    main()
