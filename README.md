# BuildPC

A PC building engine: Django REST backend for hardware data and compatibility
matching, plus a Vue 3 frontend for browsing/building.

This guide is written for moving between the two development machines:

- **Work computer:** Zorin OS (desktop)
- **Home computer:** Ubuntu Server (headless, backend-focused)

The goal is that a fresh `git clone` runs with two commands, without depending
on secrets or a database that only exists on one machine.

## Requirements

| Tool | Version | Notes |
|---|---|---|
| Python | 3.12+ | `sudo apt install python3 python3-venv python3-pip` |
| Node.js | 20+ | Only needed for the frontend |
| Git | any recent | |

Ubuntu 24.04 includes Python 3.12. Ubuntu 22.04 ships Python 3.10; install
Python 3.12 with `pyenv` or the deadsnakes PPA before running setup.

## First setup on a new machine

```bash
git clone https://github.com/dev-automizze/buildpc.git
cd buildpc
./scripts/setup.sh
```

On a headless Ubuntu server without Node.js:

```bash
./scripts/setup.sh --backend-only
```

The script creates `backend/venv`, installs Python dependencies, copies
`backend/.env.example` to `backend/.env` if needed, runs migrations, and
installs frontend dependencies when Node is available.

After pulling changes on an existing machine, the safe routine is:

```bash
./scripts/setup.sh          # idempotent; installs new deps and applies migrations
make test                   # confirm nothing broke
```

`make backend` starts Django on `127.0.0.1:8088`; `make frontend` starts Vite.

## Configuration

Configuration lives in `backend/.env` (ignored by git). Copy the example once:

```bash
cd backend
cp .env.example .env
```

### Option A: local SQLite (easiest, works offline)

Leave `DATABASE_URL` empty. Django uses `backend/db.sqlite3`. This is the
default for a fresh clone and is ideal for UI work or a quick test.

### Option B: shared PostgreSQL (same data on both machines)

Set `DATABASE_URL` in each machine's `backend/.env`:

```dotenv
DATABASE_URL=postgresql://user:password@host:5432/pc_builder_db
```

Use the remote database if both machines can reach it. If the home Ubuntu
server hosts PostgreSQL, use its LAN address (for example
`192.168.1.50`) and make sure PostgreSQL accepts remote connections.

Frontend configuration goes in `frontend/.env`:

```dotenv
VITE_API_URL=http://localhost:8088
```

When the frontend runs on one machine and the backend on another, point this at
the backend machine's LAN address, for example `http://192.168.1.50:8088`.

## Running

```bash
make backend       # http://127.0.0.1:8088
make backend-lan   # http://<this-machine-ip>:8088, reachable on the LAN
make frontend      # http://localhost:5173
```

For LAN access, also allow the host/IP in `backend/.env`:

```dotenv
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,[::1],192.168.1.50
CORS_ALLOWED_ORIGINS=http://192.168.1.50:5173
CSRF_TRUSTED_ORIGINS=http://192.168.1.50:8088,http://192.168.1.50:5173
```

## Fresh home server setup (Ubuntu)

Use this when you have deleted the old directory and want a clean clone.

**On the work computer**, copy the configured environment file over SSH:

```bash
scp backend/.env your-user@HOME_SERVER_IP:/tmp/buildpc.env
```

**On the home server:**

```bash
cd ~
rm -rf buildpc-dev
git clone https://github.com/dev-automizze/buildpc-dev.git
cd buildpc-dev

cp /tmp/buildpc.env backend/.env
chmod 600 backend/.env
rm /tmp/buildpc.env

# Add the server's LAN IP so the admin/API is reachable from your browser.
nano backend/.env
#   DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,[::1],192.168.1.50

./scripts/setup.sh --backend-only
make test
make backend-lan
```

Then open `http://192.168.1.50:8088/admin/` (replace with the server IP).

The setup output prints the database engine and component count. If you copied
the shared `.env`, you should see `engine: postgresql` and your existing
components. If you see `engine: sqlite3` with `components: 0`, the `.env` was
not copied correctly.

No `createsuperuser` is needed when using the shared PostgreSQL database — the
existing admin account is there. Only create one for a fresh SQLite database.

## Moving hardware data between machines

The database is not in git. To move your components, export them to CSV and
copy the folder to the other machine:

```bash
cd backend
./venv/bin/python manage.py export_components       # writes backend/exports/
```

`backend/exports/` contains `cpus.csv`, `motherboards.csv`, and `coolers.csv`.
Copy it with `scp`, `rsync`, a USB stick, or any file sync tool, then on the
other machine:

```bash
cd backend
./venv/bin/python manage.py import_components exports --all
```

Import is an upsert by MPN, so it is safe to run repeatedly. `exports/` is
gitignored — it is data, not source code.

## Tests

```bash
make test
```

Tests use an in-memory SQLite database and never touch the configured
PostgreSQL database, so they are safe to run on any machine.

## Troubleshooting “it only runs on my computer”

| Symptom | Cause / fix |
|---|---|
| `ModuleNotFoundError` | Dependencies not installed. Run `./scripts/setup.sh`. |
| `Could not create venv` | Install `python3-venv` (`sudo apt install python3-venv`). |
| `connection refused` / DB timeout | `DATABASE_URL` points to a host this machine cannot reach. Clear it to use SQLite, or fix the network/VPN. |
| `no such table` / migration errors | Run `make migrate`. |
| Admin has no users | Run `./venv/bin/python manage.py createsuperuser` on that database. |
| Frontend shows no data | Check `VITE_API_URL`, that the backend is running, and CORS/allowed hosts. |
| `vite: command not found` | Node dependencies missing. `cd frontend && npm ci`. |
| Wrong Node version | `nvm use` (reads `frontend/.nvmrc`, Node 20). |
| `psycopg2` install error | Use Python 3.12 and the pinned `psycopg2-binary`; `./scripts/setup.sh` handles it. |

## Security

- Never commit `backend/.env`, `frontend/.env`, database passwords, or GitHub
  tokens. They are ignored by git.
- Secrets that were previously committed remain in git history. Rotate them;
  rewriting history is optional but does not un-expose an already-pushed value.
- After pulling on a new machine, create a **local** superuser or use the
  shared database's existing account. Do not share admin passwords in chat.

## Repository note

The current remote is `github.com/dev-automizze/buildpc.git`. If the intended
repository is `buildpc-dev.git`, update it explicitly:

```bash
git remote set-url origin https://github.com/dev-automizze/buildpc-dev.git
```

See `backend/README.md` for backend-specific details and API endpoints.
