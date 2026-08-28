"""Publica automaticamente novos artigos do blog no Telegram."""

from __future__ import annotations

import json
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

from radar_vagas.config import Settings
from radar_vagas.publishing.telegram import (
    TelegramApiError,
    TelegramBotClient,
    TelegramConfig,
)

FEED_URL = "https://quebreiodespertador.com/feed/"
STATE_FILE_NAME = "blog_last_published.json"


def _fetch_feed() -> bytes:
    request = urllib.request.Request(
        FEED_URL,
        headers={"User-Agent": "AssistenteEmHomeOffice/1.0"},
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read()


def _latest_post(feed: bytes) -> tuple[str, str, str] | None:
    root = ET.fromstring(feed)

    channel = root.find("channel")
    if channel is None:
        return None

    item = channel.find("item")
    if item is None:
        return None

    title = (item.findtext("title") or "").strip()
    link = (item.findtext("link") or "").strip()
    guid = (item.findtext("guid") or link).strip()

    if not title or not link:
        return None

    return title, link, guid


def _load_last_id(path: Path) -> str | None:
    if not path.exists():
        return None

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        value = data.get("last_published_id")
        return value if isinstance(value, str) else None
    except (OSError, json.JSONDecodeError):
        return None


def _save_last_id(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    temporary = path.with_suffix(".tmp")

    temporary.write_text(
        json.dumps(
            {"last_published_id": value},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    temporary.replace(path)


async def publish_new_blog_post() -> int:
    settings = Settings.from_env()
    state_path = settings.data_dir / STATE_FILE_NAME

    try:
        entry = _latest_post(_fetch_feed())
    except (OSError, ET.ParseError) as error:
        print(f"Falha ao consultar o feed do blog: {error}")
        return 1

    if entry is None:
        print("Nenhum artigo válido encontrado no feed.")
        return 0

    title, link, entry_id = entry
    last_id = _load_last_id(state_path)

    if last_id == entry_id:
        print("Nenhum artigo novo no blog.")
        return 0

    message = (
        "📝 *NOVO CONTEÚDO NO BLOG*\n\n"
        "Acabei de publicar um novo conteúdo que pode te ajudar "
        "no seu caminho no home office:\n\n"
        f"*{title}*\n\n"
        f"👉 Leia aqui:\n{link}"
    )

    try:
        client = TelegramBotClient(
            TelegramConfig.from_settings(settings)
        )

        await client.get_me()
        await client.send_message(message)

    except (RuntimeError, TelegramApiError) as error:
        print(f"Falha ao publicar artigo no Telegram: {error}")
        return 1

    _save_last_id(state_path, entry_id)

    print(f"Artigo publicado no Telegram: {title}")

    return 0


if __name__ == "__main__":
    import asyncio

    raise SystemExit(asyncio.run(publish_new_blog_post()))
