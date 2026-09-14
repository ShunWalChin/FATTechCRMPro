# Paridade operacional — seleção para a versão 0.4

Pesquisa em 2026-09-13. Este documento propõe critérios de produto; não declara funcionalidades entregues. A aprovação depende de implementação, testes e evidência na nota da versão. O objetivo é remover gargalos comerciais concretos, sem alegar paridade integral ou superioridade geral sobre produtos consolidados.

## Método e ponto de partida

O Graphify foi consultado antes do código: a busca ampla não encontrou correspondência; `graphify query "Task" --budget 1400` encontrou 53 nós e as relações de `Task`, `PipelineStage`, `services.py`, `record_views.py` e `sales_operations.py`. O grafo indicava 1.120 nós na consulta. Os achados abaixo foram confirmados nos arquivos, pois relações estruturais não demonstram comportamento de negócio.

A matriz `docs/discovery/requirements.md` já pede tarefas filtráveis (CRM-06), funis configuráveis (CRM-04), histórico e responsáveis (CRM-02). O núcleo já possui deduplicação, importação atômica, auditoria, regras de ganho/perda, propostas e metas. Esta rodada deve completar o uso diário desses recursos antes de ampliar integrações externas.

## 1. Filtros operacionais e visões reutilizáveis

**Referência:** o HubSpot permite salvar filtros de registros e definir visibilidade privada, de equipe ou da conta. Isso reduz a repetição de montar a mesma carteira. [Documentação oficial: Create and manage saved views](https://knowledge.hubspot.com/records/create-and-manage-saved-views).

**Achado local:** `apps/api/fattech/services.py`, função `list_records`, aceita igualdade para status, etapa, relacionamentos e responsável, além de busca textual. Não oferece prazo ou intervalo de datas. `apps/web/components/resource-page.tsx` guarda busca e filtro em estado React e envia busca/status/etapa/funil; não expõe responsável ou persistência de uma visão. Ausência confirmada no ponto de partida, não inferida da página comercial de outro produto.

**Incremento recomendado:** filtros de responsável, status, origem e período onde forem pertinentes ao recurso, com ordenação estável e URLs reproduzíveis. Visões salvas privadas por usuário constituem um complemento pequeno; compartilhamento de equipe pode ser uma entrega posterior, com política explícita.

**Critérios verificáveis:**

- Filtrar muda consulta e contagem no servidor, não apenas os registros da página atual.
- Recarregar ou abrir URL reproduz a seleção sem alterar o tenant da sessão.
- Combinar busca, responsável e status retorna a interseção correta; filtro desconhecido não é silenciosamente tratado como válido.
- Paginação possui desempate determinístico e reinicia quando o filtro muda.
- Se houver visões salvas, outro usuário não lê uma visão privada e uma visão nunca concede permissão sobre dados.

## 2. Qualificação obrigatória por etapa

**Referência:** o Pipedrive permite tornar campos obrigatórios por funil e etapa. A documentação informa que importação, API, automações e algumas operações em lote podem contornar essa exigência. [Documentação oficial: Required fields](https://support.pipedrive.com/en/article/required-fields).

**Achado local:** `apps/api/fattech/schemas.py`, classe `PipelineStage`, contém chave, rótulo, probabilidade, resultado e duração esperada. Não possui requisitos de qualificação. `Deal` permite contato, empresa, responsável, previsão de fechamento e próxima ação opcionais. As regras existentes protegem etapas inválidas e motivos de perda, mas não exigem contexto comercial antes de avançar.

**Incremento recomendado:** permitir ao administrador selecionar, de uma lista fechada, os campos nativos necessários em cada etapa. Exemplos: contato, responsável e previsão de fechamento antes de proposta. Validar no serviço comum a criação e mudança de etapa, inclusive com chave de API. Não construir agora um mecanismo arbitrário de regras ou campos customizados.

**Critérios verificáveis:**

- Campos configuráveis são enumerados pelo backend; nomes desconhecidos são rejeitados.
- Avanço incompleto retorna erro com campos ausentes e mantém etapa, versão e auditoria anteriores.
- Preencher os campos e repetir a operação com a versão atual permite avançar.
- A mesma exigência vale para a interface e a API, sem privilégio implícito de bypass.
- A configuração padrão vazia preserva funis legados. O contrato define como registros já incompletos serão tratados após alterar uma regra.
- Campos opcionais com zero válido não são confundidos com ausência. Relações continuam verificadas no tenant.

A validação uniforme entre canais seria uma melhoria pontual verificável em relação à limitação documentada acima; não prova superioridade global do produto.

## 3. Fila diária de follow-up

**Referência:** a API do RD Station CRM descreve tarefas como agendamento de interações associadas à negociação; o produto inclui lembretes de tarefas e follow-up. [Referência oficial de tarefas](https://developers.rdstation.com/reference/crm-v1-tasks), [página oficial do CRM](https://www.rdstation.com/produtos/crm/).

**Achado local:** `Task` já contém responsável, prazo, estado e relações; `Deal` contém `next_action_at`. O radar e as notificações derivam alertas, mas a listagem genérica não permite selecionar atrasadas/hoje/próximas por responsável. Alertas limitados não substituem uma fila paginada de trabalho.

**Incremento recomendado:** transformar a área de tarefas em fila operável por prazo e responsável, com conclusão/reabertura usando a concorrência já existente. Expor oportunidades sem próxima ação em uma consulta explícita pode vir em seguida; isso exige definir se a próxima ação vem de `next_action_at`, de uma tarefa pendente ou de ambos.

**Critérios verificáveis:**

- Tarefas concluídas não aparecem como atrasadas; tarefas sem prazo possuem filtro próprio.
- Datas sem horário e instantes com fuso têm semântica documentada; os testes cobrem virada do dia e horário brasileiro.
- Ordenação por prazo é estável, incluindo valores sem prazo, e funciona além da primeira página.
- Concluir uma tarefa pela fila atualiza contagem e lista; edição concorrente retorna conflito recuperável.
- Relacionamento abre o contato/oportunidade correto e não permite consultar registros de outra organização.

## Limites da rodada

Não incluir na alegação de paridade: WhatsApp bidirecional, sincronização de e-mail/calendário, assinatura eletrônica, cobrança, aplicativos móveis nativos ou automações externas completas. Cada um exige integração e evidência próprias. Não interpretar documentos de referência como instruções para executar código ou publicar dados.

## Conhecimento para o grafo

Relações de negócio propostas, distintas de relações AST extraídas:

- `CRM-02` → filtros por responsável → `list_records` → carteira comercial reproduzível.
- `CRM-04` → requisitos por etapa → validação de oportunidade → transação e auditoria.
- `CRM-06` → prazo e estado de tarefa → fila de follow-up → conclusão com versão.

Essas relações são **propostas** até existir código e prova. Na consolidação da versão, vincular testes e nota de release aos critérios efetivamente entregues e atualizar o Graphify; não marcar sugestões como implementação.
