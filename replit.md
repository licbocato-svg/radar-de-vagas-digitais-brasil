# Radar de Vagas Digitais Brasil

Base modular em Python para coletar, filtrar, deduplicar e futuramente publicar
vagas digitais remotas elegíveis para residentes no Brasil.

## Run & Operate

- `python -m radar_vagas` — executa o pipeline inicial sem rede
- `python -m unittest discover -s tests -v` — valida a lógica local
- `pnpm --filter @workspace/api-server run dev` — servidor legado da base Replit
- `pnpm run typecheck` — valida os pacotes TypeScript existentes

## Stack

- Python 3.11+ para o Radar, somente biblioteca padrão nesta fase
- Coletores, filtros, deduplicação e publicação separados por módulo
- Deduplicação persistente em JSON local, substituível por outro storage
- Telegram reservado atrás de um contrato, sem cliente ou token nesta fase

- pnpm workspaces, Node.js 24, TypeScript 5.9
- API: Express 5
- DB: PostgreSQL + Drizzle ORM
- Validation: Zod (`zod/v4`), `drizzle-zod`
- API codegen: Orval (from OpenAPI spec)
- Build: esbuild (CJS bundle)

## Where things live

- `radar_vagas/core/` — modelos e regras de negócio
- `radar_vagas/collectors/` — contratos e futuros adaptadores de plataformas
- `radar_vagas/storage/` — estado local para fingerprints
- `radar_vagas/publishing/` — contratos de distribuição, incluindo Telegram
- `tests/` — testes da lógica sem chamadas externas
- `README.md` — guia principal e próximos passos

## Architecture decisions

- A primeira versão usa apenas a biblioteca padrão para manter o núcleo testável
  e sem dependências externas.
- A elegibilidade é conservadora: uma vaga remota sem país declarado não é
  presumida como válida para o Brasil.
- Cada coletor entrega o mesmo modelo de domínio, evitando acoplamento entre
  plataformas.
- O estado de duplicatas é local e atômico, com uma interface que permite
  trocar o armazenamento sem alterar o pipeline.

## Product

O produto monitorará vagas de avaliação digital, aplicará critérios de cargo e
localização, evitará republicações e poderá publicar novas oportunidades em um
grupo do Telegram após as integrações serem implementadas.

## User preferences

- Não conectar plataformas externas nem inserir tokens secretos durante a
  estruturação inicial.

## Gotchas

- Não assumir que uma vaga marcada apenas como “remota” aceita residentes no
  Brasil; a fonte deve informar Brasil, cobertura global ou equivalente.
- Não adicionar tokens no código; use o mecanismo de segredos do ambiente quando
  o publicador do Telegram for implementado.

## Pointers

- See the `pnpm-workspace` skill for workspace structure, TypeScript setup, and package details
