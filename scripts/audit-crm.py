"""Audit the CRM the way the site is audited: exercise everything, and report the denominator.

The lesson that produced this file is that a check which quietly compares nothing still reports
success. So this one states how many screens, endpoints and resources it actually exercised, and it
fails on the two things that have bitten this project before: a capability that exists in code but is
not mounted, and a screen that answers 200 while its data never loads.

Usage: python scripts/audit-crm.py [--base https://...]
"""
import argparse
import collections
import json
import pathlib
import sys

import httpx

ROOT = pathlib.Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="https://fattechcrmpro.64.181.178.125.nip.io")
    args = parser.parse_args()
    access = json.loads((ROOT / ".local/access.json").read_text(encoding="utf-8"))
    problems: list[str] = []
    totals = collections.Counter()

    sys.path.insert(0, str(ROOT / "apps/api"))
    from fattech.schemas import RESOURCES

    print(f"Auditando o CRM em {args.base}\n")
    with httpx.Client(base_url=args.base, timeout=90, follow_redirects=True) as client:
        health = client.get("/api/health").json()
        print(f"Versao {health['version']} em {health['environment']}\n")

        print("1. Fronteira privada")
        for path in ("/crm", "/crm/contatos", "/crm/equipe", "/crm/configuracoes"):
            landed = client.get(path)
            totals["privadas"] += 1
            if "/login" not in str(landed.url):
                problems.append(f"{path} nao exigiu login")
        for path in ("/api/v1/contacts", "/api/v1/deals", "/api/v1/work-queue", "/api/v1/sales/report"):
            totals["privadas"] += 1
            if client.get(path).status_code != 401:
                problems.append(f"{path} respondeu sem sessao")
        print(f"   {totals['privadas']} telas e rotas recusam acesso anonimo")

        login = client.post("/api/v1/auth/login",
                            json={"email": access["email"], "password": access["password"]},
                            headers={"Origin": args.base})
        if login.status_code != 200:
            print(f"FALHA no login: HTTP {login.status_code}")
            return 1
        client.headers["X-CSRF-Token"] = login.json()["csrf_token"]

        print("\n2. Catalogo da API")
        spec = client.get("/api/openapi.json").json()
        paths = spec["paths"]
        gets = [(p, list(ops)) for p, ops in paths.items() if "get" in ops and "{" not in p]
        print(f"   {len(paths)} caminhos declarados, {len(gets)} consultaveis sem parametro")
        for path, _ in gets:
            totals["endpoints"] += 1
            response = client.get(path)
            if response.status_code >= 500:
                problems.append(f"{path} -> HTTP {response.status_code}")
            elif response.status_code == 404:
                problems.append(f"{path} declarado no catalogo e ausente na aplicacao")
        print(f"   {totals['endpoints']} endpoints exercitados, nenhum 404/5xx esperado")

        print("\n3. Dominios de registro")
        print(f"   {len(RESOURCES)} declarados no schema")
        for kind in sorted(RESOURCES):
            totals["dominios"] += 1
            listing = client.get(f"/api/v1/{kind}?limit=1")
            if listing.status_code != 200:
                problems.append(f"{kind}: listagem HTTP {listing.status_code}")
                continue
            body = listing.json()
            if not isinstance(body.get("items"), list) or not isinstance(body.get("total"), int):
                problems.append(f"{kind}: resposta sem items/total")
        print(f"   {totals['dominios']} dominios listaveis pela API")

        print("\n4. Telas do workspace")
        telas = ["/crm", "/crm/contatos", "/crm/empresas", "/crm/pipeline", "/crm/tarefas",
                 "/crm/relatorios", "/crm/radar", "/crm/funis", "/crm/importar", "/crm/conversas",
                 "/crm/equipe", "/crm/configuracoes", "/crm/integracoes", "/crm/projetos",
                 "/crm/campanhas", "/crm/automacoes", "/crm/ia", "/crm/conhecimento",
                 "/crm/financeiro", "/crm/produtos", "/crm/aprovacoes", "/crm/propostas", "/crm/metas"]
        for tela in telas:
            totals["telas"] += 1
            response = client.get(tela)
            if response.status_code != 200:
                problems.append(f"{tela} -> HTTP {response.status_code}")
        print(f"   {totals['telas']} telas responderam")

        print("\n5. Operacoes de escrita, ida e volta")
        stamp = int(__import__("time").time())
        criados: list[tuple[str, dict]] = []
        contato = client.post("/api/v1/contacts", json={"name": f"Auditoria {stamp}",
                                                        "email": f"auditoria{stamp}@example.com"})
        if contato.status_code != 201:
            problems.append(f"criar contato -> HTTP {contato.status_code}: {contato.text[:120]}")
        else:
            registro = contato.json()
            criados.append(("contacts", registro))
            totals["escritas"] += 1
            edicao = client.patch(f"/api/v1/contacts/{registro['id']}",
                                  json={"version": registro["version"], "notes": "Conferido."})
            totals["escritas"] += 1
            if edicao.status_code != 200:
                problems.append(f"editar contato -> HTTP {edicao.status_code}")
            conflito = client.patch(f"/api/v1/contacts/{registro['id']}",
                                    json={"version": registro["version"], "notes": "Outro."})
            totals["escritas"] += 1
            if conflito.status_code != 409:
                problems.append(f"versao antiga devia dar 409, deu {conflito.status_code}")
            trilha = client.get("/api/v1/audit?limit=5")
            totals["escritas"] += 1
            if trilha.status_code != 200 or not trilha.json().get("items"):
                problems.append("a trilha de auditoria nao registrou a escrita")
        print(f"   {totals['escritas']} operacoes conferidas (criar, editar, conflito, auditoria)")

        print("\n6. Recusa explicita em vez de sucesso simulado")
        # Um rascunho real percorre o caminho inteiro ate a recusa, que e onde a garantia vive:
        # o sistema nao envia e nao finge que enviou.
        conversa = client.post("/api/v1/conversations", json={
            "title": f"Auditoria {stamp}", "channel": "whatsapp", "status": "open"})
        if conversa.status_code != 201:
            problems.append(f"criar conversa -> HTTP {conversa.status_code}: {conversa.text[:100]}")
            rascunho = conversa
        else:
            criados.insert(0, ("conversations", conversa.json()))
            rascunho = client.post("/api/v1/messages", json={
                "conversation_id": conversa.json()["id"], "body": f"Auditoria {stamp}"})
        if rascunho.status_code == 201:
            mensagem = rascunho.json()
            criados.append(("messages", mensagem))
            parecer = client.post(f"/api/v1/messages/{mensagem['id']}/compliance", json={})
            totals["recusas"] += 1
            if parecer.status_code != 200 or "allowed" not in parecer.json():
                problems.append(f"parecer de conformidade -> HTTP {parecer.status_code}")
            # Pedido valido de proposito: uma recusa por campo faltando passaria pelo motivo errado.
            envio = client.post(f"/api/v1/messages/{mensagem['id']}/send",
                                json={"version": mensagem["version"]})
            totals["recusas"] += 1
            if envio.status_code == 200:
                problems.append("o envio respondeu 200: o sistema nao deve simular entrega externa")
            elif envio.status_code not in (409, 422, 503):
                problems.append(f"envio respondeu {envio.status_code}; esperado recusa explicita")
            else:
                motivo = envio.json().get("detail")
                print(f"   envio recusado com HTTP {envio.status_code}: {str(motivo)[:88]}")
        else:
            problems.append(f"criar rascunho de mensagem -> HTTP {rascunho.status_code}: {rascunho.text[:100]}")
        print(f"   {totals['recusas']} verificacao(oes) do caminho de envio externo")

        for kind, registro in reversed(criados):
            atual = client.get(f"/api/v1/{kind}/{registro['id']}").json()
            client.delete(f"/api/v1/{kind}/{registro['id']}?version={atual['version']}")
        client.post("/api/v1/auth/logout")

    print(f"\n{'=' * 64}")
    if problems:
        print(f"{len(problems)} problema(s):")
        for item in problems:
            print(f"   {item}")
        return 1
    print("Nenhum problema: fronteira, catalogo, dominios, telas, escritas e recusas conferem.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
