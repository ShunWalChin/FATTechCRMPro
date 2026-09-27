#!/usr/bin/env python3
"""Provisiona o elenco de agentes do Palantyr v5 no FAT Tech CRM Pro.

Para cada agente em agents/roster.json:
  1. cria (ou encontra pelo nome) o registro `kind=agents` — nasce PAUSADO;
  2. emite a identidade do agente (POST /api/v1/agent/identity), que devolve a
     chave UMA vez;
  3. entrega a chave ao Doppler (`doppler secrets set`) ou, sem Doppler, grava em
     arquivo 0600 fora do Git.

Por que exige login de PESSOA: `Principal.admin()` recusa qualquer chave de API
(ver apps/api/fattech/security.py). Agente não provisiona agente — escalada de
privilégio silenciosa fica estruturalmente impossível.

Uso:
  FATTECH_CRM_URL=https://fattechcrmpro.64.181.178.125.nip.io \
  FATTECH_ADMIN_EMAIL=wal@fattech.com.br \
  python3 infra/scripts/provision-crm-agents.py --dry-run
  ... e depois sem --dry-run. A senha é pedida no terminal (getpass), nunca por argumento.

Só stdlib: roda no host sem instalar nada.
"""
from __future__ import annotations

import argparse
import getpass
import http.cookiejar
import json
import os
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ROSTER = ROOT / "agents" / "roster.json"
RECORD_FIELDS = ("name", "squad", "role", "description", "status", "autonomy", "mode", "tools",
                 "triggers", "model", "budget_month_cents", "max_actions_per_hour", "require_approval_for")


class Crm:
    def __init__(self, base_url: str):
        self.base = base_url.rstrip("/")
        self.jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.jar))
        self.csrf = ""

    def call(self, method: str, path: str, body: dict | None = None) -> dict:
        data = json.dumps(body).encode() if body is not None else None
        request = urllib.request.Request(f"{self.base}{path}", data=data, method=method)
        request.add_header("Accept", "application/json")
        if data is not None:
            request.add_header("Content-Type", "application/json")
        if self.csrf and method not in ("GET", "HEAD"):
            request.add_header("X-CSRF-Token", self.csrf)
        try:
            with self.opener.open(request, timeout=20) as response:
                raw = response.read().decode() or "{}"
                return json.loads(raw)
        except urllib.error.HTTPError as error:
            detail = error.read().decode(errors="replace")[:500]
            raise SystemExit(f"CRM {method} {path} → {error.code}: {detail}") from None

    def login(self, email: str, password: str) -> None:
        result = self.call("POST", "/api/v1/auth/login", {"email": email, "password": password})
        self.csrf = result.get("csrf_token", "")
        role = result.get("user", {}).get("role")
        if role not in ("root", "super_admin", "owner", "admin"):
            raise SystemExit(f"Usuário sem papel administrativo (papel: {role}). Provisionar agente exige admin.")


def find_agent(crm: Crm, name: str) -> dict | None:
    listing = crm.call("GET", f"/api/v1/agents?q={urllib.request.quote(name)}&limit=50")
    for item in listing.get("items", []):
        data = item.get("data", item)
        if data.get("name") == name:
            return item
    return None


def deliver_secret(name: str, value: str, doppler_project: str, doppler_config: str, fallback_dir: Path) -> str:
    if shutil.which("doppler"):
        subprocess.run(["doppler", "secrets", "set", name, "--project", doppler_project,
                        "--config", doppler_config, "--silent"],
                       input=value.encode(), check=True, stdout=subprocess.DEVNULL)
        return f"doppler:{doppler_project}/{doppler_config}/{name}"
    fallback_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
    target = fallback_dir / name
    fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as handle:
        handle.write(value)
    return f"arquivo 0600: {target}"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dry-run", action="store_true", help="mostra o que faria, sem escrever nada")
    parser.add_argument("--only", nargs="*", help="provisionar só estes openclaw_id")
    parser.add_argument("--doppler-project", default="palantyr")
    parser.add_argument("--doppler-config", default="prd_h1")
    parser.add_argument("--fallback-dir", default="/etc/palantyr/agent-keys")
    args = parser.parse_args()

    base = os.environ.get("FATTECH_CRM_URL") or sys.exit("Defina FATTECH_CRM_URL")
    email = os.environ.get("FATTECH_ADMIN_EMAIL") or sys.exit("Defina FATTECH_ADMIN_EMAIL")
    roster = json.loads(ROSTER.read_text(encoding="utf-8"))["agents"]
    if args.only:
        roster = [agent for agent in roster if agent["openclaw_id"] in args.only]

    crm = Crm(base)
    crm.login(email, getpass.getpass(f"Senha de {email}: "))
    catalog = {tool["nome"] for tool in crm.call("GET", "/api/v1/agent/tools")["items"]}

    for agent in roster:
        oid = agent["openclaw_id"].upper()
        unknown = sorted(set(agent["tools"]) - catalog)
        if unknown:
            raise SystemExit(f"{agent['name']}: ferramentas fora do catálogo do CRM: {unknown}")
        record = {key: agent[key] for key in RECORD_FIELDS}
        existing = find_agent(crm, agent["name"])
        print(f"\n== {agent['name']} ({agent['openclaw_id']}) — {'existe' if existing else 'novo'}")
        if args.dry_run:
            print(json.dumps(record, ensure_ascii=False, indent=2))
            continue
        agent_id = existing["id"] if existing else crm.call("POST", "/api/v1/agents", record)["id"]
        issued = crm.call("POST", "/api/v1/agent/identity", {"agent_id": agent_id, "tools": agent["tools"]})
        token = issued.get("token") or issued.get("api_key") or issued.get("key")
        if not token:
            raise SystemExit(f"Resposta de identidade sem token para {agent['name']}: chaves {sorted(issued)}")
        where_id = deliver_secret(f"CRM_AGENT_ID_{oid}", agent_id, args.doppler_project, args.doppler_config, Path(args.fallback_dir))
        where_key = deliver_secret(f"CRM_KEY_{oid}", token, args.doppler_project, args.doppler_config, Path(args.fallback_dir))
        print(f"   agent_id → {where_id}")
        print(f"   chave    → {where_key} (prefixo {issued.get('prefix', token[:12])})")
        print(f"   escopos  → {len(issued.get('scopes', []))}")

    print("\nPronto. Os agentes continuam PAUSADOS. Ativar é decisão do Wal, na tela /crm/agente.")


if __name__ == "__main__":
    main()
