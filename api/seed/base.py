from sqlalchemy.orm import Session

from app.db.catalogo import Categoria, Estado, FaseRoteiro, JanelaTamanho, PerfilClima
from app.db.enums import PerfilCodigo, ReferenciaFase, Tamanho
from seed.util import enum_de, inserir_se_faltar, ler_yaml


def carregar_base(sessao: Session) -> dict[str, int]:
    categorias = ler_yaml("categorias.yaml")

    fases = [
        {**f, "referencia": enum_de(ReferenciaFase, f["referencia"], f"fase '{f['codigo']}'")}
        for f in ler_yaml("fases.yaml")
    ]
    perfis = [
        {**p, "codigo": enum_de(PerfilCodigo, p["codigo"], "perfil")}
        for p in ler_yaml("perfis.yaml")
    ]
    janelas = [
        {**j, "tamanho": enum_de(Tamanho, j["tamanho"], "janela")}
        for j in ler_yaml("janelas.yaml")
    ]
    estados = [
        {**e, "perfil_padrao": enum_de(PerfilCodigo, e["perfil_padrao"], f"estado {e['uf']}")}
        for e in ler_yaml("estados.yaml")
    ]

    return {
        "categoria": inserir_se_faltar(sessao, Categoria, categorias, ["slug"]),
        "fase_roteiro": inserir_se_faltar(sessao, FaseRoteiro, fases, ["codigo"]),
        "perfil_clima": inserir_se_faltar(sessao, PerfilClima, perfis, ["codigo"]),
        "janela_tamanho": inserir_se_faltar(sessao, JanelaTamanho, janelas, ["tamanho"]),
        "estado": inserir_se_faltar(sessao, Estado, estados, ["uf"]),
    }
