# Week 3 — Data Ingestion Pipeline

`fetch_weather.py` pulls current weather (temperature, wind speed, relative humidity) for Seattle, New York, and Austin from the free Open-Meteo forecast API. Each raw JSON response is landed unchanged in `data/raw/<city>_<YYYYMMDD_HHMMSS>.json` (schema-on-read). Timeouts and connection errors are retried with exponential backoff; HTTP errors such as 400 are not retried.

```bash
pip install requests
python labs/week03-ingestion/fetch_weather.py
ls data/raw/
```

`data/` is in `.gitignore` because landed files are run output, not code.

## Reflection

**Easiest and hardest failure to trigger.** The timeout was the easiest: changing `timeout=5` to `timeout=0.001` fails every time, because no real network round trip finishes in one millisecond. The bad status code was also easy and fully deterministic, since `LATITUDE = 999` is outside the valid range (-90 to 90) and the API returns 400 Bad Request every time. The connection error was the hardest to trigger cleanly. A misspelled hostname only fails at DNS lookup, and how quickly that happens depends on the local resolver and network (WSL2 sends DNS through Windows). It also needs a bad host that doesn't happen to exist. In real life the hardest failures to reproduce are the transient ones (a network blip or a briefly overloaded server), which is why we simulate them on purpose instead of waiting for them.

**Effect of exponential backoff.** The wait between attempts doubled each time: "Retrying in 1s", then 2s, then 4s, and on the fourth attempt the script gave up with "Giving up after 4 attempts". With `MAX_RETRIES = 4` there are only three sleeps (1 + 2 + 4 = 7 s total). The 8 s delay is never used, because the last attempt gives up instead of sleeping. Short delays first let a quick blip recover fast, and longer delays later give a struggling API time to recover without being hammered. When all three cities timed out, the whole run took about 21 s of waiting, so in production you would want a cap on total time or jitter.

**Why we don't retry HTTP 400.** A 400 is a permanent client-side error: the request itself is invalid, so sending the same request again will fail the same way every time. Retrying only adds latency and load. The lecture separated transient failures (timeouts, connection errors, 5xx/429), which should be retried with backoff, from permanent failures, which should fail fast and be surfaced. It also warned that blind retries at scale cause retry storms: thousands of jobs retrying against an already-struggling API can turn a small outage into a large one. In our run the 400 case failed on the first attempt with no delay, and New York and Austin still landed.

**Data contract for consumers of `data/raw/`.**
- **Schema:** one JSON file per city per run, named `<city lowercase>_<YYYYMMDD_HHMMSS>.json`, containing the full, unmodified Open-Meteo response. Required fields are `latitude`, `longitude`, `timezone`, `current.time` (ISO 8601 local time), and `current.temperature_2m`, `current.wind_speed_10m`, `current.relative_humidity_2m` (numbers). The contract should also state that filenames can contain spaces (`new york_...json`).
- **Semantics:** units come from `current_units` (°C, km/h, %). Temperature is measured at 2 m and wind at 10 m. `current.time` is in the city's local timezone, while the filename timestamp is the ingestion machine's local time. Raw files are never edited after they land.
- **SLA:** how often the job runs (for example hourly), how fresh the data is (landed within N minutes of the run), and what a missing city means (a skipped run after retries are exhausted, not a value of zero). Plus who to contact when data is late.
- **Change management:** version the contract. Announce any renamed or removed field, unit change, filename or path change, or added city ahead of time with a deprecation window. Additive changes (new fields) are non-breaking. Breaking changes get a new version or path (for example `data/raw/v2/`), and an automated schema check runs before landing.
