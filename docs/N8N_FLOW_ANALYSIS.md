# Análise do fluxo n8n recebido

## Visão geral

O JSON representa um atendente de WhatsApp orientado a conversa, usando um webhook de uma instância Evolution API, Redis para bloqueio e buffer, memória Redis do LangChain, OpenAI para classificação/agente e Supabase para persistência. O fluxo tenta agrupar mensagens rápidas, identificar a intenção, executar uma mentoria com perguntas de qualificação, pedir ajuda humana quando necessário e enviar a resposta em partes.

O desenho é um bom protótipo de agente, mas ainda não é um workflow de produção do S.Y.N.A.P.S.E. porque o webhook carrega credenciais no payload, o envio é feito diretamente para a Evolution API, não existe uma transação de conversa no CRM, não há idempotência persistente nem janela/consentimento de canal, e o bloqueio de 15 minutos não é uma política de automação comercial.

## Fluxo completo

### 1. Entrada e roteamento

`Webhook` recebe o evento. `verifica remoteJid` decide se o evento possui um destinatário válido. `Mensagens Ajustadas` normaliza o payload para:

- `remotejid`: identificador do contato no WhatsApp;
- `data`: data do evento;
- `type`: texto, áudio, imagem ou documento;
- `content_id`: ID da mensagem do provedor;
- `fromMe`: mensagem enviada pela empresa ou recebida;
- `device`: origem do evento;
- `content`: texto ou transcrição;
- `quote` e `quote_id`: contexto de resposta encadeada.

`If` rejeita documentos e chama `No document`, que envia uma resposta fixa. Mensagens de áudio dependem de um campo `speechToText` já produzido antes; este workflow não transcreve o áudio.

### 2. Separação humano/bot

`Switch` divide mensagens `fromMe=true` e `fromMe=false`. Mensagens enviadas pela empresa acionam `Bloqueia Bot por 15 minutos`, gravando `{remoteJid}_block` no Redis com TTL de 900 segundos. Mensagens recebidas consultam esse bloqueio em `Consulta ID do bloqueio` e passam por `Bloqueio Existe?`.

Quando o bloqueio existe, o caminho termina em `No Operation`. Quando não existe, a mensagem segue para o buffer. O objetivo é permitir que um humano assuma temporariamente a conversa.

### 3. Buffer e debounce

`Insert Buffer` coloca cada mensagem em uma lista Redis `{remoteJid}_buffer`. `Get Buffer` lê a lista. `Switch2` compara o timestamp da última mensagem com `$now.minus(5 seconds)`:

- se já passaram cinco segundos, `Delete Buffer` limpa a lista e continua;
- se ainda está chegando mensagem, `Wait` aguarda e volta a ler;
- o caminho de fallback não processa.

`messages` serializa e junta os conteúdos. `Chat Memory Manager1` insere a mensagem na memória; `Chat Memory Manager` lê o histórico; `Historico de Chat` expõe o histórico ao classificador. Isso reduz respostas fragmentadas, mas não garante ordenação ou atomicidade entre duas execuções simultâneas.

### 4. Classificação de intenção

`Text Classifier` classifica o histórico em `mentoria`, `suporte_curso`, `duvidas_sobre_curso`, `implementação` ou fallback `other`. Todas as saídas, no JSON recebido, seguem para `Mentoria`; portanto a classificação atualmente documenta a intenção, mas não seleciona agentes distintos.

### 5. Agente de conversa

`Mentoria` usa um agente conversacional com `OpenAI Chat Model`, memória Redis e `Item List Output Parser`. O prompt orienta o agente a:

- descobrir tamanho da operação, clientes, gestores e problema principal;
- fazer uma pergunta por vez;
- responder “Ajuda Humana” se não souber;
- conduzir para o agendamento de uma call;
- devolver um array JSON de strings, uma afirmação/pergunta por item;
- usar `message_id` e `quote_id` para reações.

O agente também possui a ferramenta `Se auto-bloquear`, que grava o bloqueio Redis após qualificar o lead. `Juiz` classifica a resposta em `Ajuda Humana` ou `normal`.

### 6. Escalonamento humano

Quando `Juiz` retorna `Ajuda Humana`, `Solicita Ajuda ADM` avisa o administrador e `Chat Memory Manager3` registra o pedido. `Avisa que Solicitou Ajuda` comunica o usuário. Quando uma resposta humana chega em uma mensagem citada, `Juiz Resposta Mencionada` reconhece a categoria `Ajuda ADM`; `Responde Usuário (AJuda ADM) 01/02` encaminha a resposta e insere o conteúdo na memória.

Quando a mensagem não é resposta do administrador, o fluxo volta a `Zera FollowUP` e continua a automação. O mecanismo é útil, mas precisa de um estado explícito de handoff no CRM, em vez de inferir o handoff apenas por citação.

### 7. Formatação e envio

`Transforma Output em Array` escolhe o output do agente, `Split Out` divide as partes, `Remove Vazios` elimina strings vazias e `Loop Over Items` envia cada parte sequencialmente. `Resposta` chama `message/sendText/{instance}` na Evolution API, usa `remoteJid`, texto e um atraso calculado pelo tamanho ou duração do áudio. `Aggregate` reúne os resultados e `Redis` marca `{remoteJid}_FollowUp=1`. `Zera FollowUP` limpa a marca quando entra nova mensagem.

## Mapa de responsabilidades

