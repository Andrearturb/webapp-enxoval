# Etapa 2 — Motor de personalização · Plano de implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implementar o motor de personalização como funções puras e testadas: perfil de clima, cruzamento do mês de nascimento com as janelas de tamanho, fórmula de quantidades, regras do item, marcas por faixa, roteiro com datas reais, alertas de segurança por idade e a montagem do enxoval calculado.

**Architecture:** Pacote `api/app/motor/` sem nenhuma dependência de banco, HTTP ou SQLAlchemy. Entra um `Catalogo` e as `Respostas` (dataclasses imutáveis) e sai um `EnxovalCalculado`. Os testes montam o catálogo lendo os próprios YAML do seed (`api/seed/dados/`), sem banco. A conversão banco → dataclasses é trabalho da Etapa 3 (serviços).

**Tech Stack:** Python 3.12 (dataclasses, `fractions.Fraction`, `datetime`), pytest. Nada novo para instalar.

**Spec:** [`docs/superpowers/specs/2026-10-05-enxoval-inteligente-design.md`](../specs/2026-10-05-enxoval-inteligente-design.md) (seção 4, Motor de personalização) · Conteúdo: [`docs/plano-enxoval.md`](../../plano-enxoval.md) · Etapa anterior: [`2026-10-05-etapa-1-fundacao.md`](2026-10-05-etapa-1-fundacao.md)

## Global Constraints

- O motor **não importa** `sqlalchemy`, `fastapi`, `starlette`, `psycopg` nem `alembic` (nem indiretamente). Só pode importar `app.db.enums`, que é um módulo de enums puros. Um teste (Tarefa 1) falha se isso mudar.
- O "hoje" **sempre** entra como parâmetro. Nenhuma função chama `date.today()` ou `datetime.now()`.
- Contas com frações usam `fractions.Fraction`, nunca `float`. Arredondamento da divisão frio/calor é "meio para cima" (`floor(x + 1/2)`), nunca o `round()` do Python.
- Itens e alertas de segurança nunca saem por orçamento ou preferência: `orcamento` e `primeiro_filho` não podem alterar quais itens entram. Só condições físicas (moradia, carro, clima) tiram um item, e só quando o catálogo traz uma regra `incluir_so_se`.
- Mensagens de erro e avisos em português do Brasil.
- Todos os comandos são rodados na raiz do repositório e funcionam no PowerShell e no Git Bash. Testes: `docker compose run --rm api pytest ...`.
- Branch de trabalho: `etapa-2-motor`, criada a partir da `main`. Todo commit termina com a linha `Co-Authored-By:` que a sessão em execução indicar (o nome do modelo muda, então os exemplos abaixo trazem `<modelo da sessão>` no lugar).

## Desvios deliberados da spec (decididos neste plano)

- `proporcao_frio` recebe `inicio_dias` e `fim_dias` (e não o objeto janela), para servir também ao ano inteiro de itens sem tamanho.
- Itens `so_frio` entram quando há ao menos um dia em **mês frio de verdade** na janela; meses "frescos" (as noites de junho e julho no perfil quente) **não** bastam. É isso que mantém o gorro fora de Salvador, como diz a spec.
- Itens sem tamanhos (ex.: saco de dormir) usam a janela dos 12 meses inteiros (`0` a `365` dias) para decidir o clima.
- Fase "atual" do roteiro = a primeira fase, na ordem, que contém o dia de hoje (a fase "Reta final e parto" cobre até a 42ª semana e se sobrepõe à primeira fase do bebê).
- `resumo` usa "unidades" (soma das quantidades), não "itens". O progresso (% pronto, faltando) é uma função à parte, `progresso`, que recebe as quantidades marcadas, porque o motor de cálculo não conhece o que a família marcou.

## Review Focus

1. **Hoje fora do roteiro** (antes da 1ª fase ou depois dos 12 meses): sem fase atual e sem erro. Teste na Tarefa 3.
2. **Data prevista em 29/fev e fins de mês**: somar meses não pode estourar nem gerar data inexistente (31/jan + 1 mês = 28 ou 29/fev). Teste na Tarefa 3.
3. **Nascimento em dezembro** (a janela atravessa a virada de ano): os meses frios precisam ser contados mês a mês corretamente. Teste na Tarefa 2.
4. **Catálogo incompleto** (item sem janela do tamanho, sem tamanhos nem quantidade, sem marcas, catálogo vazio): o motor não quebra, devolve o que consegue e registra um aviso em português. Teste na Tarefa 5.
5. **`dias_entre_lavagens` fora de 1 a 7**: erro claro, nunca uma quantidade absurda em silêncio. Teste na Tarefa 1.

## Mapa de arquivos

```
api/app/motor/
├─ __init__.py          # vazio
├─ tipos.py             # dataclasses de entrada e saída
├─ quantidades.py       # fator_lavagem, quantidade, dividir_variantes
├─ clima.py             # resolver_perfil, proporcao_frio
├─ calendario.py        # adicionar_meses, montar_roteiro, alertas_por_idade
├─ regras.py            # avaliar_regras, marcas_para
├─ montagem.py          # montar_enxoval
└─ progresso.py         # Marcacao, Progresso, progresso
api/tests/motor/        # sem __init__.py; nomes de arquivo únicos
├─ conftest.py          # catalogo e fazer_respostas (a partir dos YAML do seed)
├─ test_motor_pureza.py
├─ test_motor_quantidades.py
├─ test_motor_clima.py
├─ test_motor_calendario.py
├─ test_motor_regras.py
├─ test_motor_montagem.py
├─ test_motor_progresso.py
└─ test_motor_seguranca.py
```

---

### Task 1: Tipos, quantidades e o teste de pureza

**Files:**
- Create: `api/app/motor/__init__.py`, `api/app/motor/tipos.py`, `api/app/motor/quantidades.py`
- Test: `api/tests/motor/test_motor_pureza.py`, `api/tests/motor/test_motor_quantidades.py`

**Interfaces:**
- Consumes: `app.db.enums` (Etapa 1).
- Produces:
  - `app.motor.tipos`: `PerfilClima(codigo, meses_frios: frozenset[int], meses_frescos: frozenset[int])`, `JanelaTamanho(tamanho, inicio_dias, fim_dias, peso_referencia=None)`, `Fase(codigo, nome, referencia, inicio, fim, texto, ordem)`, `RegraItem(condicao, efeito, valor)`, `MarcaDoItem(nome, faixa, ordem)`, `TamanhoDoItem(tamanho, quantidade_base, fase_codigo=None)`, `ItemCatalogo(...)`, `CategoriaCatalogo(slug, nome, ordem)`, `RegraSegurancaCatalogo(...)`, `Catalogo(categorias, fases, janelas, itens, regras_seguranca)`, `Respostas(...)`, `LinhaCalculada`, `MarcasEscolhidas`, `Ficha`, `FaseCalculada`, `Alerta`, `Resumo`, `EnxovalCalculado`.
  - `app.motor.quantidades`: `fator_lavagem(dias_entre_lavagens: int) -> Fraction`, `quantidade(base: int, fator: Fraction) -> int`, `dividir_variantes(total: int, proporcao_frio: Fraction) -> tuple[int, int]` (frio, calor).

- [ ] **Step 1: Criar a branch e escrever os testes que falham**

Run: `git checkout main && git checkout -b etapa-2-motor`

`api/tests/motor/test_motor_pureza.py`:
```python
import subprocess
import sys
from pathlib import Path

RAIZ_API = Path(__file__).resolve().parents[2]

PROIBIDOS = ("sqlalchemy", "fastapi", "starlette", "psycopg", "alembic")


def test_motor_nao_importa_banco_nem_http():
    """Importa todos os módulos de app.motor num processo limpo e inspeciona sys.modules."""
    codigo = (
        "import importlib, pkgutil, sys\n"
        "import app.motor as pacote\n"
        "for modulo in pkgutil.iter_modules(pacote.__path__):\n"
        "    importlib.import_module('app.motor.' + modulo.name)\n"
        f"proibidos = [n for n in sys.modules if n.split('.')[0] in {PROIBIDOS!r}]\n"
        "assert not proibidos, proibidos\n"
    )
    resultado = subprocess.run(
        [sys.executable, "-c", codigo], capture_output=True, text=True, cwd=RAIZ_API
    )
    assert resultado.returncode == 0, resultado.stderr
```

`api/tests/motor/test_motor_quantidades.py`:
```python
from fractions import Fraction

import pytest

from app.motor.quantidades import dividir_variantes, fator_lavagem, quantidade


@pytest.mark.parametrize(
    ("dias", "esperado"),
    [(1, Fraction(2, 3)), (2, Fraction(1)), (3, Fraction(4, 3)), (4, Fraction(5, 3)), (7, Fraction(8, 3))],
)
def test_fator_lavagem(dias, esperado):
    assert fator_lavagem(dias) == esperado


@pytest.mark.parametrize("dias", [-1, 0, 8, 30])
def test_fator_fora_de_1_a_7_e_recusado(dias):
    with pytest.raises(ValueError, match="entre 1 e 7"):
        fator_lavagem(dias)


@pytest.mark.parametrize(
    ("base", "dias", "esperado"),
    [(8, 2, 8), (8, 3, 11), (8, 1, 6), (0, 3, 0), (1, 1, 1), (6, 4, 10)],
)
def test_quantidade_arredonda_para_cima(base, dias, esperado):
    assert quantidade(base, fator_lavagem(dias)) == esperado


def test_quantidade_base_negativa_e_recusada():
    with pytest.raises(ValueError, match="negativa"):
        quantidade(-1, Fraction(1))


def test_dividir_preserva_o_total_em_toda_a_grade():
    for total in range(0, 31):
        for numerador in range(0, 21):
            frio, calor = dividir_variantes(total, Fraction(numerador, 20))
            assert frio + calor == total
            assert 0 <= frio <= total


@pytest.mark.parametrize(
    ("total", "proporcao", "frio", "calor"),
    [
        (8, Fraction(0), 0, 8),
        (8, Fraction(1), 8, 0),
        (1, Fraction(1, 2), 1, 0),  # meio para cima, não para o par
        (3, Fraction(1, 2), 2, 1),
        (7, Fraction(1, 5), 1, 6),
        (8, Fraction(47, 180), 2, 6),
    ],
)
def test_dividir_variantes_meio_para_cima(total, proporcao, frio, calor):
    assert dividir_variantes(total, proporcao) == (frio, calor)


def test_dividir_recusa_proporcao_fora_de_0_a_1():
    with pytest.raises(ValueError, match="entre 0 e 1"):
        dividir_variantes(5, Fraction(3, 2))


def test_dividir_recusa_total_negativo():
    with pytest.raises(ValueError, match="negativa"):
        dividir_variantes(-1, Fraction(1, 2))
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `docker compose run --rm api pytest tests/motor`
Expected: FAIL (`ModuleNotFoundError: No module named 'app.motor'` no teste de pureza e `app.motor.quantidades` nos demais).

- [ ] **Step 3: Implementar tipos e quantidades**

`api/app/motor/__init__.py`: arquivo vazio.

`api/app/motor/tipos.py`:
```python
"""Tipos do motor: dados simples de entrada e de saída, sem banco nem HTTP.

Os enums vêm de app.db.enums, que é um módulo de enums puros (sem SQLAlchemy).
"""
from dataclasses import dataclass
from datetime import date

