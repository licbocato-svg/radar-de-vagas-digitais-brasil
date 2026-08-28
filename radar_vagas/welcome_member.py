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


WELCOME = """👋 *BEM-VINDO(A) AO CLUBE HOME OFFICE!*

Olá, {name}! Seja muito bem-vindo(a)! 💙

Este grupo é exclusivo para pessoas que desejam *trabalhar em casa, no conforto do seu lar, e/ou conquistar uma renda extra online*.

Criamos esta comunidade para trocar experiências, compartilhar resultados, aprender, ajudar uns aos outros e crescer juntos, sempre com fé no nosso propósito. 🙏✨

🎯 *PROPÓSITO DO GRUPO*

Aqui você vai encontrar pessoas assim como você: pessoas que já trabalham em casa, estão procurando uma oportunidade de trabalho remoto ou desejam construir uma renda extra pela internet.

Nosso objetivo é criar um ambiente de *apoio, aprendizado, networking e compartilhamento de oportunidades*, para que cada membro possa avançar em sua própria jornada.

📌 *REGRAS DA COMUNIDADE*

*1. RESPEITO SEMPRE EM PRIMEIRO LUGAR*

Trate todos com educação, empatia e cordialidade. Brigas, discussões pessoais, ofensas ou ataques não serão tolerados.

*2. PROIBIDO SPAM*

Nada de mensagens repetitivas, correntes ou conteúdos fora de contexto. O grupo é para conteúdos que realmente agregam.

*3. CONTEÚDO SAUDÁVEL E SEGURO*

Não compartilhe conteúdo ofensivo, pornográfico, discriminatório ou excessivamente sensível.

*Homofobia, preconceito ou intolerância de qualquer tipo resultarão em banimento.*

*4. SEM POLÍTICA, RELIGIÃO OU FUTEBOL*

Para manter o foco e evitar divisões, não serão permitidos debates sobre política, religião ou futebol. Nosso objetivo é preservar um ambiente *neutro, produtivo e acolhedor*.

*5. SEM DIVULGAÇÃO EXTERNA*

Não é permitida a divulgação de mentorias, cursos, grupos, consultorias ou produtos que não sejam da comunidade. A divulgação externa será tratada com rigor.

*6. NADA DE VENDAS PESSOAIS*

Este grupo não é espaço para oferecer produtos ou serviços próprios. O foco é *apoio, aprendizado e networking*.

*7. PERGUNTAS APENAS POR ESCRITO*

Evite enviar áudios. Escreva sua dúvida para que todos possam acompanhar, participar e contribuir com a resposta.

*8. PROIBIDO CHAMAR NO PRIVADO*

O grupo não é uma mentoria individual. É proibido chamar administradores ou membros no privado para solicitar atendimento, suporte ou orientação individual.

🚨 *BANIMENTO PERMANENTE*

*Quem desrespeitar qualquer regra será BANIDO PERMANENTEMENTE, sem aviso prévio!*

💙 *Seja muito bem-vindo(a) ao Clube Home Office!*

Participe, compartilhe suas experiências, ajude outros membros e aproveite a comunidade.

*Estamos juntos nessa jornada! 🚀*
"""


def _name_from_user(user: dict[str, Any]) -> str:
    first = str(user.get("first_name") or "").strip()
    last = str(user.get("last_name") or "").strip()
    username = str(user.get("username") or "").strip()

    name = " ".join(
        part for part in (first, last)
        if part
    )

    if name:
        return name

    if username:
        return f"@{username}"

    return "novo membro"


def _load_last_update(path: Path) -> int | None:
    if not path.exists():
        return None

    try:
        data = json.loads(
            path.read_text(encoding="utf-8")
        )

        value = data.get("last_update_id")

        if isinstance(value, int):
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

    temporary = path.with_suffix(".tmp")

    temporary.write_text(
        json.dumps(
            {
                "last_update_id": update_id
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    temporary.replace(path)


async def run() -> int:

    settings = Settings.from_env()

    config = TelegramConfig.from_settings(
        settings
    )

    if config.thread_id != GENERAL_THREAD_ID:
        raise RuntimeError(
            "O TELEGRAM_THREAD_ID configurado "
            f"deve ser {GENERAL_THREAD_ID} para o tópico General."
        )

    client = TelegramBotClient(config)

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
    # apenas registra as atualizações existentes.
    # Assim o robô não envia boas-vindas para
    # pessoas que já estavam no grupo.
    if last_update_id is None:

        highest_update_id = None

        for update in updates:

            update_id = update.get(
                "update_id"
            )

            if isinstance(update_id, int):

                if (
                    highest_update_id is None
                    or update_id > highest_update_id
                ):
                    highest_update_id = update_id

        if highest_update_id is not None:
            _save_last_update(
                state_path,
                highest_update_id,
            )

        print(
            "Primeira execução concluída. "
            "As atualizações existentes foram registradas."
        )

        print(
            "O robô está pronto para novos membros."
        )

        return 0

    if not updates:

        print(
            "Nenhum novo membro encontrado."
        )

        return 0

    highest_update_id = last_update_id

    for update in updates:

        update_id = update.get(
            "update_id"
        )

        if isinstance(update_id, int):

            highest_update_id = max(
                highest_update_id,
                update_id,
            )

        message = update.get(
            "message"
        )

        if not isinstance(message, dict):
            continue

        members = message.get(
            "new_chat_members"
        )

        if not isinstance(members, list):
            continue

        if not members:
            continue

        thread_id = message.get(
            "message_thread_id"
        )

        if thread_id != GENERAL_THREAD_ID:
            continue

        for member in members:

            if not isinstance(
                member,
                dict,
            ):
                continue

            if member.get("is_bot"):
                continue

            name = _name_from_user(
                member
            )

            welcome_message = WELCOME.format(
                name=name
            )

            await client.send_message(
                welcome_message
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


if __name__ == "__main__":

    try:

        raise SystemExit(
            asyncio.run(run())
        )

    except (
        RuntimeError,
        TelegramApiError,
    ) as error:

        print(
            f"Falha no robô de boas-vindas: {error}"
        )

        raise SystemExit(1)
