# SYNAPSE — próximos upgrades para a versão 0.8

Data da proposta: 30/09/2026. Base publicada: `b5bcb51`, versão 0.7.0.

## Objetivo e ponto de partida

A entrega alvo é **uma organização operando um piloto real de atendimento pelo WhatsApp
com IA, controle humano e rastreabilidade**, com passagem consistente de vendas para entrega.
SYNAPSE é a plataforma; CRM, ERP, Comunicação e Inteligência têm responsabilidades próprias.
O objetivo não é renomear telas nem declarar paridade com o mercado por quantidade de menus.

A base já possui contatos, oportunidades, propostas, contratos, projetos, catálogo,
financeiro interno, conversas, campos personalizados, importação e deduplicação. A infraestrutura
de IA inclui identidades, ferramentas com escopo, gate de autorização, eventos, execuções,
leases e recuperação de execuções presas (`agent_dispatch.reciclar_presas`). O dispatcher
`messages.send` e a trava de envio externo existem. O recebimento do Instagram já possui
caminho para contato/conversa/mensagem; não deve ser reconstruído como se fosse inexistente.

O fechamento do deploy confirmou que envios externos estão desligados e n8n não está
configurado. Isso separa implementação disponível de uma operação externa homologada.
O runtime OpenClaw não está demonstrado como provisionado e operacional. Há gatilhos de
agentes ainda não publicados para uso operacional. Agenda/Google e assinaturas com
entitlements são lacunas da próxima engenharia.

Referências: [modelo da plataforma](SYNAPSE_PLATFORM_MODEL.md) e
[relatório de produção](releases/2026-09-30-synapse-platform.md).

## Ordem de entrega

| Ordem | Entrega | Responsáveis | Dependência |
| --- | --- | --- | --- |
| 1 | WhatsApp oficial operacional por organização | Comunicação, backend e infraestrutura | Conta/provedor oficial e credenciais válidas |
| 2 | Executor real de IA e supervisão | Inteligência, backend e segurança | 1; runtime/modelo e credenciais |
| 3 | Jornada CRM → ERP consistente | CRM, ERP e backend | Reusar catálogo e contratos existentes |
| 4 | Agenda interna e sincronização Google | Produto, frontend e backend | Autorização OAuth por usuário |
| 5 | Venda modular e ativação de organizações | Plataforma, comercial e backend | Modelo comercial validado e 3 |
| 6 | Segurança e observabilidade operacionais | Infraestrutura, backend e QA | Acompanha 1–5; requisito para ampliar o piloto |
| 7 | Homologação e promoção da 0.8 | QA, produto e engenharia | Critérios anteriores demonstrados |

### 1. WhatsApp: fechar a integração real

Reusar inbox, contatos, identificação da organização, eventos, outbox, dispatcher e regras
de envio. Confirmar quais adaptadores existentes atendem à API oficial; completar o percurso
faltante, sem um segundo armazenamento de mensagens.

- Receber webhook autenticado e resolver a organização pela conta do provedor.
- Deduplicar o evento pelo identificador externo e criar/vincular contato, conversa e mensagem.
- Registrar entrada, saída e status de entrega com correlação entre evento, conversa e envio.
- Validar elegibilidade imediatamente antes do disparo, inclusive em retries e mensagens agendadas.
- Aplicar opt-out, permissões, política do canal, limites do provedor e templates quando exigidos.
- Separar falha, pendência e entrega confirmada; aceite do provedor não é confirmação de entrega.
- Guardar credenciais por organização em armazenamento protegido; nunca enviá-las ao frontend.

**Aceite:** duas organizações de teste isoladas; evento duplicado não cria segunda mensagem;
um envio autorizado chega ao destinatário de homologação; status recebido aparece na conversa;
envio inelegível é recusado com motivo; timeout e retry não provocam disparo duplicado conhecido.
Em resultado ambíguo, reconciliar com o provedor antes de repetir. Habilitar envio apenas após
evidência, inicialmente para o piloto controlado.

### 2. IA: operar sobre a infraestrutura existente

Provisionar o runtime escolhido, incluindo bridge, rede e modelo, e conectar eventos reais
a agentes habilitados. Não tratar cadastro de agente ou worker saudável como execução comprovada.
Reusar as identidades, ferramentas, aprovações, budgets, leases e reciclagem já presentes.

- Publicar gatilhos e vincular agentes à organização, canal e política de atuação.
- Executar com contexto limitado, conhecimento autorizado e ferramenta com escopo mínimo.
- Usar o gate para cada ação; mensagens externas passam pelo mesmo dispatcher do atendimento.
- Criar sugestões em modo copiloto; autonomia exige política explícita por organização.
- Permitir pausa, transferência para pessoa e bloqueio de novas ações após revogação.
- Registrar modelo, duração, custo, fontes e decisão; não registrar segredos ou raciocínio interno.
- Recuperar falhas usando a lease existente, com idempotência nos efeitos e auditoria da recuperação.

**Aceite:** mensagem real gera execução rastreável; sugestão pode ser aprovada e enviada;
agente não lê dados de outra organização; ferramenta sem escopo é recusada; limite de orçamento
interrompe execução; pausa impede novos envios; interrupção do worker não duplica o efeito.
O piloto só ganha autonomia depois da validação do modo copiloto.

### 3. CRM → ERP: negócio consistente do início à entrega

Fechar o percurso oportunidade → proposta → contrato → projeto → cobrança interna.
Reusar registros e regras existentes; identificar os pontos ainda manuais antes de automatizar.

