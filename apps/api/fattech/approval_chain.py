"""Aprovacao em niveis, compartilhada por propostas e contratos.

A ordem pede aprovacao com multiplos niveis nos dois lugares. Escrever duas vezes daria duas
regras que divergem no primeiro ajuste, entao a cadeia mora aqui e os dois dominios a usam.

Tres regras sustentam o controle, e todas sao do servidor:

1. Os niveis sao decididos em ordem. Aprovar o nivel 2 antes do 1 tornaria o 1 decorativo.
2. Quem decide precisa de patente igual ou maior que a exigida pelo nivel.
3. A mesma pessoa nao decide dois niveis. Sem isso, "dois niveis" e um nivel escrito duas vezes,
   e a segregacao de funcoes que justifica a cadeia deixa de existir.

Uma recusa em qualquer nivel encerra a cadeia: seguir pedindo aprovacao depois de um "nao" e
transformar o "nao" em sugestao.
"""
from fastapi import HTTPException

from .models import now
from .permissions import RANK

PENDENTE, APROVADA, RECUSADA = "pending", "approved", "rejected"


def nova(niveis: list[dict]) -> dict:
    """niveis: [{"level": 1, "role": "admin", "label": "Gerência"}, ...] ja validado pelo schema."""
    ordenados = sorted(niveis, key=lambda nivel: nivel["level"])
    return {"required": ordenados, "decisions": [], "status": PENDENTE if ordenados else APROVADA}


def nivel_corrente(cadeia: dict) -> dict | None:
    decididos = {decisao["level"] for decisao in cadeia.get("decisions", [])}
    return next((nivel for nivel in cadeia.get("required", []) if nivel["level"] not in decididos), None)


def pendencias(cadeia: dict) -> list[dict]:
    decididos = {decisao["level"] for decisao in cadeia.get("decisions", [])}
    return [nivel for nivel in cadeia.get("required", []) if nivel["level"] not in decididos]


def decidir(cadeia: dict, *, level: int, actor_id: str, role: str, decision: str, reason: str = "") -> dict:
    if cadeia.get("status") != PENDENTE:
        raise HTTPException(409, "Esta aprovação já foi concluída")
    alvo = nivel_corrente(cadeia)
    if alvo is None:
        raise HTTPException(409, "Não há nível pendente nesta aprovação")
    if alvo["level"] != level:
        raise HTTPException(409, f"O nível {alvo['level']} ({alvo['label']}) precisa ser decidido antes")
    if RANK.get(role, 0) < RANK.get(alvo["role"], 0):
        raise HTTPException(403, f"O nível {alvo['label']} exige papel {alvo['role']} ou superior")
    if any(decisao["by"] == actor_id for decisao in cadeia["decisions"]):
        # Segregacao de funcoes: dois niveis decididos pela mesma pessoa sao um nivel so.
        raise HTTPException(409, "Quem já decidiu um nível não pode decidir outro desta aprovação")
    registro = {"level": level, "by": actor_id, "role": role, "decision": decision,
                "reason": reason[:2000], "at": now().isoformat(), "label": alvo["label"]}
    decisoes = [*cadeia["decisions"], registro]
    if decision == RECUSADA:
        estado = RECUSADA
    else:
        estado = APROVADA if len(decisoes) == len(cadeia["required"]) else PENDENTE
    return {**cadeia, "decisions": decisoes, "status": estado}


def resumo(cadeia: dict | None) -> dict:
    """O que a tela mostra: quem falta, quem ja decidiu, e se ainda esta aberta."""
    if not cadeia:
        return {"status": APROVADA, "required": 0, "decided": 0, "next": None, "blocking": False}
    faltam = pendencias(cadeia)
    return {"status": cadeia.get("status", PENDENTE), "required": len(cadeia.get("required", [])),
            "decided": len(cadeia.get("decisions", [])),
            "next": faltam[0] if faltam else None,
            "blocking": cadeia.get("status") != APROVADA}
