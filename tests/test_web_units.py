"""Pure unit tests for the web slice: privacy, validator, config, auth helpers, rate limits."""

from __future__ import annotations

import base64
import json
import sys
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from web_testkit import make_settings, requires_web  # noqa: E402


@requires_web
class PrivacyTests(unittest.TestCase):
    def test_scrub_removes_contact_details(self) -> None:
        from study_os.web.privacy import contains_pii, scrub

        raw = "my name is Dana, mail dana@example.com or call 555-123-4567, see https://x.io 10.0.0.1"
        cleaned = scrub(raw)
        for needle in ("dana@example.com", "555-123-4567", "https://x.io", "10.0.0.1"):
            self.assertNotIn(needle, cleaned)
        self.assertTrue(contains_pii(raw))
        self.assertFalse(contains_pii("the window sum is 17"))

    def test_scrub_is_idempotent_on_clean_text(self) -> None:
        from study_os.web.privacy import scrub

        self.assertEqual(scrub("position 4, number 6"), "position 4, number 6")


@requires_web
class ValidatorTests(unittest.TestCase):
    def test_flags_answer_leak_and_mastery(self) -> None:
        from study_os.web.validator import validate_generated

        res = validate_generated("The answer is 17. You have mastered this!", forbidden_answers=("17",), required_blocks=())
        self.assertFalse(res.ok)
        self.assertIn("ANSWER_REVEAL_FORBIDDEN", res.codes)
        self.assertIn("MASTERY_CLAIM", res.codes)

    def test_spelled_number_leak_and_multi_question(self) -> None:
        from study_os.web.validator import validate_generated

        res = validate_generated("Is it seventeen? Or what? ", forbidden_answers=("17",), required_blocks=())
        self.assertIn("ANSWER_REVEAL_FORBIDDEN", res.codes)
        self.assertIn("MULTI_QUESTION", res.codes)

    def test_clean_text_passes(self) -> None:
        from study_os.web.validator import code_blocks, validate_generated

        text = "Look at the chart again.\n\n```text\n1 2 3\n```\nCount the boxes."
        res = validate_generated(text, forbidden_answers=("17",), required_blocks=("```text\n1 2 3\n```",))
        self.assertTrue(res.ok, res.codes)
        self.assertEqual(len(code_blocks(text)), 1)

    def test_missing_chart_and_links(self) -> None:
        from study_os.web.validator import validate_generated

        res = validate_generated("See https://example.com for more", forbidden_answers=(), required_blocks=("```x```",))
        self.assertIn("MISSING_REPRESENTATION", res.codes)
        self.assertIn("LINK", res.codes)
        self.assertIn("WORD_BUDGET", validate_generated("word " * 200, forbidden_answers=(), required_blocks=()).codes)
        self.assertIn("EMPTY", validate_generated("```a```", forbidden_answers=(), required_blocks=()).codes)


@requires_web
class ConfigTests(unittest.TestCase):
    def test_rejects_rolling_alias(self) -> None:
        with self.assertRaises(ValueError):
            make_settings(jev_model="~typesafe/jev-latest")
        with self.assertRaises(ValueError):
            make_settings(jev_model="typesafe/jev-latest")

    def test_google_enabled_requires_both_keys(self) -> None:
        self.assertFalse(make_settings().google_enabled)
        self.assertFalse(make_settings(google_client_id="x").google_enabled)
        self.assertTrue(make_settings(google_client_id="x", google_client_secret="y").google_enabled)

    def test_load_settings_reads_env(self) -> None:
        import os

        from study_os.web.config import load_settings

        old = dict(os.environ)
        try:
            os.environ["ALLOWED_ORIGINS"] = "https://a.example, https://b.example"
            os.environ["COOKIE_SECURE"] = "0"
            os.environ["GLOBAL_DAILY_SPEND_USD"] = "1.5"
            s = load_settings()
            self.assertEqual(s.allowed_origins, ("https://a.example", "https://b.example"))
            self.assertFalse(s.cookie_secure)
            self.assertEqual(s.global_daily_spend_usd, 1.5)
            self.assertEqual(s.jev_model, "typesafe/jev-1.13")
        finally:
            os.environ.clear()
            os.environ.update(old)


@requires_web
class RateLimitTests(unittest.TestCase):
    def test_sliding_window(self) -> None:
        from study_os.web.ratelimit import RateLimiter

        rl = RateLimiter()
        self.assertTrue(all(rl.allow("k", 3, 60) for _ in range(3)))
        self.assertFalse(rl.allow("k", 3, 60))
        self.assertTrue(rl.allow("other", 3, 60))
        self.assertTrue(rl.allow("short", 1, 0.01))
        time.sleep(0.02)
        self.assertTrue(rl.allow("short", 1, 0.01))


def _jwt(claims: dict) -> str:
    def seg(obj: dict) -> str:
        return base64.urlsafe_b64encode(json.dumps(obj).encode()).decode().rstrip("=")

    return f"{seg({'alg': 'RS256'})}.{seg(claims)}.sig"


