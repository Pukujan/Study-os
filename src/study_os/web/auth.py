"""Invite-only pseudonymous accounts (#86): handle + argon2id passphrase + server-side session."""

from __future__ import annotations

import hashlib
import re
import secrets
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import psycopg
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

HANDLE_RE = re.compile(r"^[a-z0-9_-]{3,24}$")
MIN_PASSPHRASE = 12
MAX_PASSPHRASE = 256
LOGIN_WINDOW = timedelta(minutes=1)
LOGIN_MAX_FAILURES = 5

# argon2id with RFC 9106 "second recommended" style parameters, tuned for a small server.
_HASHER = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=2, hash_len=32, salt_len=16)
_DUMMY_HASH = _HASHER.hash("study-os-dummy-passphrase-for-timing")


class AuthError(Exception):
    def __init__(self, code: str, status: int = 400) -> None:
        super().__init__(code)
        self.code = code
        self.status = status


@dataclass(frozen=True)
class Principal:
    account_id: str
    subject_id: str
    handle: str
    role: str


def _sha256(value: str) -> bytes:
    return hashlib.sha256(value.encode("utf-8")).digest()


def normalize_handle(handle: str) -> str:
    value = (handle or "").strip().lower()
    if not HANDLE_RE.fullmatch(value):
        raise AuthError("invalid_handle")
    return value


def validate_passphrase(passphrase: str) -> None:
    if not isinstance(passphrase, str) or not (MIN_PASSPHRASE <= len(passphrase) <= MAX_PASSPHRASE):
        raise AuthError("weak_passphrase")


def hash_passphrase(passphrase: str) -> str:
    return _HASHER.hash(passphrase)


def verify_passphrase(stored: str | None, passphrase: str) -> bool:
    try:
        return _HASHER.verify(stored or _DUMMY_HASH, passphrase) and stored is not None
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def create_invite(conn: psycopg.Connection, *, role: str = "learner", created_by: str | None = None) -> str:
    if role not in ("learner", "admin"):
        raise AuthError("invalid_role")
    code = "sos-" + secrets.token_urlsafe(18)
    conn.execute(
        "INSERT INTO auth.invite (code_hash, created_by, role) VALUES (%s, %s, %s)",
        (_sha256(code), created_by, role),
    )
    return code


def _next_pseudonym(conn: psycopg.Connection) -> str:
    conn.execute("LOCK TABLE learn.subject IN SHARE ROW EXCLUSIVE MODE")
    row = conn.execute(
        "SELECT coalesce(max(substring(pseudonym from 9)::int), 1) AS n FROM learn.subject"
    ).fetchone()
    # subject-001 is the historical local-runtime learner; web subjects start at 002.
    current = int(_row_value(row, "n") or 1)
    return f"subject-{current + 1:03d}"


def _row_value(row: object, key: str) -> object:
    if row is None:
        return None
    if isinstance(row, dict):
        return row[key]
    return row[0]  # type: ignore[index]


def redeem_invite(conn: psycopg.Connection, *, invite_code: str, handle: str, passphrase: str) -> Principal:
    handle_norm = normalize_handle(handle)
    validate_passphrase(passphrase)
    invite = conn.execute(
        "SELECT role FROM auth.invite WHERE code_hash = %s AND redeemed_at IS NULL FOR UPDATE",
        (_sha256((invite_code or "").strip()),),
    ).fetchone()
    if invite is None:
        raise AuthError("invalid_invite", 403)
    exists = conn.execute("SELECT 1 FROM auth.account WHERE handle = %s", (handle_norm,)).fetchone()
    if exists is not None:
        raise AuthError("handle_taken", 409)
    role = str(_row_value(invite, "role"))
    account_id = str(uuid.uuid4())
    subject_id = str(uuid.uuid4())
    pseudonym = _next_pseudonym(conn)
    conn.execute(
        "INSERT INTO auth.account (account_id, handle, passphrase_hash, role) VALUES (%s, %s, %s, %s)",
        (account_id, handle_norm, hash_passphrase(passphrase), role),
    )
    conn.execute(
        "INSERT INTO learn.subject (subject_id, pseudonym) VALUES (%s, %s)", (subject_id, pseudonym)
    )
    conn.execute(
        "INSERT INTO auth.account_subject (account_id, subject_id) VALUES (%s, %s)",
        (account_id, subject_id),
    )
    conn.execute(
        "UPDATE auth.invite SET redeemed_at = now() WHERE code_hash = %s",
        (_sha256(invite_code.strip()),),
    )
    return Principal(account_id=account_id, subject_id=subject_id, handle=handle_norm, role=role)


