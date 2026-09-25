"""FastAPI app (#85): same-origin API under /api plus the built frontend (D018)."""

from __future__ import annotations

import json
import logging
import mimetypes
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field

from . import WEB_API_VERSION, auth, packs
from .config import Settings, load_settings
from .db import Database
from .models import DecisionTransport, InferHubLLM, LLMTransport, OpenRouterJev
from .ratelimit import RateLimiter
from .player.service import PlayerService
from .service import ServiceError, StudyService

log = logging.getLogger("study_os.web")
CSRF_HEADER = "x-csrf-token"

# Python's stdlib mimetypes table is incomplete on slim images (no .webp).
# With X-Content-Type-Options: nosniff, a wrong type blocks CSS background-image.
_EXTRA_MIME = {
    ".webp": "image/webp",
    ".json": "application/json",
    ".svg": "image/svg+xml",
    ".wasm": "application/wasm",
    ".map": "application/json",
}
for _ext, _ctype in _EXTRA_MIME.items():
    mimetypes.add_type(_ctype, _ext)


def _media_type_for(path: Path) -> str | None:
    ext = path.suffix.lower()
    if ext in _EXTRA_MIME:
        return _EXTRA_MIME[ext]
    guessed, _ = mimetypes.guess_type(str(path))
    return guessed


def _file_response(path: Path, *, headers: dict[str, str] | None = None) -> FileResponse:
    return FileResponse(path, media_type=_media_type_for(path), headers=headers or {})



