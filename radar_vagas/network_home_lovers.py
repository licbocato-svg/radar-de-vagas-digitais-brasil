"""Publica mensagens automáticas no tópico Network Home Lovers."""

from __future__ import annotations

import asyncio

from radar_vagas.config import Settings
from radar_vagas.publishing.telegram import (
    TelegramApiError,
    TelegramBotClient,
    TelegramConfig,
)


CHAT_ID = "-1004314469021"

# Tópico Network Home Lovers
THREAD_ID = 133


MESSAGES = [
    """🤝 <b>NETWORK HOME LOVERS</b>

Que tal conhecer outras pessoas que também estão construindo sua trajetória no trabalho online?

💬 <b>Compartilhe com a comunidade:</b>

• Qual área do home office você trabalha ou gostaria de trabalhar?
• O que você está buscando neste momento?
• Qual ferramenta ou plataforma você mais utiliza?

👇 <b>APRESENTE-SE NOS COMENTÁRIOS E CONHEÇA OUTROS MEMBROS!</b>""",

    """💡 <b>UMA DICA PARA QUEM TRABALHA DE CASA</b>

Networking também faz parte da nossa jornada profissional.

Às vezes, uma conversa pode trazer uma informação, uma oportunidade ou até uma nova ideia para seguir em frente.

🤝 <b>Conte para a comunidade:</b>

Qual foi a melhor descoberta que você já fez sobre trabalho online?

👇 <b>COMPARTILHE SUA EXPERIÊNCIA!</b>""",

    """🚀 <b>NETWORK HOME LOVERS</b>

Você está começando agora no home office ou já trabalha online há algum tempo?

Queremos conhecer um pouco da sua história. ❤️

💬 <b>Conte para a comunidade:</b>

De onde você é e há quanto tempo está buscando oportunidades de trabalho online?

👇 <b>VAMOS NOS CONHECER!</b>""",

    """🌎 <b>VOCÊ NÃO ESTÁ SOZINHO NESSA JORNADA</b>

Aqui temos pessoas em diferentes momentos da caminhada:

💻 Quem está começando
📚 Quem está estudando
🔎 Quem está procurando oportunidades
🚀 Quem já trabalha online

🤝 <b>Use este espaço para trocar experiências e aprender com outras pessoas.</b>

👇 <b>QUAL É O SEU MOMENTO HOJE?</b>""",

    """✨ <b>NETWORK HOME LOVERS</b>

Uma das melhores coisas de uma comunidade é poder aprender com experiências diferentes.

💬 <b>Vamos trocar ideias?</b>

Qual é a maior dificuldade que você encontra hoje para trabalhar de casa?

Pode ser sobre plataformas, rotina, organização, oportunidades ou qualquer outro desafio relacionado ao home office.

👇 <b>CONTE PARA A COMUNIDADE.</b>""",
]


async def publish_network_message(
    variation: int = 0,
) -> int:

    settings = Settings.from_env()

    token, _, _ = settings.require_telegram()

    config = TelegramConfig(
        bot_token=token,
        chat_id=CHAT_ID,
        thread_id=THREAD_ID,
    )

    client = TelegramBotClient(
        config
    )

    message = MESSAGES[
        variation % len(MESSAGES)
    ]

    try:

        await client.get_me()

        await client.send_message(
            message,
            parse_mode="HTML",
        )

    except (
        RuntimeError,
        TelegramApiError,
    ) as error:

        print(
            f"Falha ao publicar mensagem "
            f"no Network Home Lovers: {error}"
        )

        return 1

    print(
        "Mensagem publicada com sucesso "
        "no tópico Network Home Lovers."
    )

    return 0


if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser(
        description=(
            "Publica mensagens no tópico "
            "Network Home Lovers."
        )
    )

    parser.add_argument(
        "--variation",
        type=int,
        default=0,
        help=(
            "define qual variação "
            "da mensagem será publicada"
        ),
    )

    args = parser.parse_args()

    raise SystemExit(
        asyncio.run(
            publish_network_message(
                args.variation
            )
        )
    )
