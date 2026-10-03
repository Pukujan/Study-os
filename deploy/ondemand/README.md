# Study OS on-demand mode (cold starts)

The API container only runs while someone is using the site. `cloudflared`, `postgres`
and `backup` stay up.

```
Cloudflare -> cloudflared (always on) -> gateway:8000 (alias `api` on `edge`)
           -> api:8000 (alias `study-os-api-upstream` on `app`)
```

* **gateway** = `wakegate/` (about 400 lines of stdlib Go, static binary on `scratch`,
  around 10 MB RAM). It takes over the `api` alias on the `edge` network, so the tunnel's
  remote ingress (`study.design-bakery.com -> http://api:8000`) needs no Cloudflare change.
  For every request it checks the container labelled `ondemand.group=study-os` through the
  Docker socket. If the container is stopped, it starts it and holds the request until the
  Docker healthcheck says `healthy` (up to `WAKE_TIMEOUT`=90 s, otherwise a "Starting
  up…" 503 page that refreshes itself). Responses are streamed (SSE works) and WebSockets
  pass through.
* **Idle timeout (momentum based, sliding)**: every request resets the timer. After a single
  or isolated visit the API stops **30 min** after the last request (`BASE_IDLE`). When
  traffic in the hour before the last request was sustained (requests spread over
  >= 10 min, or >= 3 distinct clients by `CF-Connecting-IP`), the window is **60 min**
  (`EXTENDED_IDLE`). The API is never stopped while a request is still in flight.
* An API started outside the gateway (CD `docker compose up`, a reboot) is treated as if
  it got a request when the gateway started, so it stops 30 min later if nobody visits.
* `127.0.0.1:18400` still goes straight to the api container (the CD health check runs
  right after `compose up`). `127.0.0.1:18401` goes through the gateway (it wakes the API).
* `restart: unless-stopped` on `api` is fine: Docker does not restart a container that
  was stopped on purpose, and a crash still self-heals.
* `postgres` is not managed: it is small (about 40 MB), the nightly `backup` sidecar needs
  it, and the API runs migrations at start-up.

Operations:

```sh
docker compose logs -f gateway                      # wake / idle / momentum decisions
docker compose exec gateway /wakegate healthcheck   # gateway liveness
curl -s http://127.0.0.1:18401/api/health           # through the gateway: wakes the API
docker compose stop api                             # force idle; the next request wakes it
```

`docker compose exec api …` (create-account, stats) needs the API running: run
`docker compose start api` first. The gateway stops it again after the idle window.

Status JSON (state, last request, current keep-alive window, time until stop) is served
on the gateway's admin port 8082 inside the `app` network:
`docker run --rm --network study-os_app curlimages/curl -s http://gateway:8082/status`.

To turn it off, restore the previous `deploy/docker-compose.yml` (api back on `edge`
with no gateway) and run `docker compose up -d --remove-orphans`.