from app.db.enums import (
    Condicao,
    Efeito,
    Faixa,
    Moradia,
    PerfilCodigo,
    Prioridade,
    ReferenciaFase,
    Tamanho,
    TemaSeguranca,
    UsoClima,
)

# ---------- Entrada: catálogo ----------


@dataclass(frozen=True)
class PerfilClima:
    codigo: PerfilCodigo
    meses_frios: frozenset[int]
    meses_frescos: frozenset[int]


@dataclass(frozen=True)
class JanelaTamanho:
    tamanho: Tamanho
    inicio_dias: int
    fim_dias: int
    peso_referencia: str | None = None


@dataclass(frozen=True)
class Fase:
    codigo: str
    nome: str
    referencia: ReferenciaFase
    inicio: int
    fim: int
    texto: str
    ordem: int


@dataclass(frozen=True)
class RegraItem:
    condicao: Condicao
    efeito: Efeito
    valor: str | None = None


@dataclass(frozen=True)
class MarcaDoItem:
    nome: str
    faixa: Faixa
    ordem: int


@dataclass(frozen=True)
class TamanhoDoItem:
    tamanho: Tamanho
    quantidade_base: int
    fase_codigo: str | None = None


@dataclass(frozen=True)
class ItemCatalogo:
    slug: str
    nome: str
    categoria_slug: str
    fase_codigo: str
    ordem: int
    para_que_serve: str
    como_escolher: str
    prioridade_base: Prioridade
    idade_inicio_meses: int = 0
    e_seguranca: bool = False
    uso_clima: UsoClima = UsoClima.NEUTRO
    variante_frio: str | None = None
    variante_calor: str | None = None
    escala_lavagem: bool = False
    quantidade: int | None = None
    unidade_texto: str | None = None
    tamanhos: tuple[TamanhoDoItem, ...] = ()
    regras: tuple[RegraItem, ...] = ()
    marcas: tuple[MarcaDoItem, ...] = ()
    regras_seguranca: tuple[str, ...] = ()


@dataclass(frozen=True)
class CategoriaCatalogo:
    slug: str
    nome: str
    ordem: int


@dataclass(frozen=True)
class RegraSegurancaCatalogo:
    codigo: str
    tema: TemaSeguranca
    idade_inicio_meses: int
    idade_fim_meses: int
    texto: str
    base: str
    itens: tuple[str, ...] = ()


@dataclass(frozen=True)
class Catalogo:
    categorias: tuple[CategoriaCatalogo, ...] = ()
    fases: tuple[Fase, ...] = ()
    janelas: tuple[JanelaTamanho, ...] = ()
    itens: tuple[ItemCatalogo, ...] = ()
    regras_seguranca: tuple[RegraSegurancaCatalogo, ...] = ()


# ---------- Entrada: respostas da família ----------


@dataclass(frozen=True)
class Respostas:
    perfil: PerfilClima
    data_prevista: date
    dias_entre_lavagens: int
    moradia: Moradia
    tem_carro: bool
    orcamento: Faixa
    primeiro_filho: bool


# ---------- Saída ----------


@dataclass(frozen=True)
class LinhaCalculada:
    """Uma linha da planilha. `chave` = '<slug>:<tamanho>:<variante>' (ex.: 'body:P:frio')."""

    chave: str
    item_slug: str
    nome: str
    categoria_slug: str
    tamanho: Tamanho | None
    variante: str  # "", "frio" ou "calor"
    rotulo_variante: str | None  # ex.: "manga longa"
    quantidade: int
    unidade_texto: str | None
    prioridade: Prioridade
    fase_codigo: str
    e_seguranca: bool
    escala_lavagem: bool


@dataclass(frozen=True)
class MarcasEscolhidas:
    nomes: tuple[str, ...]
    faixa: Faixa | None
    fallback: bool  # True quando a faixa pedida não tinha marcas e usamos a vizinha


@dataclass(frozen=True)
class Ficha:
    slug: str
    nome: str
    para_que_serve: str
    como_escolher: str
    idade_inicio_meses: int
    marcas: MarcasEscolhidas
    dicas: tuple[str, ...]
    regras_seguranca: tuple[str, ...]


@dataclass(frozen=True)
class FaseCalculada:
    codigo: str
    nome: str
    texto: str
    inicio: date
    fim: date
    atual: bool


@dataclass(frozen=True)
class Alerta:
    codigo: str
    tema: TemaSeguranca
    texto: str
    base: str
    ativo_a_partir: date
    ativo_ate: date
    itens: tuple[str, ...]


@dataclass(frozen=True)
class Resumo:
    dias_sem_lavar: int
    total_unidades: int
    aviso_volume_alto: bool
    destacar_ja_tinha: bool


@dataclass(frozen=True)
class EnxovalCalculado:
    linhas: tuple[LinhaCalculada, ...]
    fichas: tuple[Ficha, ...]
    roteiro: tuple[FaseCalculada, ...]
    alertas: tuple[Alerta, ...]
    resumo: Resumo
    avisos: tuple[str, ...]
```

`api/app/motor/quantidades.py`:
```python
import math
from fractions import Fraction


def fator_lavagem(dias_entre_lavagens: int) -> Fraction:
    """(dias + 1) / 3. As quantidades-base do catálogo são calibradas para lavar a cada 2 dias."""
    if not 1 <= dias_entre_lavagens <= 7:
        raise ValueError(
            f"dias entre lavagens deve ficar entre 1 e 7 (recebido: {dias_entre_lavagens})"
        )
    return Fraction(dias_entre_lavagens + 1, 3)


def quantidade(base: int, fator: Fraction) -> int:
    if base < 0:
        raise ValueError(f"a quantidade base não pode ser negativa (recebido: {base})")
    return math.ceil(base * fator)


def dividir_variantes(total: int, proporcao_frio: Fraction) -> tuple[int, int]:
    """Divide `total` em (frio, calor), sem perder nem criar peças. Meio arredonda para cima."""
    if total < 0:
        raise ValueError(f"a quantidade total não pode ser negativa (recebido: {total})")
    if not 0 <= proporcao_frio <= 1:
        raise ValueError(f"a proporção de frio deve ficar entre 0 e 1 (recebido: {proporcao_frio})")
    frio = math.floor(total * proporcao_frio + Fraction(1, 2))
    return frio, total - frio
```

- [ ] **Step 4: Rodar e ver passar**

Run: `docker compose run --rm api pytest tests/motor`
Expected: todos passam (`1 + 17 = 18 passed`; a contagem exata depende da parametrização, o que importa é `0 failed`).

- [ ] **Step 5: Commit**

```bash
git add api/app/motor api/tests/motor
git commit -m "feat: tipos do motor e funções de quantidade (fator de lavagem, divisão frio/calor)

Co-Authored-By: <modelo da sessão> <noreply@anthropic.com>"
```

---

### Task 2: Perfil de clima e proporção de frio

**Files:**
- Create: `api/app/motor/clima.py`
- Test: `api/tests/motor/test_motor_clima.py`

**Interfaces:**
- Consumes: `PerfilClima` (Task 1), `PerfilCodigo`.
- Produces: `resolver_perfil(excecao_do_municipio: PerfilCodigo | None, padrao_do_estado: PerfilCodigo, correcao: PerfilCodigo | None) -> PerfilCodigo`; `proporcao_frio(data_prevista: date, inicio_dias: int, fim_dias: int, perfil: PerfilClima, incluir_frescos: bool = True) -> Fraction` (0 a 1; dia em mês frio vale 1, em mês fresco vale 1/2, nos demais 0; `fim_dias` é exclusivo).

- [ ] **Step 1: Escrever os testes que falham**

`api/tests/motor/test_motor_clima.py`:
```python
from datetime import date
from fractions import Fraction

import pytest

from app.db.enums import PerfilCodigo
from app.motor.clima import proporcao_frio, resolver_perfil
from app.motor.tipos import PerfilClima

FRIO = PerfilClima(PerfilCodigo.FRIO, frozenset({5, 6, 7, 8, 9}), frozenset())
QUENTE = PerfilClima(PerfilCodigo.QUENTE, frozenset(), frozenset({6, 7}))
JUNHO = date(2027, 6, 15)


def test_resolver_perfil_correcao_vence_excecao_que_vence_estado():
    assert resolver_perfil(PerfilCodigo.FRIO, PerfilCodigo.QUENTE, PerfilCodigo.MODERADO) == PerfilCodigo.MODERADO
    assert resolver_perfil(PerfilCodigo.FRIO, PerfilCodigo.QUENTE, None) == PerfilCodigo.FRIO
    assert resolver_perfil(None, PerfilCodigo.QUENTE, None) == PerfilCodigo.QUENTE


def test_janela_inteira_em_mes_frio_vale_um():
    # 15/jun a 12/set (dias 0 a 89): só meses 6, 7, 8 e 9
    assert proporcao_frio(JUNHO, 0, 90, FRIO) == 1


