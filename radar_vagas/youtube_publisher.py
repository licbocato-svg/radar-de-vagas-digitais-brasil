"""Publica automaticamente novos vídeos do YouTube no Telegram."""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

from radar_vagas.config import Settings
from radar_vagas.publishing.telegram import (
    TelegramApiError,
    TelegramBotClient,
    TelegramConfig,
)

CHANNEL_HANDLE = "liviabocato"

FEED_URL = (
    "https://www.youtube.com/feeds/videos.xml?forHandle="
    + urllib.parse.quote(CHANNEL_HANDLE)
)

STATE_FILE_NAME = "youtube_last_published.json"

ATOM_NAMESPACE = {
    "atom": "http://www.w3.org/2005/Atom"
}

YT_NAMESPACE = {
    "yt": "http://www.youtube.com/xml/schemas/2015"
}


def _fetch_feed() -> bytes:
    request = urllib.request.Request(
        FEED_URL,
        headers={
            "User-Agent": "AssistenteEmHomeOffice/1.0"
        },
    )

    with urllib.request.urlopen(
        request,
        timeout=30,
    ) as response:
        return response.read()


def _latest_video(
    feed: bytes,
) -> tuple[str, str, str] | None:

    root = ET.fromstring(feed)

    entry = root.find(
        "atom:entry",
        ATOM_NAMESPACE,
    )

    if entry is None:
        return None

    video_id = (
        entry.findtext(
            "yt:videoId",
            namespaces=YT_NAMESPACE,
        )
        or ""
    ).strip()

    title = (
        entry.findtext(
            "atom:title",
            namespaces=ATOM_NAMESPACE,
        )
        or ""
    ).strip()

    if not video_id or not title:
        return None

    link = (
        f"https://www.youtube.com/watch?v={video_id}"
    )

    return title, link, video_id


def _load_last_id(
    path: Path,
) -> str | None:

    if not path.exists():
        return None

    try:
        data = json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )

        value = data.get(
            "last_published_id"
        )

        return (
            value
            if isinstance(value, str)
            else None
        )

    except (
        OSError,
        json.JSONDecodeError,
    ):
        return None


def _save_last_id(
    path: Path,
    value: str,
) -> None:

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary = path.with_suffix(
        ".tmp"
    )

    temporary.write_text(
        json.dumps(
            {
                "last_published_id": value
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    temporary.replace(path)


async def publish_new_youtube_video() -> int:

    settings = Settings.from_env()

    state_path = (
        settings.data_dir
        / STATE_FILE_NAME
    )

    try:
        entry = _latest_video(
            _fetch_feed()
        )

    except (
        OSError,
        ET.ParseError,
    ) as error:

        print(
            f"Falha ao consultar o YouTube: {error}"
        )

        return 1

    if entry is None:

        print(
            "Nenhum vídeo válido encontrado "
            "no feed do YouTube."
        )

        return 0

    title, link, video_id = entry

    last_id = _load_last_id(
        state_path
    )

    if last_id == video_id:

        print(
            "Nenhum vídeo novo no YouTube."
        )

        return 0

    message = (
        "🎬 *VÍDEO NOVO NO CANAL*\n\n"
        "Acabei de publicar um novo conteúdo "
        "no YouTube que pode te ajudar "
        "no seu caminho no home office:\n\n"
        f"*{title}*\n\n"
        f"👉 Assista aqui:\n{link}"
    )

    try:
        client = TelegramBotClient(
            TelegramConfig.from_settings(
                settings
            )
        )

        await client.get_me()

        await client.send_message(
            message
        )

    except (
        RuntimeError,
        TelegramApiError,
    ) as error:

        print(
            f"Falha ao publicar vídeo "
            f"no Telegram: {error}"
        )

        return 1

    _save_last_id(
        state_path,
        video_id,
    )

    print(
        f"Vídeo publicado no Telegram: {title}"
    )

    return 0


if __name__ == "__main__":

    import asyncio

    raise SystemExit(
        asyncio.run(
            publish_new_youtube_video()
        )
    )
