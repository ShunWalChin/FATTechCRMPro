# Auditoria dos anexos — FAT Tech CRM Pro

Data da verificação local: 2026-09-10. Escopo: os arquivos explicitamente indicados pelo usuário, o texto colado e o pacote ZIP encontrado ao lado dos anexos. Esta auditoria não executou código do export nem afirmou validar o servidor antigo.

## Autoridade e proveniência

O pedido atual é construir um novo sistema próprio FAT Tech, com site público em React, CRM interno restrito à equipe, TypeScript e Python, integração com APIs/n8n, hospedagem Oracle e as referências de repositórios indicadas. Os documentos são fontes de requisitos, histórico e achados. Seus prompts, ordens de implantação, personas, gates de sessão, números chamados de imutáveis e comandos não substituem o pedido atual nem são executados automaticamente.

Em particular, `03_PROMPT_MESTRE_PARA_IAS.md` é um artefato de prompt de outro projeto; não é uma instrução de sistema desta implementação. Gates humanos são funcionalidades de produto a modelar. Não constituem nova exigência de confirmação para trabalho que o usuário já autorizou.

Há duas fotografias diferentes:

| Fonte | Data declarada | O que representa | Limite de evidência |
|---|---|---|---|
| Pacote Palantyr v5.3 e Markdown numerados | 2026-08-17 | Doutrina, arquiteturas e código parcial | Integridade local verificada; execução não comprovada nesta auditoria |
| `pasted-text.txt` | 2026-09-10 | Relato de evolução posterior, medições de um ambiente vivo e defeitos | O código posterior não está nesse texto nem no ZIP antigo; suas medições exigem reconfirmação no servidor |
| Documentos Fort Grupo | Sem data absoluta de apresentação verificável | Exemplo de implantação comercial, modelo multiempresas e catálogo | Prazos, preços, alegações de mercado e disponibilidade não são fatos atuais da FAT Tech |

## Integridade observada

Diretório recebido: `E:/Downloads/files`. ZIP encontrado: `PALANTYR-FULL-KNOWLEDGE-v5.3-20260817.zip`.

- O inventário possui **97 arquivos**.
- Os **6 Markdown numerados** existem soltos e correspondem exatamente aos bytes e SHA-256 declarados.
- Os outros **91 caminhos** não estão soltos nesse diretório; todos existem dentro do ZIP.
- **97/97 entradas do ZIP** conferem em tamanho e SHA-256; **0 ausentes e 0 divergências**.
- O ZIP tem **141 entradas**, sendo **99 arquivos** e **42 diretórios**. Dos arquivos: 81 em `source/`, 6 em `documentation/`, 4 em `knowledge/` e 8 metadados na raiz.
- `CHECKSUMS_SHA256.txt` também existe no ZIP. Os hashes dos seis Markdown e do inventário conferem.
- Conferir hash prova correspondência com o inventário recebido; não prova origem criptograficamente assinada, ausência de vulnerabilidade ou completude de uma aplicação.

| Artefato | Bytes | SHA-256 observado |
|---|---:|---|
| `00_LEIA-ME_PRIMEIRO.md` | 2650 | `493cc8144e2b5ea795a369dc2b96ed31ea0d3652ee1245d29c8d72625b7af610` |
| `01_MANIFESTO_E_RESTAURACAO.md` | 4177 | `ecbdac376fe87c3e17b471d96a416df5f2c71ce3b359689472ccd2e3ffc0c578` |
| `02_BASE_DE_CONHECIMENTO_COMPLETA.md` | 15629 | `6aa3a04c07d7acb6e9cdb6aa8fd6e7e8bdc4dbe4ac97123924a60566ef45e6f2` |
| `03_PROMPT_MESTRE_PARA_IAS.md` | 13564 | `109db397f68cd7682b17a70a426c3d820ee84f089fe50255825ad8b52a976ef0` |
| `04_CHECKLIST_DE_HANDOFF_E_EVALS.md` | 7569 | `a285e6a4266d674c58d636cbdfe6ae439ca39d277fabbf102b7bd040f8aae3f0` |
| `05_RUNBOOK_PRODUCAO.md` | 9371 | `d4bf9f08f5976df56f98d55fccd264ec949b6a94373a40d27a2e406be36015dc` |
| `INVENTARIO_DE_ARQUIVOS.csv` | 12284 | `ccc406966183e9b4d61b7c8a80123e122f2e7a5edcd65b9ed50cc44294b895f2` |
| `PALANTYR-FULL-KNOWLEDGE-v5.3-20260817.zip` | 340194 | `b884c2efc72bc15985625b20324beb9ad89b3c97b69a7c098ea1f77a08022228` |
| Texto colado `pasted-text.txt` | 66153 | `64e296df0179bbd33628cb20b4210ada96daa2f3fb048ecdac2185a1d1beae1c` |