def test_janela_com_parte_em_mes_frio():
    # 13/set a 11/dez (dias 90 a 179): só 13 a 30/set (18 dias) são frios, de 90
    assert proporcao_frio(JUNHO, 90, 180, FRIO) == Fraction(1, 5)


def test_janela_sem_mes_frio_vale_zero():
    # 12/dez a 10/mar (dias 180 a 269)
    assert proporcao_frio(JUNHO, 180, 270, FRIO) == 0


def test_mes_fresco_vale_metade():
    # 15/jun a 12/set: junho (16 dias) + julho (31 dias) = 47 dias frescos, cada um vale 1/2
    assert proporcao_frio(JUNHO, 0, 90, QUENTE) == Fraction(47, 180)


def test_sem_contar_os_frescos_o_perfil_quente_nunca_tem_frio():
    assert proporcao_frio(JUNHO, 0, 90, QUENTE, incluir_frescos=False) == 0


def test_mes_que_e_frio_e_fresco_conta_como_frio():
    ambos = PerfilClima(PerfilCodigo.MODERADO, frozenset({6}), frozenset({6}))
    assert proporcao_frio(date(2027, 6, 1), 0, 30, ambos) == 1


def test_nascimento_em_dezembro_atravessa_a_virada_de_ano():
    inverno_do_hemisferio_errado = PerfilClima(PerfilCodigo.FRIO, frozenset({12, 1, 2}), frozenset())
    # 20/dez/2027 a 18/mar/2028 (2028 é bissexto): 12 + 31 + 29 = 72 dias frios de 90
    assert proporcao_frio(date(2027, 12, 20), 0, 90, inverno_do_hemisferio_errado) == Fraction(4, 5)


@pytest.mark.parametrize(("inicio", "fim"), [(10, 10), (10, 5)])
def test_janela_vazia_ou_invertida_e_recusada(inicio, fim):
    with pytest.raises(ValueError, match="janela"):
        proporcao_frio(JUNHO, inicio, fim, FRIO)
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `docker compose run --rm api pytest tests/motor/test_motor_clima.py`
Expected: FAIL (`ModuleNotFoundError: No module named 'app.motor.clima'`)

- [ ] **Step 3: Implementar**

`api/app/motor/clima.py`:
```python
from datetime import date, timedelta
from fractions import Fraction

from app.db.enums import PerfilCodigo
from app.motor.tipos import PerfilClima

PONTOS_MES_FRIO = 2  # contamos em meios-dias para manter tudo em números inteiros
PONTOS_MES_FRESCO = 1


def resolver_perfil(
    excecao_do_municipio: PerfilCodigo | None,
    padrao_do_estado: PerfilCodigo,
    correcao: PerfilCodigo | None,
) -> PerfilCodigo:
    """Correção da família > exceção do município > padrão do estado."""
    return correcao or excecao_do_municipio or padrao_do_estado


def proporcao_frio(
    data_prevista: date,
    inicio_dias: int,
    fim_dias: int,
    perfil: PerfilClima,
    incluir_frescos: bool = True,
) -> Fraction:
    """Fração (0 a 1) da janela [inicio_dias, fim_dias) que cai em mês frio.

    Cada dia conta pelo mês em que cai: mês frio vale 1, mês fresco vale 1/2 (se
    `incluir_frescos`) e os demais valem 0. A idade do bebê é contada a partir da data prevista.
    """
    total = fim_dias - inicio_dias
    if total <= 0:
        raise ValueError(f"janela inválida: de {inicio_dias} a {fim_dias} dias")
    pontos = 0
    for dia in range(inicio_dias, fim_dias):
        mes = (data_prevista + timedelta(days=dia)).month
        if mes in perfil.meses_frios:
            pontos += PONTOS_MES_FRIO
        elif incluir_frescos and mes in perfil.meses_frescos:
            pontos += PONTOS_MES_FRESCO
    return Fraction(pontos, PONTOS_MES_FRIO * total)
```

- [ ] **Step 4: Rodar e ver passar**

Run: `docker compose run --rm api pytest tests/motor`
Expected: todos passam, `0 failed`.

- [ ] **Step 5: Commit**

```bash
git add api/app/motor/clima.py api/tests/motor/test_motor_clima.py
git commit -m "feat: perfil de clima e proporção de frio por janela de tamanho

Co-Authored-By: <modelo da sessão> <noreply@anthropic.com>"
```

---

### Task 3: Calendário (roteiro com datas reais e alertas por idade)

**Files:**
- Create: `api/app/motor/calendario.py`, `api/tests/motor/conftest.py`
- Test: `api/tests/motor/test_motor_calendario.py`

**Interfaces:**
- Consumes: `Fase`, `FaseCalculada`, `RegraSegurancaCatalogo`, `Alerta`, `ReferenciaFase` (Task 1). Do seed (só em testes): `seed.util.ler_yaml`.
- Produces: `adicionar_meses(d: date, meses: int) -> date` (fim de mês é ajustado), `intervalo_da_fase(fase: Fase, data_prevista: date) -> tuple[date, date]` (início e fim, ambos inclusivos), `montar_roteiro(fases: Iterable[Fase], data_prevista: date, hoje: date) -> tuple[FaseCalculada, ...]`, `alertas_por_idade(regras: Iterable[RegraSegurancaCatalogo], data_prevista: date) -> tuple[Alerta, ...]`. Fixtures de teste: `catalogo` (sessão), `perfis` (sessão), `fazer_respostas`.

- [ ] **Step 1: Criar as fixtures de teste e os testes que falham**

`api/tests/motor/conftest.py` (monta o `Catalogo` a partir dos YAML do seed; sem banco):
```python
from datetime import date

import pytest

from app.db.enums import (
    Condicao,
    Efeito,
    Faixa,
    Moradia,
    PerfilCodigo,
    Prioridade,
    ReferenciaFase,
    Tamanho,
    TemaSeguranca,
    UsoClima,
)
from app.motor.tipos import (
    Catalogo,
    CategoriaCatalogo,
    Fase,
    ItemCatalogo,
    JanelaTamanho,
    MarcaDoItem,
    PerfilClima,
    RegraItem,
    RegraSegurancaCatalogo,
    Respostas,
    TamanhoDoItem,
)
from seed.util import ler_yaml


@pytest.fixture(scope="session")
def perfis() -> dict[str, PerfilClima]:
    return {
        p["codigo"]: PerfilClima(
            PerfilCodigo(p["codigo"]),
            frozenset(p["meses_frios"]),
            frozenset(p["meses_frescos"]),
        )
        for p in ler_yaml("perfis.yaml")
    }


@pytest.fixture(scope="session")
def catalogo() -> Catalogo:
    faixas = {m["nome"]: Faixa(m["faixa"]) for m in ler_yaml("marcas.yaml")}
    seguranca = ler_yaml("seguranca.yaml")
    codigos_por_item: dict[str, list[str]] = {}
    for regra in seguranca:
        for slug in regra.get("itens", []):
            codigos_por_item.setdefault(slug, []).append(regra["codigo"])

    itens = []
    for ordem, bruto in enumerate(ler_yaml("itens.yaml")["itens"], start=1):
        fases_tamanho = bruto.get("fases_tamanho", {})
        variantes = bruto.get("variantes", {})
        marcas = []
        for posicao, entrada in enumerate(bruto.get("marcas", []), start=1):
            nome, faixa = (
                (entrada, None) if isinstance(entrada, str) else (entrada["nome"], entrada.get("faixa"))
            )
            marcas.append(MarcaDoItem(nome, Faixa(faixa) if faixa else faixas[nome], posicao))
        itens.append(
            ItemCatalogo(
                slug=bruto["slug"],
                nome=bruto["nome"],
                categoria_slug=bruto["categoria"],
                fase_codigo=bruto["fase"],
                ordem=ordem,
                para_que_serve=bruto["para_que_serve"],
                como_escolher=bruto["como_escolher"],
                prioridade_base=Prioridade(bruto["prioridade"]),
                idade_inicio_meses=bruto.get("idade_inicio_meses", 0),
                e_seguranca=bruto.get("seguranca", False),
                uso_clima=UsoClima(bruto.get("uso_clima", "neutro")),
                variante_frio=variantes.get("frio"),
                variante_calor=variantes.get("calor"),
                escala_lavagem=bruto.get("escala_lavagem", False),
                quantidade=bruto.get("quantidade"),
                unidade_texto=bruto.get("unidade"),
                tamanhos=tuple(
                    TamanhoDoItem(Tamanho(t), q, fases_tamanho.get(t))
                    for t, q in bruto.get("tamanhos", {}).items()
                ),
                regras=tuple(
                    RegraItem(Condicao(r["condicao"]), Efeito(r["efeito"]), r.get("valor"))
                    for r in bruto.get("regras", [])
                ),
                marcas=tuple(marcas),
                regras_seguranca=tuple(codigos_por_item.get(bruto["slug"], [])),
            )
        )

    return Catalogo(
        categorias=tuple(
            CategoriaCatalogo(c["slug"], c["nome"], c["ordem"]) for c in ler_yaml("categorias.yaml")
        ),
        fases=tuple(
            Fase(
                f["codigo"], f["nome"], ReferenciaFase(f["referencia"]),
                f["inicio"], f["fim"], f["texto"], f["ordem"],
            )
            for f in ler_yaml("fases.yaml")
        ),
        janelas=tuple(
            JanelaTamanho(
                Tamanho(j["tamanho"]), j["idade_inicio_dias"], j["idade_fim_dias"],
                j["peso_referencia"],
            )
            for j in ler_yaml("janelas.yaml")
        ),
        itens=tuple(itens),
        regras_seguranca=tuple(
            RegraSegurancaCatalogo(
                r["codigo"], TemaSeguranca(r["tema"]), r["idade_inicio_meses"],
                r["idade_fim_meses"], r["texto"], r["base"], tuple(r.get("itens", [])),
            )
            for r in seguranca
        ),
    )


@pytest.fixture
def fazer_respostas(perfis):
    def _fazer(
        perfil="frio",
        data_prevista=date(2027, 6, 15),
        dias=2,
        moradia=Moradia.APARTAMENTO,
        carro=True,
        orcamento=Faixa.INTERMEDIARIO,
        primeiro_filho=True,
    ) -> Respostas:
        return Respostas(
            perfil=perfis[perfil],
            data_prevista=data_prevista,
            dias_entre_lavagens=dias,
            moradia=moradia,
            tem_carro=carro,
            orcamento=orcamento,
            primeiro_filho=primeiro_filho,
        )

    return _fazer
```

