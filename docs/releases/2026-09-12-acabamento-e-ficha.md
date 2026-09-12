# Acabamento, ficha do registro e busca global — 12/09/2026

Quinta publicação na Oracle. Reúne duas frentes que correram em paralelo na mesma árvore: a correção
dos defeitos levantados percorrendo o sistema pelo navegador, e a ficha do registro com busca global,
construída pela outra frente de trabalho.

## Como os defeitos foram encontrados

Percorri as vinte telas pelo navegador, sobre a pilha local com banco descartável e dados de
demonstração, executando as ações do dia a dia: entrar, criar contato, tentar duplicar, mover
oportunidade, registrar perda, abrir o radar, tentar enviar mensagem, simular fluxo, gerar chave de
API, revisar equipe e auditoria. Nenhuma senha real foi digitada em formulário e nenhum registro de
produção foi criado pela avaliação.

## Acabamento corrigido

**Concordância em todo o CRM.** O botão concatenava `Novo {singular}`, produzindo "Novo oportunidade",
"Novo automação", "Novo empresa". O artigo agora viaja com o descritor do recurso, que passou a
declarar gênero, e o mesmo vale para "Excluir esta automação". O painel deixou de dizer
"1 tarefas em aberto".

**Auditoria legível.** Mostrava `products.created`, a coluna de recurso vazia e o responsável como
UUID. Agora traz frase em português com concordância — "Criou o produto", "Alterou a automação" — mais
o nome de quem fez e do registro afetado, resolvidos em duas consultas em lote. Uma ação não mapeada
mantém a chave crua em vez de receber texto inventado, e o assunto é omitido quando é o próprio ator,
como num login.

**Escopos derivados da API.** A tela oferecia 22 permissões e a API aceitava 35: `pipelines`,
`invoices`, `products`, `agents`, `approvals` e `dashboard:read` não podiam ser concedidos por
interface alguma. O catálogo agora é servido pelo mesmo conjunto que o endpoint de chaves valida, e um
teste cria uma chave com todos os escopos oferecidos — se divergirem de novo, ele quebra.

**Papel do proprietário.** Aparecia como "Super Admin (legado)" para o dono do sistema, ainda que o
bootstrap continue criando exatamente esse papel para todo tenant novo. Passou a ser "Proprietário".
Renomear `owner` para `super_admin` seria migração de dados e decisão de produto, não correção.

**Cartão do kanban com o cliente.** Mostrava só título, valor e probabilidade. A listagem de
oportunidades passou a trazer `contact_name` e `company_name`, resolvidos em uma consulta extra para a
página retornada — exato em qualquer volume, diferente de mapear no cliente com limite.

**Erro de duplicata com saída.** Dizia que o contato já existia e obrigava a cancelar e procurar à
mão. O conflito agora carrega o id e o nome do registro atingido, e a interface oferece abri-lo.

**Radar apontando para o registro.** O link ia para o pipeline genérico; agora abre a oportunidade.
"Parada há 0h" virou "Sem movimento ainda".

**Traduções e simulação.** Canais e integrações deixaram de aparecer como `whatsapp`, `ai`,
`calendar` e `available`. A simulação devolvia JSON cru num aviso; agora lista os passos, nomeando
cada tipo de nó e destacando os que ficam bloqueados por serem efeito externo.

## Ficha do registro e busca global

Da outra frente, entraram a página de contato e empresa com abas — dados, oportunidades, tarefas,
conversas e histórico —, o registro de atividades ligado ao contato, a busca global e os motivos de
perda configuráveis por funil. Uma oportunidade mantém seu editor no quadro, alcançado a partir da
ficha pelo mesmo link profundo `?abrir=` desta rodada.

## Dois achados do próprio conjunto de testes

**O guarda do literal do funil funcionou.** `loss_reasons` entrou no schema do funil sem entrar em
`DEFAULT_PIPELINE`, que a migração `0002` grava sem validar. O teste de round-trip que existe para isso
quebrou e apontou o campo. O literal recebeu `loss_reasons: []`, que preserva o texto livre como
comportamento atual — oferecer uma lista inicial de motivos seria decisão de produto.

**A suíte de navegador excedia o próprio limite de login.** São dezesseis autenticações contra o mesmo
e-mail, e o limite de produção é dez em cinco minutos; três testes falhavam por 429 disfarçado de
elemento invisível. Os limites viraram configuração, com os valores de produção como padrão e recusa
explícita de valores permissivos quando `env=production`. O harness em loopback os eleva.

## Evidências

| Verificação | Resultado |
|---|---|
| Testes Python | 150 passaram, 4 pulados |
| Testes de navegador | 17 passaram |
| TypeScript e build | Limpos |
| Migração | Nenhuma nova; `loss_reasons` resolve para lista vazia quando ausente |

## Limites honestos

O arrastar-e-soltar do quadro continua usando eventos HTML5, que não funcionam por toque; o seletor de
etapa segue sendo o caminho garantido no celular e por teclado.

Da lista comparativa com CRMs de mercado, permanecem abertos: e-mail integrado, agenda e agendamento,
propostas com itens do catálogo, relatórios configuráveis, campos personalizados, importação CSV,
notificações, metas e mesclagem de duplicados. Nenhum deles é acabamento; todos são escopo próprio.
