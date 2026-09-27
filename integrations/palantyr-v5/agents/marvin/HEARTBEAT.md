# HEARTBEAT.md — checklist de cada pulso (de hora em hora, 07h30–21h)

Rode em ordem. **Só escreva ao Wal se algum item disparar escalada (AGENTS.md §8).**
Caso contrário, responda ao heartbeat em silêncio.

1. `crm-marvin__crm_fila` para cada agente do squad → alguma corrida em `planning` há > 2h?
2. `palantyr-probe__probe_verificar` → algum alvo falhou em duas leituras seguidas?
3. `crm.leads.fila` → lead quente sem responsável ou com SLA estourado?
4. Contas com trava (Schellworth & Rodrigues, Silva & Rocha) → lead sem retorno > 24h?
5. `crm-marvin__crm_orcamento` de cada agente → alguém passou de 75% do orçamento do mês?

Disparou algo: mensagem única no formato de escalada. Nada: silêncio.
