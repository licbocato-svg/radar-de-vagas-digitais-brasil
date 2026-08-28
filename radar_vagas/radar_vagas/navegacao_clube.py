"""Publica a mensagem de navegação do Clube Home Office."""

from __future__ import annotations

import asyncio

from radar_vagas.config import Settings
from radar_vagas.publishing.telegram import (
    TelegramApiError,
    TelegramBotClient,
    TelegramConfig,
)


# ============================================================
# CONFIGURAÇÃO
# ============================================================

CHAT_ID = "-1004314469021"

# Tópico Materiais & Conteúdos
THREAD_ID = 10


# ============================================================
# BOTÕES DOS TÓPICOS
# ============================================================

TOPIC_BUTTONS = [
    [
        {
            "text": "💬 Geral",
            "url": "https://t.me/c/4314469021/11",
        },
        {
            "text": "📢 Vagas e Oportunidades",
            "url": "https://t.me/c/4314469021/8",
        },
    ],
    [
        {
            "text": "📚 Materiais & Conteúdos",
            "url": "https://t.me/c/4314469021/10",
        },
        {
            "text": "📁 Arquivos do Canal",
            "url": "https://t.me/c/4314469021/7",
        },
    ],
]


# ============================================================
# MENSAGEM
# ============================================================

NAVIGATION_MESSAGE = """🧭 *EXPLORE O CLUBE HOME OFFICE*

Encontre rapidamente o conteúdo que você procura e aproveite todos os espaços da nossa comunidade.

👇 *CLIQUE NO TÓPICO QUE DESEJA ACESSAR:*"""


# ============================================================
# EXECUÇÃO
# ============================================================

async def publish_navigation() -> int:

    settings = Settings.from_env()

    # Criamos uma configuração específica para
    # o tópico Materiais & Conteúdos.
    config = TelegramConfig(
        bot_token=settings.require_telegram()[0],
        chat_id=CHAT_ID,
        thread_id=THREAD_ID,
    )

    client = TelegramBotClient(
        config
    )

    try:

        await client.get_me()

        await client.send_message_with_buttons(
            NAVIGATION_MESSAGE,
            TOPIC_BUTTONS,
        )

    except (
        RuntimeError,
        TelegramApiError,
    ) as error:

        print(
            f"Falha ao publicar navegação: {error}"
        )

        return 1

    print(
        "Mensagem de navegação publicada "
        "no tópico Materiais & Conteúdos."
    )

    return 0


# ============================================================
# INICIALIZAÇÃO
# ============================================================

if __name__ == "__main__":

    raise SystemExit(
        asyncio.run(
            publish_navigation()
        )
    )
