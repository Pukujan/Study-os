from __future__ import annotations

import os
from dataclasses import dataclass, field

JEV_PINNED_MODEL = "typesafe/jev-1.13"
JEV_FORBIDDEN_ALIASES = ("~typesafe/jev-latest", "typesafe/jev-latest")
INFERHUB_PRIMARY_ROUTE = "cb/glm-5.3"
INFERHUB_FALLBACK_ROUTE = "cb/deepseek-v4.1-flash"
# IRE Top-20 snapshot that informed the route choice (docs/webapp/LLM_ROUTE.md §2).
PRICE_SNAPSHOT_ID = "ire-top20-8e2b1b323cf9438b1274f321c309729d60f133ef14915895265ca76758570e7c"


def _flag(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _float(name: str, default: float) -> float:
    raw = os.environ.get(name)
    return default if raw is None or raw.strip() == "" else float(raw)


def _csv(name: str, default: str) -> tuple[str, ...]:
    raw = os.environ.get(name, default)
    return tuple(part.strip() for part in raw.split(",") if part.strip())


@dataclass(frozen=True)
class Settings:
    database_url: str
    allowed_origins: tuple[str, ...]
    cookie_secure: bool
    cookie_name: str = "sos_session"
    session_days: int = 30
    openrouter_api_key: str | None = None
    openrouter_decisions_url: str = "https://openrouter.ai/api/alpha/decisions"
    jev_model: str = JEV_PINNED_MODEL
    inferhub_api_key: str | None = None
    inferhub_base_url: str = "https://api.inferhub.dev/v1"
    llm_primary_route: str = INFERHUB_PRIMARY_ROUTE
    llm_fallback_route: str = INFERHUB_FALLBACK_ROUTE
    llm_spend_cap_usd: float = 5.0
    tau_grade: float = 0.9
    tau_mastery: float = 0.95
    tau_misconception: float = 0.8
    audit_rate: float = 0.05
    server_secret: str = "study-os-dev-secret-change-me"
    public_base_url: str = "http://localhost:8000"
    google_client_id: str | None = None
    google_client_secret: str | None = None
    local_signup_enabled: bool = True
    static_dir: str | None = None
    user_daily_model_calls: int = 400
    global_daily_spend_usd: float = 3.0
    rate_per_ip_per_min: int = 240
    rate_per_user_per_min: int = 120
    decision_model_enabled: bool = True
    llm_enabled: bool = True
    extra: dict[str, str] = field(default_factory=dict)

    @property
    def google_enabled(self) -> bool:
        return bool(self.google_client_id and self.google_client_secret)

    def __post_init__(self) -> None:
        # P-DEC-5: never run on a rolling alias.
        if self.jev_model in JEV_FORBIDDEN_ALIASES or "latest" in self.jev_model:
            raise ValueError("decision model must be a pinned version, not an alias")


def load_settings() -> Settings:
    return Settings(
        database_url=os.environ.get(
            "DATABASE_URL", "postgresql://sos:sos@localhost:5432/study_os"
        ),
        allowed_origins=_csv(
            "ALLOWED_ORIGINS",
            "https://study.design-bakery.com,http://localhost:5173,http://localhost:8000",
        ),
        cookie_secure=_flag("COOKIE_SECURE", True),
        openrouter_api_key=os.environ.get("OPENROUTER_API_KEY") or None,
        jev_model=os.environ.get("JEV_MODEL", JEV_PINNED_MODEL),
        inferhub_api_key=os.environ.get("INFERHUB_API_KEY") or None,
        inferhub_base_url=os.environ.get("INFERHUB_API_URL", "https://api.inferhub.dev/v1"),
        llm_spend_cap_usd=_float("LLM_SPEND_CAP_USD", 5.0),
        tau_grade=_float("TAU_GRADE", 0.9),
        tau_mastery=_float("TAU_MASTERY", 0.95),
        tau_misconception=_float("TAU_MISCONCEPTION", 0.8),
        audit_rate=_float("DECISION_AUDIT_RATE", 0.05),
        server_secret=os.environ.get("SERVER_SECRET", "study-os-dev-secret-change-me"),
        public_base_url=os.environ.get("PUBLIC_BASE_URL", "http://localhost:8000").rstrip("/"),
        google_client_id=os.environ.get("GOOGLE_CLIENT_ID") or None,
        google_client_secret=os.environ.get("GOOGLE_CLIENT_SECRET") or None,
        local_signup_enabled=_flag("LOCAL_SIGNUP_ENABLED", True),
        static_dir=os.environ.get("STATIC_DIR") or None,
        user_daily_model_calls=int(_float("USER_DAILY_MODEL_CALLS", 400)),
        global_daily_spend_usd=_float("GLOBAL_DAILY_SPEND_USD", 3.0),
        rate_per_ip_per_min=int(_float("RATE_PER_IP_PER_MIN", 240)),
        rate_per_user_per_min=int(_float("RATE_PER_USER_PER_MIN", 120)),
        decision_model_enabled=_flag("DECISION_MODEL_ENABLED", True),
        llm_enabled=_flag("LLM_ENABLED", True),
    )
