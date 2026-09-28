"""Kokoro TTS thin path (Refs #180)."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from study_os.web.config import Settings
from study_os.web.tts import synthesize_kokoro, tts_config_payload


def _settings(**kwargs) -> Settings:
    base = dict(
        database_url="postgresql://sos:sos@localhost:5432/study_os",
        allowed_origins=("http://localhost:8000",),
        cookie_secure=False,
        tts_engine="browser",
        kokoro_base_url="http://kokoro:8880",
        kokoro_voice="af_heart",
        kokoro_speed=1.08,
    )
    base.update(kwargs)
    return Settings(**base)


class TtsConfigTests(unittest.TestCase):
    def test_browser_default_payload(self):
        payload = tts_config_payload(_settings())
        self.assertEqual(payload["engine"], "browser")
        self.assertFalse(payload["kokoro"])
        self.assertIsNone(payload["voice"])

    def test_kokoro_payload(self):
        payload = tts_config_payload(_settings(tts_engine="kokoro", kokoro_voice="af_bella"))
        self.assertEqual(payload["engine"], "kokoro")
        self.assertTrue(payload["kokoro"])
        self.assertEqual(payload["voice"], "af_bella")
        self.assertEqual(payload["speed"], 1.08)

    def test_unknown_engine_falls_back_to_browser(self):
        payload = tts_config_payload(_settings(tts_engine="whispering-void"))
        self.assertEqual(payload["engine"], "browser")


class SynthesizeKokoroTests(unittest.TestCase):
    def test_empty_text_raises(self):
        with self.assertRaises(ValueError):
            synthesize_kokoro(_settings(tts_engine="kokoro"), "  ")

    def test_posts_openai_compatible_body(self):
        mock_resp = MagicMock()
        mock_resp.content = b"ID3fake"
        mock_resp.headers = {"content-type": "audio/mpeg"}
        mock_resp.raise_for_status = MagicMock()
        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.post.return_value = mock_resp

        with patch("study_os.web.tts.httpx.Client", return_value=mock_client):
            audio, media = synthesize_kokoro(
                _settings(tts_engine="kokoro", kokoro_voice="af_heart"),
                "Still one lookup.",
            )

        self.assertEqual(audio, b"ID3fake")
        self.assertEqual(media, "audio/mpeg")
        args, kwargs = mock_client.post.call_args
        self.assertEqual(args[0], "http://kokoro:8880/v1/audio/speech")
        self.assertEqual(kwargs["json"]["voice"], "af_heart")
        self.assertEqual(kwargs["json"]["input"], "Still one lookup.")
        self.assertEqual(kwargs["json"]["response_format"], "mp3")


if __name__ == "__main__":
    unittest.main()
