"""Testes para o módulo de controle de acesso.

Verifica que:
1. Em modo dev (KEYCLOAK_HABILITADO=false), verificar_acesso retorna None sem validar token.
2. Todas as rotas de /enxovais dependem de verificar_acesso.
3. Token inválido retorna 401 quando Keycloak está habilitado.
"""
import pytest
from unittest.mock import patch

from app.acesso import verificar_acesso, _invalidar_jwks_cache
from app.config import Configuracoes


def _cfg_keycloak_desabilitado() -> Configuracoes:
    return Configuracoes(
        database_url="postgresql+psycopg://x/y",
        keycloak_habilitado=False,
    )


def _cfg_keycloak_habilitado() -> Configuracoes:
    return Configuracoes(
        database_url="postgresql+psycopg://x/y",
        keycloak_habilitado=True,
        keycloak_url="http://keycloak:8080",
        keycloak_issuer="http://keycloak:8080/realms/enxoval",
        keycloak_realm="enxoval",
    )


def test_verificar_acesso_retorna_none_sem_keycloak():
    """Sem Keycloak habilitado, verificar_acesso retorna None sem validar nada."""
    # Simula injeção FastAPI: credenciais=None, cfg=keycloak desabilitado
    resultado = verificar_acesso(
        credenciais=None,
        cfg=_cfg_keycloak_desabilitado(),
    )
    assert resultado is None


def test_verificar_acesso_retorna_401_sem_token_quando_keycloak_habilitado():
    """Com Keycloak habilitado e sem token, deve retornar 401."""
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        verificar_acesso(
            credenciais=None,
            cfg=_cfg_keycloak_habilitado(),
        )
    assert exc_info.value.status_code == 401


def test_verificar_acesso_retorna_401_com_token_invalido():
    """Token JWT malformado deve retornar 401."""
    from fastapi import HTTPException
    from fastapi.security import HTTPAuthorizationCredentials

    _invalidar_jwks_cache()

    credenciais = HTTPAuthorizationCredentials(scheme="Bearer", credentials="token.invalido.xxx")
    cfg = _cfg_keycloak_habilitado()

    # Mock do JWKS para não precisar do Keycloak no ar
    jwks_mock = {"keys": []}
    with patch("app.acesso._obter_jwks", return_value=jwks_mock):
        with pytest.raises(HTTPException) as exc_info:
            verificar_acesso(credenciais=credenciais, cfg=cfg)
    assert exc_info.value.status_code == 401


def test_rotas_de_enxoval_dependem_de_verificar_acesso():
    """Spec seção 7: todas as rotas /enxovais dependem de acesso.py.

    O ponto único de encaixe do Keycloak garante que nenhuma rota
    seja esquecida quando a validação for ativada em produção.
    """
    from app.rotas import enxovais, exportar, linhas

    for router in (enxovais.router, exportar.router, linhas.router):
        funcoes = {d.dependency for d in router.dependencies}
        assert verificar_acesso in funcoes


@pytest.fixture(scope="module")
def chave_rsa():
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.primitives import serialization
    from jose import jwk

    chave = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    privada = chave.private_bytes(
        serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )
    publica = chave.public_key().public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    jwks = {"keys": [{**jwk.construct(publica, "RS256").to_dict(), "kid": "teste"}]}
    return privada, jwks


@pytest.mark.parametrize("alteracao,valido", [
    ({}, True),
    ({"iss": "http://outro/realms/enxoval"}, False),
    ({"azp": "outro-client"}, False),
    ({"typ": "ID"}, False),
    ({"sub": ""}, False),
    ({"sub": None}, False),
    ({"exp": 1}, False),
    ({"exp": None}, False),
    ({"email_verified": False}, False),
    ({"email_verified": None}, False),
    ({"email_verified": "true"}, False),
])
def test_valida_assinatura_e_claims_do_token(chave_rsa, alteracao, valido):
    import time
    from fastapi import HTTPException
    from fastapi.security import HTTPAuthorizationCredentials
    from jose import jwt

    privada, jwks = chave_rsa
    payload = {"sub": "dono-123", "iss": "http://keycloak:8080/realms/enxoval",
               "azp": "webapp", "typ": "Bearer", "email_verified": True,
               "exp": int(time.time()) + 300, **alteracao}
    payload = {k: v for k, v in payload.items() if v is not None}
    token = jwt.encode(payload, privada, algorithm="RS256", headers={"kid": "teste"})
    credenciais = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    with patch("app.acesso._obter_jwks", return_value=jwks):
        if valido:
            assert verificar_acesso(credenciais, _cfg_keycloak_habilitado()) == "dono-123"
        else:
            with pytest.raises(HTTPException) as erro:
                verificar_acesso(credenciais, _cfg_keycloak_habilitado())
            assert erro.value.status_code == (403 if "email_verified" in alteracao else 401)


def test_jwks_com_erro_http_retorna_503():
    import httpx
    from fastapi import HTTPException
    from app.acesso import _obter_jwks

    _invalidar_jwks_cache()
    resposta = httpx.Response(503, request=httpx.Request("GET", "http://keycloak/certs"))
    with patch("app.acesso.httpx.get", return_value=resposta):
        with pytest.raises(HTTPException) as erro:
            _obter_jwks(_cfg_keycloak_habilitado())
    assert erro.value.status_code == 503


def test_401_preserva_mensagem_e_www_authenticate(cliente):
    from app.config import obter_configuracoes
    cliente.app.dependency_overrides.pop(verificar_acesso)
    cliente.app.dependency_overrides[obter_configuracoes] = _cfg_keycloak_habilitado
    resposta = cliente.get("/api/v1/enxovais")
    assert resposta.status_code == 401
    assert resposta.json()["erro"] == "token_ausente"
    assert resposta.headers["WWW-Authenticate"] == "Bearer"
