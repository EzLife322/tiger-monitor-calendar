# TigerMonitor market calendar

This folder generates `market-sessions.csv` for TigerMonitor from
[`exchange_calendars`](https://github.com/gerrymanoim/exchange_calendars).

The GitHub Action runs every 12 hours:

1. installs `exchange-calendars`;
2. generates `market-sessions.csv` for the next 730 days;
3. commits only if the generated file changed.

TigerMonitor should point to the raw file:

```ini
market_calendar_url=https://raw.githubusercontent.com/USER/REPO/main/market-sessions.csv
market_calendar_check_hours=12
```

Current aggregate regions:

- `AS`: `XTKS`, `XHKG`
- `EU`: `XLON`, `XETR`
- `US`: `XNYS`

Output format:

```txt
REGION|OPEN_UNIX_UTC|CLOSE_UNIX_UTC
```

Lunch breaks / intraday breaks are emitted as separate intervals when the
exchange calendar exposes them.
