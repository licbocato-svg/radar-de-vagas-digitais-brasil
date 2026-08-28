"""Publicador automático dos produtos do Clube Home Office."""

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
# PRODUTOS
# ============================================================

PRODUCTS = {
    "home-office": {
        "title": "Guia Home Office Internacional",
        "url": "https://pay.kiwify.com.br/NVpp2kM",
        "button": "🏠 CONHECER O GUIA HOME OFFICE",
        "messages": [
            """💻 *QUER COMEÇAR A TRABALHAR DE CASA?*

O *Guia Home Office Internacional para Iniciantes* foi criado para quem quer conhecer melhor as possibilidades de trabalho remoto e as oportunidades internacionais.

Se você está dando os primeiros passos nesse universo, esse material pode te ajudar a entender melhor por onde começar.

👇 *CONHEÇA O GUIA:*""",

            """🌎 *TRABALHAR ONLINE PARA EMPRESAS INTERNACIONAIS*

Pode parecer complicado no início, principalmente quando você não sabe quais caminhos existem.

Por isso, reunimos em um único material informações para ajudar quem está começando no universo do *home office internacional*.

👇 *CONHEÇA O GUIA:*""",
        ],
    },

    "formula-hol": {
        "title": "Fórmula HOL",
        "url": "https://lp.quebreiodespertador.com/formula-hol",
        "button": "🚀 CONHECER A FÓRMULA HOL",
        "messages": [
            """🚀 *QUER APRENDER UM CAMINHO MAIS COMPLETO PARA TRABALHAR DE CASA?*

A *Fórmula HOL* é um treinamento para quem quer entender melhor as oportunidades de home office e desenvolver uma nova possibilidade de renda trabalhando online.

👇 *CONHEÇA A FÓRMULA HOL:*""",

            """💡 *NÃO SABE POR ONDE COMEÇAR NO HOME OFFICE?*

A *Fórmula HOL* reúne conhecimentos e estratégias para quem quer conhecer oportunidades e desenvolver sua trajetória trabalhando pela internet.

👇 *CONHEÇA O TREINAMENTO:*""",
        ],
    },

    "avaliador-mapas": {
        "title": "Guia Avaliador de Mapas",
        "url": "https://pay.kiwify.com.br/5valD5Y",
        "button": "🗺️ CONHECER O GUIA AVALIADOR DE MAPAS",
        "messages": [
            """🗺️ *VOCÊ TEM CURIOSIDADE SOBRE O TRABALHO DE AVALIADOR DE MAPAS?*

Essa é uma área que desperta muitas dúvidas: o que faz um avaliador, onde encontrar oportunidades e como funcionam esses projetos.

Preparamos um material específico para quem quer conhecer melhor esse universo.

👇 *CONHEÇA O GUIA:*""",

            """📍 *GOOGLE MAPS, LOCALIZAÇÃO E AVALIAÇÃO DE RESULTADOS*

Esses são alguns dos elementos presentes em projetos de *Avaliação de Mapas*.

Se você quer entender melhor como funciona essa área, temos um material específico sobre o assunto.

👇 *CONHEÇA O GUIA AVALIADOR DE MAPAS:*""",
        ],
    },

    "avaliador-digital": {
        "title": "Guia Avaliador Digital",
        "url": "https://pay.kiwify.com.br/7JDByUZ",
        "button": "💻 CONHECER O GUIA AVALIADOR DIGITAL",
        "messages": [
            """🤖 *QUER CONHECER O TRABALHO DE AVALIADOR DIGITAL?*

Essa área tem despertado cada vez mais interesse entre quem busca oportunidades de trabalho online.

Antes de procurar vagas, é importante entender como esse universo funciona.

👇 *CONHEÇA O GUIA:*""",

            """📱 *JÁ OUVIU FALAR EM AVALIADOR DIGITAL?*

Se você ainda não sabe exatamente como essa área funciona, preparamos um material para ajudar a conhecer os conceitos, oportunidades e caminhos desse mercado.

👇 *CONHEÇA O GUIA AVALIADOR DIGITAL:*""",
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
