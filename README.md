# FAT Tech CRM Pro

Site público e CRM interno da FAT Tech, reescritos em React/TypeScript e Python.
Primeira versão operacional publicada na Oracle em 11/09/2026.

- [Site publicado](https://fattechcrmpro.64.181.178.125.nip.io)
- [Entrar no CRM](https://fattechcrmpro.64.181.178.125.nip.io/login)
- [Contrato interativo da API](https://fattechcrmpro.64.181.178.125.nip.io/api/docs)
- [Estado da entrega, provas e pendências](docs/releases/2026-09-11.md)
- [Funis configuráveis e motivo de perda, publicado em 11/09](docs/releases/2026-09-11-funis-configuraveis.md)
- [Compliance de envio, radar comercial e destino externo, publicado em 12/09](docs/releases/2026-09-12-compliance-e-radar.md)
- [Do lead ao trabalho, kanban arrastável e ferramental, publicado em 12/09](docs/releases/2026-09-12-lead-para-trabalho.md)
- [Acabamento, ficha do registro e busca global, publicado em 12/09](docs/releases/2026-09-12-acabamento-e-ficha.md)
- [Versão 0.2: avisos, importação e operação comercial ligada](docs/releases/2026-09-12-versao-0.2.md)
- [Versão 0.2.1: relatórios com tela e quadro que funciona no celular](docs/releases/2026-09-12-versao-0.2.1.md)

O domínio `fattech.com.br` ainda serve a versão anterior. O endereço acima é a nova
instalação isolada, com HTTPS e banco persistente, pronta para a equipe começar a operar.
As credenciais do administrador são entregues em arquivo local privado, fora deste repositório.

## O que está funcionando

- Site responsivo, 22 artigos, 20 landing pages e redirecionamentos das URLs anteriores.
- Formulário público que grava contato, consentimento, atribuição UTM e auditoria no CRM.
- Login privado, sessões revogáveis, troca de senha, papéis e administração da equipe.
- Contatos, empresas, tarefas, projetos, produtos e conhecimento.
- Funis configuráveis por etapa, com rótulo, probabilidade, resultado e duração esperada definidos
  pela equipe; oportunidades em kanban com motivo de perda obrigatório e previsão ponderada.
- Radar de risco comercial: oportunidades paradas classificadas contra a duração da etapa, com
  sumário por faixa e destaque para quem está sem próxima ação marcada.
- Avisos derivados dos próprios registros: tarefa vencida, aprovação pendente e oportunidade
  parada, com sino no topo e link direto para o registro.
- Importação de contatos com mapeamento de colunas e conferência que grava só depois de aprovada.
- Propostas com itens do catálogo, metas por responsável e relatório por safra de criação, com tela
  de recorte por responsável, origem e período — e atingimento de meta só quando o recorte permite
  a comparação.
- Lead do site vira trabalho: contato, oportunidade no funil e tarefa de retorno, sem duplicar
  pipeline nem repetir lembrete quando a mesma pessoa reenvia o formulário.
- Kanban com arrastar-e-soltar entre etapas por mouse e por toque, com alça no cartão, rolagem
  automática nas bordas e o seletor de etapa preservado para teclado e leitor de tela.
- Decisão de envio determinística e auditável antes de qualquer mensagem: consentimento, opt-out,
  janela do canal, blocklist e cooldown avaliados no instante do envio, com trava de modo seguro.
- Lançamentos financeiros internos, solicitações de aprovação, cadastro de campanhas,
  conversas/rascunhos, configurações de agentes e simulação estrutural de automações.
- Dashboard calculado no banco, busca, filtros, exportação da página atual, versionamento
  otimista e trilha de auditoria. Valores monetários são centavos inteiros.
- API com escopos, webhook n8n assinado/idempotente e outbox durável com worker de tentativas.
- PostgreSQL com políticas de isolamento, serviços Docker separados, TLS e backup diário
  com restauração inicial verificada em banco descartável.

## Escopo que continua em desenvolvimento

Esta publicação é a base operacional; não representa conclusão das 72 famílias de recursos
levantadas nos legados. Adaptadores WhatsApp/Instagram/e-mail, execução de campanhas e IA,
RAG, calendário, propostas comerciais, cobrança/fiscal, importação com deduplicação,
MFA e recuperação de conta continuam pendentes. Os endpoints de envio não simulam sucesso.
Automações armazenam e simulam estrutura; não há editor visual/executor completo.
O n8n de produção ainda precisa de workflow e credenciais próprios para consumir os eventos.

O tenant FAT Tech é provisionado; a base suporta isolamento entre organizações, mas ainda
não oferece cadastro e alternância completos de organizações pela interface. Consulte
os critérios de aceitação em [requisitos](docs/discovery/requirements.md).

## Stack e organização

| Diretório | Responsabilidade |
|---|---|
| `apps/web/app` | Rotas públicas, layout e área CRM em Next.js 16 / React 19 |
| `apps/web/components` | Interface HeroUI 3, formulários e módulos operacionais |
| `apps/web/lib` | Cliente API, descritores de recursos e conteúdo |
| `apps/web/content` | Conteúdo estruturado do site original, sanitizado na importação |
| `apps/api/fattech` | FastAPI, validação, autenticação, domínio, SQLAlchemy e worker |
| `apps/api/tests` | Comportamento, segurança, idempotência, worker e RLS PostgreSQL |
| `tests/e2e` | Fluxos reais de navegador com banco de teste isolado |
| `infra` | Imagens, Compose, Nginx, provisionamento, backup e restauração |
| `integrations/n8n` | Contrato de integração e operação de webhooks |
| `scripts` | Desenvolvimento, ferramentas, inventário, verificação de segredos e release |
| `docs` | Arquitetura, modelo de dados, fontes, operação, licenças e entrega |
| `design-system` | Direção visual e regras de interface |
| `.codex` | Skill Graphify e hooks locais de engenharia |

[Inventário com tamanho e SHA-256 de cada arquivo](docs/FILE_INVENTORY.csv).
Lockfiles: `package-lock.json` e `apps/api/uv.lock`; requisitos Python de produção incluem hashes.

## Desenvolvimento e validação

Node.js 24, Python 3.12 e uv. Instruções Windows/Linux e variáveis em
[Operação](docs/OPERATIONS.md) e [API](apps/api/API.md).

```text
npm ci
npm run dev
npm run typecheck
npm run build
npm run test:e2e
python scripts/check_secrets.py
python scripts/inventory.py
```

O teste de navegador sobe API/Next em portas 8100/3100 e cria seu próprio banco descartável.
Testes PostgreSQL exigem banco com `test` no nome; a CI provisiona um serviço separado.
Não apontar testes destrutivos para o banco operacional.

## Engenharia e referências

Ruflo 3.41.2, Ponytail 4.9.0 e Graphify 0.9.57 são ferramentas de engenharia; HeroUI 3.2.5
é usado na interface. Veja [instalação e evidências](docs/TOOLING.md),
[arquitetura](docs/ARCHITECTURE.md), [modelo de dados](docs/DATA_MODEL.md),
[auditoria dos nove repositórios](docs/discovery/repositories.md) e
[consolidação dos anexos](docs/discovery/attachments.md).

Clones, anexos privados, chaves, bancos e credenciais ficam fora do Git e das imagens.
As referências orientam o domínio; bibliotecas e ferramentas continuam tendo autoria e
licenças próprias. Consulte [avisos de terceiros](THIRD_PARTY_NOTICES.md).
