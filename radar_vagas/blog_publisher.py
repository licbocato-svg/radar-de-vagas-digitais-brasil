"""Publica automaticamente novos artigos do blog no Telegram."""

from __future__ import annotations

import json
import re
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from radar_vagas.config import Settings
from radar_vagas.publishing.telegram import (
    TelegramApiError,
    TelegramBotClient,
    TelegramConfig,
)


FEED_URL = "https://quebreiodespertador.com/feed/"

STATE_FILE_NAME = "blog_last_published.json"


def _fetch_feed() -> bytes:
    """Consulta o feed RSS do blog."""

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


def _stable_post_id(
    link: str,
    guid: str,
) -> str:
    """
    Cria um identificador estável para o artigo.

    Prioridade:
    1. ID numérico do WordPress (?p=10901).
    2. GUID do RSS.
    3. URL do artigo.
    """

    # --------------------------------------------------------
    # Tenta encontrar o ID do WordPress na URL.
    # Exemplo:
    # https://quebreiodespertador.com/?p=10901
    # --------------------------------------------------------

    try:

        parsed = urlsplit(
            link.strip()
        )

        query = parse_qs(
            parsed.query
        )

        post_ids = query.get(
            "p"
        )

        if post_ids:

            post_id = post_ids[0].strip()

            if post_id:

                return f"wordpress:{post_id}"

    except Exception:
        pass

    # --------------------------------------------------------
    # Também aceita URLs que contenham ?p=10901
    # mesmo que tenham outros parâmetros.
    # --------------------------------------------------------

    match = re.search(
        r"[?&]p=(\d+)",
        link,
        flags=re.IGNORECASE,
    )

    if match:

        return (
            f"wordpress:{match.group(1)}"
        )

    # --------------------------------------------------------
    # Se não houver ID WordPress, usa o GUID.
    # --------------------------------------------------------

    if guid.strip():

        return (
            f"guid:{guid.strip()}"
        )

    # --------------------------------------------------------
    # Último recurso: URL.
    # --------------------------------------------------------

    return (
        f"url:{link.strip()}"
    )


def _latest_post(
    feed: bytes,
) -> tuple[str, str, str] | None:
    """Obtém o artigo mais recente do feed."""

    root = ET.fromstring(
        feed
    )

    channel = root.find(
        "channel"
    )

    if channel is None:

        return None

    item = channel.find(
        "item"
    )

    if item is None:

        return None

    title = (
        item.findtext(
            "title"
        )
        or ""
    ).strip()

    link = (
        item.findtext(
            "link"
        )
        or ""
    ).strip()

    guid = (
        item.findtext(
            "guid"
        )
        or ""
    ).strip()

    if not title or not link:

        return None

    entry_id = _stable_post_id(
        link,
        guid,
    )

    return (
        title,
        link,
        entry_id,
    )


def _load_last_id(
    path: Path,
) -> str | None:
    """Carrega o identificador do último artigo publicado."""

    if not path.exists():

        return None

    try:

        data = json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )

        if not isinstance(
            data,
            dict,
        ):

            return None

        value = data.get(
            "last_published_id"
        )

        if isinstance(
            value,
            str,
        ):

            return value

        return None

    except (
        OSError,
        json.JSONDecodeError,
    ):

        return None


def _save_last_id(
    path: Path,
    value: str,
) -> None:
    """Salva o identificador do último artigo publicado."""

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

    temporary.replace(
        path
    )


async def publish_new_blog_post() -> int:
    """Publica somente se houver um artigo realmente novo."""

    settings = Settings.from_env()

    state_path = (
        settings.data_dir
        / STATE_FILE_NAME
    )

    # --------------------------------------------------------
    # Consulta o feed.
    # --------------------------------------------------------

    try:

        entry = _latest_post(
            _fetch_feed()
        )

    except (
        OSError,
        ET.ParseError,
    ) as error:

        print(
            "Falha ao consultar o feed "
            f"do blog: {error}"
        )

        return 1

    if entry is None:

        print(
            "Nenhum artigo válido encontrado "
            "no feed."
        )

        return 0

    title, link, entry_id = entry

    # --------------------------------------------------------
    # Carrega o último artigo publicado.
    # --------------------------------------------------------

    last_id = _load_last_id(
        state_path
    )

    print(
        f"Artigo mais recente encontrado: "
        f"{title}"
    )

    print(
        f"ID do artigo encontrado: "
        f"{entry_id}"
    )

    if last_id:

        print(
            f"Último artigo registrado: "
            f"{last_id}"
        )

    else:

        print(
            "Nenhum artigo anterior "
            "registrado no histórico."
        )

    # --------------------------------------------------------
    # Se for o mesmo artigo, NÃO publica.
    # --------------------------------------------------------

    if last_id == entry_id:

        print(
            "Nenhum artigo novo no blog."
        )

        return 0

    # --------------------------------------------------------
    # Mensagem.
    # --------------------------------------------------------

    message = (
        "📝 *NOVO CONTEÚDO NO BLOG*\n\n"
        "Acabei de publicar um novo conteúdo "
        "que pode te ajudar no seu caminho "
        "no home office:\n\n"
        f"*{title}*\n\n"
        "👇 *ACESSE O ARTIGO COMPLETO:*"
    )

    buttons = [
        [
            {
                "text": (
                    "📰 LER O ARTIGO COMPLETO"
                ),
                "url": link,
            }
        ]
    ]

    # --------------------------------------------------------
    # Envia para o Telegram.
    # --------------------------------------------------------

    try:

        config = TelegramConfig.from_settings(
            settings
        )

        client = TelegramBotClient(
            config
        )

        await client.get_me()

        await client.send_message_with_buttons(
            message,
            buttons,
        )

    except (
        RuntimeError,
        TelegramApiError,
    ) as error:

        print(
            "Falha ao publicar artigo "
            f"no Telegram: {error}"
        )

        return 1

    # --------------------------------------------------------
    # Só salva o histórico depois que o Telegram
    # confirmou o envio.
    # --------------------------------------------------------

    _save_last_id(
        state_path,
        entry_id,
    )

    print(
        f"Artigo publicado no Telegram: "
        f"{title}"
    )

    print(
        "Botão do artigo enviado com sucesso."
    )

    print(
        f"Histórico atualizado: "
        f"{entry_id}"
    )

    return 0


if __name__ == "__main__":

    raise SystemExit(
        __import__("asyncio").run(
            publish_new_blog_post()
        )
    )