| Responsabilidade | Nós atuais | Destino no S.Y.N.A.P.S.E. |
|---|---|---|
| Receber webhook | Webhook | Channel Gateway + Webhook Inbox |
| Normalizar mensagem | Mensagens Ajustadas | Conversation Normalizer |
| Bloqueio humano | Redis block nodes | `automation_policies` + handoff persistente |
| Debounce | Insert/Get Buffer, Wait | Redis stream + worker idempotente |
| Memória | Chat Memory Manager, Redis Chat Memory | `conversations/messages` + memória de sessão |
| Classificar | Text Classifier | Intent Router versionado |
| Responder | Mentoria, OpenAI | Agent Runtime com tools tipadas |
| Escalar | Juiz, Solicita Ajuda ADM | `agent_approvals` e tarefa humana |
| Enviar | Resposta, Responde Usuário | Outbox + provider adapter |
| Persistir | Supabase/Supabase1 | CRM API, nunca acesso direto do agente |

## Problemas que precisam ser corrigidos antes de produção

1. **Credenciais no evento:** `server_url`, `instance` e `apikey` são lidos do corpo do webhook. O gateway do CRM deve resolver o canal por assinatura autenticada e buscar o segredo no cofre.
2. **Sem assinatura/idempotência:** validar assinatura do provedor e deduplicar por `provider_event_id` antes de qualquer chamada ao modelo.
3. **Envio fora do CRM:** chamadas diretas à Evolution API não criam `message_delivery`, atividade ou auditoria no CRM.
4. **Bloqueio frágil:** `block` por telefone não distingue organização, canal, agente, motivo ou operador; uma chave deve ser `org:channel:contact:automation_lock`.
5. **Condição de corrida:** duas execuções podem ler o mesmo buffer, responder duas vezes ou apagar uma mensagem ainda não processada. Usar lock com token, consumidor único e ack.
6. **Classificador sem roteamento:** cinco categorias chegam ao mesmo agente. Cada intenção precisa de playbook e agente configuráveis.
7. **Memória sem governança:** Redis LangChain não é histórico jurídico nem fonte do CRM. Mensagens devem ser persistidas com retenção, consentimento e tenant.
8. **JSON não validado:** `Item List Output Parser` reduz risco, mas a API deve validar schema, tamanho, linguagem proibida e rodapé obrigatório antes do envio.
9. **Follow-up apenas como flag:** `_FollowUp=1/0` não representa campanha, etapa, próxima ação ou consentimento. Usar `playbook_runs` e `tasks`.
10. **Fallback perigoso:** `No document` e respostas de erro não registram falha nem oferecem handoff; devem criar atividade e motivo.
11. **Fuso e datas:** expressão `plus('3' 'hours')` é frágil e pode estar inválida; usar timestamp do provedor em UTC e converter na apresentação.
12. **Supabase sem contrato visível:** confirmar tabelas, RLS, chaves e operação usada; n8n deve consumir endpoints do CRM com service identity limitada.

## Reengenharia recomendada

1. Um webhook fino valida assinatura, resolve `organization_id/channel_id`, grava o evento idempotente e retorna 2xx.
2. Um worker normaliza a mensagem, encontra/cria contato e conversa, aplica opt-out/janela e publica `conversation.message_received`.
3. Um agregador por conversa aplica debounce de 5 segundos com lock distribuído e ordenação por timestamp.
4. O Intent Router seleciona um playbook: vendas S.Y.N.A.P.S.E., suporte, implantação, humano ou outro.
5. O Agent Runtime recupera conhecimento filtrado, executa apenas as ferramentas autorizadas e retorna um plano estruturado:

```json
{
  "messages": [{"text": "...", "kind": "text"}],
  "actions": [{"type": "create_task", "payload": {}}],
  "handoff": null,
  "confidence": 0.86,
  "knowledge_refs": ["doc:..."],
  "policy_checks": ["consent", "window", "rate_limit"]
}
```

6. O CRM valida o plano, grava atividade/auditoria e põe mensagens em `event_outbox`.
7. O provider adapter envia, atualiza entrega e aplica retries; o workflow nunca afirma sucesso antes do retorno do provedor.
8. O mesmo evento alimenta Kanban, scoring, próxima ação, agenda e métricas.

## Como este fluxo vira o agente S.Y.N.A.P.S.E.

- A pergunta por vez vira uma política de qualificação versionada.
- `Mentoria` vira um agente de vendas configurável por produto, segmento e plano.
- `Se auto-bloquear` vira uma regra de handoff/pausa com duração e motivo visíveis.
- `Juiz` vira guardrail de confiança, com fallback humano real.
- `Solicita Ajuda ADM` vira aprovação/tarefa dentro do CRM.
- `Resposta` vira o adaptador oficial de WhatsApp, sujeito a consentimento, janela e opt-out.
- `FollowUp` vira sequência no Kanban com próxima ação, SLA e cancelamento por resposta.
- Redis continua adequado para debounce e locks curtos; PostgreSQL permanece fonte de verdade.

## Testes obrigatórios

- webhook repetido não duplica mensagem, contato, conversa ou oportunidade;
- eventos de duas organizações nunca compartilham buffer ou memória;
- mensagens rápidas são agrupadas uma única vez e preservam ordem;
- bloqueio humano impede envio automático até expirar ou ser liberado;
- opt-out cancela campanhas e bloqueia novas automações;
- janela inválida retorna rejeição legível, sem chamada ao provedor;
- agente sem evidência faz handoff em vez de inventar;
- tool call duplicada é idempotente;
- falha do WhatsApp aparece como `failed` e permite retry;
- resposta humana retoma a conversa sem duas respostas concorrentes;
- RLS, auditoria e retenção são verificados em dois tenants.