@requires_web
class AuthHelperTests(unittest.TestCase):
    def test_passphrase_hash_roundtrip(self) -> None:
        from study_os.web import auth

        h = auth.hash_passphrase("correct horse battery staple")
        self.assertTrue(h.startswith("$argon2id$"))
        self.assertTrue(auth.verify_passphrase(h, "correct horse battery staple"))
        self.assertFalse(auth.verify_passphrase(h, "wrong"))
        self.assertFalse(auth.verify_passphrase(None, "x"))

    def test_passphrase_policy_and_normalisation(self) -> None:
        from study_os.web import auth

        with self.assertRaises(auth.AuthError):
            auth.validate_passphrase("short")
        self.assertEqual(auth.normalize_email("  A@Example.COM "), "a@example.com")
        with self.assertRaises(auth.AuthError):
            auth.normalize_email("not-an-email")
        self.assertEqual(auth.normalize_handle("  Dana_Q "), "dana_q")
        with self.assertRaises(auth.AuthError):
            auth.normalize_handle("x!")

    def test_pkce_is_s256(self) -> None:
        import hashlib

        from study_os.web import auth

        verifier = "a" * 64
        expected = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip("=")
        self.assertEqual(auth.pkce_challenge(verifier), expected)

    def test_id_token_claims_checked(self) -> None:
        from study_os.web import auth

        good = {"iss": "https://accounts.google.com", "aud": "cid", "exp": time.time() + 60, "nonce": "n1", "sub": "123"}
        self.assertEqual(auth.verify_google_id_token(_jwt(good), client_id="cid", nonce="n1")["sub"], "123")
        for bad in (
            {**good, "aud": "other"},
            {**good, "iss": "https://evil.example"},
            {**good, "exp": time.time() - 5},
            {**good, "nonce": "n2"},
        ):
            with self.assertRaises(auth.AuthError):
                auth.verify_google_id_token(_jwt(bad), client_id="cid", nonce="n1")
        with self.assertRaises(auth.AuthError):
            auth.verify_google_id_token("garbage", client_id="cid", nonce="n1")

    def test_ip_hash_is_keyed(self) -> None:
        from study_os.web import auth

        self.assertNotEqual(auth.ip_hash("a", "1.2.3.4"), auth.ip_hash("b", "1.2.3.4"))
        self.assertEqual(len(auth.sha256("x")), 32)


@requires_web
class ModelTransportTests(unittest.TestCase):
    def _resp(self, status: int, body: dict) -> object:
        from unittest import mock

        r = mock.Mock(status_code=status)
        r.json.return_value = body
        return r

    def test_jev_success_and_failures(self) -> None:
        from unittest import mock

        import httpx

        from study_os.web.models import ModelUnavailable, OpenRouterJev

        jev = OpenRouterJev("k", "https://example.invalid/decisions", "typesafe/jev-1.13")
        body = {"model": "typesafe/jev-1.13-20260917", "answers": {"g": {"choice": "pass"}},
                "usage": {"input_tokens": 10, "output_tokens": 2, "cost": 0.0001}}
        with mock.patch("study_os.web.models.httpx.post", return_value=self._resp(200, body)) as post:
            out = jev.decide("state", {"g": {"type": "choice"}})
        self.assertEqual(out.model_version, "typesafe/jev-1.13-20260917")
        self.assertEqual(out.cost_usd, 0.0001)
        self.assertEqual(post.call_args.kwargs["json"]["model"], "typesafe/jev-1.13")
        with mock.patch("study_os.web.models.httpx.post", return_value=self._resp(500, {})):
            with self.assertRaises(ModelUnavailable):
                jev.decide("s", {"g": {}})
        with mock.patch("study_os.web.models.httpx.post", side_effect=httpx.ConnectError("x")):
            with self.assertRaises(ModelUnavailable):
                jev.decide("s", {"g": {}})

    def test_inferhub_falls_back_to_second_route(self) -> None:
        from unittest import mock

        import httpx

        from study_os.web.models import InferHubLLM, ModelUnavailable

        llm = InferHubLLM("k", "https://example.invalid/v1/")
        tool = {"type": "function", "function": {"name": "emit_turn", "parameters": {}}}
        ok = {"choices": [{"message": {"tool_calls": [{"function": {"arguments": json.dumps({"markdown": "hi"})}}]}}],
              "usage": {"prompt_tokens": 100, "completion_tokens": 20}}
        with mock.patch("study_os.web.models.httpx.post", side_effect=[self._resp(503, {}), self._resp(200, ok)]):
            out = llm.complete(("cb/glm-5.3", "cb/deepseek-v4.1-flash"), [{"role": "user", "content": "x"}], tool)
        self.assertEqual(out.route, "cb/deepseek-v4.1-flash")
        self.assertEqual(out.args, {"markdown": "hi"})
        self.assertGreater(out.cost_usd, 0)
        no_tool = {"choices": [{"message": {"content": "plain"}}]}
        with mock.patch("study_os.web.models.httpx.post", side_effect=[httpx.ReadTimeout("x"), self._resp(200, no_tool)]):
            with self.assertRaises(ModelUnavailable):
                llm.complete(("a", "b"), [], tool)


if __name__ == "__main__":
    unittest.main()