`api/tests/motor/test_motor_calendario.py`:
```python
from datetime import date

import pytest

from app.motor.calendario import (
    adicionar_meses,
    alertas_por_idade,
    intervalo_da_fase,
    montar_roteiro,
)

DPP = date(2027, 6, 15)


@pytest.mark.parametrize(
    ("origem", "meses", "esperado"),
    [
        (date(2027, 1, 31), 1, date(2027, 2, 28)),
        (date(2028, 1, 31), 1, date(2028, 2, 29)),  # ano bissexto
        (date(2028, 2, 29), 12, date(2029, 2, 28)),  # 29/fev + 1 ano
        (date(2026, 12, 15), 2, date(2027, 2, 15)),  # virada de ano
        (date(2027, 6, 15), 0, date(2027, 6, 15)),
        (date(2027, 6, 15), 12, date(2028, 6, 15)),
    ],
)
def test_adicionar_meses_ajusta_fim_de_mes(origem, meses, esperado):
    assert adicionar_meses(origem, meses) == esperado


def test_intervalo_de_fase_da_gestacao_conta_a_partir_de_dpp_menos_40_semanas(catalogo):
    fase = next(f for f in catalogo.fases if f.codigo == "gestacao_5_7m")  # semanas 18 a 26

    # início da gestação = 15/jun/2027 - 280 dias = 8/set/2026; semana 18 começa 126 dias depois
    assert intervalo_da_fase(fase, DPP) == (date(2027, 1, 12), date(2027, 3, 15))


def test_intervalo_de_fase_do_bebe_conta_meses_completos_depois_da_dpp(catalogo):
    fase = next(f for f in catalogo.fases if f.codigo == "bebe_0_3m")  # meses 0 a 2

    assert intervalo_da_fase(fase, DPP) == (date(2027, 6, 15), date(2027, 9, 14))


def test_fases_da_gestacao_sao_contiguas(catalogo):
    fases = [f for f in montar_roteiro(catalogo.fases, DPP, date(2027, 2, 1))][:4]

    for anterior, seguinte in zip(fases, fases[1:], strict=False):
        assert (seguinte.inicio - anterior.fim).days == 1


def test_fase_atual_e_a_que_contem_hoje(catalogo):
    roteiro = montar_roteiro(catalogo.fases, DPP, date(2027, 2, 1))

    atuais = [f.codigo for f in roteiro if f.atual]
    assert atuais == ["gestacao_5_7m"]
    assert len(roteiro) == 8


def test_na_sobreposicao_vale_a_primeira_fase_na_ordem(catalogo):
    # 5 dias depois da DPP ainda estamos na "Reta final e parto" (até a 42ª semana)
    roteiro = montar_roteiro(catalogo.fases, DPP, date(2027, 6, 20))

    assert [f.codigo for f in roteiro if f.atual] == ["parto"]


@pytest.mark.parametrize("hoje", [date(2026, 1, 1), date(2030, 1, 1)])
def test_hoje_fora_do_roteiro_nao_tem_fase_atual_e_nao_quebra(catalogo, hoje):
    roteiro = montar_roteiro(catalogo.fases, DPP, hoje)

    assert len(roteiro) == 8
    assert not any(f.atual for f in roteiro)


def test_roteiro_com_dpp_em_29_de_fevereiro(catalogo):
    roteiro = montar_roteiro(catalogo.fases, date(2028, 2, 29), date(2028, 3, 1))

    ultima = roteiro[-1]  # bebe_9_12m: meses 9 a 11
    assert ultima.inicio == date(2028, 11, 29)
    assert ultima.fim == date(2029, 2, 27)  # 29/fev/2028 + 12 meses = 28/fev/2029, menos 1 dia


def test_alertas_comecam_na_idade_certa_e_vem_em_ordem(catalogo):
    alertas = alertas_por_idade(catalogo.regras_seguranca, DPP)

    por_codigo = {a.codigo: a for a in alertas}
    assert len(alertas) == 8
    assert por_codigo["sono-seguro"].ativo_a_partir == date(2027, 6, 15)
    assert por_codigo["sono-seguro"].ativo_ate == date(2028, 6, 15)
    assert por_codigo["introducao-alimentar"].ativo_a_partir == date(2027, 12, 15)
    assert por_codigo["introducao-alimentar"].ativo_ate == date(2028, 3, 15)
    datas = [a.ativo_a_partir for a in alertas]
    assert datas == sorted(datas)
    assert "berco" in por_codigo["sono-seguro"].itens
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `docker compose run --rm api pytest tests/motor/test_motor_calendario.py`
Expected: FAIL (`ModuleNotFoundError: No module named 'app.motor.calendario'`)

- [ ] **Step 3: Implementar**

`api/app/motor/calendario.py`:
```python
import calendar
from collections.abc import Iterable
from datetime import date, timedelta

from app.db.enums import ReferenciaFase
from app.motor.tipos import Alerta, Fase, FaseCalculada, RegraSegurancaCatalogo

SEMANAS_DE_GESTACAO = 40


def adicionar_meses(d: date, meses: int) -> date:
    """Soma meses de calendário; se o dia não existir no mês de destino, usa o último dia."""
    indice = d.month - 1 + meses
    ano = d.year + indice // 12
    mes = indice % 12 + 1
    dia = min(d.day, calendar.monthrange(ano, mes)[1])
    return date(ano, mes, dia)


def intervalo_da_fase(fase: Fase, data_prevista: date) -> tuple[date, date]:
    """Início e fim da fase, ambos inclusivos.

    Fases da gestação contam semanas desde (data prevista - 40 semanas); fases do bebê contam
    meses completos desde a data prevista (de `inicio` até o fim do mês `fim`).
    """
    if fase.referencia == ReferenciaFase.GESTACAO_SEMANA:
        comeco = data_prevista - timedelta(weeks=SEMANAS_DE_GESTACAO)
        return (
            comeco + timedelta(weeks=fase.inicio),
            comeco + timedelta(weeks=fase.fim + 1) - timedelta(days=1),
        )
    return (
        adicionar_meses(data_prevista, fase.inicio),
        adicionar_meses(data_prevista, fase.fim + 1) - timedelta(days=1),
    )


def montar_roteiro(
    fases: Iterable[Fase], data_prevista: date, hoje: date
) -> tuple[FaseCalculada, ...]:
    """Fases com datas reais. A fase atual é a primeira, na ordem, que contém `hoje`."""
    calculadas = []
    for fase in sorted(fases, key=lambda f: f.ordem):
        inicio, fim = intervalo_da_fase(fase, data_prevista)
        calculadas.append((fase, inicio, fim, inicio <= hoje <= fim))
    primeira_atual = next((i for i, c in enumerate(calculadas) if c[3]), None)
    return tuple(
        FaseCalculada(f.codigo, f.nome, f.texto, inicio, fim, atual=(i == primeira_atual))
        for i, (f, inicio, fim, _) in enumerate(calculadas)
    )


def alertas_por_idade(
    regras: Iterable[RegraSegurancaCatalogo], data_prevista: date
) -> tuple[Alerta, ...]:
    """Regras de segurança com a data em que passam a valer, da mais cedo para a mais tarde."""
    alertas = [
        Alerta(
            codigo=r.codigo,
            tema=r.tema,
            texto=r.texto,
            base=r.base,
            ativo_a_partir=adicionar_meses(data_prevista, r.idade_inicio_meses),
            ativo_ate=adicionar_meses(data_prevista, r.idade_fim_meses),
            itens=r.itens,
        )
        for r in regras
    ]
    return tuple(sorted(alertas, key=lambda a: (a.ativo_a_partir, a.codigo)))
```

- [ ] **Step 4: Rodar e ver passar**

Run: `docker compose run --rm api pytest tests/motor`
Expected: todos passam, `0 failed`. Se `test_roteiro_com_dpp_em_29_de_fevereiro` falhar, **não ajuste o teste às cegas**: calcule a mão `adicionar_meses(date(2028, 2, 29), 9)` e `adicionar_meses(date(2028, 2, 29), 12)` e use `systematic-debugging`.

- [ ] **Step 5: Commit**

```bash
git add api/app/motor/calendario.py api/tests/motor
git commit -m "feat: roteiro com datas reais e alertas de segurança por idade

Co-Authored-By: <modelo da sessão> <noreply@anthropic.com>"
```

---

### Task 4: Regras do item e marcas por faixa

**Files:**
- Create: `api/app/motor/regras.py`
- Test: `api/tests/motor/test_motor_regras.py`

**Interfaces:**
- Consumes: `ItemCatalogo`, `RegraItem`, `Respostas`, `MarcaDoItem`, `MarcasEscolhidas` (Task 1); enums `Condicao`, `Efeito`, `Prioridade`, `Faixa`, `Moradia`, `PerfilCodigo`.
- Produces: `Avaliacao(incluir: bool, prioridade: Prioridade, dicas: tuple[str, ...])` (dataclass congelada); `condicao_vale(condicao: Condicao, respostas: Respostas) -> bool`; `avaliar_regras(item: ItemCatalogo, respostas: Respostas) -> Avaliacao`; `marcas_para(marcas: Iterable[MarcaDoItem], orcamento: Faixa) -> MarcasEscolhidas`.

Semântica (decidida aqui): um item com regras `incluir_so_se` entra se **alguma** delas valer (ou). `mudar_prioridade` vale quando a condição vale (a última regra que vale prevalece). `dica` soma o texto quando a condição vale. **Nenhuma condição depende de orçamento ou de "primeiro filho"** (não existem em `Condicao`), e é isso que garante que segurança não sai por preferência.

- [ ] **Step 1: Escrever os testes que falham**

`api/tests/motor/test_motor_regras.py`:
```python
from dataclasses import replace

