"""Publicador automático dos produtos do Clube Home Office."""

from __future__ import annotations

import asyncio
from html import escape

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
# PRODUTOS
# ============================================================

PRODUCTS = {
    "home-office": {
        "title": "Guia Home Office Internacional",
        "url": "https://pay.kiwify.com.br/NVpp2kM",
        "button": "🏠 CONHECER O GUIA HOME OFFICE",
        "messages": [
            """💻 <b>QUER COMEÇAR A TRABALHAR DE CASA?</b>

O <b>Guia Home Office Internacional para Iniciantes</b> foi criado para quem quer conhecer melhor as possibilidades de trabalho remoto e as oportunidades internacionais.

Se você está dando os primeiros passos nesse universo, esse material pode te ajudar a entender melhor por onde começar.

👇 <b>CONHEÇA O GUIA:</b>""",

            """🌎 <b>TRABALHAR ONLINE PARA EMPRESAS INTERNACIONAIS</b>

Pode parecer complicado no início, principalmente quando você não sabe quais caminhos existem.

Por isso, reunimos em um único material informações para ajudar quem está começando no universo do <b>home office internacional</b>.

👇 <b>CONHEÇA O GUIA:</b>""",
        ],
    },

    "formula-hol": {
        "title": "Fórmula HOL",
        "url": "https://lp.quebreiodespertador.com/formula-hol",
        "button": "🚀 CONHECER A FÓRMULA HOL",
        "messages": [
            """🚀 <b>QUER APRENDER UM CAMINHO MAIS COMPLETO PARA TRABALHAR DE CASA?</b>

A <b>Fórmula HOL</b> é um treinamento para quem quer entender melhor as oportunidades de home office e desenvolver uma nova possibilidade de renda trabalhando online.

👇 <b>CONHEÇA A FÓRMULA HOL:</b>""",

            """💡 <b>NÃO SABE POR ONDE COMEÇAR NO HOME OFFICE?</b>

A <b>Fórmula HOL</b> reúne conhecimentos e estratégias para quem quer conhecer oportunidades e desenvolver sua trajetória trabalhando pela internet.

👇 <b>CONHEÇA O TREINAMENTO:</b>""",
        ],
    },

    "avaliador-mapas": {
        "title": "Guia Avaliador de Mapas",
        "url": "https://pay.kiwify.com.br/5valD5Y",
        "button": "🗺️ CONHECER O GUIA AVALIADOR DE MAPAS",
        "messages": [
            """🗺️ <b>VOCÊ TEM CURIOSIDADE SOBRE O TRABALHO DE AVALIADOR DE MAPAS?</b>

Essa é uma área que desperta muitas dúvidas: o que faz um avaliador, onde encontrar oportunidades e como funcionam esses projetos.

Preparamos um material específico para quem quer conhecer melhor esse universo.

👇 <b>CONHEÇA O GUIA:</b>""",

            """📍 <b>GOOGLE MAPS, LOCALIZAÇÃO E AVALIAÇÃO DE RESULTADOS</b>

Esses são alguns dos elementos presentes em projetos de <b>Avaliação de Mapas</b>.

Se você quer entender melhor como funciona essa área, temos um material específico sobre o assunto.

👇 <b>CONHEÇA O GUIA AVALIADOR DE MAPAS:</b>""",
        ],
    },

    "avaliador-digital": {
        "title": "Guia Avaliador Digital",
        "url": "https://pay.kiwify.com.br/7JDByUZ",
        "button": "💻 CONHECER O GUIA AVALIADOR DIGITAL",
        "messages": [
            """🤖 <b>QUER CONHECER O TRABALHO DE AVALIADOR DIGITAL?</b>

Essa área tem despertado cada vez mais interesse entre quem busca oportunidades de trabalho online.

Antes de procurar vagas, é importante entender como esse universo funciona.

👇 <b>CONHEÇA O GUIA:</b>""",

            """📱 <b>JÁ OUVIU FALAR EM AVALIADOR DIGITAL?</b>

Se você ainda não sabe exatamente como essa área funciona, preparamos um material para ajudar a conhecer os conceitos, oportunidades e caminhos desse mercado.

👇 <b>CONHEÇA O GUIA AVALIADOR DIGITAL:</b>""",
        ],
    },
}


# ============================================================
# PUBLICAÇÃO
# ============================================================

async def publish_product(
    product_key: str,
    variation: int = 0,
) -> int:

    settings = Settings.from_env()

    if product_key not in PRODUCTS:
        print(
            f"Produto inválido: {product_key}"
        )
        return 1

    product = PRODUCTS[
        product_key
    ]

    token, _, _ = settings.require_telegram()

    config = TelegramConfig(
        bot_token=token,
        chat_id=CHAT_ID,
        thread_id=THREAD_ID,
    )

    client = TelegramBotClient(
        config
    )

    messages = product["messages"]

    message = messages[
        variation % len(messages)
    ]

    buttons = [
        [
            {
                "text": product["button"],
                "url": product["url"],
            }
        ]
    ]

    try:

        await client.get_me()

        await client.send_message_with_buttons(
            message,
            buttons,
            parse_mode="HTML",
        )

    except (
        RuntimeError,
        TelegramApiError,
    ) as error:

        print(
            f"Falha ao publicar produto: {error}"
        )

        return 1

    print(
        f"Produto publicado: "
        f"{product['title']}"
    )

    print(
        "Botão enviado com sucesso."
    )

    return 0


# ============================================================
# INICIALIZAÇÃO
# ============================================================

if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser(
        description=(
            "Publica produtos do "
            "Clube Home Office."
        )
    )

    parser.add_argument(
        "produto",
        choices=PRODUCTS.keys(),
        help="produto que será publicado",
    )

    parser.add_argument(
        "--variation",
        type=int,
        default=0,
        help="variação da mensagem",
    )

    args = parser.parse_args()

    raise SystemExit(
        asyncio.run(
            publish_product(
                args.produto,
                args.variation,
            )
        )
    )
