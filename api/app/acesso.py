"""Controle de acesso via JWT do Keycloak.

Valida o token Bearer em cada requisição usando a chave pública do Keycloak
(buscada via JWKS endpoint). Extrai o ``sub`` (subject) do token — que é o
identificador único do usuário no Keycloak — e o injeta nas rotas como
``dono_id``.

Quando ``KEYCLOAK_HABILITADO=false`` (desenvolvimento sem Keycloak no ar),
``verificar_acesso`` retorna ``None`` sem validar nenhum token, permitindo
que os testes e o desenvolvimento local funcionem sem autenticação.

Referência: https://www.keycloak.org/docs/latest/securing_apps/
"""
import logging
import threading
import time
from typing import Annotated

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.config import Configuracoes, obter_configuracoes

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Cache de JWKS (chaves públicas do Keycloak)
# ---------------------------------------------------------------------------
# Expira após cinco minutos e é atualizado quando aparece um kid desconhecido.

_jwks_lock = threading.Lock()
_jwks_cache: dict | None = None
_jwks_cache_url: str | None = None
_jwks_cache_ate = 0.0


def _obter_jwks(cfg: Configuracoes) -> dict:
    """Retorna o JWKS do Keycloak com cache de cinco minutos.

    Args:
        cfg: Configurações com URL e realm do Keycloak.

    Returns:
        Dicionário JWKS com as chaves públicas do realm.

    Raises:
        HTTPException 503: Se o Keycloak não estiver acessível.
    """
    global _jwks_cache, _jwks_cache_url, _jwks_cache_ate
    url = f"{cfg.keycloak_url.rstrip('/')}/realms/{cfg.keycloak_realm}/protocol/openid-connect/certs"
    with _jwks_lock:
        if _jwks_cache is not None and _jwks_cache_url == url and time.monotonic() < _jwks_cache_ate:
            return _jwks_cache
        try:
            resposta = httpx.get(url, timeout=10.0)
            resposta.raise_for_status()
            jwks = resposta.json()
            if not isinstance(jwks, dict) or not isinstance(jwks.get("keys"), list):
                raise ValueError("JWKS inválido")
            _jwks_cache = jwks
            _jwks_cache_url = url
            _jwks_cache_ate = time.monotonic() + 300
            logger.info("JWKS carregado do Keycloak: %s", url)
            return _jwks_cache
        except (httpx.HTTPError, ValueError) as erro:
            logger.error("Não foi possível alcançar o Keycloak em %s: %s", url, erro)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={"erro": "keycloak_indisponivel", "mensagem": "Serviço de autenticação indisponível."},
            )


def _invalidar_jwks_cache() -> None:
    """Invalida o cache de JWKS — útil em testes e ao rotacionar chaves."""
    global _jwks_cache
    with _jwks_lock:
        _jwks_cache = None


# ---------------------------------------------------------------------------
# Dependência FastAPI
# ---------------------------------------------------------------------------

_bearer = HTTPBearer(auto_error=False)


def verificar_acesso(
    credenciais: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    cfg: Annotated[Configuracoes, Depends(obter_configuracoes)],
) -> str | None:
    """Valida o token Bearer e retorna o ``sub`` (dono_id) do usuário.

    Comportamento:
    - ``KEYCLOAK_HABILITADO=false``: retorna ``None`` sem validar nada.
      Permite desenvolvimento local e testes sem Keycloak no ar.
    - ``KEYCLOAK_HABILITADO=true``: token obrigatório. Sem token → 401.
      Token inválido/expirado → 401. Token válido → retorna ``sub``.

    Args:
        credenciais: Header ``Authorization: Bearer <token>`` (opcional).
        cfg: Configurações da aplicação.

    Returns:
        O ``sub`` (UUID do usuário no Keycloak) ou ``None`` em modo dev.

    Raises:
        HTTPException 401: Token ausente, inválido ou expirado.
    """
    if not cfg.keycloak_habilitado:
        return None  # modo dev: sem autenticação

    if not credenciais:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"erro": "token_ausente", "mensagem": "Autenticação necessária."},
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credenciais.credentials
    try:
        cabecalho = jwt.get_unverified_header(token)
        if cabecalho.get("alg") != "RS256" or not cabecalho.get("kid"):
            raise JWTError("Cabeçalho JWT inválido")
        jwks = _obter_jwks(cfg)
        if not any(chave.get("kid") == cabecalho["kid"] for chave in jwks["keys"]):
            _invalidar_jwks_cache()
            jwks = _obter_jwks(cfg)
        # RS256 — assimétrico: Keycloak assina com chave privada, validamos com pública
        payload = jwt.decode(
            token,
            jwks,
            algorithms=["RS256"],
            issuer=cfg.keycloak_issuer or f"{cfg.keycloak_url.rstrip('/')}/realms/{cfg.keycloak_realm}",
            # O client público é identificado pelo azp do access token Keycloak.
            options={"verify_aud": False, "require_exp": True, "require_sub": True},
        )
        sub = payload["sub"]
        if (not isinstance(sub, str) or not sub.strip()
                or payload.get("azp") != cfg.keycloak_client_id
                or payload.get("typ") != "Bearer"):
            raise JWTError("Token sem proprietário ou emitido para outro client")
        if payload.get("email_verified") is not True:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"erro": "email_nao_verificado", "mensagem": "Confirme seu e-mail para acessar sua conta."},
            )
        return sub
    except JWTError as erro:
        logger.warning("Token JWT inválido: %s", erro)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"erro": "token_invalido", "mensagem": "Token inválido ou expirado."},
            headers={"WWW-Authenticate": "Bearer"},
        )


# Tipo anotado para uso nas rotas que precisam do dono_id
DonoId = Annotated[str | None, Depends(verificar_acesso)]