from app.db.enums import Condicao, Efeito, Faixa, Moradia, Prioridade
from app.motor.regras import avaliar_regras, condicao_vale, marcas_para
from app.motor.tipos import ItemCatalogo, MarcaDoItem, RegraItem

BASE = ItemCatalogo(
    slug="x", nome="X", categoria_slug="c", fase_codigo="f", ordem=1,
    para_que_serve="a", como_escolher="b", prioridade_base=Prioridade.ESSENCIAL, quantidade=1,
)


def _item(*regras, **extra) -> ItemCatalogo:
    return replace(BASE, regras=tuple(regras), **extra)


def test_item_sem_regras_entra_com_a_prioridade_base(fazer_respostas):
    avaliacao = avaliar_regras(_item(), fazer_respostas())

    assert avaliacao.incluir is True
    assert avaliacao.prioridade == Prioridade.ESSENCIAL
    assert avaliacao.dicas == ()


def test_incluir_so_se_depende_da_moradia(fazer_respostas):
    portao = _item(RegraItem(Condicao.CASA_COM_ESCADA, Efeito.INCLUIR_SO_SE))

    assert avaliar_regras(portao, fazer_respostas(moradia=Moradia.APARTAMENTO)).incluir is False
    assert avaliar_regras(portao, fazer_respostas(moradia=Moradia.CASA_SEM_ESCADA)).incluir is False
    assert avaliar_regras(portao, fazer_respostas(moradia=Moradia.CASA_COM_ESCADA)).incluir is True


def test_incluir_so_se_depende_do_clima(fazer_respostas):
    mosquiteiro = _item(RegraItem(Condicao.PERFIL_QUENTE, Efeito.INCLUIR_SO_SE))

    assert avaliar_regras(mosquiteiro, fazer_respostas(perfil="quente")).incluir is True
    assert avaliar_regras(mosquiteiro, fazer_respostas(perfil="frio")).incluir is False


def test_varias_regras_incluir_so_se_valem_como_ou(fazer_respostas):
    item = _item(
        RegraItem(Condicao.PERFIL_QUENTE, Efeito.INCLUIR_SO_SE),
        RegraItem(Condicao.PERFIL_MODERADO, Efeito.INCLUIR_SO_SE),
    )

    assert avaliar_regras(item, fazer_respostas(perfil="moderado")).incluir is True
    assert avaliar_regras(item, fazer_respostas(perfil="frio")).incluir is False


def test_mudar_prioridade_so_quando_a_condicao_vale(fazer_respostas):
    conforto = _item(RegraItem(Condicao.SEM_CARRO, Efeito.MUDAR_PRIORIDADE, "util"))

    assert avaliar_regras(conforto, fazer_respostas(carro=True)).prioridade == Prioridade.ESSENCIAL
    assert avaliar_regras(conforto, fazer_respostas(carro=False)).prioridade == Prioridade.UTIL


def test_dica_aparece_so_quando_a_condicao_vale(fazer_respostas):
    item = _item(RegraItem(Condicao.APARTAMENTO, Efeito.DICA, "Escolha um modelo compacto."))

    assert avaliar_regras(item, fazer_respostas(moradia=Moradia.APARTAMENTO)).dicas == (
        "Escolha um modelo compacto.",
    )
    assert avaliar_regras(item, fazer_respostas(moradia=Moradia.CASA_SEM_ESCADA)).dicas == ()


def test_item_de_seguranca_sem_regra_fisica_entra_em_qualquer_combinacao(fazer_respostas):
    berco = _item(e_seguranca=True)

    for orcamento in Faixa:
        for primeiro_filho in (True, False):
            respostas = fazer_respostas(orcamento=orcamento, primeiro_filho=primeiro_filho)
            assert avaliar_regras(berco, respostas).incluir is True


def test_condicao_vale_cobre_todas_as_condicoes(fazer_respostas):
    respostas = fazer_respostas(perfil="moderado", moradia=Moradia.CASA_COM_ESCADA, carro=False)

    esperado = {
        Condicao.COM_CARRO: False,
        Condicao.SEM_CARRO: True,
        Condicao.APARTAMENTO: False,
        Condicao.CASA_SEM_ESCADA: False,
        Condicao.CASA_COM_ESCADA: True,
        Condicao.PERFIL_QUENTE: False,
        Condicao.PERFIL_MODERADO: True,
        Condicao.PERFIL_FRIO: False,
    }
    assert {c: condicao_vale(c, respostas) for c in Condicao} == esperado


MARCAS = (
    MarcaDoItem("Barata 1", Faixa.ECONOMICO, 1),
    MarcaDoItem("Meio 1", Faixa.INTERMEDIARIO, 2),
    MarcaDoItem("Barata 2", Faixa.ECONOMICO, 3),
    MarcaDoItem("Cara 1", Faixa.INVESTIR, 4),
)


def test_marcas_da_faixa_pedida_na_ordem_do_catalogo():
    escolhidas = marcas_para(MARCAS, Faixa.ECONOMICO)

    assert escolhidas.nomes == ("Barata 1", "Barata 2")
    assert escolhidas.faixa == Faixa.ECONOMICO
    assert escolhidas.fallback is False


def test_faixa_sem_marcas_usa_a_vizinha_mais_barata_em_caso_de_empate():
    so_extremos = (MarcaDoItem("Barata", Faixa.ECONOMICO, 1), MarcaDoItem("Cara", Faixa.INVESTIR, 2))

    escolhidas = marcas_para(so_extremos, Faixa.INTERMEDIARIO)

    assert escolhidas.nomes == ("Barata",)
    assert escolhidas.faixa == Faixa.ECONOMICO
    assert escolhidas.fallback is True


def test_faixa_sem_marcas_anda_para_a_mais_proxima():
    so_caras = (MarcaDoItem("Cara", Faixa.INVESTIR, 1),)

    escolhidas = marcas_para(so_caras, Faixa.ECONOMICO)

    assert escolhidas.nomes == ("Cara",)
    assert escolhidas.faixa == Faixa.INVESTIR
    assert escolhidas.fallback is True


def test_item_sem_nenhuma_marca():
    escolhidas = marcas_para((), Faixa.INTERMEDIARIO)

    assert escolhidas.nomes == ()
    assert escolhidas.faixa is None
    assert escolhidas.fallback is False
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `docker compose run --rm api pytest tests/motor/test_motor_regras.py`
Expected: FAIL (`ModuleNotFoundError: No module named 'app.motor.regras'`)

- [ ] **Step 3: Implementar**

`api/app/motor/regras.py`:
```python
from collections.abc import Iterable
from dataclasses import dataclass

from app.db.enums import Condicao, Efeito, Faixa, Moradia, PerfilCodigo, Prioridade
from app.motor.tipos import ItemCatalogo, MarcaDoItem, MarcasEscolhidas, Respostas

ORDEM_FAIXAS = (Faixa.ECONOMICO, Faixa.INTERMEDIARIO, Faixa.INVESTIR)


@dataclass(frozen=True)
class Avaliacao:
    incluir: bool
    prioridade: Prioridade
    dicas: tuple[str, ...]


def condicao_vale(condicao: Condicao, respostas: Respostas) -> bool:
    """Condições físicas da família: carro, moradia e clima. Orçamento e 'primeiro filho'
    não existem aqui de propósito: nenhuma regra pode tirar um item por preferência."""
    match condicao:
        case Condicao.COM_CARRO:
            return respostas.tem_carro
        case Condicao.SEM_CARRO:
            return not respostas.tem_carro
        case Condicao.APARTAMENTO:
            return respostas.moradia == Moradia.APARTAMENTO
        case Condicao.CASA_SEM_ESCADA:
            return respostas.moradia == Moradia.CASA_SEM_ESCADA
        case Condicao.CASA_COM_ESCADA:
            return respostas.moradia == Moradia.CASA_COM_ESCADA
        case Condicao.PERFIL_QUENTE:
            return respostas.perfil.codigo == PerfilCodigo.QUENTE
        case Condicao.PERFIL_MODERADO:
            return respostas.perfil.codigo == PerfilCodigo.MODERADO
        case Condicao.PERFIL_FRIO:
            return respostas.perfil.codigo == PerfilCodigo.FRIO


def avaliar_regras(item: ItemCatalogo, respostas: Respostas) -> Avaliacao:
    restricoes = [r for r in item.regras if r.efeito == Efeito.INCLUIR_SO_SE]
    incluir = not restricoes or any(condicao_vale(r.condicao, respostas) for r in restricoes)

    prioridade = item.prioridade_base
    dicas: list[str] = []
    for regra in item.regras:
        if not condicao_vale(regra.condicao, respostas):
            continue
        if regra.efeito == Efeito.MUDAR_PRIORIDADE:
            prioridade = Prioridade(regra.valor)
        elif regra.efeito == Efeito.DICA and regra.valor:
            dicas.append(regra.valor)
    return Avaliacao(incluir=incluir, prioridade=prioridade, dicas=tuple(dicas))


def marcas_para(marcas: Iterable[MarcaDoItem], orcamento: Faixa) -> MarcasEscolhidas:
    """Marcas da faixa do orçamento; se não houver, a faixa mais próxima (empate: a mais barata)."""
    marcas = sorted(marcas, key=lambda m: m.ordem)
    alvo = ORDEM_FAIXAS.index(orcamento)
    por_proximidade = sorted(ORDEM_FAIXAS, key=lambda f: (abs(ORDEM_FAIXAS.index(f) - alvo), ORDEM_FAIXAS.index(f)))
    for faixa in por_proximidade:
        nomes = tuple(m.nome for m in marcas if m.faixa == faixa)
        if nomes:
            return MarcasEscolhidas(nomes=nomes, faixa=faixa, fallback=faixa != orcamento)
    return MarcasEscolhidas(nomes=(), faixa=None, fallback=False)
```

- [ ] **Step 4: Rodar e ver passar**

Run: `docker compose run --rm api pytest tests/motor`
Expected: todos passam, `0 failed`.

- [ ] **Step 5: Commit**

