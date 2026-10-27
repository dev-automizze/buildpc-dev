# BuildPC Backend

Django + Django REST Framework backend for the PC building engine.

## Setup

```bash
cd backend
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
cp .env.example .env      # edit DATABASE_URL or leave empty for SQLite
./venv/bin/python manage.py migrate
./venv/bin/python manage.py createsuperuser
./venv/bin/python manage.py runserver 8088
```

Use `make setup` / `make backend` / `make test` from the repository root for
the short version. See the root `README.md` for multi-machine setup and LAN
access.

Admin: http://localhost:8088/admin/  
API root: http://localhost:8088/api/

## Tests

Tests use an in-memory SQLite database, so they never touch the configured
PostgreSQL database:

```bash
./venv/bin/python manage.py test --settings=pc_engine.settings_test
```

## API

| Endpoint | Description |
|---|---|
| `GET /api/cpus/` | CPUs with nested `cpu_spec` |
| `GET /api/motherboards/` | Motherboards with nested `specs` |
| `GET /api/coolers/` | Coolers with nested `specs` |
| `GET /api/sockets/` | Canonical socket names |

Optional filters:

- `/api/cpus/?socket=AM5`
- `/api/motherboards/?socket=LGA1700`
- `/api/coolers/?socket=AM5`
- `/api/coolers/?type=AIO`

## CSV import

Use **Import CSV** on any category changelist in the admin. Sockets are
normalised automatically (`LGA 1700`, `lga-1700`, and `1700` all become
`LGA1700`). Each row is imported in its own savepoint, so one bad row is
reported without discarding the good rows.

Column lists are shown on the upload page. A starter file is available at
`sample_data/coolers_template.csv` — the rows in it are placeholders, so verify
specs before using them as real data. `sample_data/cooler.csv` is the 28-cooler
import used during development and can be re-imported with:

```bash
./venv/bin/python manage.py import_components sample_data/cooler.csv --type Cooler
```

### Cooler columns

```
mpn,brand,model,msrp,coolerType,supportedSockets,tdpRatingWatts,heightMm,
ramClearanceMm,radiatorSizeMm,radiatorThicknessMm,radiatorLengthMm,
radiatorWidthMm,fanCount,fanSizeMm,noiseDbMax,weightG,powerConnector
```

- `supportedSockets` is comma, semicolon, or pipe separated.
- Air coolers: set `heightMm` and optionally `ramClearanceMm`.
- AIO coolers: set `radiatorSizeMm` (120/240/280/360/420) and leave `heightMm` empty.

## Data portability

```bash
./venv/bin/python manage.py export_components          # -> exports/*.csv
./venv/bin/python manage.py import_components exports --all
```

Import is an upsert by MPN and uses the same validation as the admin uploader.

## Data model notes

- `Component` stores shared fields and a `category` enum.
- `Cpu`, `Motherboard`, and `Cooler` are proxy models with managers that
  automatically scope queries to their category.
- `Socket` is a shared lookup table referenced by CPU, motherboard, and cooler
  specs, so socket matching is a single join instead of string comparison.
- `CpuSpec.max_power_watts` stores sustained package power (AMD PPT / Intel
  PL2). `effective_power_watts` falls back to `tdp_watts` when it is empty; use
  this for cooler matching.
