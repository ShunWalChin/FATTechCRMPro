# Atribuições e componentes de terceiros

O código de domínio e a interface deste repositório foram escritos para a FAT Tech.
Isso não transfere autoria de bibliotecas, ferramentas ou conteúdos de referência.
O conteúdo comercial do site foi migrado do repositório do próprio solicitante,
com sanitização do HTML de artigos. Scripts dos legados não são carregados na aplicação.

## Dependências de execução

As versões exatas, inclusive transitivas, estão em `package-lock.json` e `apps/api/uv.lock`.
As distribuições instaladas conservam suas licenças. Entre os componentes principais:
React, Next.js, HeroUI, Tailwind CSS, Lucide, Inter, FastAPI, Pydantic, SQLAlchemy,
psycopg, Argon2, Uvicorn, HTTPX, Python, Node.js e PostgreSQL.

HeroUI React e Styles 3.2.5 incluem licença Apache 2.0, copyright 2025 NextUI Inc.
O texto distribuído foi preservado em `docs/licenses/HeroUI-Apache-2.0.txt`.
O registro de descoberta identifica a divergência entre o manifest e o arquivo LICENSE;
este aviso usa o arquivo incluído no pacote instalado.

## Ferramentas e referências

Ruflo, Ponytail e Graphify mantêm autoria e licenças próprias; seus executores não são
incorporados ao runtime do CRM. A skill Graphify é distribuída em `.codex/skills/graphify`.
Graphify: copyright 2026 Safi Shamsi and the Graphify contributors. Licença Apache 2.0;
partes anteriores permanecem sob MIT. LICENSE, LICENSE-MIT e NOTICE foram preservados
em `docs/licenses/Graphify-*`.

FORT-CRM, WalChat, FGOS e DeskcommCRM são referências de requisitos e engenharia.
Não foram copiados integralmente para a distribuição. Fontes, commits, arquivos de
licença observados e lacunas estão em `docs/discovery/repositories.md`.
Os anexos Palantyr foram usados como material de conhecimento; segredos e bases privadas
não são publicados neste repositório.