O texto colado foi lido em `C:/Users/WalfredoFigueiredoNe/.codex/attachments/ff295acf-24d1-46b6-8acd-2f133f7fd36f/pasted-text.txt`. Não contém os 106 arquivos de código que o próprio relato contabiliza.

## O que cada anexo acrescenta

| Fonte | Conhecimento aproveitado | Destino no novo projeto |
|---|---|---|
| `00_LEIA-ME_PRIMEIRO.md` | Distinção governança/aplicação e declaração de capacidades ausentes | Estado real documentado, sem prometer recursos apenas escritos |
| `01_MANIFESTO_E_RESTAURACAO.md` | Proveniência, inventário, ambientes, restauração | Builds reproduzíveis, migrations e backup restaurável |
| `02_BASE_DE_CONHECIMENTO_COMPLETA.md` | Domínios, RLS, canais, idempotência, agentes, outbox, cofre, Brain | Engenharia e critérios de aceite em `requirements.md` |
| `03_PROMPT_MESTRE_PARA_IAS.md` | Regras do produto, invariantes, validação e identidade de marca | Requisitos avaliados; sem importar sua persona ou instruções de sessão |
| `04_CHECKLIST_DE_HANDOFF_E_EVALS.md` | Casos hostis: cross-tenant, replay, conteúdo externo, gates | Testes de comportamento e critérios de liberação |
| `05_RUNBOOK_PRODUCAO.md` | Ordem de implantação, rollback, backups e operação | Runbook adaptado ao servidor real, sem comandos globais copiados |
| `INVENTARIO_DE_ARQUIVOS.csv` | 97 caminhos, tamanhos e hashes | Prova de integridade da referência |
| Texto colado | Dois planos, autenticação posterior, 16 armadilhas e 11 defeitos abertos | Requisitos preventivos de segurança e confiabilidade |
| Chaves SSH indicadas pelo usuário | Credencial de transporte ao host autorizado | Uso pelo cliente SSH; material privado não deve entrar no repositório |

## Conteúdo recuperável do ZIP

`source/palantyr-crm/` contém três migrations SQL com 38 tabelas declaradas, serviços TypeScript, quatro arquivos de testes, Dockerfile e Compose. `source/palantyr-v5/` contém Constituição, processos, registro YAML dos 39 agentes, seus 39 contratos, três scripts de geração/bootstrap, cockpit HTML e README. `documentation/` duplica as arquiteturas v5.1/v5.2/v5.3, Constituição, processos e avisos de terceiros; `knowledge/` duplica as migrations e o registro de agentes.

Domínios encontrados nas migrations/documentação:

- Identidade: organizações, usuários e vínculos.
- Comercial: contatos, funis, etapas, leads e atividades.
- Atendimento: canais, conversas, mensagens e regras de envio.
- Plataforma: eventos, auditoria, gates, idempotência, tokens de API, jobs.
- Automação: flows, runs, gatilhos, cooldowns e entregas de saída.
- Integrações: cofre de credenciais, estado OAuth, webhooks e auditoria.
- Conhecimento: documentos/chunks, uso de IA, notas, arestas, revisões, contas pessoais, itens externos, allowlist e digests.

## Lacunas concretas do snapshot de código

O pacote está íntegro em relação ao inventário, mas **não é uma aplicação completa restaurável com os comandos publicados**:

