# Radar de Vagas Digitais Brasil

Base inicial, em Python, para monitorar oportunidades de trabalho remoto
relacionadas a avaliação de mapas, dados, conteúdo, anúncios, mídias sociais,
qualidade de busca e inteligência artificial, priorizando vagas elegíveis para
residentes no Brasil.

## Status atual

Esta primeira versão contém somente a estrutura local e a lógica de domínio.
Nenhuma plataforma externa foi conectada, nenhum coletor HTTP foi implementado
e nenhum envio ao Telegram é realizado. O projeto não contém tokens, chaves ou
outros segredos.

O comando principal executa um pipeline vazio de forma segura, servindo como
ponto de partida para os próximos coletores.

## Estrutura

```text
.
├── radar_vagas/
│   ├── config.py                    # Configuração via variáveis de ambiente
│   ├── __main__.py                  # Ponto de entrada da CLI
│   ├── core/
│   │   ├── eligibility.py           # Elegibilidade para residentes no Brasil
│   │   ├── models.py                # Modelo de oportunidade
│   │   ├── pipeline.py              # Orquestração da coleta e filtragem
│   │   └── roles.py                 # Termos e correspondência de cargos
│   ├── collectors/
│   │   ├── base.py                  # Contrato para futuros coletores
│   │   └── empty.py                 # Coletor vazio, sem rede
│   ├── publishing/
│   │   └── telegram.py              # API oficial e formatador para Telegram
│   └── storage/
│       └── seen_jobs.py             # Deduplicação persistente em JSON local
├── tests/
│   ├── test_filtering.py            # Testes de cargos e elegibilidade
│   └── test_deduplication.py       # Testes de fingerprints e duplicatas
├── data/
│   └── .gitkeep                     # Dados locais ficam fora do versionamento
├── .env.example                     # Nomes das variáveis, sem valores secretos
├── pyproject.toml
└── README.md
```

## Como executar

Requer Python 3.11 ou superior.

```bash
# Executa o pipeline inicial sem coletores externos
python -m radar_vagas

# Verifica o token com getMe, sem enviar mensagem
python -m radar_vagas --check-telegram

# Envia uma mensagem fixa de teste, somente com confirmação explícita
python -m radar_vagas --send-test --confirm-send-test

# Executa os testes da lógica local
python -m unittest discover -s tests -v
```

Se o pacote for instalado no ambiente, a CLI equivalente é:

```bash
radar-vagas
```

## Como a arquitetura funciona

1. Cada plataforma futura implementará `JobCollector` em
   `radar_vagas/collectors/`.
2. O coletor transforma sua resposta em `JobOpportunity`, sem espalhar
   detalhes da plataforma pelo restante do sistema.
3. `roles.py` procura os cargos-alvo no título, descrição e palavras-chave.
4. `eligibility.py` aplica uma regra conservadora para o Brasil: aceita Brasil,
   BR, cobertura global ou localização explicitamente compatível; localização
   desconhecida não é assumida como elegível.
5. `SeenJobStore` registra fingerprints em `data/seen_jobs.json` para que uma
   vaga aceita não seja processada novamente entre execuções.
6. `publishing/telegram.py` usa a API HTTP oficial do Telegram com a biblioteca
   padrão do Python. `--check-telegram` chama apenas `getMe`; o envio só ocorre
   com `--send-test --confirm-send-test`.

## Variáveis de ambiente

Copie `.env.example` apenas como referência. O código lê:

- `RADAR_DATA_DIR`: diretório do arquivo local de deduplicação.
- `TELEGRAM_BOT_TOKEN`: token do bot criado no BotFather.
- `TELEGRAM_CHAT_ID`: identificador do grupo de destino.
- `TELEGRAM_THREAD_ID`: identificador do tópico do grupo; pode ficar ausente
  quando a mensagem deve ir para o tópico geral.
- `RADAR_TIMEZONE`: fuso operacional, com padrão `America/Sao_Paulo`.
- `RADAR_LOG_LEVEL`: nível de logs, com padrão `INFO`.

### Onde cadastrar os três valores

No editor do Replit:

1. Abra o painel **Tools**.
2. Selecione **Secrets**.
3. Clique em **+ New secret**.
4. Cadastre exatamente estes nomes, um por vez, e seus respectivos valores:
   `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` e `TELEGRAM_THREAD_ID`.
5. Clique em **Add Secret** para cada item.

Os Secrets são criptografados pelo Replit e ficam disponíveis ao programa como
variáveis de ambiente. Eles não devem ser colocados no código, no
`.env.example`, no README ou no chat. A documentação oficial está em
<https://docs.replit.com/core-concepts/project-editor/app-setup/secrets>.

Depois do cadastro, rode primeiro `python -m radar_vagas --check-telegram`.
Esse comando confirma o bot com `getMe` e não publica nada. Quando quiser
autorizar o envio da mensagem fixa de teste, use explicitamente:

```bash
python -m radar_vagas --send-test --confirm-send-test
```

O comando faz uma verificação `getMe` antes e, em seguida, usa `sendMessage`
com `TELEGRAM_CHAT_ID` e, quando preenchido, `TELEGRAM_THREAD_ID`. Ele nunca
envia vagas reais nessa etapa.

## Próximos passos sugeridos

- Implementar um coletor por plataforma, cada um com sua própria validação.
- Definir limites, cache e política de retry para cada fonte.
- Adicionar armazenamento transacional se o volume exigir mais que o JSON local.
- Conectar um cliente oficial do Telegram atrás do contrato de publicação.
- Adicionar observabilidade e uma rotina agendada somente depois que os
  coletores forem validados individualmente.