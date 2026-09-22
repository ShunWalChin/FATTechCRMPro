# FAT Tech Posiciona — a vertente dentro do CRM

Dois materiais entraram no projeto e foram tratados de formas diferentes, porque são coisas
diferentes.

| Material | Onde está | O que virou sistema |
|---|---|---|
| `FAT_Tech_Posiciona_Entregaveis.zip` — página da vertente, kit de 330 pautas, planilha de produção | `docs/sources/` (original), `docs/knowledge/data/` (extraído), `apps/web/public/posiciona.html` (publicado) | Três domínios novos no CRM, apuração mensal e faixa de preço no catálogo |
| `Manual_Execucao_v4.docx` — runbook da infraestrutura Palantyr v4 | `docs/sources/`, `docs/palantyr/MANUAL_EXECUCAO_V4.md` | A cadeia de integridade da trilha de auditoria (passo F1-03), com duas correções |

O manual **não descreve este sistema**. Ele descreve a infraestrutura Palantyr — n8n, Evolution API,
Doppler, Ollama, MCP Gateway — que roda em outro host e atende a operação de tráfego da agência.
Ele foi guardado inteiro porque é a documentação da operação, e dele foi trazido o que o CRM
consegue cumprir e verificar.

## O que o material vende, e o que o sistema passou a fazer

A planilha de produção já escreve o que vai ao ar e quando. O que ela não responde é a pergunta
que paga a conta: **entregamos o que o contrato diz?** A frequência contratada mora na aba de
clientes, o publicado mora na grade semanal, e ninguém cruza as duas todo mês, por conta. Agora é
uma consulta: `GET /api/v1/content/indicadores?mes=AAAA-MM`.

Três domínios, com persistência, versão, RLS, trilha e permissão como qualquer outro do CRM:

- **`content_accounts`** — as contas sob gestão, com a frequência do contrato. Frequência zero
  desliga a cobrança em vez de acusar déficit de zero. "Sem frequência contratada" e "contratou
  zero" são estados diferentes; tratá-los igual acusaria toda conta de vitrine de inadimplência.
- **`content_ideas`** — o banco de pautas. Uma pauta só é marcada como usada pela peça que a
  **publica**; cancelar a peça devolve a pauta ao banco. A planilha marcava "Usado? S" na escolha,
  então uma peça abandonada levava a ideia junto.
- **`content_posts`** — o calendário. `publicado` exige `published_at` e `agendado` exige
  `scheduled_at`, recusados na escrita: uma peça publicada sem data não entra em apuração nenhuma,
  e a apuração nunca precisa adivinhar a que mês ela pertence.

O catálogo ganhou `price_max_cents` e `setup_cents` porque serviço se vende em faixa negociada com
implantação à parte — até o próprio site publica setup separado do mensal. Guardar só o piso fazia
toda proposta nascer no mínimo da tabela; guardar a média inventaria um preço que ninguém cotou.

## O que foi medido nos materiais

**As 330 pautas cobrem cinco dos seis pilares.** 110 em autoridade, 55 em cada um dos outros
quatro, e **nenhuma em performance** — que é justamente o pilar vendido à Linha 3, a de maior
ticket. A divergência só apareceu porque o importador comparou os pilares do kit com os da página
em vez de assumir que os dois materiais falavam a mesma língua: o kit separa "Autoridade Jurídica"
de "Compliance & Alerta", e a página os vende como um pilar só. É um vazio do material, não do
sistema, e a tela de apuração o mostra em vez de escondê-lo.

**O catálogo tem 15 produtos, não 17.** Cinco linhas de três. O extrator errou duas vezes antes de
acertar, e as duas merecem registro porque erraram em silêncio:

1. O teto da faixa nunca era lido — `R$ 397–497` tem cifrão só no primeiro número, e a expressão
   procurava `R$` antes de cada valor. Todo produto ficou com faixa de um lado só.
2. Ao remover o setup da lista de preços **por valor**, o piso de "R$ 1.200–1.997/mês setup
   R$ 800–1.200" foi apagado: o teto do setup é o piso do produto. O produto ficou custando zero.

**A página tinha um único CTA de conversão, e ele apontava para `href="#"`.** A navegação inteira
desemboca em `#contato`, e `#contato` termina num link morto. Publicada com o CTA ligado ao
WhatsApp +55 35 99849-1017 e com a marca e o rodapé linkando `/index.html` — sem isso a página
ficava órfã do site que a hospeda. As três correções estão declaradas em `docs/site-patches.json`
sob `adicionados`.

## O que veio do manual Palantyr

O passo **F1-03** do manual monta uma `audit_log` com hash encadeado e gatilhos de append-only.
O CRM já revogava `UPDATE` e `DELETE` da role da aplicação, que é a metade fácil: isso impede a
aplicação de alterar a trilha e não impede restore parcial, superusuário do banco, dump editado
nem `DELETE` rodado por fora. Nenhum desses deixa marca.

A cadeia não torna a alteração impossível — torna **detectável**, que é o que uma auditoria
externa pede. `GET /api/v1/audit/verify` percorre os elos e devolve o veredito com o denominador:
quantas linhas conferiu, de quantas existem, e onde a numeração saltou.

Duas diferenças em relação ao manual, ambas por concorrência e por armazenamento:

1. **A numeração é serializada por organização.** O gatilho do manual lê o último elo com
   `ORDER BY id DESC LIMIT 1` sem travar nada: duas requisições simultâneas do mesmo cliente leem
   a mesma cauda e a cadeia bifurca em silêncio, fazendo a verificação acusar problema num banco
   intacto. Aqui há trava consultiva por organização e índice único em `(tenant_id, seq)`, que
   transforma a bifurcação restante em erro de gravação.
2. **A cadeia é por organização, não global.** Uma cadeia única acoplaria clientes: a verificação
   de um dependeria das linhas de outro, que ele não pode ler sob RLS.

E uma lição própria, que custou uma rodada: o selo é calculado sobre a forma que **sobrevive à ida
e volta do banco**. A primeira versão selava o `isoformat()` cru do carimbo de tempo, e toda linha
falhava a reconferência um instante depois de gravada — o SQLite perde o fuso e o Postgres o
devolve reescrito. Um controle que acusa adulteração num banco intacto é pior que nenhum: ele
grita sempre, e quem confere aprende a ignorá-lo.

## O que a migração 0007 faz, e o que ela não prova

Ela numera e sela a trilha existente sem alterar o conteúdo de uma linha sequer — o teste
`test_a_migracao_sela_uma_trilha_que_nasceu_sem_cadeia` compara as ações antes e depois.

O que ela **não** faz: provar nada sobre o passado. O selo é calculado sobre o que já está
gravado, então uma linha adulterada antes desta migração será selada adulterada, e a cadeia não
tem como saber. A garantia começa aqui, e dizer o contrário seria vender prova retroativa.

## O que continua fora

- As 330 pautas não são semeadas automaticamente: entram por
  `POST /api/v1/content/pautas/importar`, com prévia antes da confirmação.
- Os 15 produtos do catálogo estão em `docs/knowledge/data/posiciona-catalogo.json` e **ainda não
  têm importador** — entram pela tela de Produtos, um a um, até que alguém precise do contrário.
- A página `posiciona.html` está no repositório e **não está publicada em produção**: o site no ar
  continua sendo o build anterior.
