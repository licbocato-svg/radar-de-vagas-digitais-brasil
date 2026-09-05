"""Robô de boas-vindas para novos membros do Clube Home Office."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

from radar_vagas.config import Settings
from radar_vagas.publishing.telegram import (
    TelegramApiError,
    TelegramBotClient,
    TelegramConfig,
)


GENERAL_THREAD_ID = 11
STATE_FILE_NAME = "welcome_last_update.json"


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
# MENSAGEM ÚNICA DE BOAS-VINDAS
# ============================================================

WELCOME_MESSAGE = """👋 Bem-vindo(a) ao Clube Home Office, {name}!

🧭 Explore o Clube Home Office e acesse rapidamente os conteúdos da comunidade:"""


# ============================================================
# NOME DO MEMBRO
# ============================================================

def _name_from_user(
    user: dict[str, Any],
) -> str:

    first = str(
        user.get("first_name") or ""
    ).strip()

    last = str(
        user.get("last_name") or ""
    ).strip()

    username = str(
        user.get("username") or ""
    ).strip()

    name = " ".join(
        part
        for part in (first, last)
        if part
    )

    if name:
        return name

    if username:
        return f"@{username}"

    return "novo membro"


# ============================================================
# CONTROLE DE ATUALIZAÇÕES
# ============================================================

def _load_last_update(
    path: Path,
) -> int | None:

    if not path.exists():
        return None

    try:

        data = json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )

        value = data.get(
            "last_update_id"
        )

        if isinstance(
            value,
            int,
        ):
            return value

    except (
        OSError,
        json.JSONDecodeError,
    ):
        pass

    return None


def _save_last_update(
    path: Path,
    update_id: int,
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
                "last_update_id": update_id
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    temporary.replace(
        path
    )


# ============================================================
# DETECTAR ENTRADA DO MEMBRO
# ============================================================

def _member_from_chat_member_update(
    update: dict[str, Any],
) -> dict[str, Any] | None:

    event = update.get(
        "chat_member"
    )

    if not isinstance(
        event,
        dict,
    ):
        return None

    chat = event.get(
        "chat"
    )

    if not isinstance(
        chat,
        dict,
    ):
        return None

    chat_id = chat.get(
        "id"
    )

    if str(chat_id) != "-1004314469021":
        return None

    new_chat_member = event.get(
        "new_chat_member"
    )

    if not isinstance(
        new_chat_member,
        dict,
    ):
        return None

    old_chat_member = event.get(
        "old_chat_member"
    )

    if not isinstance(
        old_chat_member,
        dict,
    ):
        old_chat_member = {}

    user = new_chat_member.get(
        "user"
    )

    if not isinstance(
        user,
        dict,
    ):
        return None

    old_status = str(
        old_chat_member.get(
            "status",
            "",
        )
    )

    new_status = str(
        new_chat_member.get(
            "status",
            "",
        )
    )

    # Entrada real no grupo.
    if old_status not in {
        "left",
        "kicked",
    }:
        return None

    if new_status not in {
        "member",
        "restricted",
    }:
        return None

    # Ignorar bots.
    if user.get(
        "is_bot"
    ):
        return None

    return user


# ============================================================
# EXECUÇÃO PRINCIPAL
# ============================================================

async def run() -> int:

    settings = Settings.from_env()

    config = TelegramConfig.from_settings(
        settings
    )

    if config.thread_id != GENERAL_THREAD_ID:

        raise RuntimeError(
            "TELEGRAM_THREAD_ID deve ser 11 "
            "para o tópico Geral."
        )

    client = TelegramBotClient(
        config
    )

    await client.get_me()

    state_path = (
        settings.data_dir
        / STATE_FILE_NAME
    )

    last_update_id = _load_last_update(
        state_path
    )

    offset = (
        last_update_id + 1
        if last_update_id is not None
        else None
    )

    updates = await client.get_updates(
        offset=offset,
        poll_timeout_seconds=0,
    )

    # Primeira execução:
    # registra os eventos existentes sem enviar
    # boas-vindas antigas.
    if last_update_id is None:

        highest_update_id = max(
            (
                update.get(
                    "update_id"
                )
                for update in updates
                if isinstance(
                    update.get(
                        "update_id"
                    ),
                    int,
                )
            ),
            default=None,
        )

        if highest_update_id is not None:

            _save_last_update(
                state_path,
                highest_update_id,
            )

        print(
            "Primeira execução concluída."
        )

        print(
            "Atualizações existentes registradas."
        )

        print(
            "Robô pronto para novos membros."
        )

        return 0

    if not updates:

        print(
            "Nenhum novo membro encontrado."
        )

        return 0

    highest_update_id = (
        last_update_id
    )

    for update in updates:

        update_id = update.get(
            "update_id"
        )

        if isinstance(
            update_id,
            int,
        ):

            highest_update_id = max(
                highest_update_id,
                update_id,
            )

        member = (
            _member_from_chat_member_update(
                update
            )
        )

        if member is None:
            continue

        name = _name_from_user(
            member
        )

        # ====================================================
        # MENSAGEM ÚNICA COM BOAS-VINDAS + BOTÕES
        # ====================================================

        message = WELCOME_MESSAGE.format(
            name=name
        )

        await client.send_message_with_buttons(
            message,
            TOPIC_BUTTONS,
        )

        print(
            f"Boas-vindas enviadas para: {name}"
        )

    _save_last_update(
        state_path,
        highest_update_id,
    )

    print(
        "Verificação de novos membros concluída."
    )

    return 0


# ============================================================
# INICIALIZAÇÃO
# ============================================================

if __name__ == "__main__":

    try:

        raise SystemExit(
            asyncio.run(
                run()
            )
        )

    except (
        RuntimeError,
        TelegramApiError,
    ) as error:

        print(
            f"Falha no robô de boas-vindas: {error}"
        )

        raise SystemExit(1)