```bash
git add api/app/motor/regras.py api/tests/motor/test_motor_regras.py
git commit -m "feat: regras de item (moradia, carro, clima) e marcas por faixa de orçamento

Co-Authored-By: <modelo da sessão> <noreply@anthropic.com>"
```

---

### Task 5: Montagem do enxoval

**Files:**
- Create: `api/app/motor/montagem.py`
- Test: `api/tests/motor/test_motor_montagem.py`

**Interfaces:**
- Consumes: tudo das Tasks 1 a 4.
- Produces: `montar_enxoval(respostas: Respostas, catalogo: Catalogo, hoje: date, limite_volume: int = LIMITE_VOLUME_PADRAO) -> EnxovalCalculado`; constantes `LIMITE_VOLUME_PADRAO = 40` (unidades de roupa num mesmo tamanho) e `DIAS_PRIMEIRO_ANO = 365`.

Regras da montagem (conforme spec, seção 4 e o plano de produto):
- Itens ordenados por (ordem da categoria, ordem do item). Item que a regra exclui não gera linha nem ficha.
- Quantidade por tamanho: `quantidade(base, fator)`, com `fator = fator_lavagem(dias)` só se `item.escala_lavagem`; senão a base. Item sem tamanhos usa `item.quantidade` do mesmo jeito.
- `uso_clima`: `neutro` = 1 linha (variante `""`); `divide` = até 2 linhas (`frio` e `calor`, a de quantidade 0 é omitida); `so_frio` = 1 linha, só se houver mês frio de verdade (sem contar frescos) na janela do tamanho (itens sem tamanho: nos 12 meses).
- Fase de compra da linha = fase do tamanho, ou a do item se o tamanho não tiver.
- Linhas com quantidade 0 são omitidas.
- Aviso de volume alto: maior soma de unidades de um mesmo tamanho > `limite_volume`.
- `destacar_ja_tinha` = `not primeiro_filho`.

- [ ] **Step 1: Escrever os testes que falham**

`api/tests/motor/test_motor_montagem.py`:
```python
from dataclasses import replace
from datetime import date

import pytest

from app.db.enums import Faixa, Moradia, Prioridade, ReferenciaFase, Tamanho, UsoClima
from app.motor.montagem import montar_enxoval
from app.motor.tipos import Catalogo, CategoriaCatalogo, Fase, ItemCatalogo, JanelaTamanho, TamanhoDoItem

HOJE = date(2027, 2, 1)


def _linhas(enxoval) -> dict:
    return {linha.chave: linha for linha in enxoval.linhas}


def test_curitiba_com_nascimento_em_junho(catalogo, fazer_respostas):
    enxoval = montar_enxoval(fazer_respostas("frio"), catalogo, HOJE)
    linhas = _linhas(enxoval)

    # P cobre 15/jun a 12/set: tudo frio, então só a variante de frio
    assert linhas["body:P:frio"].quantidade == 8
    assert linhas["body:P:frio"].rotulo_variante == "manga longa"
    assert "body:P:calor" not in linhas
    # M cobre 13/set a 11/dez: 18 dias de frio em 90 (1/5), então 1 de frio e 6 de calor
    assert linhas["body:M:frio"].quantidade == 1
    assert linhas["body:M:calor"].quantidade == 6
    assert linhas["body:M:calor"].rotulo_variante == "manga curta"
    # peças só de frio aparecem nas janelas com mês frio (G cobre dez a mar, sem frio)
    gorros = {l.tamanho for l in enxoval.linhas if l.item_slug == "gorro"}
    assert gorros == {Tamanho.RN, Tamanho.P, Tamanho.M, Tamanho.GG}
    assert "saco-dormir::" in linhas
    assert "mosquiteiro::" not in linhas


def test_salvador_com_nascimento_em_junho(catalogo, fazer_respostas):
    enxoval = montar_enxoval(fazer_respostas("quente"), catalogo, HOJE)
    linhas = _linhas(enxoval)

    # P: 47 dias frescos (meio valor) em 90 = 47/180; 8 * 47/180 arredonda para 2
    assert linhas["body:P:frio"].quantidade == 2
    assert linhas["body:P:calor"].quantidade == 6
    # G cobre dez a mar: sem mês fresco, só calor
    assert linhas["body:G:calor"].quantidade == 6
    assert "body:G:frio" not in linhas
    # gorro e saco de dormir só entram com mês frio de verdade; mosquiteiro entra no calor
    assert not [l for l in enxoval.linhas if l.item_slug in ("gorro", "saco-dormir")]
    assert "mosquiteiro::" in linhas


def test_quantidade_acompanha_a_frequencia_de_lavagem(catalogo, fazer_respostas):
    a_cada_2 = _linhas(montar_enxoval(fazer_respostas("frio", dias=2), catalogo, HOJE))
    a_cada_3 = _linhas(montar_enxoval(fazer_respostas("frio", dias=3), catalogo, HOJE))

    assert a_cada_2["body:P:frio"].quantidade == 8
    assert a_cada_3["body:P:frio"].quantidade == 11
    # gorro não escala com a lavagem
    assert a_cada_3["gorro:P:"].quantidade == a_cada_2["gorro:P:"].quantidade == 2
    # item sem tamanho que escala: 4 lençóis viram ceil(4 * 4/3) = 6
    assert a_cada_3["lencol-elastico::"].quantidade == 6


def test_bebe_conforto_sem_carro_continua_na_lista_como_util(catalogo, fazer_respostas):
    com_carro = montar_enxoval(fazer_respostas(carro=True), catalogo, HOJE)
    sem_carro = montar_enxoval(fazer_respostas(carro=False), catalogo, HOJE)

    assert _linhas(com_carro)["bebe-conforto::"].prioridade == Prioridade.ESSENCIAL
    assert _linhas(sem_carro)["bebe-conforto::"].prioridade == Prioridade.UTIL
    ficha = next(f for f in sem_carro.fichas if f.slug == "bebe-conforto")
    assert any("táxi" in dica for dica in ficha.dicas)
    assert _linhas(sem_carro)["sling::"].prioridade == Prioridade.ESSENCIAL


@pytest.mark.parametrize(
    ("moradia", "tem_portao"),
    [(Moradia.APARTAMENTO, False), (Moradia.CASA_SEM_ESCADA, False), (Moradia.CASA_COM_ESCADA, True)],
)
def test_portao_so_em_casa_com_escada(catalogo, fazer_respostas, moradia, tem_portao):
    enxoval = montar_enxoval(fazer_respostas(moradia=moradia), catalogo, HOJE)

    assert ("portao-seguranca::" in _linhas(enxoval)) is tem_portao


def test_fase_de_compra_do_tamanho_prevalece_sobre_a_do_item(catalogo, fazer_respostas):
    linhas = _linhas(montar_enxoval(fazer_respostas("frio"), catalogo, HOJE))

    assert linhas["body:P:frio"].fase_codigo == "gestacao_7_8m"
    assert linhas["body:M:frio"].fase_codigo == "bebe_0_3m"
    assert linhas["body:GG:calor"].fase_codigo == "bebe_6_9m"
    assert linhas["berco::"].fase_codigo == "gestacao_5_7m"


def test_linhas_vem_na_ordem_das_categorias(catalogo, fazer_respostas):
    enxoval = montar_enxoval(fazer_respostas(), catalogo, HOJE)

    ordem_categoria = {c.slug: c.ordem for c in catalogo.categorias}
    ordens = [ordem_categoria[l.categoria_slug] for l in enxoval.linhas]
    assert ordens == sorted(ordens)
    assert enxoval.linhas[0].categoria_slug == "roupas"


def test_ficha_traz_as_marcas_da_faixa_do_orcamento(catalogo, fazer_respostas):
    intermediario = montar_enxoval(fazer_respostas(orcamento=Faixa.INTERMEDIARIO), catalogo, HOJE)
    economico = montar_enxoval(fazer_respostas(orcamento=Faixa.ECONOMICO), catalogo, HOJE)

    ficha = next(f for f in intermediario.fichas if f.slug == "berco")
    assert ficha.marcas.nomes == ("Tcil", "Reller")
    assert ficha.marcas.fallback is False
    ficha_economica = next(f for f in economico.fichas if f.slug == "berco")
    assert ficha_economica.marcas.nomes == ("Burigotto", "Galzerano")
    assert ficha_economica.regras_seguranca == ("inmetro-cordoes", "sono-seguro")


def test_roteiro_e_alertas_vem_junto(catalogo, fazer_respostas):
    enxoval = montar_enxoval(fazer_respostas(), catalogo, HOJE)

    assert len(enxoval.roteiro) == 8
    assert [f.codigo for f in enxoval.roteiro if f.atual] == ["gestacao_5_7m"]
    assert len(enxoval.alertas) == 8


def test_resumo_avisa_quando_o_volume_fica_alto_demais(catalogo, fazer_respostas):
    a_cada_2 = montar_enxoval(fazer_respostas("frio", dias=2), catalogo, HOJE)
    a_cada_4 = montar_enxoval(fazer_respostas("frio", dias=4), catalogo, HOJE)

    assert a_cada_2.resumo.dias_sem_lavar == 2
    assert a_cada_2.resumo.aviso_volume_alto is False
    assert a_cada_4.resumo.dias_sem_lavar == 4
    assert a_cada_4.resumo.aviso_volume_alto is True
    assert a_cada_4.resumo.total_unidades > a_cada_2.resumo.total_unidades


def test_limite_de_volume_e_configuravel(catalogo, fazer_respostas):
    enxoval = montar_enxoval(fazer_respostas("frio", dias=2), catalogo, HOJE, limite_volume=10)

    assert enxoval.resumo.aviso_volume_alto is True


def test_nao_ser_o_primeiro_filho_destaca_ja_tinha(catalogo, fazer_respostas):
    primeiro = montar_enxoval(fazer_respostas(primeiro_filho=True), catalogo, HOJE)
    segundo = montar_enxoval(fazer_respostas(primeiro_filho=False), catalogo, HOJE)

    assert primeiro.resumo.destacar_ja_tinha is False
    assert segundo.resumo.destacar_ja_tinha is True


def test_dias_entre_lavagens_invalido_e_recusado(catalogo, fazer_respostas):
    with pytest.raises(ValueError, match="entre 1 e 7"):
        montar_enxoval(fazer_respostas(dias=0), catalogo, HOJE)


# ---------- catálogo incompleto: o motor não quebra e avisa ----------

ITEM = ItemCatalogo(
    slug="body", nome="Body", categoria_slug="roupas", fase_codigo="f", ordem=1,
    para_que_serve="a", como_escolher="b", prioridade_base=Prioridade.ESSENCIAL,
    uso_clima=UsoClima.DIVIDE, variante_frio="longa", variante_calor="curta",
    escala_lavagem=True, tamanhos=(TamanhoDoItem(Tamanho.P, 8),),
)
CATEGORIAS = (CategoriaCatalogo("roupas", "Roupas", 1),)


def test_catalogo_vazio_devolve_enxoval_vazio(fazer_respostas):
    enxoval = montar_enxoval(fazer_respostas(), Catalogo(), HOJE)

    assert enxoval.linhas == () and enxoval.fichas == () and enxoval.roteiro == ()
    assert enxoval.resumo.total_unidades == 0
    assert enxoval.resumo.aviso_volume_alto is False


def test_item_sem_janela_do_tamanho_entra_sem_divisao_de_clima_e_avisa(fazer_respostas):
    catalogo = Catalogo(categorias=CATEGORIAS, itens=(ITEM,))

    enxoval = montar_enxoval(fazer_respostas("frio"), catalogo, HOJE)

    assert [(l.chave, l.quantidade) for l in enxoval.linhas] == [("body:P:", 8)]
    assert any("body" in aviso and "janela" in aviso for aviso in enxoval.avisos)


def test_item_sem_tamanhos_nem_quantidade_e_ignorado_com_aviso(fazer_respostas):
    vazio = replace(ITEM, tamanhos=())
    catalogo = Catalogo(categorias=CATEGORIAS, itens=(vazio,))

    enxoval = montar_enxoval(fazer_respostas(), catalogo, HOJE)

    assert enxoval.linhas == ()
    assert any("body" in aviso and "quantidade" in aviso for aviso in enxoval.avisos)


def test_item_sem_marcas_gera_ficha_sem_marcas(fazer_respostas):
    janela = JanelaTamanho(Tamanho.P, 0, 90)
    catalogo = Catalogo(categorias=CATEGORIAS, itens=(ITEM,), janelas=(janela,))

    enxoval = montar_enxoval(fazer_respostas("frio"), catalogo, HOJE)

    assert enxoval.fichas[0].marcas.nomes == ()
    assert enxoval.fichas[0].marcas.faixa is None


def test_fase_de_roteiro_sem_itens_nao_atrapalha(fazer_respostas):
    fase = Fase("f", "Fase", ReferenciaFase.BEBE_MES, 0, 2, "t", 1)

    enxoval = montar_enxoval(fazer_respostas(), Catalogo(fases=(fase,)), HOJE)

    assert len(enxoval.roteiro) == 1
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `docker compose run --rm api pytest tests/motor/test_motor_montagem.py`
Expected: FAIL (`ModuleNotFoundError: No module named 'app.motor.montagem'`)

- [ ] **Step 3: Implementar**

`api/app/motor/montagem.py`:
```python
from collections import defaultdict
from datetime import date
from fractions import Fraction

