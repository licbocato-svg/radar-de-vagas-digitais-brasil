from __future__ import annotations

import asyncio
import json
import unittest
from typing import Any
from urllib.request import Request

from radar_vagas.publishing.telegram import TelegramBotClient, TelegramConfig


class FakeResponse:
    def __init__(self, payload: dict[str, Any]) -> None:
        self.payload = payload

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")


class TelegramTests(unittest.TestCase):
    def test_get_me_uses_api_without_sending_message(self) -> None:
        requests: list[Request] = []

        def fake_urlopen(request: Request, *, timeout: float) -> FakeResponse:
            requests.append(request)
            return FakeResponse(
                {"ok": True, "result": {"id": 123, "is_bot": True, "username": "radar_test"}}
            )

        client = TelegramBotClient(
            TelegramConfig("test-token-not-a-secret", "-100123", 42),
            urlopen=fake_urlopen,
        )
        result = asyncio.run(client.get_me())

        self.assertEqual(result["username"], "radar_test")
        self.assertEqual(len(requests), 1)
        self.assertTrue(requests[0].full_url.endswith("/getMe"))
        self.assertIsNone(requests[0].data)

    def test_send_message_includes_configured_chat_and_thread(self) -> None:
        requests: list[Request] = []

        def fake_urlopen(request: Request, *, timeout: float) -> FakeResponse:
            requests.append(request)
            return FakeResponse({"ok": True, "result": {"message_id": 7}})

        client = TelegramBotClient(
            TelegramConfig("test-token-not-a-secret", "-100123", 42),
            urlopen=fake_urlopen,
        )
        asyncio.run(client.send_message("mensagem segura de teste"))

        body = json.loads(requests[0].data.decode("utf-8"))
        self.assertEqual(body["chat_id"], "-100123")
        self.assertEqual(body["message_thread_id"], 42)
        self.assertEqual(body["text"], "mensagem segura de teste")