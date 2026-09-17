"""Pontuacao de leads por regra configuravel, com a explicacao como produto principal.

A ordem exige que toda qualificacao seja explicavel e auditavel. Um numero sozinho nao e
explicavel: por isso `avaliar` devolve **todos** os criterios, os que somaram e os que nao
somaram, com o valor que cada um leu do contato. Quem discorda do score consegue apontar a
linha exata em que discorda, em vez de discutir com um total.

Nada aqui toca banco nem relogio global: sao funcoes puras sobre dois dicionarios. E o que
permite testar a regra sem montar um tenant, e o que impede a regra de depender de contexto.
"""
from datetime import datetime, timedelta, timezone

TEMPERATURAS = ("frio", "morno", "quente")
LIMITE = (0, 100)


def _texto(valor) -> str:
    if valor is None:
        return ""
    if isinstance(valor, bool):
        return "sim" if valor else "nao"
    if isinstance(valor, (list, tuple)):
        return ", ".join(_texto(item) for item in valor)
    return str(valor).strip()


def _numero(valor):
    try:
        return float(_texto(valor).replace(",", "."))
    except (TypeError, ValueError):
        return None


def ler(contato: dict, caminho: str):
    """Um ponto de profundidade, e so um: `qualification.fit` resolve, `a.b.c` nao existe."""
    alvo, _, folha = caminho.partition(".")
    valor = contato.get(alvo)
    if not folha:
        return valor
    return valor.get(folha) if isinstance(valor, dict) else None


def compara(operador: str, lido, esperado: str) -> bool:
    texto, alvo = _texto(lido).lower(), _texto(esperado).lower()
    if operador == "preenchido":
        return bool(texto)
    if operador == "vazio":
        return not texto
    if operador == "igual":
        return texto == alvo
    if operador == "diferente":
        return texto != alvo
    if operador == "contem":
        return bool(alvo) and alvo in texto
    if operador == "em":
        return texto in {parte.strip() for parte in alvo.split(",") if parte.strip()}
    esquerda, direita = _numero(lido), _numero(esperado)
    if esquerda is None or direita is None:
        # Comparacao numerica com texto nao e falsa nem verdadeira: nao aplicar e a resposta honesta.
        return False
    return {"maior": esquerda > direita, "maior_igual": esquerda >= direita,
            "menor": esquerda < direita, "menor_igual": esquerda <= direita}[operador]


def temperatura(score: int, warm_at: int, hot_at: int) -> str:
    return "quente" if score >= hot_at else "morno" if score >= warm_at else "frio"


def avaliar(regras: dict | None, contato: dict, quando: datetime | None = None) -> dict | None:
    """Sem conjunto de regras ativo devolve None -- e a diferenca entre 'pontuou zero' e 'ninguem pontuou'."""
    if not regras or regras.get("status") != "active":
        return None
    quando = quando or datetime.now(timezone.utc)
    criterios, total = [], 0
    for criterio in regras.get("criteria", []):
        lido = ler(contato, criterio["field"])
        bateu = compara(criterio["operator"], lido, criterio.get("value", ""))
        if bateu:
            total += criterio["points"]
        criterios.append({
            "label": criterio["label"], "field": criterio["field"], "operator": criterio["operator"],
            "expected": criterio.get("value", ""), "read": _texto(lido),
            "points": criterio["points"], "matched": bateu,
        })
    # Limitar aqui, e nao a cada criterio, mantem a soma reproduzivel a partir da propria lista.
    score = max(LIMITE[0], min(LIMITE[1], total))
    return {
        "score": score, "raw": total,
        "temperature": temperatura(score, regras.get("warm_at", 35), regras.get("hot_at", 65)),
        "criteria": criterios, "rules_name": regras.get("name", ""),
        "computed_at": quando.isoformat(),
    }


def prazo_sla(criado_em: datetime, sla_hours: int) -> datetime:
    return criado_em + timedelta(hours=sla_hours)


def sla_estourado(criado_em: datetime, sla_hours: int, respondido_em: datetime | None,
                  agora: datetime) -> bool:
    """Responder dentro do prazo encerra o SLA para sempre; responder depois nao o desfaz."""
    if respondido_em is not None:
        return respondido_em > prazo_sla(criado_em, sla_hours)
    return agora > prazo_sla(criado_em, sla_hours)
