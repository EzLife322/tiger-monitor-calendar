# TigerMonitor market calendar

This folder generates `market-sessions.csv` for TigerMonitor from
[`exchange_calendars`](https://github.com/gerrymanoim/exchange_calendars).

The GitHub Action runs every 12 hours, but normally only checks the latest
published `exchange_calendars` version on PyPI:

1. reads the stored version from `market-calendar/exchange_calendars.version`;
2. checks the latest PyPI version;
3. exits without installing dependencies when the version is unchanged;
4. when the version changed, installs `exchange-calendars`, generates
   `market-sessions.csv` for the next 1095 days and commits the CSV together
   with the new version file.

Manual `workflow_dispatch` has a `force=true` option to regenerate the CSV even
when the library version is unchanged.

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
