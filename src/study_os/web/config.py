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
    posthog_project_key: str | None = None
    posthog_host: str = "https://us.i.posthog.com"
    analytics_salt: str = "study-os-dev-salt"
    decision_model_enabled: bool = True
    llm_enabled: bool = True
    extra: dict[str, str] = field(default_factory=dict)

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
            "https://www.design-bakery.com,https://design-bakery.com,http://localhost:5173",
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
        posthog_project_key=os.environ.get("POSTHOG_PROJECT_KEY") or None,
        posthog_host=os.environ.get("POSTHOG_HOST", "https://us.i.posthog.com"),
        analytics_salt=os.environ.get("ANALYTICS_SALT", "study-os-dev-salt"),
        decision_model_enabled=_flag("DECISION_MODEL_ENABLED", True),
        llm_enabled=_flag("LLM_ENABLED", True),
    )