- Definir transições autorizadas, pré-condições e responsável por cada estado.
- Congelar preços, descontos e itens aceitos; usar cálculos monetários decimais e totais reproduzíveis.
- Exigir versão esperada nas mudanças concorrentes; revisar permissões no backend.
- Tornar a criação derivada idempotente e vinculada à origem: um contrato não cria dois projetos.
- Manter a mesma identidade de cliente e documentar conflitos de cadastro.
- Publicar efeitos via outbox na mesma transação do negócio; consumidores podem repetir eventos.
- Registrar cancelamento, reabertura e reversões sem apagar o histórico.

**Aceite:** cenário completo aprovado com preços reproduzíveis; requisição repetida não duplica
projeto/cobrança; alteração concorrente retorna conflito claro; usuário sem autorização não
fecha contrato nem altera liquidação; relatório reconcilia origem e resultado.
Faturas continuam sendo controle interno, sem promessa de documento fiscal.

### 4. Agenda interna vinculável ao Google

Separar compromissos operacionais do calendário editorial. Criar agenda interna como fonte
da reunião e conexão Google por usuário, com reconciliação explícita dos calendários vinculados.

- Modelar participantes, proprietário, organização, timezone, duração e vínculo ao contato/oportunidade.
- Tratar disponibilidade, conflito, reagendamento, cancelamento e histórico de alterações.
- OAuth com escopos mínimos e tokens protegidos; desconectar deve interromper sincronização.
- Mapear IDs externos e versões para evitar ciclos de atualização e eventos duplicados.
- Usar fila, retries e cursor de sincronização; mostrar falha/reconexão pendente ao usuário.
- Executar notificações e convites pelo canal autorizado; não simular sucesso de uma integração ausente.

**Aceite:** criar, alterar e cancelar reunião reflete no calendário vinculado; mudança externa
é reconciliada; token expirado não perde evento; horário de verão/timezone não desloca reunião;
dois pedidos simultâneos respeitam a política de disponibilidade.

### 5. Comercialização modular da plataforma

Definir planos, módulos, limites, implantação e serviços antes de conectar cobrança pública.
Os produtos existentes devem alimentar propostas e contratação; identidade SYNAPSE e contrato
comercial precisam estar coerentes com o que a organização realmente poderá utilizar.

- Criar assinatura, período de vigência, estado comercial e concessões de módulos por organização.
- Separar **permissão do usuário**, **direito do plano** e **prontidão da integração**.
- Validar direitos no backend e comunicar restrições no frontend, sem depender da ocultação do menu.
- Registrar uso, limites, upgrade/downgrade, suspensão e reativação de forma auditável.
- Criar onboarding com etapas verificáveis: organização, equipe, canais, conhecimento e piloto.
- Se houver checkout, validar webhook, deduplicação, conciliação e tratamento de falha de pagamento.
- Alinhar formulário público, origem do lead e oferta a um fluxo real de captura, sem alterar
  automaticamente a promessa do site ou ativar envio externo por mudança de plano.

**Aceite:** plano contratado concede apenas os módulos comprados; pagamento duplicado não
duplica concessão; downgrade não apaga dados; suspensão respeita a política aprovada;
onboarding mostra a dependência externa que impede ativação. Nenhum pacote é vendido como
plenamente operacional antes da homologação das suas capacidades.

### 6. Confiabilidade, segurança e conhecimento

- MFA para contas administrativas, revogação de sessões e recuperação auditada de acesso.
- Métricas de atraso de fila, erro do provedor, lease expirada, custo de IA e sincronização Google.
- Alertas acionáveis com responsável; dashboard de containers não substitui métricas do negócio.
- Backups com restauração periódica demonstrada; ensaio de rollback compatível com as migrações.
- Testes negativos com duas organizações, perfis distintos e credenciais revogadas.
- Registro único de capacidades com estados: implementada, homologada e ativa em produção.
- Atualizar grafo e documentação com decisão, código, teste, dependência e evidência de produção.
  Não promover automaticamente um nó do grafo a “funcional” por existir endpoint ou tela.

**Aceite:** alerta dispara numa falha de teste e identifica a ação; uma restauração é demonstrada;
MFA tem recuperação controlada; testes de isolamento passam; o registro de capacidades concorda
com a configuração real e distingue integração desativada de defeito de código.

### 7. Promoção da versão

Promover para 0.8 somente após demonstração integrada do piloto, documentação de limites e
validação de recuperação. Enquanto uma etapa estiver incompleta, publicar incrementos compatíveis
da 0.7, sem rotular protótipo como entrega operacional.

O fechamento deve incluir: commit e imagens, migrações aplicadas, resultados de testes,
backup restaurado, smoke autenticado, evidência de conversa real, trilha da ação de IA,
lista de dependências externas pendentes e procedimento de reversão. Registrar quais fluxos
foram apenas testados em homologação e quais foram ativados em produção.

## Primeiro trabalho da próxima rodada

Inventariar os adaptadores e a configuração oficial do WhatsApp, escolher uma organização
piloto e fechar o webhook até a inbox com um evento real. Em paralelo, provisionar e provar
uma execução do runtime de IA com ferramenta de leitura. Só então conectar a ferramenta de
envio, inicialmente mediante aprovação humana. Essa sequência entrega evidência útil antes
de ampliar autonomia ou comercializar o atendimento como produto pronto.
