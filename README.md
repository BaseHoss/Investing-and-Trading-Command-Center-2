# Investing &amp; Trading Command Center — Model 2

Live dashboard: https://basehoss.github.io/Investing-and-Trading-Command-Center-2/

Two-page dashboard (Market Pulse + Investing Planner). 9-asset universe (NVDA, MSFT, INTC, AVGO, QQQ, SMH, SPY, GOLD, BTC) on FMP Starter data, 36-month price database, Position Consultant v7.1 with situational intelligence layer. Personal educational research, not financial advice.

## Architecture

- `dashboard_template_beta.html` — fixed template (ASCII-only), `__DATA__` token. Never hand-edited day to day.
- `dashboard_data_beta.json` — full dashboard data (series + editorial). Rebuilt server-side from deltas.
- `stock_price_db_*.json` — 36-month price database, 9 symbols. Updated by daily deltas; filename carries the covered period.
- `daily_update.json` — the ONLY file pushed daily (small delta: new closes, VIX, macro, notes, news, situations, build_meta).
- `apply_daily_update.py` — applies a delta: appends DB rows, refreshes series/editorial in the data file, validates (9 assets, ASCII, dash ban).
- `refresh_dashboard_beta.py` — assembler: template + data → `investing-dashboard-beta.html` (copied to `index.html`).
- `update_beta_from_db.py`, `db_append.py`, `add_symbol_db.py` — DB tooling (local pipeline + new-symbol onboarding).

## Workflows

- `daily.yml` — on `daily_update.json` push: apply delta → rebuild → commit DB + data + index.html.
- `rebuild.yml` — on direct `dashboard_data_beta.json` push (seeding/manual edits): validate → rebuild → commit index.html.

Predecessor (Model 1, retired from active refresh): https://github.com/BaseHoss/Investing-and-Trading-Command-Center