def _recent_failures(conn: psycopg.Connection, handle_hash: bytes) -> int:
    row = conn.execute(
        "SELECT count(*) AS n FROM auth.login_attempt "
        "WHERE handle_hash = %s AND NOT succeeded AND created_at > now() - %s::interval",
        (handle_hash, f"{int(LOGIN_WINDOW.total_seconds())} seconds"),
    ).fetchone()
    return int(_row_value(row, "n") or 0)  # type: ignore[arg-type]


def login(conn: psycopg.Connection, *, handle: str, passphrase: str) -> Principal:
    try:
        handle_norm = normalize_handle(handle)
    except AuthError:
        verify_passphrase(None, passphrase or "x")
        raise AuthError("invalid_credentials", 401)
    handle_hash = _sha256(handle_norm)
    if _recent_failures(conn, handle_hash) >= LOGIN_MAX_FAILURES:
        raise AuthError("rate_limited", 429)
    row = conn.execute(
        "SELECT a.account_id::text AS account_id, a.passphrase_hash, a.role, a.disabled_at, "
        "s.subject_id::text AS subject_id "
        "FROM auth.account a JOIN auth.account_subject s USING (account_id) WHERE a.handle = %s",
        (handle_norm,),
    ).fetchone()
    stored = None if row is None else str(_row_value(row, "passphrase_hash"))
    ok = verify_passphrase(stored, passphrase or "")
    if row is not None and _row_value(row, "disabled_at") is not None:
        ok = False
    conn.execute(
        "INSERT INTO auth.login_attempt (handle_hash, succeeded) VALUES (%s, %s)", (handle_hash, ok)
    )
    if not ok or row is None:
        raise AuthError("invalid_credentials", 401)
    return Principal(
        account_id=str(_row_value(row, "account_id")),
        subject_id=str(_row_value(row, "subject_id")),
        handle=handle_norm,
        role=str(_row_value(row, "role")),
    )


def open_session(conn: psycopg.Connection, principal: Principal, *, days: int = 30) -> str:
    token = secrets.token_urlsafe(32)  # 256-bit
    conn.execute(
        "INSERT INTO auth.session (session_id_hash, account_id, expires_at) VALUES (%s, %s, %s)",
        (_sha256(token), principal.account_id, datetime.now(timezone.utc) + timedelta(days=days)),
    )
    return token


def resolve_session(conn: psycopg.Connection, token: str | None, *, days: int = 30) -> Principal | None:
    if not token or len(token) > 128:
        return None
    row = conn.execute(
        "SELECT a.account_id::text AS account_id, a.handle::text AS handle, a.role, "
        "m.subject_id::text AS subject_id "
        "FROM auth.session s JOIN auth.account a USING (account_id) "
        "JOIN auth.account_subject m USING (account_id) "
        "WHERE s.session_id_hash = %s AND s.revoked_at IS NULL AND s.expires_at > now() "
        "AND a.disabled_at IS NULL",
        (_sha256(token),),
    ).fetchone()
    if row is None:
        return None
    # 30-day sliding window.
    conn.execute(
        "UPDATE auth.session SET last_seen_at = now(), expires_at = %s WHERE session_id_hash = %s",
        (datetime.now(timezone.utc) + timedelta(days=days), _sha256(token)),
    )
    return Principal(
        account_id=str(_row_value(row, "account_id")),
        subject_id=str(_row_value(row, "subject_id")),
        handle=str(_row_value(row, "handle")),
        role=str(_row_value(row, "role")),
    )


def revoke_session(conn: psycopg.Connection, token: str | None) -> None:
    if token:
        conn.execute(
            "UPDATE auth.session SET revoked_at = now() WHERE session_id_hash = %s AND revoked_at IS NULL",
            (_sha256(token),),
        )
