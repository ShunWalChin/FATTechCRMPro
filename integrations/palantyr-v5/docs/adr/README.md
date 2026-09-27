# Registro de decisões de arquitetura

| ADR | Decisão | Status |
|---|---|---|
| [ADR-001](ADR-001.md) | Dois hosts com papéis fixos: H1 núcleo, H2 borda | aceito |
| [ADR-002](ADR-002.md) | CRM é a camada de restrição; OpenClaw é a camada de intenção | aceito |
| [ADR-003](ADR-003.md) | n8n é braço externo, fora do caminho agente↔CRM | aceito |
| [ADR-004](ADR-004.md) | Modelos Nemotron-first por nível de privacidade | aceito |
| [ADR-005](ADR-005.md) | Ruflo é o squad de engenharia, não o runtime | aceito |
| [ADR-006](ADR-006.md) | Um gateway, seis agentes, uma identidade por agente | aceito |
| [ADR-007](ADR-007.md) | Nenhum agente tem shell; sem docker.sock | aceito |
| [ADR-008](ADR-008.md) | Rede: loopback + tailnet; nada novo na internet | aceito |
| [ADR-009](ADR-009.md) | O agente puxa; o CRM não empurra | aceito |
| [ADR-010](ADR-010.md) | Autonomia sobe por degrau, um agente por vez, por decisão humana | aceito |

Gerenciado pelo plugin `ruflo-adr`: `/adr-review` compara cada PR com as decisões aceitas.
