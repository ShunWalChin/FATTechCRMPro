# Desktop GPU — nó de inferência local (hoth-desktop-do-wal)

Ryzen 5600GT · RTX 4060 **8 GB VRAM** · 28 GB RAM · Windows 11 + WSL2 (Debian/Ubuntu).

## Papel no Palantyr v5

O desktop deixa de ser **cérebro** (v2) e vira **nó opcional** do gateway que roda 24/7 no H1.
Quando está ligado, os agentes ganham inferência local e privada pela ferramenta `node_inference`
do OpenClaw. Quando está desligado, **nada para** — só perde o nível T1 de roteamento.

O prompt e a resposta atravessam a conexão autenticada gateway↔nó; o Ollama continua escutando
**só em `127.0.0.1:11434`** do desktop. Nenhuma porta do Ollama é exposta, nem na tailnet.

## Modelo: Nemotron 3 Nano 4B

| Candidato | Tamanho | Cabe em 8 GB VRAM? | Veredito |
|---|---|---|---|
| `nemotron-3-nano:4b` | 2,8 GB | ✅ com folga para contexto | **padrão T1** |
| `nemotron-3-nano:30b` (A3.5B MoE) | 24 GB | ❌ offload pesado para 28 GB de RAM, trava o desktop | descartado |
| `qwen2.5:14b` (legado v4) | ~9 GB | ⚠ estoura VRAM, offload parcial | só fallback PT-BR se o eval reprovar o Nano |

⚠ **Português não está na lista oficial de idiomas do Nemotron 3 Nano** (inglês, alemão, espanhol,
francês, italiano, japonês). O T1 só entra em produção para tarefas PT-BR depois de passar no
harness `evals/ptbr` com nota ≥ 4,0. Até lá, use T1 para classificação, extração e resumo interno,
não para texto que o cliente lê.

## Instalação (WSL Ubuntu)

```bash
# 1. Ollama
curl -fsSL https://ollama.com/install.sh | sh
ollama pull nemotron-3-nano:4b
ollama run nemotron-3-nano:4b "Responda apenas: OK"

# 2. Tailscale (tag de desktop GPU)
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up --advertise-tags=tag:desktop-gpu

# 3. OpenClaw CLI (Node 24) e pareamento como nó
npm install -g openclaw@2026.9.6
openclaw node run \
  --host <h1>.<tailnet>.ts.net --port 8443 --tls \
  --display-name "desktop-gpu" \
  --commands ollama.models,ollama.chat
```

No H1, aprovar o dispositivo e os comandos (uma vez):

```bash
docker compose -f /opt/palantyr/infra/h1-nucleo/openclaw/compose.yml exec openclaw-gateway \
  node dist/index.js devices list          # → devices approve <id>
docker compose -f /opt/palantyr/infra/h1-nucleo/openclaw/compose.yml exec openclaw-gateway \
  node dist/index.js nodes pending         # → nodes approve <id>
```

`--commands ollama.models,ollama.chat` limita o nó a **só** inferência: ele não anuncia câmera,
tela, arquivos nem shell ao gateway. É a diferença entre emprestar a GPU e emprestar a máquina.

## Serviço permanente (systemd no WSL)

```ini
# ~/.config/systemd/user/openclaw-node.service
[Unit]
Description=Palantyr — nó de inferência local
After=network-online.target ollama.service

[Service]
ExecStart=/usr/bin/env openclaw node run --host <h1>.<tailnet>.ts.net --port 8443 --tls --display-name desktop-gpu --commands ollama.models,ollama.chat
Restart=on-failure
RestartSec=15

[Install]
WantedBy=default.target
```

```bash
systemctl --user daemon-reload && systemctl --user enable --now openclaw-node
```

## Ruflo mora aqui

O squad de engenharia (Ruflo + Claude Code) roda neste desktop, no repositório do CRM e no
`palantyr-v5`. Ver `ruflo/README.md`.
