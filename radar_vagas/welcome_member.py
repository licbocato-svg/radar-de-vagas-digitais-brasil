"""Dá boas-vindas a novos membros no tópico Geral do Telegram."""

from __future__ import annotations

import asyncio
from typing import Any

from radar_vagas.config import Settings
from radar_vagas.publishing.telegram import (
    TelegramApiError,
    TelegramBotClient,
    TelegramConfig,
)


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
        part for part in (first, last) if part
    )

    if name:
        return name

    if username:
        return f"@{username}"

    return "novo membro"


async def run() -> int:
    settings = Settings.from_env()

    config = TelegramConfig.from_settings(
        settings
    )

    if config.thread_id is None:
        raise RuntimeError(
            "TELEGRAM_THREAD_ID não está configurado."
        )

    client = TelegramBotClient(config)

    await client.get_me()

    updates = await client.get_updates(
        poll_timeout_seconds=0
    )

    for update in updates:

        message = update.get("message")

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

        if thread_id != config.thread_id:
            continue

        for member in members:

            if not isinstance(member, dict):
                continue

            if member.get("is_bot"):
                continue

            name = _name_from_user(member)

            welcome_message = WELCOME.format(
                name=name
            )

            await client.send_message(
                welcome_message
            )

            print(
                f"Boas-vindas enviadas para: {name}"
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
