"""Cofre de credenciais externas: cifra em repouso com a chave fora do banco.

O banco guarda somente texto cifrado. A chave vive em FATTECH_CREDENTIAL_KEY, no
/etc/fattechcrmpro.env do servidor (0600, gerado la), de modo que um dump do banco
sozinho nao devolve token nenhum. O contexto autenticado amarra o texto cifrado ao
par tenant/conta: uma linha copiada para outro tenant nao decifra, falha.
"""
import base64
import hashlib
import os

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

VERSAO = "v1"


class CofreIndisponivel(RuntimeError):
    """Sem chave nao se cifra nem se decifra. Recusar e melhor do que guardar em claro."""


def material_valido(chave: str) -> bytes:
    if not chave:
        raise CofreIndisponivel("FATTECH_CREDENTIAL_KEY ausente")
    try:
        bruto = base64.urlsafe_b64decode(chave.encode())
    except Exception as erro:
        raise CofreIndisponivel("FATTECH_CREDENTIAL_KEY nao e base64 urlsafe") from erro
    if len(bruto) != 32:
        raise CofreIndisponivel("FATTECH_CREDENTIAL_KEY precisa decodificar para 32 bytes")
    return bruto


def gerar_chave() -> str:
    """Material novo para o operador gerar no servidor. Nunca chamado em tempo de requisicao."""
    return base64.urlsafe_b64encode(os.urandom(32)).decode()


def selar(chave: str, segredo: str, contexto: str) -> str:
    nonce = os.urandom(12)
    corpo = AESGCM(material_valido(chave)).encrypt(nonce, segredo.encode(), contexto.encode())
    return f"{VERSAO}.{base64.urlsafe_b64encode(nonce).decode()}.{base64.urlsafe_b64encode(corpo).decode()}"


def abrir(chave: str, selado: str, contexto: str) -> str:
    versao, _, resto = selado.partition(".")
    nonce_b64, _, corpo_b64 = resto.partition(".")
    if versao != VERSAO or not nonce_b64 or not corpo_b64:
        raise CofreIndisponivel("Formato de credencial selada desconhecido")
    try:
        aberto = AESGCM(material_valido(chave)).decrypt(base64.urlsafe_b64decode(nonce_b64),
                                                       base64.urlsafe_b64decode(corpo_b64), contexto.encode())
    except InvalidTag as erro:
        # Chave errada e contexto errado chegam aqui iguais; nao distinguimos qual foi.
        raise CofreIndisponivel("Credencial nao pode ser aberta com esta chave neste contexto") from erro
    return aberto.decode()


def contexto_de(tenant_id: str, account_id: str) -> str:
    return f"instagram:{tenant_id}:{account_id}"


def digital(segredo: str) -> str:
    """Impressao digital curta: prova que o token mudou sem revelar parte alguma dele."""
    return hashlib.sha256(segredo.encode()).hexdigest()[:16]
