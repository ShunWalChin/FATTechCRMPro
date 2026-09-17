"""Campos personalizados por organizacao, validados no servidor.

O esquema do CRM e estrito de proposito: `extra="forbid"` recusa qualquer chave que ninguem
declarou. Campos personalizados nao furam essa regra, eles a estendem -- o valor chega numa
chave separada, `custom`, e e conferido contra as definicoes que a propria organizacao criou.
O que nao tem definicao continua sendo recusado.

Visibilidade e permissao vivem aqui, e nao na tela. Um campo escondido apenas no navegador
continua saindo na resposta da API, e a ordem proibe regra implementada so no frontend.
"""
import re
from datetime import datetime

from fastapi import HTTPException

from .models import Record
from .permissions import ADMIN_ROLES
from .services import scoped

ENTIDADES = ("contacts", "companies", "deals", "projects")
VAZIOS = (None, "", [], {})


def definicoes(db, tenant_id: str, entity: str, *, ativos=True) -> list[dict]:
    campos = [registro.data for registro in db.scalars(scoped(tenant_id, "custom_fields"))
              if registro.data.get("entity") == entity]
    if ativos:
        campos = [campo for campo in campos if campo.get("status") == "active"]
    return sorted(campos, key=lambda campo: (campo.get("position", 0), campo.get("label", "")))


def chave_duplicada(db, tenant_id: str, data: dict, excluindo: str | None = None) -> bool:
    for registro in db.scalars(scoped(tenant_id, "custom_fields")):
        if registro.id == excluindo:
            continue
        if registro.data.get("entity") == data["entity"] and registro.data.get("key") == data["key"]:
            return True
    return False


def _numero(valor, campo):
    try:
        return float(str(valor).replace(",", "."))
    except (TypeError, ValueError):
        raise HTTPException(422, f"{campo['label']}: informe um número") from None


def _valor(campo: dict, bruto):
    """Converte e confere um valor. Devolve o valor normalizado ou levanta 422 com o rotulo."""
    tipo, rotulo, regra = campo["type"], campo["label"], campo.get("validation") or {}
    if tipo == "checkbox":
        if isinstance(bruto, bool):
            return bruto
        raise HTTPException(422, f"{rotulo}: informe verdadeiro ou falso")
    if tipo in ("number", "money"):
        numero = _numero(bruto, campo)
        if regra.get("minimum") is not None and numero < regra["minimum"]:
            raise HTTPException(422, f"{rotulo}: mínimo {regra['minimum']:g}")
        if regra.get("maximum") is not None and numero > regra["maximum"]:
            raise HTTPException(422, f"{rotulo}: máximo {regra['maximum']:g}")
        # Dinheiro vira centavos inteiros pela mesma razao do resto do sistema: float nao soma.
        return round(numero * 100) if tipo == "money" else numero
    if tipo == "multiselect":
        if not isinstance(bruto, list):
            raise HTTPException(422, f"{rotulo}: informe uma lista de opções")
        escolhas = [str(item).strip() for item in bruto if str(item).strip()]
        invalidas = [item for item in escolhas if item not in campo["options"]]
        if invalidas:
            raise HTTPException(422, f"{rotulo}: opção inválida — {invalidas[0]}")
        return escolhas
    texto = str(bruto).strip()
    if tipo == "select" and texto not in campo["options"]:
        raise HTTPException(422, f"{rotulo}: opção inválida")
    if tipo == "date":
        try:
            datetime.fromisoformat(texto)
        except ValueError:
            raise HTTPException(422, f"{rotulo}: data ISO-8601 obrigatória") from None
    if tipo == "email" and ("@" not in texto or texto.startswith("@") or texto.endswith("@")):
        raise HTTPException(422, f"{rotulo}: e-mail inválido")
    if tipo == "url" and not texto.startswith(("http://", "https://")):
        raise HTTPException(422, f"{rotulo}: informe uma URL começando com http:// ou https://")
    limite = regra.get("max_length") or (20000 if tipo == "textarea" else 500)
    if len(texto) > limite:
        raise HTTPException(422, f"{rotulo}: máximo de {limite} caracteres")
    if regra.get("pattern") and not re.fullmatch(regra["pattern"], texto):
        raise HTTPException(422, f"{rotulo}: formato inválido")
    return texto


def aplicar(db, tenant_id: str, kind: str, enviados: dict | None, anteriores: dict | None,
            role: str, *, exigir: bool = True) -> dict:
    """Mescla os valores enviados sobre os que existiam, conferindo definicao, permissao e regra.

    Enviar apenas uma chave altera apenas aquela: um formulario que nao conhece um campo novo
    nao pode apaga-lo sem querer, e um campo que a pessoa nao pode editar nao muda nem mesmo
    quando o valor chega igual ao que ja estava.
    """
    anteriores = dict(anteriores or {})
    if kind not in ENTIDADES or enviados is None:
        return anteriores
    if not isinstance(enviados, dict):
        raise HTTPException(422, "Campos personalizados precisam ser um objeto")
    catalogo = {campo["key"]: campo for campo in definicoes(db, tenant_id, kind)}
    desconhecidas = [chave for chave in enviados if chave not in catalogo]
    if desconhecidas:
        raise HTTPException(422, f"Campo personalizado desconhecido: {desconhecidas[0]}")
    admin = role in ADMIN_ROLES
    resultado = dict(anteriores)
    for chave, bruto in enviados.items():
        campo = catalogo[chave]
        if campo["editable_by"] == "admin" and not admin:
            raise HTTPException(403, f"{campo['label']}: somente administradores podem editar")
        if bruto in VAZIOS:
            if campo.get("required"):
                raise HTTPException(422, f"{campo['label']}: obrigatório")
            resultado.pop(chave, None)
            continue
        resultado[chave] = _valor(campo, bruto)
    faltando = [campo["label"] for chave, campo in catalogo.items()
                if exigir and campo.get("required") and resultado.get(chave) in VAZIOS]
    if faltando:
        raise HTTPException(422, f"Campo obrigatório não preenchido: {faltando[0]}")
    return resultado


def ocultar(db, tenant_id: str, kind: str, corpo: dict, role: str) -> dict:
    """Remove da resposta o que este papel nao pode ver. Roda onde ha principal, nao na serializacao."""
    if kind not in ENTIDADES or role in ADMIN_ROLES:
        return corpo
    restritos = {campo["key"] for campo in definicoes(db, tenant_id, kind, ativos=False)
                 if campo.get("visibility") == "admin"}
    if not restritos:
        return corpo
    # serialize() achata data no topo do corpo; procurar corpo["data"] faria esta funcao nao
    # apagar nada e ainda assim parecer que funciona, que e a pior forma de um controle falhar.
    if not isinstance(corpo.get("custom"), dict):
        return corpo
    return {**corpo, "custom": {chave: valor for chave, valor in corpo["custom"].items()
                                if chave not in restritos}}


def guardar_remocao(db, tenant_id: str, registro: Record):
    """Uma definicao com valores gravados nao some: inativar preserva o que ja foi respondido."""
    campo = registro.data
    if campo.get("entity") not in ENTIDADES:
        return
    em_uso = sum(1 for alvo in db.scalars(scoped(tenant_id, campo["entity"]))
                 if isinstance(alvo.data.get("custom"), dict) and campo["key"] in alvo.data["custom"])
    if em_uso:
        raise HTTPException(409, {"message": f"{campo['label']} já tem valor em {em_uso} registro(s). "
                                             "Marque como inativo em vez de excluir.",
                                  "records": em_uso})