from app.db.enums import Tamanho, UsoClima
from app.motor.calendario import alertas_por_idade, montar_roteiro
from app.motor.clima import proporcao_frio
from app.motor.quantidades import dividir_variantes, fator_lavagem, quantidade
from app.motor.regras import Avaliacao, avaliar_regras, marcas_para
from app.motor.tipos import (
    Catalogo,
    EnxovalCalculado,
    Ficha,
    ItemCatalogo,
    JanelaTamanho,
    LinhaCalculada,
    Respostas,
    Resumo,
)

LIMITE_VOLUME_PADRAO = 40
DIAS_PRIMEIRO_ANO = 365
ORDEM_TAMANHOS = {tamanho: posicao for posicao, tamanho in enumerate(Tamanho)}


def montar_enxoval(
    respostas: Respostas,
    catalogo: Catalogo,
    hoje: date,
    limite_volume: int = LIMITE_VOLUME_PADRAO,
) -> EnxovalCalculado:
    fator = fator_lavagem(respostas.dias_entre_lavagens)
    janelas = {j.tamanho: j for j in catalogo.janelas}
    ordem_categoria = {c.slug: c.ordem for c in catalogo.categorias}
    avisos: list[str] = []
    linhas: list[LinhaCalculada] = []
    fichas: list[Ficha] = []

    itens = sorted(
        catalogo.itens, key=lambda i: (ordem_categoria.get(i.categoria_slug, 10**6), i.ordem)
    )
    for item in itens:
        avaliacao = avaliar_regras(item, respostas)
        if not avaliacao.incluir:
            continue
        novas = _linhas_do_item(item, avaliacao, respostas, janelas, fator, avisos)
        if not novas:
            continue
        linhas.extend(novas)
        marcas = marcas_para(item.marcas, respostas.orcamento)
        if marcas.fallback:
            avisos.append(
                f"item '{item.slug}': sem marcas na faixa '{respostas.orcamento.value}'; "
                f"usando a faixa '{marcas.faixa.value}'"
            )
        fichas.append(
            Ficha(
                slug=item.slug,
                nome=item.nome,
                para_que_serve=item.para_que_serve,
                como_escolher=item.como_escolher,
                idade_inicio_meses=item.idade_inicio_meses,
                marcas=marcas,
                dicas=avaliacao.dicas,
                regras_seguranca=item.regras_seguranca,
            )
        )

    return EnxovalCalculado(
        linhas=tuple(linhas),
        fichas=tuple(fichas),
        roteiro=montar_roteiro(catalogo.fases, respostas.data_prevista, hoje),
        alertas=alertas_por_idade(catalogo.regras_seguranca, respostas.data_prevista),
        resumo=_resumir(linhas, respostas, limite_volume),
        avisos=tuple(avisos),
    )


def _linhas_do_item(
    item: ItemCatalogo,
    avaliacao: Avaliacao,
    respostas: Respostas,
    janelas: dict[Tamanho, JanelaTamanho],
    fator: Fraction,
    avisos: list[str],
) -> list[LinhaCalculada]:
    escala = fator if item.escala_lavagem else Fraction(1)
    if item.tamanhos:
        saida: list[LinhaCalculada] = []
        for tamanho in sorted(item.tamanhos, key=lambda t: ORDEM_TAMANHOS[t.tamanho]):
            janela = janelas.get(tamanho.tamanho)
            if janela is None:
                avisos.append(
                    f"item '{item.slug}': sem janela de tamanho {tamanho.tamanho.value}; "
                    "sem divisão de clima"
                )
            saida += _por_clima(
                item,
                avaliacao,
                respostas,
                quantidade(tamanho.quantidade_base, escala),
                (janela.inicio_dias, janela.fim_dias) if janela else None,
                tamanho.tamanho,
                tamanho.fase_codigo or item.fase_codigo,
            )
        return saida
    if item.quantidade is None:
        avisos.append(f"item '{item.slug}': sem tamanhos nem quantidade; ignorado")
        return []
    return _por_clima(
        item,
        avaliacao,
        respostas,
        quantidade(item.quantidade, escala),
        (0, DIAS_PRIMEIRO_ANO),
        None,
        item.fase_codigo,
    )


def _por_clima(
    item: ItemCatalogo,
    avaliacao: Avaliacao,
    respostas: Respostas,
    total: int,
    intervalo: tuple[int, int] | None,
    tamanho: Tamanho | None,
    fase_codigo: str,
) -> list[LinhaCalculada]:
    if total <= 0:
        return []

    def linha(variante: str, rotulo: str | None, qtd: int) -> LinhaCalculada:
        return LinhaCalculada(
            chave=f"{item.slug}:{tamanho.value if tamanho else ''}:{variante}",
            item_slug=item.slug,
            nome=item.nome,
            categoria_slug=item.categoria_slug,
            tamanho=tamanho,
            variante=variante,
            rotulo_variante=rotulo,
            quantidade=qtd,
            unidade_texto=item.unidade_texto,
            prioridade=avaliacao.prioridade,
            fase_codigo=fase_codigo,
            e_seguranca=item.e_seguranca,
            escala_lavagem=item.escala_lavagem,
        )

    if item.uso_clima == UsoClima.NEUTRO or (intervalo is None and item.uso_clima == UsoClima.DIVIDE):
        return [linha("", None, total)]

    inicio, fim = intervalo or (0, DIAS_PRIMEIRO_ANO)
    data = respostas.data_prevista
    if item.uso_clima == UsoClima.SO_FRIO:
        tem_frio = proporcao_frio(data, inicio, fim, respostas.perfil, incluir_frescos=False) > 0
        return [linha("", None, total)] if tem_frio else []

    frio, calor = dividir_variantes(total, proporcao_frio(data, inicio, fim, respostas.perfil))
    saida = []
    if frio:
        saida.append(linha("frio", item.variante_frio, frio))
    if calor:
        saida.append(linha("calor", item.variante_calor, calor))
    return saida


def _resumir(linhas: list[LinhaCalculada], respostas: Respostas, limite_volume: int) -> Resumo:
    por_tamanho: dict[Tamanho, int] = defaultdict(int)
    for linha in linhas:
        if linha.tamanho is not None:
            por_tamanho[linha.tamanho] += linha.quantidade
    return Resumo(
        dias_sem_lavar=respostas.dias_entre_lavagens,
        total_unidades=sum(l.quantidade for l in linhas),
        aviso_volume_alto=max(por_tamanho.values(), default=0) > limite_volume,
        destacar_ja_tinha=not respostas.primeiro_filho,
    )
