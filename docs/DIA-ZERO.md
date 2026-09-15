# Dia zero — colocar a equipe da FAT Tech para operar no CRM

Este documento é para ser seguido na ordem, uma vez. Depois dele, o sistema é rotina.

Endereço: **https://fattechcrmpro.64.181.178.125.nip.io**
Site público e workspace vivem no mesmo endereço; `/crm` é privado e exige login.

---

## Antes de convocar a equipe — três decisões que são suas

Estas não são tarefas técnicas pendentes. São escolhas que só o dono da operação faz, e cada uma tem
consequência conhecida.

### 1. Cópia de backup fora do servidor · **bloqueia operação crítica**

Hoje o backup roda todo dia e guarda os dumps **na mesma instância do banco**. Se a instância Oracle
for perdida, o banco e os backups vão juntos.

Enquanto os dados forem de teste, o risco é aceitável. No dia em que a carteira de clientes estiver
dentro, não é. Escolha um destino — R2 da Cloudflare, outro provedor de objeto, ou uma cópia
automática para máquina local — e a configuração é rápida.

### 2. Segundo fator de autenticação

O acesso é por e-mail e senha, com sessões revogáveis e limite de tentativas. Não há segundo fator.
Para uma base com dados de clientes sob LGPD, isso é uma decisão consciente, não um esquecimento:
defina se entra agora ou depois da homologação.

### 3. Chave do n8n

A fila de eventos acumula e reentrega; ninguém a consome porque não há credencial que autentique na
sua instância n8n. Sem isso, o CRM registra tudo e integra nada.

---

## Passo 1 · Acessos da equipe

Entre em **Equipe** e crie uma conta por pessoa. Papéis, do mais amplo ao mais restrito:

| Papel | Para quem | Pode |
|---|---|---|
| Root / Super Admin | Você | Tudo, incluindo gerir administradores |
| Admin | Coordenação comercial | Equipe, integrações, auditoria, metas |
| Integrante | Vendedores | Criar e editar registros da operação |
| Somente leitura | Quem só acompanha | Ler, nunca escrever |

Cada pessoa troca a própria senha no primeiro acesso. Mudança de papel, desativação e reset
administrativo **revogam sessões e chaves** da pessoa na hora.

## Passo 2 · O funil, antes de qualquer oportunidade

Em **Funis**. Já existe o *Funil comercial* com seis etapas. Ajuste para o seu processo real, porque
tudo depois depende disso:

1. **Nomes das etapas** como sua equipe fala, não como um manual fala.
2. **Probabilidade** de cada etapa — é ela que calcula o pipeline ponderado.
3. **Duração esperada** em horas — é contra ela que o Radar decide o que está parado.
4. **Desfecho** de cada etapa: em andamento, ganho ou perdido.
5. **Motivos de perda** padronizados. Com a lista preenchida, o relatório compara perdas por causa;
   sem ela, cada um escreve um texto diferente e nada é comparável.
6. **Campos obrigatórios por etapa** — o que precisa estar preenchido para uma oportunidade avançar.
   Comece pouco: contato antes de Proposta já evita a maior parte do lixo.

## Passo 3 · Base inicial

- **Contatos**: use **Importar**. O CSV é conferido antes de gravar — ele mostra quantas linhas estão
  prontas, quais já existem e quais têm problema, com o número da linha. Nada entra até você confirmar.
- **Produtos e serviços**: cadastre o que você vende com preço. Propostas congelam o preço no momento
  da emissão, então o que estiver aqui é o que sai na proposta.
- **Empresas**: só se você vende para empresa e precisa agrupar contatos.

## Passo 4 · A rotina que faz o CRM funcionar

O sistema só devolve valor se três hábitos existirem. Não são opcionais:

1. **Toda oportunidade tem próxima ação marcada.** É o que tira do Radar e mantém em voo.
2. **Perdeu, registra o motivo.** O sistema exige, e é de onde sai o relatório de perdas.
3. **A fila de Tarefas é aberta todo dia.** Filtro *Vencidas* primeiro, depois *Hoje*.

## Passo 5 · Onde se olha o resultado

- **Radar** — o que parou e há quanto tempo, contra a duração da etapa.
- **Relatórios** — dois recortes diferentes, e a diferença importa:
  - *Criação* responde "das oportunidades que entraram neste período, como estão hoje".
  - *Último fechamento* responde "o que de fato fechou neste período".
  Metas só comparam com fechamento, mês inteiro e mesmo responsável — em qualquer outro recorte a
  tela se recusa a dividir, em vez de mostrar um número que parece atingimento e não é.
- **Metas** — por vendedor e por mês.

---

## O que o sistema faz, e o que ainda não faz

**Faz:** contatos, empresas, funil configurável, quadro por mouse e por toque, radar de risco,
tarefas com fila filtrável, propostas com preço congelado, metas, relatórios por criação e por
fechamento, importação conferida, avisos derivados, trilha de auditoria completa, papéis e permissões,
chaves de API com escopo, isolamento por organização no banco.

**Não faz, e não finge fazer:** WhatsApp e Instagram bidirecionais, e-mail integrado, agenda e
agendamento, campos personalizados, mesclagem de duplicatas, segundo fator. Os endpoints de envio
**recusam com erro explícito** em vez de simular entrega — se você mandar enviar, o sistema diz por que
não pode.

**O formulário do site não alimenta o CRM.** O site da FAT Tech envia o contato para o WhatsApp, como
sempre enviou. Lead do site chega como mensagem e é cadastrado por uma pessoa. O endpoint de captura
existe e está testado; ligá-lo ao site é decisão de produto.

---

## Como saber que está tudo de pé

Três comandos, qualquer dia:

```bash
python scripts/audit-site.py    # site: páginas, CSS e JS embutidos, assets, links, URLs antigas
python scripts/audit-crm.py     # CRM: fronteira privada, catálogo, domínios, telas, escrita, recusas
python scripts/verify-site-fidelity.py --base https://fattechcrmpro.64.181.178.125.nip.io
```

Cada um informa **quantas coisas comparou**, não só se passou. Um verificador que compara nada também
diz "nenhum problema"; é por isso que o denominador aparece.

## Se algo der errado

- **Backup do dia**: `/var/backups/fattechcrmpro/`, um por dia, com SHA-256 ao lado.
- **Restaurar**: `sudo bash infra/verify-backup.sh <arquivo.dump>` confere o hash antes de qualquer
  coisa.
- **Voltar uma versão**: `infra/install-release.sh` com o pacote anterior. A instalação faz backup
  antes de tocar em qualquer arquivo.
- **Registro do que mudou**: cada publicação tem sua nota em `docs/releases/`, com evidências.
