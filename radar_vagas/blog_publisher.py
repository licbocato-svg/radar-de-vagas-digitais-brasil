"""Publica automaticamente novos artigos do blog no Telegram."""

from __future__ import annotations

import asyncio
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


def _extract_wordpress_id(
    value: str,
) -> str | None:
    """
    Tenta extrair o ID numérico de um artigo WordPress.

    Exemplos reconhecidos:

    https://quebreiodespertador.com/?p=10901
    https://quebreiodespertador.com/?p=10901&utm_source=...
    """

    if not value:
        return None

    text = value.strip()

    # --------------------------------------------------------
    # Tenta analisar a URL.
    # --------------------------------------------------------

    try:
        parsed = urlsplit(text)

        query = parse_qs(
            parsed.query,
            keep_blank_values=True,
        )

        post_ids = query.get("p")

        if post_ids:

            post_id = post_ids[0].strip()

            if post_id.isdigit():
                return post_id

    except Exception:
        pass

    # --------------------------------------------------------
    # Fallback: procura ?p=10901 ou &p=10901.
    # --------------------------------------------------------

    match = re.search(
        r"(?:\?|&)p=(\d+)",
        text,
        flags=re.IGNORECASE,
    )

    if match:
        return match.group(1)

    return None


def _normalize_identifier(
    value: str,
) -> str:
    """
    Normaliza um identificador para comparação.

    Se encontrar um ID WordPress, usa:

        wordpress:10901

    Caso contrário, preserva o valor de forma normalizada.
    """

    value = value.strip()

    if not value:
        return ""

    wordpress_id = _extract_wordpress_id(
        value
    )

    if wordpress_id:
        return (
            f"wordpress:{wordpress_id}"
        )

    return value.rstrip("/").casefold()


def _identifiers_for_post(
    link: str,
    guid: str,
) -> set[str]:
    """
    Cria todas as identificações possíveis para o artigo.

    Isso permite reconhecer o mesmo artigo mesmo quando
    o RSS apresenta o GUID e o link em formatos diferentes.
    """

    identifiers: set[str] = set()

    for value in (
        link,
        guid,
    ):

        if not value:
            continue

        normalized = _normalize_identifier(
            value
        )

        if normalized:
            identifiers.add(
                normalized
            )

    # Também adiciona explicitamente o ID WordPress.
    for value in (
        link,
        guid,
    ):

        wordpress_id = _extract_wordpress_id(
            value
        )

        if wordpress_id:

            identifiers.add(
                f"wordpress:{wordpress_id}"
            )

    return identifiers


def _latest_post(
    feed: bytes,
) -> tuple[str, str, str, tuple[str, ...]] | None:
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

    identifiers = _identifiers_for_post(
        link,
        guid,
    )

    if not identifiers:
        return None

    # Usa o identificador mais estável disponível.
    wordpress_id = _extract_wordpress_id(
        link
    )

    if wordpress_id:
        primary_id = (
            f"wordpress:{wordpress_id}"
        )
    else:

        wordpress_id = _extract_wordpress_id(
            guid
        )

        if wordpress_id:
            primary_id = (
                f"wordpress:{wordpress_id}"
            )
        else:
            primary_id = (
                _normalize_identifier(
                    guid or link
                )
            )

    return (
        title,
        link,
        primary_id,
        tuple(sorted(identifiers)),
    )


def _load_last_ids(
    path: Path,
) -> set[str]:
    """
    Carrega o histórico do último artigo publicado.

    Aceita tanto o formato antigo quanto o novo.
    """

    if not path.exists():
        return set()

    try:

        data = json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )

    except (
        OSError,
        json.JSONDecodeError,
    ):

        return set()

    if not isinstance(
        data,
        dict,
    ):
        return set()

    value = data.get(
        "last_published_id"
    )

    if not isinstance(
        value,
        str,
    ):
        return set()

    normalized = _normalize_identifier(
        value
    )

    if not normalized:
        return set()

    return {
        normalized
    }


def _save_last_id(
    path: Path,
    value: str,
) -> None:
    """Salva o identificador estável do último artigo publicado."""

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

    (
        title,
        link,
        primary_id,
        entry_identifiers,
    ) = entry

    # --------------------------------------------------------
    # Carrega o histórico.
    # --------------------------------------------------------

    last_ids = _load_last_ids(
        state_path
    )

    print(
        f"Artigo mais recente encontrado: "
        f"{title}"
    )

    print(
        f"ID estável do artigo: "
        f"{primary_id}"
    )

    print(
        "Identificadores encontrados: "
        f"{', '.join(entry_identifiers)}"
    )

    if last_ids:

        print(
            "Último identificador registrado: "
            f"{', '.join(sorted(last_ids))}"
        )

    else:

        print(
            "Nenhum artigo anterior "
            "registrado no histórico."
        )

    # --------------------------------------------------------
    # COMPARAÇÃO ROBUSTA
    #
    # Se qualquer identificador do artigo atual coincidir
    # com o histórico, consideramos que já foi publicado.
    # --------------------------------------------------------

    if last_ids.intersection(
        entry_identifiers
    ):

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
    # SOMENTE DEPOIS DO ENVIO BEM-SUCEDIDO,
    # salva o histórico.
    # --------------------------------------------------------

    _save_last_id(
        state_path,
        primary_id,
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
        f"{primary_id}"
    )

    return 0


if __name__ == "__main__":

    raise SystemExit(
        asyncio.run(
            publish_new_blog_post()
        )
    )