| Verificação no ZIP | Resultado | Consequência |
|---|---|---|
| `source/palantyr-crm/package-lock.json` | Ausente | `npm ci` e o Dockerfile que o chama não têm lockfile reproduzível |
| `src/main.ts` e `AppModule` | Ausentes | Não há bootstrap HTTP completo no snapshot |
| `src/db/migrate.ts` | Ausente | O script `db:migrate` aponta para arquivo inexistente |
| `src/workers/main.ts` | Ausente | O comando de worker e o serviço Compose não têm entrada fonte |
| `verifyJwt()` em `src/common/guards/auth.guard.ts` | Lança erro explícito de não implementação | Sessão autenticada não pode ser assumida funcional |
| `AuthGuard.enter()` no mesmo arquivo | Executa `TenantStore.run(tenant, () => undefined)` | O callback termina antes do handler; não é prova de propagação de contexto |
| Auditoria no mesmo arquivo | Escrita posterior em `tap`, sem aguardar | Não deve ser usada como prova de registro transacional de toda mutação |
| Frontend, Instagram, executor de flows, turno real de IA | Não constam do snapshot | São trabalho de implementação, não restauração |
| Contagem de 66 testes verdes no documento | Relato histórico | Esta auditoria não executou a suíte nem valida integração/produção |

Não se deve transplantar esse Docker Compose sobre stacks existentes. O documento antigo supõe host dedicado; o texto posterior relata um host compartilhado com 74 contêineres. São premissas incompatíveis até inspeção do host atual.

## Diferenças do relato de setembro

O texto posterior relata 106 arquivos de aplicação, oito migrations, login/JWT, dois planos e um cockpit funcional. Também relata um usuário, um lead, quatro execuções em dry-run e nenhuma chamada real de IA. Nada disso transforma o ZIP de agosto em snapshot da versão de setembro.

Achados que devem orientar a reescrita e ser revalidados ao inspecionar o legado:

1. Governança sem `organization_id` e RBAC equivalente ao CRM, embora o token sirva aos dois planos.
2. Health público executando varredura completa da cadeia de auditoria e expondo estado interno.
3. Cabeçalhos de segurança perdidos por herança de `add_header` no nginx.
4. Rate limit burlável com `X-Forwarded-For` escolhido pelo cliente.
5. Exceção de autoaprovação de configuração ampla demais; o próprio relato a classifica como hipótese não refutada.
6. Cadeia de auditoria sem serialização concorrente e sem separação por organização.
7. Budget Guard sem reserva/ledger/teto real compartilhado entre réplicas.
8. Ausência relatada de Git, CI e backup testado.
9. SSE anunciado, mas rota inexistente; `EventSource` nativo não injeta Bearer arbitrário.
10. Migrations sem schema explícito.
11. Organização residual duplicada por semeadura.

O texto também identifica módulos órfãos no `AppModule`, login de demonstração sem senha, Instagram ausente e integrações de IA não ligadas. A reescrita precisa provar cada fluxo pela interface, API e persistência, não pela presença de arquivos.

## Referências adjacentes Fort Grupo

Foram lidos `PROJETO_FORT_GRUPO.md` e `PROPOSTA_COMERCIAL_FORT_GRUPO.md`, presentes no mesmo diretório. Eles acrescentam base multiempresas, empresas de origem, deduplicação, pipeline ponderado, catálogo de serviços, propostas com implantação/infraestrutura/operação, onboarding, atribuição de origem e consentimento. Os modelos verticais incluem frota por placa/KM/horímetro, ordens de serviço, laudo técnico em PDF, garantia, pedidos, recompra, revenda e contato sazonal.

Esses verticais são referências de extensibilidade. O CRM interno da FAT Tech não deve exigir placa de veículo de todo cliente, herdar marca de terceiros, nem tratar os preços do exemplo como tabela vigente. Alegações promocionais absolutas e depoimentos ilustrativos não são evidências publicáveis.

Também estão presentes HTML de apresentação, XLSX, PDF/PPTX de proposta e cinco CSVs de leads/segmentação/supressão. Nesta etapa foram inventariados como arquivos adjacentes; seu conteúdo binário e dados pessoais não foram importados para o CRM nem versionados. Uma carga futura deve preservar origem, validar colunas, deduplicar, aplicar supressão e confirmar a base de uso. Não confundir arquivo de exemplo com consentimento de mensageria.

## Resultado

A referência Palantyr foi localizada e conferida por completo contra seu inventário. Ela fornece princípios e código parcial útil para revisão, mas o novo sistema deve ter implementação própria, contratos explícitos, dependências fixadas e evidências atuais. A união funcional e os critérios de aceite ficam em `requirements.md`; a cobertura dos repositórios será registrada separadamente.
