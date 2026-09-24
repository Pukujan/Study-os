"""Accounts and sessions (#86, D018).

Open signup. Google sign-in (OIDC authorization code + state + PKCE + nonce) is primary; a
local email/passphrase fallback (argon2id) serves dev and use before Google keys exist.
Minimal profile only (Google subject, email, display name, handle), stored in ``auth.*``.
Learning tables see only the pseudonymous ``subject_id``.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import re
import secrets
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from .db import Conn
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

HANDLE_RE = re.compile(r"^[a-z0-9_-]{3,24}$")
EMAIL_RE = re.compile(r"^[^@\s]{1,64}@[^@\s]{1,190}\.[A-Za-z]{2,}$")
MIN_PASSPHRASE = 10
MAX_PASSPHRASE = 256
THROTTLE_WINDOW = timedelta(minutes=15)
MAX_FAILURES_PER_ACCOUNT = 5
MAX_FAILURES_PER_IP = 20
SESSION_ABSOLUTE = timedelta(days=30)
SESSION_IDLE = timedelta(days=7)
OAUTH_STATE_TTL = timedelta(minutes=10)

_HASHER = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=2, hash_len=32, salt_len=16)
_DUMMY_HASH = _HASHER.hash("study-os-dummy-passphrase-for-timing")


class AuthError(Exception):
    def __init__(self, code: str, status: int = 400, retry_after: int | None = None) -> None:
        super().__init__(code)
        self.code = code
        self.status = status
        self.retry_after = retry_after


@dataclass(frozen=True)
class Principal:
    account_id: str
    subject_id: str
    handle: str
    role: str
    display_name: str | None = None
    csrf_hash: bytes = b""


@dataclass(frozen=True)
class OpenedSession:
    token: str
    csrf_token: str


def sha256(value: str) -> bytes:
    return hashlib.sha256(value.encode("utf-8")).digest()


def ip_hash(secret: str, ip: str | None) -> bytes:
    return hmac.new(secret.encode("utf-8"), (ip or "unknown").encode("utf-8"), hashlib.sha256).digest()


def normalize_handle(handle: str) -> str:
    value = (handle or "").strip().lower()
    if not HANDLE_RE.fullmatch(value):
        raise AuthError("invalid_handle")
    return value


def normalize_email(email: str) -> str:
    value = (email or "").strip().lower()
    if not EMAIL_RE.fullmatch(value):
        raise AuthError("invalid_email")
    return value


def validate_passphrase(passphrase: str) -> None:
    if not isinstance(passphrase, str) or not (MIN_PASSPHRASE <= len(passphrase) <= MAX_PASSPHRASE):
        raise AuthError("weak_passphrase")


def hash_passphrase(passphrase: str) -> str:
    return _HASHER.hash(passphrase)


def verify_passphrase(stored: str | None, passphrase: str) -> bool:
    try:
        ok = _HASHER.verify(stored or _DUMMY_HASH, passphrase)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False
    return bool(ok) and stored is not None


def _val(row: Any, key: str) -> Any:
    return None if row is None else row[key]


def _next_pseudonym(conn: Conn) -> str:
    conn.execute("LOCK TABLE learn.subject IN SHARE ROW EXCLUSIVE MODE")
    row = conn.execute(
        "SELECT coalesce(max(substring(pseudonym from 9)::int), 1) AS n FROM learn.subject"
    ).fetchone()
    # subject-001 is the historical local-runtime learner; web subjects start at 002.
    return f"subject-{int(_val(row, 'n') or 1) + 1:03d}"


def _unique_handle(conn: Conn, base: str) -> str:
    stem = re.sub(r"[^a-z0-9_-]", "", (base or "").lower())[:16] or "learner"
    if len(stem) < 3:
        stem = (stem + "learner")[:16]
    candidate = stem
    for _ in range(20):
        if conn.execute("SELECT 1 FROM auth.account WHERE handle = %s", (candidate,)).fetchone() is None:
            return candidate
        candidate = f"{stem}-{secrets.randbelow(10_000):04d}"
    raise AuthError("handle_unavailable", 409)


def _create_account(
    conn: Conn,
    *,
    handle: str,
    email: str | None,
    display_name: str | None,
    role: str = "learner",
) -> Principal:
    account_id = str(uuid.uuid4())
    subject_id = str(uuid.uuid4())
    if conn.execute("SELECT 1 FROM auth.account WHERE handle = %s", (handle,)).fetchone():
        raise AuthError("handle_taken", 409)
    if email and conn.execute("SELECT 1 FROM auth.account WHERE email = %s", (email,)).fetchone():
        raise AuthError("email_taken", 409)
    conn.execute(
        "INSERT INTO auth.account (account_id, handle, email, display_name, role) "
        "VALUES (%s, %s, %s, %s, %s)",
        (account_id, handle, email, (display_name or None) and display_name[:80], role),
    )
    conn.execute(
        "INSERT INTO learn.subject (subject_id, pseudonym) VALUES (%s, %s)",
        (subject_id, _next_pseudonym(conn)),
    )
    conn.execute(
        "INSERT INTO auth.account_subject (account_id, subject_id) VALUES (%s, %s)",
        (account_id, subject_id),
    )
    return Principal(account_id, subject_id, handle, role, display_name)


def signup_local(
    conn: Conn,
    *,
    email: str,
    passphrase: str,
    handle: str | None = None,
    display_name: str | None = None,
    role: str = "learner",
) -> Principal:
    email_norm = normalize_email(email)
    validate_passphrase(passphrase)
    handle_norm = normalize_handle(handle) if handle else _unique_handle(conn, email_norm.split("@")[0])
    principal = _create_account(
        conn, handle=handle_norm, email=email_norm, display_name=display_name, role=role
    )
    conn.execute(
        "INSERT INTO auth.local_credential (account_id, passphrase_hash) VALUES (%s, %s)",
        (principal.account_id, hash_passphrase(passphrase)),
    )
    conn.execute(
        "INSERT INTO auth.identity (provider, provider_subject, account_id) VALUES ('local', %s, %s)",
        (email_norm, principal.account_id),
    )
    return principal


def _throttle(conn: Conn, account_key: bytes, ip_key: bytes) -> None:
    window = f"{int(THROTTLE_WINDOW.total_seconds())} seconds"
    acct = conn.execute(
        "SELECT count(*) AS n, max(created_at) AS last FROM auth.login_attempt "
        "WHERE account_key_hash = %s AND NOT succeeded AND created_at > now() - %s::interval",
        (account_key, window),
    ).fetchone()
    ipr = conn.execute(
        "SELECT count(*) AS n FROM auth.login_attempt "
        "WHERE ip_hash = %s AND NOT succeeded AND created_at > now() - %s::interval",
        (ip_key, window),
    ).fetchone()
    failures = int(_val(acct, "n") or 0)
    if failures >= MAX_FAILURES_PER_ACCOUNT or int(_val(ipr, "n") or 0) >= MAX_FAILURES_PER_IP:
        raise AuthError("rate_limited", 429, retry_after=int(THROTTLE_WINDOW.total_seconds()))
    # Exponential backoff after the second failure: 2, 4, 8 ... seconds since the last failure.
    last = _val(acct, "last")
    if failures >= 2 and last is not None:
        wait = 2 ** (failures - 1)
        elapsed = (datetime.now(timezone.utc) - last).total_seconds()
        if elapsed < wait:
            raise AuthError("rate_limited", 429, retry_after=int(wait - elapsed) + 1)


def login_local(
    conn: Conn, *, email: str, passphrase: str, ip_key: bytes
) -> Principal:
    try:
        email_norm = normalize_email(email)
    except AuthError:
        verify_passphrase(None, passphrase or "x")
        raise AuthError("invalid_credentials", 401)
    account_key = sha256("local:" + email_norm)
    _throttle(conn, account_key, ip_key)
    row = conn.execute(
        "SELECT a.account_id::text AS account_id, a.handle::text AS handle, a.role, a.display_name, "
        "a.disabled_at, c.passphrase_hash, m.subject_id::text AS subject_id "
        "FROM auth.identity i JOIN auth.account a USING (account_id) "
        "JOIN auth.local_credential c USING (account_id) JOIN auth.account_subject m USING (account_id) "
        "WHERE i.provider = 'local' AND i.provider_subject = %s",
        (email_norm,),
    ).fetchone()
    ok = verify_passphrase(_val(row, "passphrase_hash"), passphrase or "")
    if row is not None and row["disabled_at"] is not None:
        ok = False
    conn.execute(
        "INSERT INTO auth.login_attempt (account_key_hash, ip_hash, succeeded) VALUES (%s, %s, %s)",
        (account_key, ip_key, ok),
    )
    conn.execute("DELETE FROM auth.login_attempt WHERE created_at < now() - interval '1 day'")
    if not ok or row is None:
        raise AuthError("invalid_credentials", 401)
    return Principal(row["account_id"], row["subject_id"], row["handle"], row["role"], row["display_name"])


def upsert_google_account(
    conn: Conn, *, google_sub: str, email: str | None, display_name: str | None
) -> Principal:
    if not google_sub or len(google_sub) > 255:
        raise AuthError("invalid_identity")
    row = conn.execute(
        "SELECT a.account_id::text AS account_id, a.handle::text AS handle, a.role, a.display_name, "
        "a.disabled_at, m.subject_id::text AS subject_id FROM auth.identity i "
        "JOIN auth.account a USING (account_id) JOIN auth.account_subject m USING (account_id) "
        "WHERE i.provider = 'google' AND i.provider_subject = %s",
        (google_sub,),
    ).fetchone()
    if row is not None:
        if row["disabled_at"] is not None:
            raise AuthError("account_disabled", 403)
        return Principal(row["account_id"], row["subject_id"], row["handle"], row["role"], row["display_name"])
    email_norm = None
    if email:
        try:
            email_norm = normalize_email(email)
        except AuthError:
            email_norm = None
    if email_norm:
        # Link to an existing local account with the same verified Google email.
        existing = conn.execute(
            "SELECT a.account_id::text AS account_id, a.handle::text AS handle, a.role, a.display_name, "
            "m.subject_id::text AS subject_id FROM auth.account a "
            "JOIN auth.account_subject m USING (account_id) WHERE a.email = %s AND a.disabled_at IS NULL",
            (email_norm,),
        ).fetchone()
        if existing is not None:
            conn.execute(
                "INSERT INTO auth.identity (provider, provider_subject, account_id) VALUES ('google', %s, %s)",
                (google_sub, existing["account_id"]),
            )
            return Principal(
                existing["account_id"], existing["subject_id"], existing["handle"], existing["role"],
                existing["display_name"],
            )
    handle = _unique_handle(conn, (email_norm or "learner").split("@")[0])
    principal = _create_account(conn, handle=handle, email=email_norm, display_name=display_name)
    conn.execute(
        "INSERT INTO auth.identity (provider, provider_subject, account_id) VALUES ('google', %s, %s)",
        (google_sub, principal.account_id),
    )
    return principal


def open_session(conn: Conn, principal: Principal) -> OpenedSession:
    token = secrets.token_urlsafe(32)  # 256-bit
    csrf = secrets.token_urlsafe(24)
    now = datetime.now(timezone.utc)
    conn.execute(
        "INSERT INTO auth.session (session_id_hash, account_id, csrf_token_hash, absolute_expires_at, "
        "idle_expires_at) VALUES (%s, %s, %s, %s, %s)",
        (sha256(token), principal.account_id, sha256(csrf), now + SESSION_ABSOLUTE, now + SESSION_IDLE),
    )
    return OpenedSession(token=token, csrf_token=csrf)


def resolve_session(conn: Conn, token: str | None) -> Principal | None:
    if not token or len(token) > 128:
        return None
    row = conn.execute(
        "SELECT a.account_id::text AS account_id, a.handle::text AS handle, a.role, a.display_name, "
        "m.subject_id::text AS subject_id, s.csrf_token_hash, s.last_seen_at "
        "FROM auth.session s JOIN auth.account a USING (account_id) "
        "JOIN auth.account_subject m USING (account_id) "
        "WHERE s.session_id_hash = %s AND s.revoked_at IS NULL AND s.absolute_expires_at > now() "
        "AND s.idle_expires_at > now() AND a.disabled_at IS NULL",
        (sha256(token),),
    ).fetchone()
    if row is None:
        return None
    last_seen = row["last_seen_at"]
    if last_seen is None or datetime.now(timezone.utc) - last_seen > timedelta(minutes=5):
        conn.execute(
            "UPDATE auth.session SET last_seen_at = now(), idle_expires_at = least(absolute_expires_at, now() + %s::interval) "
            "WHERE session_id_hash = %s",
            (f"{int(SESSION_IDLE.total_seconds())} seconds", sha256(token)),
        )
    return Principal(
        row["account_id"], row["subject_id"], row["handle"], row["role"], row["display_name"],
        bytes(row["csrf_token_hash"]),
    )


def check_csrf(principal: Principal, csrf_token: str | None) -> bool:
    if not csrf_token or not principal.csrf_hash:
        return False
    return hmac.compare_digest(sha256(csrf_token), principal.csrf_hash)


def revoke_session(conn: Conn, token: str | None) -> None:
    if token:
        conn.execute(
            "UPDATE auth.session SET revoked_at = now() WHERE session_id_hash = %s AND revoked_at IS NULL",
            (sha256(token),),
        )


def set_handle(conn: Conn, principal: Principal, handle: str) -> str:
    value = normalize_handle(handle)
    taken = conn.execute(
        "SELECT 1 FROM auth.account WHERE handle = %s AND account_id <> %s", (value, principal.account_id)
    ).fetchone()
    if taken:
        raise AuthError("handle_taken", 409)
    conn.execute("UPDATE auth.account SET handle = %s WHERE account_id = %s", (value, principal.account_id))
    return value


# ---- Google OIDC (authorization code + state + PKCE S256 + nonce) ----

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_ISSUERS = ("https://accounts.google.com", "accounts.google.com")


def pkce_challenge(verifier: str) -> str:
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")


def begin_google(conn: Conn, *, client_id: str, redirect_uri: str) -> str:
    state = secrets.token_urlsafe(32)
    verifier = secrets.token_urlsafe(48)
    nonce = secrets.token_urlsafe(24)
    conn.execute(
        "INSERT INTO auth.oauth_state (state_hash, code_verifier, nonce, expires_at) VALUES (%s, %s, %s, %s)",
        (sha256(state), verifier, nonce, datetime.now(timezone.utc) + OAUTH_STATE_TTL),
    )
    conn.execute("DELETE FROM auth.oauth_state WHERE expires_at < now() - interval '1 hour'")
    from urllib.parse import urlencode

    query = urlencode(
        {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
            "nonce": nonce,
            "code_challenge": pkce_challenge(verifier),
            "code_challenge_method": "S256",
            "prompt": "select_account",
        }
    )
    return f"{GOOGLE_AUTH_URL}?{query}"


def consume_google_state(conn: Conn, state: str | None) -> tuple[str, str]:
    if not state or len(state) > 128:
        raise AuthError("invalid_state", 400)
    row = conn.execute(
        "UPDATE auth.oauth_state SET consumed_at = now() WHERE state_hash = %s AND consumed_at IS NULL "
        "AND expires_at > now() RETURNING code_verifier, nonce",
        (sha256(state),),
    ).fetchone()
    if row is None:
        raise AuthError("invalid_state", 400)
    return row["code_verifier"], row["nonce"]


def _b64json(segment: str) -> dict[str, Any]:
    import json

    padded = segment + "=" * (-len(segment) % 4)
    return json.loads(base64.urlsafe_b64decode(padded.encode("ascii")))


def verify_google_id_token(id_token: str, *, client_id: str, nonce: str) -> dict[str, Any]:
    """Validate claims of an ID token received directly from Google's token endpoint over TLS.

    OIDC Core 3.1.3.7 allows TLS server validation in place of signature checking for tokens
    obtained directly from the token endpoint; issuer, audience, expiry, and nonce are checked.
    """

    parts = (id_token or "").split(".")
    if len(parts) != 3:
        raise AuthError("invalid_id_token", 400)
    claims = _b64json(parts[1])
    now = datetime.now(timezone.utc).timestamp()
    if claims.get("iss") not in GOOGLE_ISSUERS:
        raise AuthError("invalid_id_token", 400)
    aud = claims.get("aud")
    if aud != client_id and not (isinstance(aud, list) and client_id in aud):
        raise AuthError("invalid_id_token", 400)
    if float(claims.get("exp", 0)) < now:
        raise AuthError("invalid_id_token", 400)
    if not hmac.compare_digest(str(claims.get("nonce", "")), nonce):
        raise AuthError("invalid_id_token", 400)
    if not claims.get("sub"):
        raise AuthError("invalid_id_token", 400)
    return claims
