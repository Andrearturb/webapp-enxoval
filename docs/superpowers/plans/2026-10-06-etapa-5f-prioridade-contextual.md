# Plano — Etapa 5f: Prioridade Contextual por Fase

Data: 2026-10-06 · Status: aprovado · Próxima etapa após 5e

## Problema

A `prioridade` dos itens (essencial/util/pode_esperar) é estática e
descontextualizada do momento da família. Quando o bebê já nasceu,
itens de gestação aparecem com prioridade igual a itens de 9 meses.
O usuário não sabe o que comprar agora vs. o que pode esperar.

## Decisão de design

Introduzir `momento_compra` como dimensão calculada pelo motor,
**separada** da `prioridade` permanente do item:

| momento_compra | Significado |
|---|---|
| `atrasado` | Fase já passou, item não comprado — comprar imediatamente |
| `agora` | Fase atual — comprar neste período |
| `proxima_fase` | Próxima fase — planejar e pesquisar |
| `futuro` | Fases distantes — só ter ciência |

A combinação `momento_compra` + `prioridade` define o que o usuário vê:

- atrasado + essencial → "⚠ Urgente"
- agora + essencial → "Comprar agora"
- agora + util → "Recomendado nesta fase"
- proxima_fase + essencial → "Planejar para breve"
- futuro + qualquer → "Mais para frente"

## O que foi descartado

- **Preços por fase**: sem base de dados de preços por SKU, qualquer
  número seria impreciso. Feature futura.
- **Zíper como variante de macacão**: exige mudança no modelo de dados.
  Feature futura.

## Correções de catálogo incluídas nesta etapa

- `macacao` tamanho RN: quantidade_base 2 → **4**
- Novo item `cueiro`: categoria roupas, quantidade 6, fase
  gestacao_7_8m, prioridade essencial, escala_lavagem: true

## Tasks

### Task 1 — Enum MomentoCompra no backend

**Arquivo:** `api/app/db/enums.py`
Adicionar:
```python
class MomentoCompra(str, Enum):
    atrasado = "atrasado"
    agora = "agora"
    proxima_fase = "proxima_fase"
    futuro = "futuro"
```

**Arquivo:** `api/app/motor/tipos.py`
Adicionar campo em `LinhaCalculada`:
```python
momento_compra: MomentoCompra = MomentoCompra.futuro
```

Demo: mypy passa, imports funcionam.

---

### Task 2 — Lógica de momento_compra no motor

**Arquivo:** `api/app/motor/montagem.py`

```python
def _momento_compra(
    fase_codigo: str,
    roteiro: tuple[FaseCalculada, ...]
) -> MomentoCompra:
    ordem_atual = next((f.ordem for f in roteiro if f.atual), None)
    ordem_linha = next((f.ordem for f in roteiro if f.codigo == fase_codigo), None)
    if ordem_linha is None or ordem_atual is None:
        return MomentoCompra.futuro
    diff = ordem_linha - ordem_atual
    if diff < 0:
        return MomentoCompra.atrasado
    if diff == 0:
        return MomentoCompra.agora
    if diff == 1:
        return MomentoCompra.proxima_fase
    return MomentoCompra.futuro
```

Testes TDD em `api/tests/motor/test_motor_momento_compra.py`:
- linha de fase passada → `atrasado`
- linha de fase atual → `agora`
- linha de próxima fase → `proxima_fase`
- linha de fase distante → `futuro`
- bebê já nascido → itens de gestação são `atrasado`

---

### Task 3 — Expor momento_compra na API

**Arquivo:** `api/app/rotas/schemas.py`
Adicionar em `LinhaSaida`:
```python
momento_compra: MomentoCompra
```
Atualizar `montar_saida` para mapear o campo.

Após isso: rodar `npm run gen:api` com a API no ar para regenerar
`web/src/api/tipos.ts`.

---

### Task 4 — Ajuste no catálogo (YAML)

**Arquivo:** `api/seed/dados/itens.yaml`

1. Macacão RN: `{RN: 4, P: 4, M: 4, G: 3, GG: 3}` (era RN: 2)
2. Novo item cueiro após fralda-pano:
```yaml
- slug: cueiro
  nome: Cueiro
  categoria: roupas
  fase: gestacao_7_8m
  prioridade: essencial
  escala_lavagem: true
  quantidade: 6
  unidade: cueiros
  para_que_serve: Enrolar o bebê nos primeiros dias, acalmar e ajudar
    no sono com o método do embrulho.
  como_escolher: Musselina ou algodão leve, pelo menos 1,2 m × 1,2 m.
  marcas: [Aden + Anais, Buba, Papi, Linhas de loja]
```

---

### Task 5 — Planilha: agrupamento por momento_compra

**Arquivo:** `web/src/paginas/Planilha.tsx` e componentes em
`web/src/paginas/planilha/`

Substituir agrupamento só por categoria por agrupamento primário por
`momento_compra`, secundário por categoria:

```
⚠ Comprar agora (atrasado)
  └─ Roupas: Body RN, Macacão RN, Cueiro...
📋 Nesta fase (agora)
  └─ ...
🗓 Próxima fase (proxima_fase)
  └─ ...
🗓 Mais para frente (futuro) — colapsado por padrão
  └─ ...
```

Os filtros existentes (Faltando, Essencial, etc.) continuam
funcionando dentro de cada grupo.

---

### Task 6 — Planilha: painel de fases

**Arquivo:** `web/src/paginas/planilha/PainelFases.tsx` (novo)

Cards horizontais roláveis no topo da planilha:
```
[⚠ Reta final · 8 itens] [Primeiros meses · 5 itens] [3–6 meses · 4 itens]
```
Card da fase atual destacado. Clique filtra a planilha para aquela fase.

---

## Ordem de execução

1. Task 4 (catálogo YAML) — independente
2. Task 1 → Task 2 → Task 3 (backend em sequência)
3. Rodar `npm run gen:api` após Task 3
4. Task 5 → Task 6 (frontend em sequência)

## Comandos úteis

```bash
# Testes backend
docker compose run --rm api pytest

# Testes front
docker compose run --rm --no-deps web npm test -- --run

# Regenerar tipos TypeScript (API precisa estar no ar)
docker compose up -d api db
docker compose run --rm --no-deps web npm run gen:api

# Typecheck + build
docker compose run --rm --no-deps web npm run typecheck
docker compose run --rm --no-deps web npm run build
```

## Estado do projeto ao iniciar esta etapa

- Etapas 1, 2, 3 concluídas (backend completo)
- Etapas 5a–5e concluídas (front completo)
- 95 testes front passando, typecheck e build limpos
- Último commit: `8205d91`
- Branch: `main`

## Referências

- Spec de design: `docs/superpowers/specs/2026-10-05-enxoval-inteligente-design.md`
- Catálogo: `api/seed/dados/itens.yaml`
- Fases: `api/seed/dados/fases.yaml`
- Motor: `api/app/motor/montagem.py`
- Tipos motor: `api/app/motor/tipos.py`
- Enums: `api/app/db/enums.py`
- Schema API: `api/app/rotas/schemas.py`
- Planilha front: `web/src/paginas/Planilha.tsx`
