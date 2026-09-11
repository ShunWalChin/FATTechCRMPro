# Integração n8n ↔ FAT Tech CRM

O contrato completo é `apps/api/API.md` e o schema executável é `/api/openapi.json`.
Não há vínculo obrigatório com uma instância n8n específica. O CRM guarda as transações
e a outbox em PostgreSQL; o n8n é consumidor e produtor autorizado de eventos.

## n8n → CRM: operação de negócio

1. No CRM, um proprietário cria uma chave com escopos mínimos (por exemplo,
   `contacts:read` e `contacts:write`). Guardar em credencial **HTTP Header Auth** do n8n,
   header `Authorization`, valor `Bearer <chave>`. Nunca colocar a chave no JSON do workflow.
2. Node **HTTP Request**: método POST, URL `https://DOMINIO/api/v1/contacts`,
   authentication Generic Credential Type → Header Auth, body JSON com `name`, `email`,
   `source: n8n`, `consent: false` (alterar só com evidência de consentimento).
3. Timeout 10s, retornar status e body. POST de cadastro não deve ser repetido cegamente:
   consultar o registro e usar PATCH com versão quando houver uma chave de negócio conhecida.

## n8n → CRM: evento idempotente

`POST /api/v1/webhooks/n8n` requer chave de API `webhooks:write`, chave idempotente estável,
timestamp Unix em segundos e assinatura HMAC SHA-256. A mensagem assinada é exatamente
`timestamp + '.' + bytes_do_corpo`. O corpo enviado deve ser o mesmo texto assinado.

```json
{
  "event_type": "external.lead.qualified",
  "payload": {"external_id": "lead-123"},
  "trace_id": "journey-123",
  "hops": 0
}
```

Headers: `Idempotency-Key: journey-123-qualified`, `X-Fattech-Timestamp`,
`X-Fattech-Signature: sha256=<hex>`, `Authorization: Bearer <chave>`,
`Content-Type: application/json`. A janela de replay é ±300 segundos; `hops > 5` é recusado.
Mesmo id+corpo retorna o recibo anterior. Mesmo id+outro corpo retorna 409.

Receber 202 confirma **persistência do evento**, não execução de qualquer comando contido no payload.
Não existe execução de código arbitrário enviado por webhook.

## CRM → n8n: outbox durável

Configurar no ambiente privado `FATTECH_N8N_OUTBOUND_URL` (HTTPS público) e
`FATTECH_N8N_OUTBOUND_TOKEN` (credencial de Header Auth no Webhook receptor).
Sem URL, o worker conserva os eventos pendentes e não simula entrega.

O receptor deve persistir o id de evento antes de efeitos externos e deduplicar repetições.
Entrega é **pelo menos uma vez**: falha após o receptor executar e antes de o worker confirmar
pode repetir a chamada. O worker possui claim persistido, lease, retry limitado e dead letter.
Não conectar automaticamente essa outbox a mensagens ou pagamentos sem idempotência no receptor.

## Matriz de validação

| Entrada/falha | Comportamento esperado |
|---|---|
| Sem API key / chave revogada | 401 |
| Escopo insuficiente | 403 |
| HMAC incorreto / timestamp vencido | 401 |
| JSON inválido / hops excedidos | 422 |
| Evento válido | 202 e outbox persistida |
| Mesmo id e corpo | Recibo original; sem novo evento |
| Mesmo id e corpo diferente | 409 |
| Provider ausente | Evento pending; nenhum envio |
| Falha transitória | Retry limitado com atraso |
| Tentativas esgotadas | Dead letter; reprocessamento explícito |

Workflow importável deve ser gerado após conhecer a versão e o export nativo da instância n8n.
Este documento é um contrato de configuração, não um workflow afirmado como executado.

Referências primárias consultadas: [HTTP Request](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.httprequest/),
[credenciais HTTP](https://docs.n8n.io/integrations/builtin/credentials/httprequest/).