```

- [ ] **Step 4: Rodar e ver passar**

Run: `docker compose run --rm api pytest tests/motor`
Expected: todos passam, `0 failed`. Se algum número dos testes de Curitiba/Salvador divergir, **calcule à mão** a janela (dias de idade somados à data prevista) antes de mexer: os valores esperados vêm da conta dia a dia (ver comentários nos testes), e um desvio indica bug no código ou erro de aritmética meu, que precisa ser decidido com `systematic-debugging` e registrado.

- [ ] **Step 5: Commit**

```bash
git add api/app/motor/montagem.py api/tests/motor/test_motor_montagem.py
git commit -m "feat: montagem do enxoval (quantidades, clima, regras, fichas, roteiro e resumo)

Co-Authored-By: <modelo da sessão> <noreply@anthropic.com>"
```

---

### Task 6: Progresso (compradas, ganhadas e já tinha)

**Files:**
- Create: `api/app/motor/progresso.py`
- Test: `api/tests/motor/test_motor_progresso.py`

**Interfaces:**
- Consumes: `LinhaCalculada` (Task 1).
- Produces: `Marcacao(comprada=0, ganhada=0, ja_tinha=0)` com a propriedade `total`; `Progresso(total_unidades, atendidas, faltam, percentual, fora_da_lista: tuple[str, ...])`; `progresso(linhas: Iterable[LinhaCalculada], marcadas: Mapping[str, Marcacao]) -> Progresso`. Uma linha nunca "atende" mais que a sua quantidade (ganhar além do sugerido não pode esconder o que falta em outra linha). `fora_da_lista` = chaves marcadas, com total maior que zero, que não existem mais nas linhas (ex.: a família trocou de cidade), em ordem alfabética.

- [ ] **Step 1: Escrever o teste que falha**

`api/tests/motor/test_motor_progresso.py`:
```python
from app.db.enums import Prioridade
from app.motor.progresso import Marcacao, progresso
from app.motor.tipos import LinhaCalculada


def _linha(chave: str, quantidade: int) -> LinhaCalculada:
    return LinhaCalculada(
        chave=chave, item_slug=chave.split(":")[0], nome="X", categoria_slug="c",
        tamanho=None, variante="", rotulo_variante=None, quantidade=quantidade,
        unidade_texto=None, prioridade=Prioridade.UTIL, fase_codigo="f",
        e_seguranca=False, escala_lavagem=False,
    )


def test_marcacao_soma_as_tres_origens():
    assert Marcacao(comprada=3, ganhada=4, ja_tinha=1).total == 8


def test_progresso_limita_cada_linha_a_sua_quantidade():
    linhas = [_linha("a::", 8), _linha("b::", 4)]
    marcadas = {
        "a::": Marcacao(comprada=3, ganhada=4, ja_tinha=3),  # 10 de 8: conta só 8
        "b::": Marcacao(comprada=1),
        "c::": Marcacao(ganhada=2),  # linha que saiu da lista
        "d::": Marcacao(),  # zerada: não conta como fora da lista
    }

    resultado = progresso(linhas, marcadas)

    assert resultado.total_unidades == 12
    assert resultado.atendidas == 9
    assert resultado.faltam == 3
    assert resultado.percentual == 75
    assert resultado.fora_da_lista == ("c::",)


def test_progresso_sem_marcacoes():
    resultado = progresso([_linha("a::", 5)], {})

    assert (resultado.atendidas, resultado.faltam, resultado.percentual) == (0, 5, 0)
    assert resultado.fora_da_lista == ()


def test_progresso_sem_linhas_nao_divide_por_zero():
    resultado = progresso([], {"x::": Marcacao(comprada=2)})

    assert (resultado.total_unidades, resultado.percentual) == (0, 0)
    assert resultado.fora_da_lista == ("x::",)
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `docker compose run --rm api pytest tests/motor/test_motor_progresso.py`
Expected: FAIL (`ModuleNotFoundError: No module named 'app.motor.progresso'`)

- [ ] **Step 3: Implementar**

`api/app/motor/progresso.py`:
```python
from collections.abc import Iterable, Mapping
from dataclasses import dataclass

from app.motor.tipos import LinhaCalculada


@dataclass(frozen=True)
class Marcacao:
    comprada: int = 0
    ganhada: int = 0
    ja_tinha: int = 0

    @property
    def total(self) -> int:
        return self.comprada + self.ganhada + self.ja_tinha


@dataclass(frozen=True)
class Progresso:
    total_unidades: int
    atendidas: int
    faltam: int
    percentual: int
    fora_da_lista: tuple[str, ...]


def progresso(
    linhas: Iterable[LinhaCalculada], marcadas: Mapping[str, Marcacao]
) -> Progresso:
    linhas = list(linhas)
    total = sum(l.quantidade for l in linhas)
    atendidas = sum(
        min(l.quantidade, marcadas[l.chave].total) for l in linhas if l.chave in marcadas
    )
    chaves = {l.chave for l in linhas}
    fora = tuple(sorted(c for c, m in marcadas.items() if c not in chaves and m.total > 0))
    return Progresso(
        total_unidades=total,
        atendidas=atendidas,
        faltam=total - atendidas,
        percentual=(100 * atendidas) // total if total else 0,
        fora_da_lista=fora,
    )
```

- [ ] **Step 4: Rodar e ver passar**

Run: `docker compose run --rm api pytest tests/motor`
Expected: todos passam, `0 failed`.

- [ ] **Step 5: Commit**

```bash
git add api/app/motor/progresso.py api/tests/motor/test_motor_progresso.py
git commit -m "feat: progresso do enxoval (compradas, ganhadas, já tinha e linhas fora da lista)

Co-Authored-By: <modelo da sessão> <noreply@anthropic.com>"
```

---

### Task 7: A regra de ouro — segurança nunca sai

**Files:**
- Test: `api/tests/motor/test_motor_seguranca.py`

**Interfaces:**
- Consumes: `montar_enxoval`, fixtures `catalogo` e `fazer_respostas`.
- Produces: nada novo; é a garantia de que nenhuma combinação de respostas remove um item ou alerta de segurança por orçamento ou preferência, e de que o orçamento só muda marcas, nunca a lista.

Este teste deve **passar de primeira** (a lógica já está nas Tasks 4 e 5). Para provar que ele protege de verdade, o Step 3 quebra o código de propósito e exige ver o teste falhar.

- [ ] **Step 1: Escrever os testes**

`api/tests/motor/test_motor_seguranca.py`:
```python
from datetime import date
from itertools import product

from app.db.enums import Faixa, Moradia
from app.motor.montagem import montar_enxoval

HOJE = date(2027, 2, 1)
PERFIS = ("quente", "moderado", "frio")
DIAS = (1, 2, 4, 7)


def test_item_de_seguranca_nunca_sai_por_orcamento_ou_preferencia(catalogo, fazer_respostas):
    de_seguranca = {i.slug for i in catalogo.itens if i.e_seguranca}
    assert len(de_seguranca) == 9  # berço, colchão, lençol, bebê conforto, termômetro, 4 da casa

    for perfil, moradia, carro, orcamento, primeiro_filho, dias in product(
        PERFIS, Moradia, (True, False), Faixa, (True, False), DIAS
    ):
        respostas = fazer_respostas(
            perfil, dias=dias, moradia=moradia, carro=carro,
            orcamento=orcamento, primeiro_filho=primeiro_filho,
        )
        enxoval = montar_enxoval(respostas, catalogo, HOJE)

        presentes = {l.item_slug for l in enxoval.linhas if l.e_seguranca}
        # só uma condição física tira um item de segurança: o portão sem escada
        esperados = de_seguranca - (
            set() if moradia == Moradia.CASA_COM_ESCADA else {"portao-seguranca"}
        )
        assert presentes == esperados, (perfil, moradia, carro, orcamento, primeiro_filho, dias)
        assert len(enxoval.alertas) == 8


def test_orcamento_e_primeiro_filho_so_mudam_marcas_e_destaque_nunca_as_linhas(
    catalogo, fazer_respostas
):
    for perfil, moradia, carro, dias in product(PERFIS, Moradia, (True, False), DIAS):
        referencia = montar_enxoval(
            fazer_respostas(perfil, dias=dias, moradia=moradia, carro=carro), catalogo, HOJE
        )
        for orcamento, primeiro_filho in product(Faixa, (True, False)):
            outra = montar_enxoval(
                fazer_respostas(
                    perfil, dias=dias, moradia=moradia, carro=carro,
                    orcamento=orcamento, primeiro_filho=primeiro_filho,
                ),
                catalogo,
                HOJE,
            )
            assert outra.linhas == referencia.linhas, (perfil, moradia, carro, dias, orcamento)
            assert outra.alertas == referencia.alertas
            assert [f.slug for f in outra.fichas] == [f.slug for f in referencia.fichas]
```

- [ ] **Step 2: Rodar e ver passar**

Run: `docker compose run --rm api pytest tests/motor/test_motor_seguranca.py`
Expected: `2 passed`.

- [ ] **Step 3: Provar que o teste protege (mutação temporária)**

Em `api/app/motor/regras.py`, dentro de `avaliar_regras`, logo antes do `return`, acrescente **temporariamente** a linha:
```python
    if respostas.orcamento == Faixa.ECONOMICO and item.slug == "termometro":
        incluir = False
```
Run: `docker compose run --rm api pytest tests/motor/test_motor_seguranca.py`
Expected: FAIL nos dois testes (o termômetro some no orçamento econômico). Depois **desfaça a mutação**: `git checkout api/app/motor/regras.py` e rode de novo para ver `2 passed`.

- [ ] **Step 4: Suíte completa e commit**

Run: `docker compose run --rm api pytest`
Expected: todos passam (Etapa 1 + Etapa 2), `0 failed`.

```bash
git add api/tests/motor/test_motor_seguranca.py
git commit -m "test: segurança nunca sai por orçamento ou preferência (todas as combinações)

Co-Authored-By: <modelo da sessão> <noreply@anthropic.com>"
```

---

## Ao terminar a Etapa 2

- `docker compose run --rm api pytest` passa por inteiro; `api/app/motor/` não importa banco nem HTTP (teste de pureza).
- Próximo passo: escrever o plano da **Etapa 3 (API)**, que inclui os adaptadores banco → `Catalogo`/`Respostas`, o serviço que cria e lê enxovais, as rotas, a normalização de `nome_busca` ao salvar município (já anotada) e as exportações.
