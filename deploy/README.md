# Deploying Study OS on gravebuster (D018)

Everything runs on gravebuster and is served at **https://study.design-bakery.com**:
the frontend at `/` and the API at `/api` from one container, plus Postgres 16, a
Cloudflare named tunnel, and a nightly `pg_dump` job. No Vercel and no PostHog.

## Layout on the host

```
/srv/study-os/
  .env                 # secrets, chmod 600 (template: deploy/.env.example)
  docker-compose.yml   # copy of deploy/docker-compose.yml
  app/                 # repository checkout (build context)
  pg/                  # Postgres data volume
  backups/             # nightly pg_dump -Fc files, kept 14 days
```

The API is published only on `127.0.0.1:18400` (for local health checks). Public traffic
arrives through `cloudflared` → `http://api:8000` on the compose network. Postgres is on an
internal-only network.

## Cloudflare (API tokens, no dashboard login)

The tunnel `study-os-gravebuster` was created with the Cloudflare API
(`POST /accounts/{id}/cfd_tunnel` with `config_src: cloudflare`). Its ingress is
`study.design-bakery.com → http://api:8000` (`PUT …/configurations`), and a proxied
`CNAME study → <tunnel-id>.cfargotunnel.com` was added with the zone token. The tunnel token
(`GET …/token`) goes into `TUNNEL_TOKEN` in `/srv/study-os/.env`. Existing tunnels
(`fossil-chatgpt-action`, `study-os-wsl`) are untouched.

## Deploy or update

```sh
cd /srv/study-os
# refresh app/ from the repo (git archive / bundle), then:
cp app/deploy/docker-compose.yml docker-compose.yml
docker compose up -d --build
curl -fsS http://127.0.0.1:18400/api/health
curl -fsS https://study.design-bakery.com/api/health
```

Migrations run automatically at API start (advisory-locked, idempotent).

## First account

Open signup is on: anyone can create an account on the sign-in page. To create an admin
from the host:

```sh
docker compose exec -T api python -m study_os.web.cli create-account --email you@example.com --admin <<< 'your long passphrase'
docker compose exec api python -m study_os.web.cli stats
```

## Google sign-in

Create an OAuth client ("Web application") in Google Cloud Console with the redirect URI
`https://study.design-bakery.com/api/auth/google/callback`. Put `GOOGLE_CLIENT_ID` and
`GOOGLE_CLIENT_SECRET` in `/srv/study-os/.env`, then run `docker compose up -d api`. The
Google button appears automatically.

## Backups and restore

```sh
ls /srv/study-os/backups
docker compose exec -T postgres pg_restore -U study -d study_os --clean < backups/study_os-YYYY-MM-DD.dump
```

Copying the dumps to R2 is optional and not enabled yet.

## Analytics

Learning and UX events live in Postgres. Metabase (or `psql`) can read the views in the
`analytics` schema: `v_learning_event` (xAPI-shaped), `v_decision`,
`v_daily_active_learners`, `v_step_funnel`, `v_drop_off`, `v_hint_rate`,
`v_accuracy_by_concept`, `v_time_on_step`.
