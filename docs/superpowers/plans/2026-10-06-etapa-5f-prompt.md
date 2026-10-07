# Prompt de contexto — Etapa 5f

Cole este prompt ao iniciar uma nova sessão para continuar o desenvolvimento.

---

Continuando o desenvolvimento do webapp-enxoval.

## Estado atual

As etapas 5a–5e estão **concluídas e mergeadas no `main`**
(último commit: `8205d91`). O projeto tem:

- Backend FastAPI completo (etapas 1–3)
- Front React/TypeScript completo com todas as páginas:
  Início, Questionário (6 passos), Planilha (contadores otimistas),
  Roteiro, Guia dos itens, Segurança, Ajustes
- 95 testes front passando, typecheck e build limpos

Para rodar localmente: copie `.env.example` para `.env` (os valores
padrão já servem para dev local).
- Testes do front: `docker compose run --rm --no-deps web npm test -- --run`
- Testes do backend: `docker compose run --rm api pytest`
- Build: `docker compose run --rm --no-deps web npm run build`
- Typecheck: `docker compose run --rm --no-deps web npm run typecheck`
- API em http://localhost:8010 · Front em http://localhost:5180

## Próxima etapa: 5f — Prioridade contextual por fase

O plano completo está em:
`docs/superpowers/plans/2026-10-06-etapa-5f-prioridade-contextual.md`

**Leia esse arquivo antes de qualquer coisa.**

## O que fazer (resumo)

Introduzir `momento_compra` como campo calculado pelo motor Python,
expor na API e usar no front para agrupar itens da planilha por
momento de compra.

Os 4 valores possíveis:
- `atrasado` — fase já passou, comprar imediatamente
- `agora` — fase atual
- `proxima_fase` — próxima fase, planejar
- `futuro` — fases distantes

Também corrigir o catálogo YAML:
- macacão RN: quantidade_base 2 → 4
- novo item cueiro (musselina, 6 unidades, essencial, escala_lavagem)

## Ordem de execução das tasks

1. **Task 4** (catálogo YAML) — `api/seed/dados/itens.yaml`
2. **Task 1** (enum MomentoCompra) — `api/app/db/enums.py` + `api/app/motor/tipos.py`
3. **Task 2** (lógica no motor) — `api/app/motor/montagem.py` com testes TDD
4. **Task 3** (API) — `api/app/rotas/schemas.py` + `npm run gen:api`
5. **Task 5** (planilha agrupada) — `web/src/paginas/Planilha.tsx`
6. **Task 6** (painel de fases) — `web/src/paginas/planilha/PainelFases.tsx`

## Metodologia obrigatória

Use TDD: escreva o teste que falha (RED) antes de implementar (GREEN).
Commite por task. Rode a suíte completa + typecheck + build antes de
declarar cada task concluída.

## Atenção sobre porta da API

O `--no-deps` nos comandos de front evita que o compose suba a API na
porta 8010, que pode colidir com outro projeto (`service-tracker-backend`)
rodando na mesma máquina.