class _Body(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SignupBody(_Body):
    email: str = Field(max_length=254)
    passphrase: str = Field(max_length=256)
    handle: str | None = Field(default=None, max_length=24)
    display_name: str | None = Field(default=None, max_length=80)


class LoginBody(_Body):
    email: str = Field(max_length=254)
    passphrase: str = Field(max_length=256)


class HandleBody(_Body):
    handle: str = Field(max_length=24)


class StartBody(_Body):
    track: str = Field(max_length=8)
    topic_id: str | None = Field(default=None, max_length=64)
    checkpoint: str | None = Field(default=None, max_length=64)


class TryBody(_Body):
    lesson_id: str | None = Field(default="fractions-compare", max_length=64)


class PlayerSessionBody(_Body):
    lesson_id: str = Field(max_length=64)


class PlayerAttemptBody(_Body):
    response: str = Field(max_length=2000)
    modality: str = Field(max_length=16)
    idempotency_key: str = Field(max_length=80)


class TutorBody(_Body):
    message: str = Field(max_length=500)


class AdaptBody(_Body):
    kind: str = Field(max_length=16)


class ClaimBody(_Body):
    email: str = Field(max_length=254)
    passphrase: str = Field(max_length=256)


class FeedbackBody(_Body):
    session_id: str | None = Field(default=None, max_length=64)
    step_id: str | None = Field(default=None, max_length=120)
    target_kind: str = Field(max_length=16)
    target_id: str = Field(max_length=64)
    rating: str = Field(max_length=8)
    reasons: list[str] = Field(default_factory=list)
    free_text: str | None = Field(default=None, max_length=500)


class AttemptBody(_Body):
    turn_id: str = Field(max_length=64)
    response: str = Field(max_length=2000)
    idempotency_key: str = Field(max_length=80)
    latency_ms: int | None = Field(default=None, ge=0, le=86_400_000)


class ExpandBody(_Body):
    turn_id: str = Field(max_length=64)
    kind: str = Field(max_length=32)


class ReactionBody(_Body):
    kind: str = Field(max_length=16)


class EventsBody(_Body):
    events: list[dict[str, Any]] = Field(max_length=100)

class DecomposerReviewBody(_Body):
    review_batch_id: str | None = Field(default=None, max_length=64)
    client_session: str = Field(max_length=64)
    problem_id: str = Field(max_length=80)
    variant_id: str = Field(max_length=160)
    ratings: list[dict[str, Any]] = Field(max_length=200)
    overall: dict[str, Any] | None = None
    client_ts: str | None = Field(default=None, max_length=40)



def _client_ip(request: Request) -> str:
    # Behind Cloudflare Tunnel the connecting peer is cloudflared; CF sets CF-Connecting-IP.
    return request.headers.get("cf-connecting-ip") or (request.client.host if request.client else "unknown")


def create_app(
    settings: Settings | None = None,
    *,
    db: Database | None = None,
    jev: DecisionTransport | None = None,
    llm: LLMTransport | None = None,
    use_env_models: bool = True,
) -> FastAPI:
    settings = settings or load_settings()
    if settings.cookie_secure and settings.server_secret == "study-os-dev-secret-change-me":
        raise RuntimeError("SERVER_SECRET must be set in production (COOKIE_SECURE=1)")
    if use_env_models:
        if jev is None and settings.openrouter_api_key:
            jev = OpenRouterJev(settings.openrouter_api_key, settings.openrouter_decisions_url, settings.jev_model)
        if llm is None and settings.inferhub_api_key:
            llm = InferHubLLM(settings.inferhub_api_key, settings.inferhub_base_url)
    state: dict[str, Any] = {}
    limiter = RateLimiter()

    @asynccontextmanager
    async def lifespan(_app: FastAPI):  # type: ignore[no-untyped-def]
        database = db or Database(settings.database_url)
        database.migrate()
        state["db"] = database
        state["svc"] = StudyService(database, settings, jev=jev, llm=llm)
        state["player"] = PlayerService(database, settings, llm=llm)
        # Compile lesson graphs once per process (D018 caching).
        for section in packs.topic_graph():
            for topic in section["topics"]:
                if topic["available"]:
                    packs.compile_topic(topic["topic_id"])
        yield
        if db is None:
            database.close()

    app = FastAPI(title="Study OS", version=WEB_API_VERSION, lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)

    def svc() -> StudyService:
        return state["svc"]

    def player() -> PlayerService:
        return state["player"]

    def database() -> Database:
        return state["db"]

    @app.middleware("http")
    async def guard(request: Request, call_next):  # type: ignore[no-untyped-def]
        path = request.url.path
        if path.startswith("/api/"):
            ip = _client_ip(request)
            if not limiter.allow("ip:" + ip, settings.rate_per_ip_per_min):
                return JSONResponse({"error": "rate_limited"}, status_code=429, headers={"Retry-After": "60"})
            if request.method in ("POST", "PUT", "PATCH", "DELETE"):
                origin = request.headers.get("origin")
                if origin is not None and origin not in settings.allowed_origins and origin != settings.public_base_url:
                    return JSONResponse({"error": "bad_origin"}, status_code=403)
                if request.headers.get("x-study-os") != "1":
                    return JSONResponse({"error": "missing_header"}, status_code=403)
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "same-origin"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; "
            "script-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self' https://accounts.google.com"
        )
        if settings.cookie_secure:
            response.headers["Strict-Transport-Security"] = "max-age=31536000"
        if path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response

    def principal(request: Request, *, mutate: bool = False) -> auth.Principal:
        token = request.cookies.get(settings.cookie_name)
        with database().tx() as conn:
            p = auth.resolve_session(conn, token)
        if p is None:
            raise HTTPException(401, "unauthenticated")
        if not limiter.allow("user:" + p.account_id, settings.rate_per_user_per_min):
            raise HTTPException(429, "rate_limited")
        if mutate and not auth.check_csrf(p, request.headers.get(CSRF_HEADER)):
            raise HTTPException(403, "csrf")
        return p

    def set_cookie(resp: Response, token: str) -> None:
        resp.set_cookie(
            settings.cookie_name, token, max_age=int(auth.SESSION_ABSOLUTE.total_seconds()),
            httponly=True, secure=settings.cookie_secure, samesite="lax", path="/",
        )

    @app.exception_handler(ServiceError)
    async def _svc_err(_request: Request, exc: ServiceError) -> JSONResponse:
        return JSONResponse({"error": exc.code}, status_code=exc.status)

    @app.exception_handler(auth.AuthError)
    async def _auth_err(_request: Request, exc: auth.AuthError) -> JSONResponse:
        headers = {"Retry-After": str(exc.retry_after)} if exc.retry_after else None
        return JSONResponse({"error": exc.code}, status_code=exc.status, headers=headers)

    # ---------- health ----------
    @app.get("/api/health")
    def health() -> dict[str, Any]:
        with database().tx() as conn:
            conn.execute("SELECT 1")
        return {"ok": True, "version": WEB_API_VERSION, "google": settings.google_enabled,
                "decision_model": bool(jev) and settings.decision_model_enabled, "llm": bool(llm) and settings.llm_enabled}

    # ---------- auth ----------
    @app.get("/api/auth/config")
    def auth_config() -> dict[str, Any]:
        return {"google": settings.google_enabled, "local_signup": settings.local_signup_enabled}

    def _session_response(p: auth.Principal) -> JSONResponse:
        with database().tx() as conn:
            opened = auth.open_session(conn, p)
        resp = JSONResponse({"handle": p.handle, "display_name": p.display_name, "role": p.role, "csrf_token": opened.csrf_token})
        set_cookie(resp, opened.token)
        return resp

    @app.post("/api/auth/signup")
    def signup(body: SignupBody, request: Request) -> JSONResponse:
        if not settings.local_signup_enabled:
            raise HTTPException(403, "local_signup_disabled")
        if not limiter.allow("signup:" + _client_ip(request), 10, 3600):
            raise HTTPException(429, "rate_limited")
        with database().tx() as conn:
            p = auth.signup_local(conn, email=body.email, passphrase=body.passphrase, handle=body.handle, display_name=body.display_name)
        return _session_response(p)

    @app.post("/api/auth/login")
    def login(body: LoginBody, request: Request) -> JSONResponse:
        ip_key = auth.ip_hash(settings.server_secret, _client_ip(request))
        try:
            with database().tx() as conn:
                p = auth.login_local(conn, email=body.email, passphrase=body.passphrase, ip_key=ip_key)
        except auth.AuthError as exc:
            if exc.code == "invalid_credentials":
                # Persist the failed attempt (the transaction above rolled back on raise).
                with database().tx() as conn:
                    conn.execute(
                        "INSERT INTO auth.login_attempt (account_key_hash, ip_hash, succeeded) VALUES (%s, %s, false)",
                        (auth.sha256("local:" + (body.email or "").strip().lower()), ip_key),
                    )
            raise
        return _session_response(p)

    @app.post("/api/auth/logout")
    def logout(request: Request) -> JSONResponse:
        with database().tx() as conn:
            auth.revoke_session(conn, request.cookies.get(settings.cookie_name))
        resp = JSONResponse({"ok": True})
        resp.delete_cookie(settings.cookie_name, path="/")
        return resp

    @app.get("/api/auth/me")
    def me(request: Request) -> dict[str, Any]:
        p = principal(request)
        # Rotate a fresh CSRF token into the session for SPA reloads.
        import secrets as _secrets

        csrf = _secrets.token_urlsafe(24)
        with database().tx() as conn:
            conn.execute(
                "UPDATE auth.session SET csrf_token_hash = %s WHERE session_id_hash = %s",
                (auth.sha256(csrf), auth.sha256(request.cookies.get(settings.cookie_name) or "")),
            )
        return {"handle": p.handle, "display_name": p.display_name, "role": p.role, "is_guest": p.is_guest, "csrf_token": csrf}

    @app.post("/api/auth/handle")
    def change_handle(body: HandleBody, request: Request) -> dict[str, Any]:
        p = principal(request, mutate=True)
        with database().tx() as conn:
            return {"handle": auth.set_handle(conn, p, body.handle)}

    @app.get("/api/auth/google/start")
    def google_start() -> RedirectResponse:
        if not settings.google_enabled or not settings.google_client_id:
            raise HTTPException(404, "google_disabled")
        with database().tx() as conn:
            url = auth.begin_google(conn, client_id=settings.google_client_id,
                                    redirect_uri=settings.public_base_url + "/api/auth/google/callback")
        return RedirectResponse(url, status_code=302)

    @app.get("/api/auth/google/callback")
    def google_callback(request: Request, code: str | None = None, state: str | None = None) -> Response:
        if not settings.google_enabled or not settings.google_client_id or not settings.google_client_secret:
            raise HTTPException(404, "google_disabled")
        if not code:
            return RedirectResponse("/login?error=google_cancelled", status_code=302)
        with database().tx() as conn:
            verifier, nonce = auth.consume_google_state(conn, state)
        try:
            token_resp = httpx.post(auth.GOOGLE_TOKEN_URL, data={
                "code": code, "client_id": settings.google_client_id, "client_secret": settings.google_client_secret,
                "redirect_uri": settings.public_base_url + "/api/auth/google/callback",
                "grant_type": "authorization_code", "code_verifier": verifier,
            }, timeout=10)
        except httpx.HTTPError:
            return RedirectResponse("/login?error=google_unreachable", status_code=302)
        if token_resp.status_code != 200:
            return RedirectResponse("/login?error=google_exchange", status_code=302)
        claims = auth.verify_google_id_token(token_resp.json().get("id_token", ""), client_id=settings.google_client_id, nonce=nonce)
        email = claims.get("email") if claims.get("email_verified") else None
        with database().tx() as conn:
            p = auth.upsert_google_account(conn, google_sub=str(claims["sub"]), email=email, display_name=claims.get("name"))
            opened = auth.open_session(conn, p)
        resp = RedirectResponse("/", status_code=302)
        set_cookie(resp, opened.token)
        return resp

    # ---------- learning ----------
    @app.get("/api/home")
    def home(request: Request) -> dict[str, Any]:
        return svc().home(principal(request))

    @app.post("/api/sessions")
    def start(body: StartBody, request: Request) -> dict[str, Any]:
        return svc().start_session(principal(request, mutate=True), track=body.track, topic_id=body.topic_id, checkpoint=body.checkpoint)

    @app.get("/api/sessions/{session_id}")
    def view(session_id: str, request: Request) -> dict[str, Any]:
        return svc().session_view(principal(request), session_id)

    @app.post("/api/sessions/{session_id}/attempts")
    def attempt(session_id: str, body: AttemptBody, request: Request) -> dict[str, Any]:
        return svc().submit_attempt(principal(request, mutate=True), session_id, turn_id=body.turn_id,
                                    response=body.response, idempotency_key=body.idempotency_key, latency_ms=body.latency_ms)

    @app.post("/api/sessions/{session_id}/expansions")
    def expand(session_id: str, body: ExpandBody, request: Request) -> dict[str, Any]:
        return svc().expand(principal(request, mutate=True), session_id, turn_id=body.turn_id, kind=body.kind)

    @app.post("/api/sessions/{session_id}/end")
    def end(session_id: str, request: Request) -> dict[str, Any]:
        return svc().end_session(principal(request, mutate=True), session_id)

    @app.get("/api/sessions/{session_id}/summary")
    def summary(session_id: str, request: Request) -> dict[str, Any]:
        return svc().summary(principal(request), session_id)

    @app.post("/api/turns/{turn_id}/reactions")
    def react(turn_id: str, body: ReactionBody, request: Request) -> dict[str, Any]:
        svc().react(principal(request, mutate=True), turn_id, body.kind)
        return {"ok": True}

    @app.post("/api/events")
    def events(body: EventsBody, request: Request) -> dict[str, Any]:
        token = request.cookies.get(settings.cookie_name)
        p = None
        if token:
            with database().tx() as conn:
                p = auth.resolve_session(conn, token)
        if p is not None and not auth.check_csrf(p, request.headers.get(CSRF_HEADER)):
            p = None  # still accept anonymous-shaped events, but never attribute them
        return {"stored": svc().record_events(p, body.events)}

    # ---------- player ----------
    @app.get("/api/lanes")
    def lanes(request: Request) -> dict[str, Any]:
        return player().lanes(principal(request))

    @app.post("/api/try")
    def try_first(body: TryBody, request: Request) -> JSONResponse:
        token = request.cookies.get(settings.cookie_name)
        if token:
            with database().tx() as conn:
                if auth.resolve_session(conn, token) is not None:
                    raise HTTPException(409, "already_signed_in")
        if not limiter.allow("signup:" + _client_ip(request), 10, 3600):
            raise HTTPException(429, "rate_limited")
        with database().tx() as conn:
            p = auth.create_guest_account(conn)
            opened = auth.open_session(conn, p)
        view = player().start_or_resume(p, body.lesson_id or "fractions-compare")
        resp = JSONResponse({
            "me": {
                "handle": p.handle,
                "display_name": p.display_name,
                "role": p.role,
                "is_guest": p.is_guest,
                "csrf_token": opened.csrf_token,
            },
            "session": view,
        })
        set_cookie(resp, opened.token)
        return resp

    @app.post("/api/auth/claim")
    def claim(body: ClaimBody, request: Request) -> dict[str, Any]:
        p = principal(request, mutate=True)
        if not p.is_guest:
            raise HTTPException(403, "not_guest")
        with database().tx() as conn:
            p = auth.claim_local(conn, principal=p, email=body.email, passphrase=body.passphrase)
        return {
            "handle": p.handle,
            "display_name": p.display_name,
            "role": p.role,
            "is_guest": p.is_guest,
        }

    @app.post("/api/player/sessions")
    def player_start(body: PlayerSessionBody, request: Request) -> dict[str, Any]:
        return player().start_or_resume(principal(request, mutate=True), body.lesson_id)

    @app.get("/api/player/sessions/{session_id}")
    def player_get(session_id: str, request: Request) -> dict[str, Any]:
        return player().get(principal(request), session_id)

    @app.post("/api/player/sessions/{session_id}/attempt")
    def player_attempt(session_id: str, body: PlayerAttemptBody, request: Request) -> dict[str, Any]:
        return player().attempt(
            principal(request, mutate=True), session_id, body.response, body.modality, body.idempotency_key
        )

    @app.post("/api/player/sessions/{session_id}/confused")
    def player_confused(session_id: str, request: Request) -> dict[str, Any]:
        return player().confused(principal(request, mutate=True), session_id)

    @app.post("/api/player/sessions/{session_id}/next")
    def player_next(session_id: str, request: Request) -> dict[str, Any]:
        return player().next(principal(request, mutate=True), session_id)

    @app.post("/api/player/sessions/{session_id}/tutor")
    def player_tutor(session_id: str, body: TutorBody, request: Request) -> dict[str, Any]:
        return player().tutor(principal(request, mutate=True), session_id, body.message)

    @app.post("/api/player/sessions/{session_id}/adapt")
    def player_adapt(session_id: str, body: AdaptBody, request: Request) -> dict[str, Any]:
        return player().adapt(principal(request, mutate=True), session_id, body.kind)

    @app.post("/api/feedback")
    def feedback(body: FeedbackBody, request: Request) -> dict[str, Any]:
        return player().feedback(principal(request, mutate=True), body)

    @app.get("/api/admin/feedback")
    def admin_feedback(request: Request) -> dict[str, Any]:
        return player().admin_feedback(principal(request))


    @app.post("/api/review/decomposer")
    def review_decomposer(body: DecomposerReviewBody, request: Request) -> dict[str, Any]:
        """SOS-0011: append-only per-step ratings for pedagogical decomposer proposals. Auth optional."""
        token = request.cookies.get(settings.cookie_name)
        p = None
        if token:
            with database().tx() as conn:
                p = auth.resolve_session(conn, token)
            if p is not None and not auth.check_csrf(p, request.headers.get(CSRF_HEADER)):
                p = None
        return svc().record_decomposer_reviews(p, body.model_dump())

    @app.get("/api/review/decomposer/variants")
    def review_decomposer_variants() -> dict[str, Any]:
        """List packaged decomposer review variants (static JSON under /review/decomposer/data/)."""
        sdir = settings.static_dir or os.environ.get("STATIC_DIR")
        if not sdir:
            return {"problems": [], "variants": []}
        data_dir = Path(sdir).resolve() / "review" / "decomposer" / "data"
        variants = []
        if data_dir.is_dir():
            for path in sorted(data_dir.glob("*.json")):
                if path.name in ("index.json", "spend.json"):
                    continue
                try:
                    meta = json.loads(path.read_text(encoding="utf-8")).get("_meta") or {}
                    variants.append({
                        "variant_id": meta.get("variant_id") or path.stem,
                        "problem_id": meta.get("problem_id"),
                        "problem_title": meta.get("problem_title"),
                        "variant_kind": meta.get("variant_kind"),
                        "model": meta.get("model"),
                        "route": meta.get("route"),
                        "file": path.name,
                    })
                except Exception:
                    continue
        problems = sorted({v["problem_id"] for v in variants if v.get("problem_id")})
        return {"problems": problems, "variants": variants}



    # ---------- static frontend ----------
    static_dir = settings.static_dir or os.environ.get("STATIC_DIR")
    if static_dir and Path(static_dir).is_dir():
        root = Path(static_dir).resolve()

        # Mount real asset trees BEFORE the SPA catch-all so /mascot/*.webp and
        # /review/decomposer/data/*.json never fall through to index.html.
        mascot_dir = root / "mascot"
        if mascot_dir.is_dir():
            app.mount("/mascot", StaticFiles(directory=str(mascot_dir)), name="mascot")
        review_data = root / "review" / "decomposer" / "data"
        if review_data.is_dir():
            app.mount(
                "/review/decomposer/data",
                StaticFiles(directory=str(review_data)),
                name="decomposer-data",
            )

        @app.get("/review/decomposer", include_in_schema=False)
        @app.get("/review/decomposer/", include_in_schema=False)
        def decomposer_review_page() -> Response:
            index = root / "review" / "decomposer" / "index.html"
            if not index.is_file():
                raise HTTPException(404, "not_found")
            return _file_response(index, headers={"Cache-Control": "no-cache"})

        @app.get("/{full_path:path}", include_in_schema=False)
        def spa(full_path: str) -> Response:
            if full_path.startswith("api/"):
                raise HTTPException(404, "not_found")
            # Mounted prefixes should never reach here; guard anyway.
            if full_path == "mascot" or full_path.startswith("mascot/"):
                raise HTTPException(404, "not_found")
            if full_path.startswith("review/decomposer/data"):
                raise HTTPException(404, "not_found")
            candidate = (root / full_path).resolve()
            try:
                candidate.relative_to(root)
            except ValueError as exc:
                raise HTTPException(404, "not_found") from exc
            if full_path and candidate.is_file():
                headers = (
                    {"Cache-Control": "public, max-age=31536000, immutable"}
                    if full_path.startswith("assets/")
                    else {"Cache-Control": "public, max-age=300"}
                )
                return _file_response(candidate, headers=headers)
            # Directory index for review sub-apps (and similar static folders)
            if full_path and candidate.is_dir():
                index = candidate / "index.html"
                if index.is_file():
                    return _file_response(index, headers={"Cache-Control": "no-cache"})
            if full_path.startswith("assets/"):
                raise HTTPException(404, "not_found")
            return _file_response(root / "index.html", headers={"Cache-Control": "no-cache"})

    return app


def app_factory() -> FastAPI:
    return create_app()
