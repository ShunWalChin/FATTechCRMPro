# evals/ptbr — portão de promoção de modelo

**Regra:** nenhum modelo assume um papel (Marvin, SDR, Conteúdo…) sem passar aqui com
**média ≥ 4,0 e zero caso crítico 🔒 abaixo de 4.** O resultado vai para o PR que troca o modelo.

```bash
cd evals/ptbr
# rodada barata (só regex), sem juiz
node run.mjs --model openrouter:nvidia/nemotron-3.5-lightning --papel sdr

# rodada completa, com juiz
node run.mjs \
  --model openrouter:nvidia/nemotron-3-super-120b-a12b \
  --model openrouter:nvidia/nemotron-3.5-lightning \
  --model ollama:nemotron-3-nano:4b \
  --model openrouter:anthropic/claude-sonnet-4.6 \
  --judge openrouter:anthropic/claude-sonnet-4.6 \
  --out resultados/$(date +%F).md
```

- 12 casos sintéticos, 6 papéis, 3 críticos (injeção, autoridade falsa, número inventado).
- Casos são **sintéticos**: dado real de cliente nunca entra aqui. Por isso o provedor `nvidia:`
  (API trial gratuita, que proíbe dado pessoal e produção) pode ser usado **só neste harness**.
- Saída com código 1 quando algum modelo reprova — dá para usar como gate de CI.
- Novo incidente em produção vira caso novo aqui (regressão nunca volta calada).
