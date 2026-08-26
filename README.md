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
│   │   └── telegram.py              # Contrato e formatador para Telegram
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
6. `publishing/telegram.py` define o contrato e o formato da mensagem que um
   publicador oficial poderá usar futuramente. Nesta versão ele não faz
   requisições.

## Variáveis de ambiente

Copie `.env.example` apenas como referência. O código lê:

- `RADAR_DATA_DIR`: diretório do arquivo local de deduplicação.
- `TELEGRAM_BOT_TOKEN`: reservado para o futuro bot, ainda não utilizado.
- `TELEGRAM_CHAT_ID`: reservado para o futuro grupo, ainda não utilizado.
- `RADAR_TIMEZONE`: fuso operacional, com padrão `America/Sao_Paulo`.
- `RADAR_LOG_LEVEL`: nível de logs, com padrão `INFO`.

Não coloque tokens no código ou no repositório. Quando a integração do
Telegram for adicionada, os valores deverão ser fornecidos pelo mecanismo de
segredos do ambiente.

## Próximos passos sugeridos

- Implementar um coletor por plataforma, cada um com sua própria validação.
- Definir limites, cache e política de retry para cada fonte.
- Adicionar armazenamento transacional se o volume exigir mais que o JSON local.
- Conectar um cliente oficial do Telegram atrás do contrato de publicação.
- Adicionar observabilidade e uma rotina agendada somente depois que os
  coletores forem validados individualmente.