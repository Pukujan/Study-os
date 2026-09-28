# Kokoro TTS on gravebuster (Refs #180)

Cute feminine tutor voice via self-hosted **Kokoro-82M** (Apache-2.0), swapped in behind `STUDY_OS_TTS=kokoro`. Browser `speechSynthesis` remains the default and the fallback when Kokoro is down.

Research background: [`docs/research/voice-robustness.md`](../research/voice-robustness.md) (§3.4 TTS smoke, §9).

## Voice choice

Kokoro has no Hu Tao / Ayaka named packs. For a soft, bright, anime-adjacent English tutor we pick:

| Env | Value | Why |
|---|---|---|
| `KOKORO_VOICE` | **`af_heart`** (default) | Highest-graded US female (warm, natural). Soft/cute without sounding robotic. |
| optional blend | `af_heart(60)+jf_alpha(40)` | Measured “anime-flavoured” blend from the research smoke (`kokoro_blend_heart60_jfalpha40.wav`). Use if FastAPI image supports weighted mixes (remsky/Kokoro-FastAPI). |
| alt | `af_bella` @ speed ~1.12 | Brighter / more expressive. |

Default speed: `KOKORO_SPEED=1.08` (lively without chipmunk).

## Compose service (CPU)

gravebuster is **CPU-only** (no NVIDIA). Use the Kokoro-FastAPI CPU image (OpenAI-compatible `POST /v1/audio/speech`).

Add to `/srv/study-os/docker-compose.yml` (also mirrored in `deploy/docker-compose.yml` under profile `tts`):

```yaml
  kokoro:
    profiles: ["tts"]
    image: ghcr.io/remsky/kokoro-fastapi-cpu:latest
    restart: unless-stopped
    # Internal only — API reaches it on the compose network.
    networks: [internal]
    environment:
      # Optional; Study OS passes voice per request.
      KOKORO_VOICE: af_heart
    # No host ports published; api uses KOKORO_BASE_URL=http://kokoro:8880
```

Wire the API container:

```yaml
  api:
    environment:
      DATABASE_URL: postgresql://study:${POSTGRES_PASSWORD}@postgres:5432/study_os
      STUDY_OS_TTS: kokoro          # or omit / browser for Web Speech
      KOKORO_BASE_URL: http://kokoro:8880
      KOKORO_VOICE: af_heart
      KOKORO_SPEED: "1.08"
    depends_on:
      postgres:
        condition: service_healthy
      # When using profile tts, start kokoro with the stack:
      #   docker compose --profile tts up -d
```

## Host `.env` (`/srv/study-os/.env`)

```sh
# TTS engine: browser (default) | kokoro
STUDY_OS_TTS=kokoro
KOKORO_BASE_URL=http://kokoro:8880
KOKORO_VOICE=af_heart
KOKORO_SPEED=1.08
```

## Bring-up

```sh
cd /srv/study-os
cp app/deploy/docker-compose.yml docker-compose.yml
# ensure .env has STUDY_OS_TTS=kokoro …
docker compose --profile tts up -d --build
curl -fsS http://127.0.0.1:18400/api/tts/config
# expect: {"engine":"kokoro","voice":"af_heart",...}
curl -fsS -X POST http://127.0.0.1:18400/api/tts/speech \
  -H 'content-type: application/json' \
  -d '{"text":"Nice work. Still one lookup."}' -o /tmp/sos-tts.mp3
file /tmp/sos-tts.mp3
```

First pull of the Kokoro image + model cache is slow; later synth of a tutor line is typically sub-second on idle CPU (research: RTF ≈ 0.2). Under gravebuster load, expect multi-second latency — keep an audio cache as a follow-up.

## App behaviour

- `GET /api/tts/config` — engine the UI should use.
- `POST /api/tts/speech` `{ "text": "…" }` — MP3 from Kokoro when `STUDY_OS_TTS=kokoro`; `503` otherwise.
- Frontend (`web/src/player/tts.ts`) speaks via that API when engine is `kokoro`, else `speechSynthesis`. If Kokoro returns an error, it falls back to the browser voice.

## Rollback

Set `STUDY_OS_TTS=browser` (or unset), `docker compose up -d api`, and optionally `docker compose --profile tts stop kokoro` to free RAM.

## Follow-ups (out of this thin slice)

- In-browser `kokoro-js` option (no gravebuster CPU).
- Audio response cache keyed by `(voice, speed, text hash)`.
- Voice dropdown (Pocket TTS / Piper) per research §9.
