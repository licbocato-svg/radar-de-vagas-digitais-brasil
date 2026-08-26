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
│   │   └── telegram.py              # API oficial, leitura e formatador
│   └── storage/
│       └── seen_jobs.py             # Deduplicação persistente em JSON local
├── tests/
│   ├── test_filtering.py            # Testes de cargos e elegibilidade
│   ├── test_deduplication.py        # Testes de fingerprints e duplicatas
│   └── test_telegram.py             # Testes HTTP simulados, sem rede
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

# Aguarda uma mensagem no tópico e descobre o destino
python -m radar_vagas --discover-telegram-topic

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
   padrão do Python. `--check-telegram` chama apenas `getMe`; o modo de
   descoberta usa somente `getUpdates`; o envio só ocorre com
   `--send-test --confirm-send-test`.

## Variáveis de ambiente

Copie `.env.example` apenas como referência. O código lê:

- `RADAR_DATA_DIR`: diretório do arquivo local de deduplicação.
- `TELEGRAM_BOT_TOKEN`: token do bot criado no BotFather. É o único Secret
  necessário nesta etapa.
- `TELEGRAM_CHAT_ID`: será descoberto pelo modo de configuração e cadastrado
  posteriormente.
- `TELEGRAM_THREAD_ID`: será descoberto pelo modo de configuração e cadastrado
  posteriormente.
- `RADAR_TIMEZONE`: fuso operacional, com padrão `America/Sao_Paulo`.
- `RADAR_LOG_LEVEL`: nível de logs, com padrão `INFO`.

### Onde cadastrar o token nesta etapa

No editor do Replit:

1. Abra o painel **Tools**.
2. Selecione **Secrets**.
3. Clique em **+ New secret**.
4. Cadastre somente o nome `TELEGRAM_BOT_TOKEN` e o valor do token.
5. Clique em **Add Secret**.

Os Secrets são criptografados pelo Replit e ficam disponíveis ao programa como
variáveis de ambiente. Eles não devem ser colocados no código, no
`.env.example`, no README ou no chat. A documentação oficial está em
<https://docs.replit.com/core-concepts/project-editor/app-setup/secrets>.

Depois do cadastro, rode primeiro `python -m radar_vagas --check-telegram`.
Esse comando confirma o bot com `getMe` e não publica nada. Quando quiser
descobrir os IDs do grupo e do tópico, siga este fluxo:

1. Adicione o bot ao grupo que contém o tópico **Vagas & Oportunidades**.
2. Se o grupo usar o modo de privacidade do Telegram, desative-o no BotFather
   com `/setprivacy` ou torne o bot administrador, para que ele receba a
   mensagem comum enviada no tópico.
3. Execute:

```bash
python -m radar_vagas --discover-telegram-topic
```

4. Sem fechar o comando, envie uma mensagem qualquer dentro do tópico
   **Vagas & Oportunidades**.
5. O programa exibirá `TELEGRAM_CHAT_ID` e `TELEGRAM_THREAD_ID`. Ele não grava
   esses valores automaticamente e não envia nenhuma mensagem.

Mensagens de fórum normalmente trazem o `message_thread_id`, mas não o nome do
tópico em cada atualização. Por isso o modo descarta atualizações antigas e
captura a próxima mensagem de tópico enquanto estiver aguardando. Se a API
fornecer o nome de criação do tópico, ele também será conferido.

Somente depois de cadastrar os IDs descobertos, e com autorização explícita,
o envio da mensagem fixa de teste poderá ser feito com:

```bash
python -m radar_vagas --send-test --confirm-send-test
```

O comando faz uma verificação `getMe` antes e, em seguida, usa `sendMessage`.
Ele nunca envia vagas reais nessa etapa.

## Próximos passos sugeridos

- Implementar um coletor por plataforma, cada um com sua própria validação.
- Definir limites, cache e política de retry para cada fonte.
- Adicionar armazenamento transacional se o volume exigir mais que o JSON local.
- Conectar um cliente oficial do Telegram atrás do contrato de publicação.
- Adicionar observabilidade e uma rotina agendada somente depois que os
  coletores forem validados individualmente.