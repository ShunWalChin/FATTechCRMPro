# Compliance de envio, radar comercial e destino externo — 12/09/2026

Terceira publicação na Oracle. Reescreve no FAT Tech CRM Pro as funções extraídas do WalChat que
codificam regra de negócio não óbvia, e leva junto o trabalho de identidade e relacionamentos que
estava na árvore.

## Este commit carrega trabalho de duas frentes

A árvore continha alterações não commitadas de outra pessoa quando esta rodada começou. Elas passam
na suíte e foram incluídas porque o empacotamento de release exige árvore limpa. O que veio junto:

- Deduplicação de contatos por identificador normalizado, com `pg_advisory_xact_lock` por organização
  e normalização E.164 de telefone brasileiro (`services.py`, `test_contacts.py`).
- Hierarquia de papéis `root / super_admin / admin / member / viewer` com posto numérico e
  `can_manage` (`permissions.py`).
- Limite de memória do Argon2 por processo, via semáforo compartilhado entre hash e verificação
  (`passwords.py`, `test_password_limits.py`).
- Seletores de relação por nome na interface, substituindo o UUID colado à mão
  (`crm-ui.tsx`, `resources.ts`, `relationships.spec.ts`).

A autoria dessas partes não é desta sessão; o registro fica aqui para que a proveniência não se perca.

## O que foi reescrito do WalChat

### Elegibilidade de envio

`apps/api/fattech/compliance.py` é um módulo puro: não importa banco nem rede, recebe o retrato do
contato e devolve decisão determinística com motivo auditável. A ordem dos bloqueios é contrato, não
acaso — opt-out e ausência de inbound precedem conteúdo, cooldown e janelas, de modo que o motivo
registrado é sempre o mesmo diante do mesmo estado.

Dois detalhes vieram junto porque existem por experiência de produção, não por elegância: a
normalização remove caracteres invisíveis antes de comparar com a blocklist, senão um espaço de
largura zero entre letras derrota a lista inteira; e o rodapé de opt-out é contado **antes** do
truncamento, senão a mensagem sai cortada sem a saída obrigatória.

WhatsApp tem motor próprio porque não possui a extensão de atendimento humano do Instagram: fora da
janela de 24 horas só sai template `APPROVED`, e automação exige template que contenha a saída.

`POST /messages/{id}/compliance` devolve a decisão sem enviar, e `POST /messages/{id}/send` aplica
exatamente a mesma decisão — o operador nunca vê um veredito diferente do que o envio aplicaria.

### Trava de modo seguro

`FATTECH_EXTERNAL_SENDS_ENABLED` nasce desarmada. Mesmo quando a avaliação libera, nenhuma mensagem
sai. Isso fecha o GOV-05 antes de existir qualquer conector, que é mais barato do que retroceder depois.

### Destino externo

`apps/api/fattech/outbound.py` concentra a política de saída. A implementação usa `is_global` do
módulo `ipaddress` em vez da tabela manual de octetos do original: além de menor, pega o CGNAT
`100.64/10`, que `is_private` deixa passar. Endereço literal é conferido na carga da configuração;
o worker recusa iniciar contra host que resolva para rede privada ou reservada.

A checagem ficou na partida do worker, e não a cada entrega: resolver DNS por evento adiciona latência
e transformaria uma falha transitória de resolução em dead letter permanente.

### Radar comercial

`classify_risk` classifica em `em_dia`, `em_voo`, `em_risco` e `critico`, comparando o tempo desde a
última atividade com a duração esperada da etapa — agora configurável por etapa em Funis. Uma próxima
ação marcada no futuro segura a oportunidade em voo: quem já agendou o próximo passo não está parado.

`GET /crm/radar` ordena por risco e devolve o sumário por faixa junto da lista, com destaque para as
oportunidades sem próxima ação. A página `/crm/radar` mostra isso à equipe.

### Captação pública deixou de recusar reenvio

A deduplicação de contatos fazia o formulário público responder 409 quando o e-mail já existia. O
WEB-03 pede que o reenvio **não duplique**, não que falhe — e um 409 no formulário também revelaria ao
visitante que o endereço já está no CRM. A recaptação agora enriquece o contato existente e devolve
202 com o mesmo id, preservando a atribuição de primeiro toque e o instante original do consentimento.

## Evidências

| Verificação | Resultado |
|---|---|
| Testes Python | 78 passaram, 2 pulados (PostgreSQL e um marcado no trabalho de terceiros) |
| Testes de navegador | 11 passaram, incluindo relacionamentos e radar |
| TypeScript e build | Limpos; rota `/crm/radar` registrada |
| Módulos puros | `compliance.py` e `outbound.py` não importam banco nem SQLAlchemy |

Os testes novos cobrem precedência do opt-out sobre janela válida, blocklist contra caractere
invisível, rodapé contado no limite, extensão de atendimento humano negada à automação, template
WhatsApp não aprovado e sem saída, desvio de relógio, cooldown, janela de resposta privada, dezesseis
faixas reservadas de IP, política de URL de saída e as quatro faixas de risco.

## Limites honestos

Nenhuma mensagem é enviada: não há adaptador de canal. O que existe agora é a decisão correta antes do
envio, mais uma trava desarmada. Receber `allowed: true` significa que a política permite, não que
algo saiu.

O cofre de credenciais AES-256-GCM **não** foi implementado: exigiria a dependência `cryptography`,
ausente do ambiente, e com ela uma alteração de lockfile com hashes. Como nenhum conector existe para
usá-lo, ficou para a rodada que trouxer o primeiro conector — e continua sendo pré-requisito dele.

Roteamento de atendimento não foi portado porque depende de disponibilidade e capacidade por
integrante, que não existem no modelo de usuário. Portar as funções puras sem esse modelo produziria
código morto.

`last_activity_at` é gravado a cada alteração da oportunidade, inclusive uma renomeação. É a mesma
semântica de `updated_at` e serve ao radar; não é um registro de contato com o cliente.

## Migração 0003

Os campos novos vivem no JSON de `records` e resolvem por default quando ausentes, então o radar
funciona sem migração: `expected_duration_hours` cai em 72 horas e `last_activity_at` recua para o
`updated_at` do registro.

A verificação contra a produção, porém, mostrou um descompasso real: o funil criado pela `0002` é
anterior ao campo, então a resposta de `GET /pipelines` não o trazia, ainda que o radar calculasse
certo pelo fallback. Dados e contrato publicado precisam coincidir, então `0003` grava nas etapas
existentes exatamente a duração que a ausência já produzia — `version` e `updated_at` intactos,
porque normalização não é edição de usuário.

Diferente da `0002`, a `0003` **não** é exigida na inicialização da API: sem ela o sistema se comporta
igual, e exigir a marca só acrescentaria fragilidade de implantação sem ganho de segurança.

A mesma verificação expôs a outra ponta: o campo estava no schema e no radar, mas não no editor de
funis — ou seja, uma configuração que ninguém conseguia configurar. O editor agora tem o prazo por
etapa, ao lado da probabilidade.
