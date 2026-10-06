# Etapa 5b — Questionário · Plano de implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implementar as 6 perguntas do questionário em `/questionario/:passo` — cidade com perfil de clima sugerido e correção, data prevista, frequência de lavagem, moradia e carro, orçamento e primeiro filho —, terminando num único `POST /enxovais` que redireciona para `/enxoval/:id/planilha`.

**Architecture:** Um container (`Questionario.tsx`, já existe como placeholder da Etapa 5a) lê `:passo` da URL, guarda as 6 respostas num único `useState` (só em memória, nunca em localStorage) e renderiza o componente do passo atual a partir de uma lista de 6 componentes. Cada "Passo" é controlado (recebe `respostas` + `onChange`) e não tem estado próprio de domínio — a cidade é a única exceção, com um estado local só para o texto de busca. Botões Voltar/Avançar navegam trocando a URL; o container nunca perde dados ao trocar de passo porque ele é a mesma instância React o tempo todo (só `:passo` muda). `Concluir` (passo 6) dispara `POST /enxovais` via `useMutation` do TanStack Query e navega para a planilha no sucesso.

**Tech Stack:** React Router (`useParams`/`useNavigate`), TanStack Query (`useQuery` para buscar cidade, `useMutation` para criar o enxoval), `fetch` nativo (sem biblioteca de cliente HTTP nova), Vitest + Testing Library (`fireEvent`, sem `@testing-library/user-event` — não é dependência do projeto e `fireEvent` cobre tudo que esta etapa precisa).

**Spec:** [`docs/superpowers/specs/2026-10-05-enxoval-inteligente-design.md`](../specs/2026-10-05-enxoval-inteligente-design.md) (seções 5, 6) e contrato real em `api/app/rotas/schemas.py`, `api/app/rotas/catalogo.py`, `api/app/db/enums.py`.

## Global Constraints

- Mobile first, acessível (contraste AA, alvos de toque ≥ 44 px), todo texto visível em português do Brasil (spec seção 1).
- Respostas do questionário ficam **só em memória** do componente — nenhum `localStorage`/`sessionStorage`; um único `POST /enxovais` no final (spec seção 6, rota `/questionario/:passo`).
- `web/src/api/tipos.ts` é gerado e commitado (Etapa 5a) — nunca editar à mão; os tipos usados aqui (`RespostasEntrada`, `MunicipioBuscaSaida`, `EnxovalCriado`, `Erro`, `Moradia`, `Faixa`, `PerfilCodigo`) já existem no arquivo.
- Formato de erro da API é sempre `{"erro": "<codigo>", "mensagem": "<texto pt-BR>"}`, inclusive para 404, 422 e 429 (confirmado em `api/app/main.py`) — o cliente HTTP do front deve assumir esse formato, não o `{"detail": ...}` padrão do FastAPI.
- `dias_entre_lavagens` é um inteiro de 1 a 7 enviado direto pelo front; as 4 opções de resposta da tela mapeiam para os valores 1, 2, 3 e 4 (spec seção 4, função `fator_lavagem`).
- Testes: `docker compose run --rm web npm test`. Build: `docker compose run --rm web npm run build`. Typecheck: `docker compose run --rm web npm run typecheck`.

## Review Focus

1. **`/questionario/0`, `/questionario/99`, `/questionario/abc`** (passo inválido ou fora do intervalo) não pode deixar tela branca — cai no passo 1. Teste na Tarefa 3.
2. **Pular pergunta obrigatória nunca é possível**: Avançar fica desabilitado enquanto o passo atual estiver incompleto, e Concluir só habilita quando as 6 respostas estiverem completas — mesmo se a pessoa entrar direto em `/questionario/6` pela URL sem passar pelas anteriores. Teste nas Tarefas 3 e 8.
3. **Voltar e Avançar preservam as respostas já dadas** — perder uma resposta ao navegar entre passos seria o pior resultado possível neste formulário. Teste na Tarefa 3.
4. **Erro da API ao concluir** (422 de validação, 429 do limite por IP, ou falha de rede) aparece em português na tela, não trava o botão em "Enviando..." para sempre, e não apaga as respostas já preenchidas. Teste na Tarefa 8.
5. **Trocar de cidade depois de já ter escolhido uma** não pode manter o perfil de clima (sugerido ou corrigido) da cidade antiga colado na nova escolha. Teste na Tarefa 3.

---

### Task 1: Tipos e regras de validação do questionário

**Files:**
- Create: `web/src/paginas/questionario/tipos.ts`, `web/src/paginas/questionario/validacao.ts`, `web/src/paginas/questionario/validacao.test.ts`

**Interfaces:**
- Consumes: `components["schemas"]` de `web/src/api/tipos.ts` (Etapa 5a).
- Produces: `RespostasParciais`, `PassoProps`, `TOTAL_PASSOS`, `passoValido(passo, respostas)`, `todosPassosValidos(respostas)` — usados por todas as tarefas seguintes.

Lógica pura, sem UI — a mais fácil de testar primeiro e a que trava o contrato de dados para o resto da etapa.

- [ ] **Step 1: Escrever o teste que falha**

`web/src/paginas/questionario/validacao.test.ts`:
```ts
import { describe, expect, it } from 'vitest'
import { passoValido, todosPassosValidos } from './validacao'
import type { RespostasParciais } from './tipos'

const completas: RespostasParciais = {
  municipio_codigo: 4106902,
  data_prevista: '2027-06-15',
  dias_entre_lavagens: 2,
  moradia: 'apartamento',
  tem_carro: true,
  orcamento: 'intermediario',
  primeiro_filho: true,
}

describe('passoValido', () => {
  it.each([1, 2, 3, 4, 5, 6])(
    'passo %i é válido quando todas as respostas estão presentes',
    (passo) => {
      expect(passoValido(passo, completas)).toBe(true)
    },
  )

  it('passo 1 é inválido sem cidade', () => {
    expect(passoValido(1, {})).toBe(false)
  })

  it('passo 4 é inválido só com moradia, sem resposta sobre carro', () => {
    expect(passoValido(4, { moradia: 'apartamento' })).toBe(false)
  })

  it('passo fora do intervalo 1-6 é inválido', () => {
    expect(passoValido(0, completas)).toBe(false)
    expect(passoValido(7, completas)).toBe(false)
  })
})

describe('todosPassosValidos', () => {
  it('é verdadeiro só quando as 6 respostas estão completas', () => {
    expect(todosPassosValidos(completas)).toBe(true)
    expect(todosPassosValidos({ ...completas, primeiro_filho: undefined })).toBe(false)
  })
})
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `docker compose run --rm web npm test`
Expected: FAIL — `./tipos` e `./validacao` não existem.

- [ ] **Step 3: Implementar `tipos.ts`**

`web/src/paginas/questionario/tipos.ts`:
```ts
import type { components } from '../../api/tipos'

export const TOTAL_PASSOS = 6

export interface RespostasParciais {
  municipio_codigo?: number
  municipio_nome?: string
  municipio_uf?: string
  perfil_sugerido?: components['schemas']['PerfilCodigo']
  correcao_perfil?: components['schemas']['PerfilCodigo']
  data_prevista?: string
  dias_entre_lavagens?: number
  moradia?: components['schemas']['Moradia']
  tem_carro?: boolean
  orcamento?: components['schemas']['Faixa']
  primeiro_filho?: boolean
}

export interface PassoProps {
  respostas: RespostasParciais
  onChange: (parcial: Partial<RespostasParciais>) => void
}
```

- [ ] **Step 4: Implementar `validacao.ts`**

`web/src/paginas/questionario/validacao.ts`:
```ts
import { TOTAL_PASSOS, type RespostasParciais } from './tipos'

export function passoValido(passo: number, r: RespostasParciais): boolean {
  switch (passo) {
    case 1:
      return r.municipio_codigo !== undefined
    case 2:
      return !!r.data_prevista
    case 3:
      return r.dias_entre_lavagens !== undefined
    case 4:
      return r.moradia !== undefined && r.tem_carro !== undefined
    case 5:
      return r.orcamento !== undefined
    case 6:
      return r.primeiro_filho !== undefined
    default:
      return false
  }
}

export function todosPassosValidos(r: RespostasParciais): boolean {
  for (let passo = 1; passo <= TOTAL_PASSOS; passo++) {
    if (!passoValido(passo, r)) return false
  }
  return true
}
```

- [ ] **Step 5: Rodar e ver passar**

Run: `docker compose run --rm web npm test`
Expected: todos os testes passam.

- [ ] **Step 6: Commit**

```bash
git add web/src/paginas/questionario/tipos.ts web/src/paginas/questionario/validacao.ts web/src/paginas/questionario/validacao.test.ts
git commit -m "feat(front): tipos e regras de validação das 6 respostas do questionário

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

### Task 2: Cliente de API tipado

**Files:**
- Create: `web/src/api/cliente.ts`, `web/src/api/cliente.test.ts`, `web/src/api/municipios.ts`, `web/src/api/municipios.test.ts`, `web/src/api/enxovais.ts`, `web/src/api/enxovais.test.ts`

**Interfaces:**
- Consumes: `components["schemas"]` de `web/src/api/tipos.ts`.
- Produces: `ErroApi` (classe, campos `codigo`, `status`, `message`), `apiFetch<T>(caminho, opcoes?)`, `buscarMunicipios(busca)`, `criarEnxoval(dados)` — usados pelo container e pelo Passo da cidade.

Nenhum componente ainda consome isto; os testes mockam `fetch` global (sem rede real).

- [ ] **Step 1: Escrever os testes que falham**

`web/src/api/cliente.test.ts`:
```ts
import { afterEach, describe, expect, it, vi } from 'vitest'
import { apiFetch, ErroApi } from './cliente'

describe('apiFetch', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('devolve o JSON da resposta quando a chamada dá certo', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({ ok: true }),
      }),
    )
    await expect(apiFetch('/saude')).resolves.toEqual({ ok: true })
  })

  it('lança ErroApi com o código e a mensagem do corpo quando a resposta não é ok', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: false,
        status: 422,
        json: async () => ({ erro: 'dados_invalidos', mensagem: 'Confira os dados.' }),
      }),
    )
    await expect(apiFetch('/enxovais')).rejects.toMatchObject({
      codigo: 'dados_invalidos',
      message: 'Confira os dados.',
      status: 422,
    })
  })

  it('lança ErroApi de sem_conexao quando o fetch falha', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('network')))
    await expect(apiFetch('/saude')).rejects.toMatchObject({ codigo: 'sem_conexao' })
    await expect(apiFetch('/saude')).rejects.toBeInstanceOf(ErroApi)
  })
})
```

`web/src/api/municipios.test.ts`:
```ts
import { describe, expect, it, vi } from 'vitest'
import { apiFetch } from './cliente'
import { buscarMunicipios } from './municipios'

vi.mock('./cliente', () => ({ apiFetch: vi.fn() }))

describe('buscarMunicipios', () => {
  it('busca com o termo codificado na URL', async () => {
    vi.mocked(apiFetch).mockResolvedValue([])
    await buscarMunicipios('são paulo')
    expect(apiFetch).toHaveBeenCalledWith('/municipios?busca=s%C3%A3o%20paulo')
  })
})
```

`web/src/api/enxovais.test.ts`:
```ts
import { describe, expect, it, vi } from 'vitest'
import { apiFetch } from './cliente'
import { criarEnxoval } from './enxovais'

vi.mock('./cliente', () => ({ apiFetch: vi.fn() }))

describe('criarEnxoval', () => {
  it('faz POST para /enxovais com o corpo em JSON', async () => {
    vi.mocked(apiFetch).mockResolvedValue({ id: 'abc' })
    const dados = {
      municipio_codigo: 1,
      data_prevista: '2027-06-15',
      dias_entre_lavagens: 2,
      moradia: 'apartamento' as const,
      tem_carro: true,
      orcamento: 'intermediario' as const,
      primeiro_filho: true,
    }
    await criarEnxoval(dados)
    expect(apiFetch).toHaveBeenCalledWith('/enxovais', {
      method: 'POST',
      body: JSON.stringify(dados),
    })
  })
})
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `docker compose run --rm web npm test`
Expected: FAIL — `./cliente`, `./municipios` e `./enxovais` não existem.

- [ ] **Step 3: Implementar `cliente.ts`**

`web/src/api/cliente.ts`:
```ts
export class ErroApi extends Error {
  codigo: string
  status: number

  constructor(codigo: string, mensagem: string, status: number) {
    super(mensagem)
    this.codigo = codigo
    this.status = status
  }
}

const BASE = '/api/v1'

export async function apiFetch<T>(caminho: string, opcoes?: RequestInit): Promise<T> {
  let resposta: Response
  try {
    resposta = await fetch(`${BASE}${caminho}`, {
      headers: { 'Content-Type': 'application/json', ...opcoes?.headers },
      ...opcoes,
    })
  } catch {
    throw new ErroApi(
      'sem_conexao',
      'Não foi possível conectar. Confira sua internet e tente de novo.',
      0,
    )
  }
  if (!resposta.ok) {
    const corpo = await resposta.json().catch(() => null)
    throw new ErroApi(
      corpo?.erro ?? 'erro_desconhecido',
      corpo?.mensagem ?? 'Algo deu errado. Tente de novo.',
      resposta.status,
    )
  }
  if (resposta.status === 204) return undefined as T
  return resposta.json() as Promise<T>
}
```

- [ ] **Step 4: Implementar `municipios.ts`**

`web/src/api/municipios.ts`:
```ts
import { apiFetch } from './cliente'
import type { components } from './tipos'

export type Municipio = components['schemas']['MunicipioBuscaSaida']

export function buscarMunicipios(busca: string): Promise<Municipio[]> {
  return apiFetch<Municipio[]>(`/municipios?busca=${encodeURIComponent(busca)}`)
}
```

- [ ] **Step 5: Implementar `enxovais.ts`**

`web/src/api/enxovais.ts`:
```ts
import { apiFetch } from './cliente'
import type { components } from './tipos'

export type RespostasEntrada = components['schemas']['RespostasEntrada']
export type EnxovalCriado = components['schemas']['EnxovalCriado']

export function criarEnxoval(dados: RespostasEntrada): Promise<EnxovalCriado> {
  return apiFetch<EnxovalCriado>('/enxovais', {
    method: 'POST',
    body: JSON.stringify(dados),
  })
}
```

- [ ] **Step 6: Rodar e ver passar**

Run: `docker compose run --rm web npm test`
Expected: todos os testes passam.

- [ ] **Step 7: Commit**

```bash
git add web/src/api/cliente.ts web/src/api/cliente.test.ts web/src/api/municipios.ts web/src/api/municipios.test.ts web/src/api/enxovais.ts web/src/api/enxovais.test.ts
git commit -m "feat(front): cliente de API tipado (erro uniforme, buscar cidade, criar enxoval)

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

### Task 3: Container do questionário + primitivas de UI + Passo 1 (Cidade)

**Files:**
- Create: `web/src/componentes/ui/button.tsx`, `web/src/componentes/ui/label.tsx`, `web/src/componentes/ui/input.tsx`, `web/src/hooks/useDebounce.ts`, `web/src/hooks/useDebounce.test.ts`, `web/src/paginas/questionario/BarraProgresso.tsx`, `web/src/paginas/questionario/BarraProgresso.test.tsx`, `web/src/paginas/questionario/PassoCidade.tsx`, `web/src/paginas/questionario/PassoCidade.test.tsx`, `web/src/paginas/Questionario.test.tsx`
- Modify: `web/src/paginas/Questionario.tsx` (substitui o placeholder da Etapa 5a pelo container de verdade)

**Interfaces:**
- Consumes: `PassoProps`, `RespostasParciais`, `TOTAL_PASSOS`, `passoValido`, `todosPassosValidos` (Tarefa 1); `buscarMunicipios`, `criarEnxoval`, `ErroApi` (Tarefa 2).
- Produces: `Button`, `Label`, `Input` (componentes genéricos, reusados pelas tarefas seguintes e por etapas futuras); `useDebounce` (hook genérico); `BarraProgresso`; `Questionario` (default export, já é o consumido por `App.tsx` desde a Etapa 5a — assinatura não muda). Os passos 2 a 6 entram como um placeholder `PassoEmConstrucao` dentro de `Questionario.tsx`, substituído um a um nas Tarefas 4 a 8.

`Button`/`Label`/`Input` são wrappers finos de estilo sobre elementos HTML nativos, sem lógica própria — cobertura vem dos testes das páginas que os usam (mesmo critério da Tarefa 3 da Etapa 5a para os tokens de tema: não há comportamento isolado para testar).

- [ ] **Step 1: Escrever o teste do `useDebounce` que falha**

`web/src/hooks/useDebounce.test.ts`:
```ts
import { act, renderHook } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { useDebounce } from './useDebounce'

describe('useDebounce', () => {
  it('só atualiza depois do atraso', () => {
    vi.useFakeTimers()
    const { result, rerender } = renderHook(({ valor }) => useDebounce(valor, 300), {
      initialProps: { valor: 'a' },
    })
    expect(result.current).toBe('a')

    rerender({ valor: 'ab' })
    expect(result.current).toBe('a')

    act(() => vi.advanceTimersByTime(300))
    expect(result.current).toBe('ab')

    vi.useRealTimers()
  })
})
```

Run: `docker compose run --rm web npm test`
Expected: FAIL — `./useDebounce` não existe.

- [ ] **Step 2: Implementar `useDebounce.ts`**

`web/src/hooks/useDebounce.ts`:
```ts
import { useEffect, useState } from 'react'

export function useDebounce<T>(valor: T, atrasoMs: number): T {
  const [debounced, setDebounced] = useState(valor)

  useEffect(() => {
    const id = setTimeout(() => setDebounced(valor), atrasoMs)
    return () => clearTimeout(id)
  }, [valor, atrasoMs])

  return debounced
}
```

Run: `docker compose run --rm web npm test`
Expected: passa.

- [ ] **Step 3: Implementar as primitivas de UI**

`web/src/componentes/ui/button.tsx`:
```tsx
import { type ButtonHTMLAttributes, forwardRef } from 'react'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '../../lib/utils'

const buttonVariants = cva(
  'inline-flex min-h-11 items-center justify-center rounded-xl px-5 py-3 text-sm font-medium transition-colors disabled:pointer-events-none disabled:opacity-50',
  {
    variants: {
      variant: {
        principal: 'bg-principal text-white hover:bg-principal/90',
        secundario: 'bg-principal-suave text-principal hover:bg-principal-suave/80',
      },
    },
    defaultVariants: { variant: 'principal' },
  },
)

export interface ButtonProps
  extends ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, ...props }, ref) => (
    <button ref={ref} className={cn(buttonVariants({ variant }), className)} {...props} />
  ),
)
Button.displayName = 'Button'
```

`web/src/componentes/ui/label.tsx`:
```tsx
import { type LabelHTMLAttributes } from 'react'
import { cn } from '../../lib/utils'

export function Label({ className, ...props }: LabelHTMLAttributes<HTMLLabelElement>) {
  return <label className={cn('text-sm font-medium text-texto', className)} {...props} />
}
```

`web/src/componentes/ui/input.tsx`:
```tsx
import { type InputHTMLAttributes, forwardRef } from 'react'
import { cn } from '../../lib/utils'

export const Input = forwardRef<HTMLInputElement, InputHTMLAttributes<HTMLInputElement>>(
  ({ className, ...props }, ref) => (
    <input
      ref={ref}
      className={cn(
        'min-h-11 w-full rounded-xl border border-principal-suave bg-superficie px-4 py-3 text-texto placeholder:text-texto-suave focus:outline focus:outline-2 focus:outline-principal',
        className,
      )}
      {...props}
    />
  ),
)
Input.displayName = 'Input'
```

- [ ] **Step 4: Escrever o teste da `BarraProgresso` que falha**

`web/src/paginas/questionario/BarraProgresso.test.tsx`:
```tsx
import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { BarraProgresso } from './BarraProgresso'

describe('BarraProgresso', () => {
  it('mostra o passo atual e o total', () => {
    render(<BarraProgresso passo={2} total={6} />)
    expect(screen.getByText('Passo 2 de 6')).toBeInTheDocument()
    expect(screen.getByRole('progressbar')).toHaveAttribute('aria-valuenow', '2')
  })
})
```

Run: `docker compose run --rm web npm test`
Expected: FAIL.

- [ ] **Step 5: Implementar `BarraProgresso.tsx`**

`web/src/paginas/questionario/BarraProgresso.tsx`:
```tsx
interface Props {
  passo: number
  total: number
}

export function BarraProgresso({ passo, total }: Props) {
  const percentual = Math.round((passo / total) * 100)
  return (
    <div role="progressbar" aria-valuenow={passo} aria-valuemin={1} aria-valuemax={total}>
      <p className="text-sm text-texto-suave">
        Passo {passo} de {total}
      </p>
      <div className="h-2 w-full rounded-full bg-principal-suave">
        <div className="h-2 rounded-full bg-principal" style={{ width: `${percentual}%` }} />
      </div>
    </div>
  )
}
```

Run: `docker compose run --rm web npm test`
Expected: passa.

- [ ] **Step 6: Escrever o teste do `PassoCidade` que falha**

`web/src/paginas/questionario/PassoCidade.test.tsx`:
```tsx
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { describe, expect, it, vi } from 'vitest'
import { buscarMunicipios } from '../../api/municipios'
import type { RespostasParciais } from './tipos'
import PassoCidade from './PassoCidade'

vi.mock('../../api/municipios')

function renderPasso(respostas: RespostasParciais, onChange = vi.fn()) {
  const queryClient = new QueryClient()
  render(
    <QueryClientProvider client={queryClient}>
      <PassoCidade respostas={respostas} onChange={onChange} />
    </QueryClientProvider>,
  )
  return { onChange }
}

describe('PassoCidade', () => {
  it('busca e lista cidades depois de digitar', async () => {
    vi.mocked(buscarMunicipios).mockResolvedValue([
      { codigo_ibge: 4106902, nome: 'Curitiba', uf: 'PR', perfil_sugerido: 'frio' },
    ])
    renderPasso({})

    fireEvent.change(screen.getByLabelText('Cidade'), { target: { value: 'curitiba' } })

    await waitFor(() => expect(screen.getByText('Curitiba - PR')).toBeInTheDocument())
  })

  it('escolhe a cidade e mostra o perfil sugerido', async () => {
    vi.mocked(buscarMunicipios).mockResolvedValue([
      { codigo_ibge: 4106902, nome: 'Curitiba', uf: 'PR', perfil_sugerido: 'frio' },
    ])
    const { onChange } = renderPasso({})

    fireEvent.change(screen.getByLabelText('Cidade'), { target: { value: 'curitiba' } })
    await waitFor(() => screen.getByText('Curitiba - PR'))
    fireEvent.click(screen.getByText('Curitiba - PR'))

    expect(onChange).toHaveBeenCalledWith(
      expect.objectContaining({ municipio_codigo: 4106902, perfil_sugerido: 'frio' }),
    )
    expect(screen.getByText(/Inverno frio/)).toBeInTheDocument()
  })

  it('permite corrigir o perfil sugerido', () => {
    const { onChange } = renderPasso({
      municipio_codigo: 4106902,
      municipio_nome: 'Curitiba',
      municipio_uf: 'PR',
      perfil_sugerido: 'frio',
    })

    fireEvent.click(screen.getByText('Quente o ano todo'))

    expect(onChange).toHaveBeenCalledWith({ correcao_perfil: 'quente' })
  })

  it('trocar o texto de busca depois de escolher uma cidade limpa a escolha e o perfil', () => {
    const { onChange } = renderPasso({
      municipio_codigo: 4106902,
      municipio_nome: 'Curitiba',
      municipio_uf: 'PR',
      perfil_sugerido: 'frio',
    })

    fireEvent.change(screen.getByLabelText('Cidade'), { target: { value: 'outra cidade' } })

    expect(onChange).toHaveBeenCalledWith({
      municipio_codigo: undefined,
      municipio_nome: undefined,
      municipio_uf: undefined,
      perfil_sugerido: undefined,
      correcao_perfil: undefined,
    })
  })
})
```

Run: `docker compose run --rm web npm test`
Expected: FAIL — `./PassoCidade` não existe.

- [ ] **Step 7: Implementar `PassoCidade.tsx`**

`web/src/paginas/questionario/PassoCidade.tsx`:
```tsx
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { buscarMunicipios, type Municipio } from '../../api/municipios'
import { useDebounce } from '../../hooks/useDebounce'
import { Button } from '../../componentes/ui/button'
import { Input } from '../../componentes/ui/input'
import { Label } from '../../componentes/ui/label'
import type { PassoProps } from './tipos'

const PERFIS = [
  { codigo: 'quente', nome: 'Quente o ano todo' },
  { codigo: 'moderado', nome: 'Inverno moderado' },
  { codigo: 'frio', nome: 'Inverno frio' },
] as const

export default function PassoCidade({ respostas, onChange }: PassoProps) {
  const cidadeEscolhida = respostas.municipio_codigo !== undefined
  const [busca, setBusca] = useState(
    respostas.municipio_nome ? `${respostas.municipio_nome} - ${respostas.municipio_uf}` : '',
  )
  const buscaDebounced = useDebounce(busca, 300)

  const { data: resultados = [] } = useQuery({
    queryKey: ['municipios', buscaDebounced],
    queryFn: () => buscarMunicipios(buscaDebounced),
    enabled: buscaDebounced.trim().length >= 2 && !cidadeEscolhida,
  })

  function escolher(m: Municipio) {
    setBusca(`${m.nome} - ${m.uf}`)
    onChange({
      municipio_codigo: m.codigo_ibge,
      municipio_nome: m.nome,
      municipio_uf: m.uf,
      perfil_sugerido: m.perfil_sugerido,
      correcao_perfil: undefined,
    })
  }

  function aoDigitar(valor: string) {
    setBusca(valor)
    if (cidadeEscolhida) {
      onChange({
        municipio_codigo: undefined,
        municipio_nome: undefined,
        municipio_uf: undefined,
        perfil_sugerido: undefined,
        correcao_perfil: undefined,
      })
    }
  }

  const perfilAtual = respostas.correcao_perfil ?? respostas.perfil_sugerido

  return (
    <div className="space-y-4">
      <h2 className="text-xl">Qual é a sua cidade?</h2>
      <Label htmlFor="cidade">Cidade</Label>
      <Input
        id="cidade"
        value={busca}
        onChange={(e) => aoDigitar(e.target.value)}
        placeholder="Digite o nome da cidade"
        autoComplete="off"
      />
      {!cidadeEscolhida && resultados.length > 0 && (
        <ul className="rounded-xl border border-principal-suave bg-superficie">
          {resultados.map((m) => (
            <li key={m.codigo_ibge}>
              <button
                type="button"
                className="min-h-11 w-full px-4 py-3 text-left hover:bg-principal-suave"
                onClick={() => escolher(m)}
              >
                {m.nome} - {m.uf}
              </button>
            </li>
          ))}
        </ul>
      )}
      {cidadeEscolhida && perfilAtual && (
        <div className="rounded-xl bg-principal-suave p-4">
          <p>Perfil de clima sugerido: {PERFIS.find((p) => p.codigo === perfilAtual)?.nome}</p>
          <p className="text-sm text-texto-suave">Não é isso? Escolha outro perfil:</p>
          <div className="flex flex-wrap gap-2">
            {PERFIS.map((p) => (
              <Button
                key={p.codigo}
                type="button"
                variant={perfilAtual === p.codigo ? 'principal' : 'secundario'}
                onClick={() => onChange({ correcao_perfil: p.codigo })}
              >
                {p.nome}
              </Button>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
```

Run: `docker compose run --rm web npm test`
Expected: passa.

- [ ] **Step 8: Escrever o teste do container que falha**

`web/src/paginas/Questionario.test.tsx`:
```tsx
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import { buscarMunicipios } from '../api/municipios'
import Questionario from './Questionario'

vi.mock('../api/municipios')
vi.mock('../api/enxovais')

function renderEm(caminho: string) {
  const queryClient = new QueryClient()
  render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[caminho]}>
        <Routes>
          <Route path="/questionario/:passo" element={<Questionario />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('Questionario', () => {
  it('mostra o passo 1 por padrão e desabilita Voltar', () => {
    renderEm('/questionario/1')
    expect(screen.getByText('Passo 1 de 6')).toBeInTheDocument()
    expect(screen.getByText('Voltar')).toBeDisabled()
  })

  it.each(['/questionario/0', '/questionario/99', '/questionario/abc'])(
    '%s cai no passo 1 em vez de tela branca',
    (caminho) => {
      renderEm(caminho)
      expect(screen.getByText('Passo 1 de 6')).toBeInTheDocument()
    },
  )

  it('Avançar fica desabilitado até escolher uma cidade, e habilita depois', async () => {
    vi.mocked(buscarMunicipios).mockResolvedValue([
      { codigo_ibge: 4106902, nome: 'Curitiba', uf: 'PR', perfil_sugerido: 'frio' },
    ])
    renderEm('/questionario/1')
    expect(screen.getByText('Avançar')).toBeDisabled()

    fireEvent.change(screen.getByLabelText('Cidade'), { target: { value: 'curitiba' } })
    await waitFor(() => screen.getByText('Curitiba - PR'))
    fireEvent.click(screen.getByText('Curitiba - PR'))

    expect(screen.getByText('Avançar')).toBeEnabled()
  })

  it('preserva a cidade escolhida ao avançar e voltar', async () => {
    vi.mocked(buscarMunicipios).mockResolvedValue([
      { codigo_ibge: 4106902, nome: 'Curitiba', uf: 'PR', perfil_sugerido: 'frio' },
    ])
    renderEm('/questionario/1')

    fireEvent.change(screen.getByLabelText('Cidade'), { target: { value: 'curitiba' } })
    await waitFor(() => screen.getByText('Curitiba - PR'))
    fireEvent.click(screen.getByText('Curitiba - PR'))
    fireEvent.click(screen.getByText('Avançar'))

    expect(screen.getByText('Passo 2 de 6')).toBeInTheDocument()

    fireEvent.click(screen.getByText('Voltar'))

    expect(screen.getByDisplayValue('Curitiba - PR')).toBeInTheDocument()
  })
})
```

Run: `docker compose run --rm web npm test`
Expected: FAIL — `Questionario.tsx` ainda é o placeholder da Etapa 5a (`<h1>Questionário</h1>` sem passos).

- [ ] **Step 9: Implementar o container `Questionario.tsx`**

`web/src/paginas/Questionario.tsx`:
```tsx
import { type ComponentType, useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { useNavigate, useParams } from 'react-router-dom'
import { Button } from '../componentes/ui/button'
import { ErroApi } from '../api/cliente'
import { criarEnxoval, type EnxovalCriado, type RespostasEntrada } from '../api/enxovais'
import { BarraProgresso } from './questionario/BarraProgresso'
import { todosPassosValidos, passoValido } from './questionario/validacao'
import { TOTAL_PASSOS, type PassoProps, type RespostasParciais } from './questionario/tipos'
import PassoCidade from './questionario/PassoCidade'

function PassoEmConstrucao() {
  return <p className="text-texto-suave">Em construção.</p>
}

const PASSOS: ComponentType<PassoProps>[] = [
  PassoCidade,
  PassoEmConstrucao,
  PassoEmConstrucao,
  PassoEmConstrucao,
  PassoEmConstrucao,
  PassoEmConstrucao,
]

function passoDaUrl(valor: string | undefined): number {
  const n = Number(valor)
  if (!Number.isInteger(n) || n < 1 || n > TOTAL_PASSOS) return 1
  return n
}

export default function Questionario() {
  const { passo: passoParam } = useParams()
  const passo = passoDaUrl(passoParam)
  const navigate = useNavigate()
  const [respostas, setRespostas] = useState<RespostasParciais>({})
  const [erro, setErro] = useState<string | null>(null)

  const mutacao = useMutation<EnxovalCriado, ErroApi, RespostasEntrada>({
    mutationFn: criarEnxoval,
    onSuccess: (criado) => navigate(`/enxoval/${criado.id}/planilha`),
    onError: (e) => setErro(e.message),
  })

  function atualizar(parcial: Partial<RespostasParciais>) {
    setErro(null)
    setRespostas((atual) => ({ ...atual, ...parcial }))
  }

  function avancar() {
    if (passo < TOTAL_PASSOS) navigate(`/questionario/${passo + 1}`)
  }

  function voltar() {
    if (passo > 1) navigate(`/questionario/${passo - 1}`)
  }

  function concluir() {
    if (!todosPassosValidos(respostas)) return
    mutacao.mutate({
      municipio_codigo: respostas.municipio_codigo!,
      data_prevista: respostas.data_prevista!,
      dias_entre_lavagens: respostas.dias_entre_lavagens!,
      moradia: respostas.moradia!,
      tem_carro: respostas.tem_carro!,
      orcamento: respostas.orcamento!,
      primeiro_filho: respostas.primeiro_filho!,
      correcao_perfil: respostas.correcao_perfil ?? null,
    })
  }

  const PassoAtual = PASSOS[passo - 1]
  const passoAtualValido = passoValido(passo, respostas)

  return (
    <div className="mx-auto max-w-md space-y-6 p-4">
      <h1 className="text-2xl">Questionário</h1>
      <BarraProgresso passo={passo} total={TOTAL_PASSOS} />
      <PassoAtual respostas={respostas} onChange={atualizar} />
      {erro && (
        <p role="alert" className="rounded-xl bg-alerta-fundo p-3 text-alerta-texto">
          {erro}
        </p>
      )}
      <div className="flex justify-between gap-3">
        <Button type="button" variant="secundario" onClick={voltar} disabled={passo === 1}>
          Voltar
        </Button>
        {passo < TOTAL_PASSOS ? (
          <Button type="button" onClick={avancar} disabled={!passoAtualValido}>
            Avançar
          </Button>
        ) : (
          <Button
            type="button"
            onClick={concluir}
            disabled={!todosPassosValidos(respostas) || mutacao.isPending}
          >
            {mutacao.isPending ? 'Enviando...' : 'Concluir'}
          </Button>
        )}
      </div>
    </div>
  )
}
```

- [ ] **Step 10: Rodar e ver passar**

Run: `docker compose run --rm web npm test`
Expected: todos os testes passam, incluindo o teste de fumaça de `App.test.tsx` da Etapa 5a (`/questionario/1` ainda mostra o texto "Questionário", agora como `<h1>` real).

- [ ] **Step 11: Verificar manualmente**

Run: `docker compose up -d --build web`
Abra `http://localhost:${WEB_PORT:-5180}/questionario/1`, digite uma cidade (ex.: "curitiba"), escolha o resultado, confira o perfil sugerido e o botão Avançar habilitando.

- [ ] **Step 12: Commit**

```bash
git add web/src/componentes web/src/hooks web/src/paginas/questionario web/src/paginas/Questionario.tsx web/src/paginas/Questionario.test.tsx
git commit -m "feat(front): container do questionário, barra de progresso e passo 1 (cidade)

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

### Task 4: Passo 2 — Data prevista

**Files:**
- Create: `web/src/paginas/questionario/PassoDataPrevista.tsx`, `web/src/paginas/questionario/PassoDataPrevista.test.tsx`
- Modify: `web/src/paginas/Questionario.tsx` (troca o 2º item de `PASSOS` por `PassoDataPrevista`)

**Interfaces:**
- Consumes: `PassoProps` (Tarefa 1), `Input`/`Label` (Tarefa 3).
- Produces: `PassoDataPrevista` (default export), consumido só pelo container.

- [ ] **Step 1: Escrever o teste que falha**

`web/src/paginas/questionario/PassoDataPrevista.test.tsx`:
```tsx
import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import PassoDataPrevista from './PassoDataPrevista'

describe('PassoDataPrevista', () => {
  it('chama onChange com a data escolhida', () => {
    const onChange = vi.fn()
    render(<PassoDataPrevista respostas={{}} onChange={onChange} />)

    fireEvent.change(screen.getByLabelText('Data prevista'), {
      target: { value: '2027-06-15' },
    })

    expect(onChange).toHaveBeenCalledWith({ data_prevista: '2027-06-15' })
  })

  it('mostra a data já escolhida ao reabrir o passo', () => {
    render(<PassoDataPrevista respostas={{ data_prevista: '2027-06-15' }} onChange={vi.fn()} />)
    expect(screen.getByLabelText('Data prevista')).toHaveValue('2027-06-15')
  })
})
```

Run: `docker compose run --rm web npm test`
Expected: FAIL.

- [ ] **Step 2: Implementar `PassoDataPrevista.tsx`**

`web/src/paginas/questionario/PassoDataPrevista.tsx`:
```tsx
import { Input } from '../../componentes/ui/input'
import { Label } from '../../componentes/ui/label'
import type { PassoProps } from './tipos'

export default function PassoDataPrevista({ respostas, onChange }: PassoProps) {
  return (
    <div className="space-y-4">
      <h2 className="text-xl">Qual é a data prevista do parto?</h2>
      <Label htmlFor="data-prevista">Data prevista</Label>
      <Input
        id="data-prevista"
        type="date"
        value={respostas.data_prevista ?? ''}
        onChange={(e) => onChange({ data_prevista: e.target.value || undefined })}
      />
    </div>
  )
}
```

- [ ] **Step 3: Rodar e ver passar**

Run: `docker compose run --rm web npm test`
Expected: passa.

- [ ] **Step 4: Ligar o passo 2 no container**

Em `web/src/paginas/Questionario.tsx`, importe `PassoDataPrevista` e troque o 2º item do array:
```ts
import PassoDataPrevista from './questionario/PassoDataPrevista'
```
```ts
const PASSOS: ComponentType<PassoProps>[] = [
  PassoCidade,
  PassoDataPrevista,
  PassoEmConstrucao,
  PassoEmConstrucao,
  PassoEmConstrucao,
  PassoEmConstrucao,
]
```

- [ ] **Step 5: Rodar a suíte inteira**

Run: `docker compose run --rm web npm test`
Expected: todos os testes passam (nenhum teste existente depende do passo 2).

- [ ] **Step 6: Commit**

```bash
git add web/src/paginas/questionario/PassoDataPrevista.tsx web/src/paginas/questionario/PassoDataPrevista.test.tsx web/src/paginas/Questionario.tsx
git commit -m "feat(front): passo 2 do questionário (data prevista)

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

### Task 5: Passo 3 — Frequência de lavagem + `GrupoOpcoes`

**Files:**
- Create: `web/src/paginas/questionario/GrupoOpcoes.tsx`, `web/src/paginas/questionario/GrupoOpcoes.test.tsx`, `web/src/paginas/questionario/PassoFrequenciaLavagem.tsx`, `web/src/paginas/questionario/PassoFrequenciaLavagem.test.tsx`
- Modify: `web/src/paginas/Questionario.tsx` (troca o 3º item de `PASSOS`)

**Interfaces:**
- Consumes: `PassoProps` (Tarefa 1).
- Produces: `GrupoOpcoes` (componente genérico de escolha única, reusado pelas Tarefas 6, 7 e 8), `PassoFrequenciaLavagem`.

- [ ] **Step 1: Escrever o teste do `GrupoOpcoes` que falha**

`web/src/paginas/questionario/GrupoOpcoes.test.tsx`:
```tsx
import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { GrupoOpcoes } from './GrupoOpcoes'

const OPCOES = [
  { valor: 'a', rotulo: 'Opção A' },
  { valor: 'b', rotulo: 'Opção B' },
] as const

describe('GrupoOpcoes', () => {
  it('marca a opção escolhida e chama onEscolher ao clicar', () => {
    const onEscolher = vi.fn()
    render(<GrupoOpcoes nome="Teste" opcoes={OPCOES} valor="a" onEscolher={onEscolher} />)

    expect(screen.getByText('Opção A')).toHaveAttribute('aria-checked', 'true')
    expect(screen.getByText('Opção B')).toHaveAttribute('aria-checked', 'false')

    fireEvent.click(screen.getByText('Opção B'))
    expect(onEscolher).toHaveBeenCalledWith('b')
  })
})
```

Run: `docker compose run --rm web npm test`
Expected: FAIL.

- [ ] **Step 2: Implementar `GrupoOpcoes.tsx`**

`web/src/paginas/questionario/GrupoOpcoes.tsx`:
```tsx
import { cn } from '../../lib/utils'

interface Opcao<T extends string> {
  valor: T
  rotulo: string
}

interface Props<T extends string> {
  nome: string
  opcoes: readonly Opcao<T>[]
  valor?: T
  onEscolher: (valor: T) => void
}

export function GrupoOpcoes<T extends string>({ nome, opcoes, valor, onEscolher }: Props<T>) {
  return (
    <div role="radiogroup" aria-label={nome} className="flex flex-col gap-2">
      {opcoes.map((opcao) => (
        <button
          key={opcao.valor}
          type="button"
          role="radio"
          aria-checked={valor === opcao.valor}
          onClick={() => onEscolher(opcao.valor)}
          className={cn(
            'min-h-11 rounded-xl border px-4 py-3 text-left',
            valor === opcao.valor
              ? 'border-principal bg-principal-suave text-principal'
              : 'border-principal-suave bg-superficie text-texto',
          )}
        >
          {opcao.rotulo}
        </button>
      ))}
    </div>
  )
}
```

- [ ] **Step 3: Rodar e ver passar**

Run: `docker compose run --rm web npm test`
Expected: passa.

- [ ] **Step 4: Escrever o teste do `PassoFrequenciaLavagem` que falha**

`web/src/paginas/questionario/PassoFrequenciaLavagem.test.tsx`:
```tsx
import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import PassoFrequenciaLavagem from './PassoFrequenciaLavagem'

describe('PassoFrequenciaLavagem', () => {
  it('converte a opção escolhida em dias_entre_lavagens', () => {
    const onChange = vi.fn()
    render(<PassoFrequenciaLavagem respostas={{}} onChange={onChange} />)

    fireEvent.click(screen.getByText('Lavo a cada 2 dias'))

    expect(onChange).toHaveBeenCalledWith({ dias_entre_lavagens: 2 })
  })

  it('marca a opção já escolhida ao reabrir o passo', () => {
    render(
      <PassoFrequenciaLavagem respostas={{ dias_entre_lavagens: 3 }} onChange={vi.fn()} />,
    )
    expect(screen.getByText('Lavo a cada 3 dias')).toHaveAttribute('aria-checked', 'true')
  })
})
```

Run: `docker compose run --rm web npm test`
Expected: FAIL.

- [ ] **Step 5: Implementar `PassoFrequenciaLavagem.tsx`**

`web/src/paginas/questionario/PassoFrequenciaLavagem.tsx`:
```tsx
import { GrupoOpcoes } from './GrupoOpcoes'
import type { PassoProps } from './tipos'

const OPCOES = [
  { valor: '1', rotulo: 'Lavo todo dia' },
  { valor: '2', rotulo: 'Lavo a cada 2 dias' },
  { valor: '3', rotulo: 'Lavo a cada 3 dias' },
  { valor: '4', rotulo: 'Lavo cerca de 2 vezes por semana' },
] as const

export default function PassoFrequenciaLavagem({ respostas, onChange }: PassoProps) {
  return (
    <div className="space-y-4">
      <h2 className="text-xl">Com que frequência você lava roupa?</h2>
      <GrupoOpcoes
        nome="Frequência de lavar roupa"
        opcoes={OPCOES}
        valor={
          respostas.dias_entre_lavagens !== undefined
            ? String(respostas.dias_entre_lavagens)
            : undefined
        }
        onEscolher={(v) => onChange({ dias_entre_lavagens: Number(v) })}
      />
    </div>
  )
}
```

- [ ] **Step 6: Rodar e ver passar**

Run: `docker compose run --rm web npm test`
Expected: passa.

- [ ] **Step 7: Ligar o passo 3 no container**

Em `web/src/paginas/Questionario.tsx`:
```ts
import PassoFrequenciaLavagem from './questionario/PassoFrequenciaLavagem'
```
```ts
const PASSOS: ComponentType<PassoProps>[] = [
  PassoCidade,
  PassoDataPrevista,
  PassoFrequenciaLavagem,
  PassoEmConstrucao,
  PassoEmConstrucao,
  PassoEmConstrucao,
]
```

- [ ] **Step 8: Rodar a suíte inteira e commit**

Run: `docker compose run --rm web npm test`
Expected: todos os testes passam.

```bash
git add web/src/paginas/questionario/GrupoOpcoes.tsx web/src/paginas/questionario/GrupoOpcoes.test.tsx web/src/paginas/questionario/PassoFrequenciaLavagem.tsx web/src/paginas/questionario/PassoFrequenciaLavagem.test.tsx web/src/paginas/Questionario.tsx
git commit -m "feat(front): passo 3 do questionário (frequência de lavagem) e grupo de opções reusável

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

### Task 6: Passo 4 — Moradia e carro

**Files:**
- Create: `web/src/paginas/questionario/PassoMoradia.tsx`, `web/src/paginas/questionario/PassoMoradia.test.tsx`
- Modify: `web/src/paginas/Questionario.tsx` (troca o 4º item de `PASSOS`)

**Interfaces:**
- Consumes: `GrupoOpcoes` (Tarefa 5), `PassoProps` (Tarefa 1).
- Produces: `PassoMoradia`.

- [ ] **Step 1: Escrever o teste que falha**

`web/src/paginas/questionario/PassoMoradia.test.tsx`:
```tsx
import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import PassoMoradia from './PassoMoradia'

describe('PassoMoradia', () => {
  it('registra moradia e carro separadamente', () => {
    const onChange = vi.fn()
    render(<PassoMoradia respostas={{}} onChange={onChange} />)

    fireEvent.click(screen.getByText('Casa com escada'))
    expect(onChange).toHaveBeenCalledWith({ moradia: 'casa_com_escada' })

    fireEvent.click(screen.getByText('Sim'))
    expect(onChange).toHaveBeenCalledWith({ tem_carro: true })
  })

  it('mostra Não para tem_carro quando a resposta já é falsa', () => {
    render(<PassoMoradia respostas={{ tem_carro: false }} onChange={vi.fn()} />)
    expect(screen.getByText('Não')).toHaveAttribute('aria-checked', 'true')
  })
})
```

Run: `docker compose run --rm web npm test`
Expected: FAIL.

- [ ] **Step 2: Implementar `PassoMoradia.tsx`**

`web/src/paginas/questionario/PassoMoradia.tsx`:
```tsx
import { GrupoOpcoes } from './GrupoOpcoes'
import type { PassoProps } from './tipos'

const OPCOES_MORADIA = [
  { valor: 'apartamento', rotulo: 'Apartamento' },
  { valor: 'casa_sem_escada', rotulo: 'Casa sem escada' },
  { valor: 'casa_com_escada', rotulo: 'Casa com escada' },
] as const

const OPCOES_CARRO = [
  { valor: 'sim', rotulo: 'Sim' },
  { valor: 'nao', rotulo: 'Não' },
] as const

export default function PassoMoradia({ respostas, onChange }: PassoProps) {
  return (
    <div className="space-y-6">
      <div className="space-y-4">
        <h2 className="text-xl">Onde vocês moram?</h2>
        <GrupoOpcoes
          nome="Moradia"
          opcoes={OPCOES_MORADIA}
          valor={respostas.moradia}
          onEscolher={(v) => onChange({ moradia: v })}
        />
      </div>
      <div className="space-y-4">
        <h2 className="text-xl">Vocês têm carro?</h2>
        <GrupoOpcoes
          nome="Tem carro"
          opcoes={OPCOES_CARRO}
          valor={respostas.tem_carro === undefined ? undefined : respostas.tem_carro ? 'sim' : 'nao'}
          onEscolher={(v) => onChange({ tem_carro: v === 'sim' })}
        />
      </div>
    </div>
  )
}
```

- [ ] **Step 3: Rodar e ver passar**

Run: `docker compose run --rm web npm test`
Expected: passa.

- [ ] **Step 4: Ligar o passo 4 no container**

Em `web/src/paginas/Questionario.tsx`:
```ts
import PassoMoradia from './questionario/PassoMoradia'
```
```ts
const PASSOS: ComponentType<PassoProps>[] = [
  PassoCidade,
  PassoDataPrevista,
  PassoFrequenciaLavagem,
  PassoMoradia,
  PassoEmConstrucao,
  PassoEmConstrucao,
]
```

- [ ] **Step 5: Rodar a suíte inteira e commit**

Run: `docker compose run --rm web npm test`
Expected: todos os testes passam.

```bash
git add web/src/paginas/questionario/PassoMoradia.tsx web/src/paginas/questionario/PassoMoradia.test.tsx web/src/paginas/Questionario.tsx
git commit -m "feat(front): passo 4 do questionário (moradia e carro)

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

### Task 7: Passo 5 — Orçamento

**Files:**
- Create: `web/src/paginas/questionario/PassoOrcamento.tsx`, `web/src/paginas/questionario/PassoOrcamento.test.tsx`
- Modify: `web/src/paginas/Questionario.tsx` (troca o 5º item de `PASSOS`)

**Interfaces:**
- Consumes: `GrupoOpcoes` (Tarefa 5), `PassoProps` (Tarefa 1).
- Produces: `PassoOrcamento`.

- [ ] **Step 1: Escrever o teste que falha**

`web/src/paginas/questionario/PassoOrcamento.test.tsx`:
```tsx
import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import PassoOrcamento from './PassoOrcamento'

describe('PassoOrcamento', () => {
  it('registra a faixa de orçamento escolhida', () => {
    const onChange = vi.fn()
    render(<PassoOrcamento respostas={{}} onChange={onChange} />)

    fireEvent.click(screen.getByText('Investir mais'))

    expect(onChange).toHaveBeenCalledWith({ orcamento: 'investir' })
  })
})
```

Run: `docker compose run --rm web npm test`
Expected: FAIL.

- [ ] **Step 2: Implementar `PassoOrcamento.tsx`**

`web/src/paginas/questionario/PassoOrcamento.tsx`:
```tsx
import { GrupoOpcoes } from './GrupoOpcoes'
import type { PassoProps } from './tipos'

const OPCOES = [
  { valor: 'economico', rotulo: 'Econômico' },
  { valor: 'intermediario', rotulo: 'Intermediário' },
  { valor: 'investir', rotulo: 'Investir mais' },
] as const

export default function PassoOrcamento({ respostas, onChange }: PassoProps) {
  return (
    <div className="space-y-4">
      <h2 className="text-xl">Qual orçamento vocês têm em mente?</h2>
      <GrupoOpcoes
        nome="Orçamento"
        opcoes={OPCOES}
        valor={respostas.orcamento}
        onEscolher={(v) => onChange({ orcamento: v })}
      />
    </div>
  )
}
```

- [ ] **Step 3: Rodar e ver passar**

Run: `docker compose run --rm web npm test`
Expected: passa.

- [ ] **Step 4: Ligar o passo 5 no container**

Em `web/src/paginas/Questionario.tsx`:
```ts
import PassoOrcamento from './questionario/PassoOrcamento'
```
```ts
const PASSOS: ComponentType<PassoProps>[] = [
  PassoCidade,
  PassoDataPrevista,
  PassoFrequenciaLavagem,
  PassoMoradia,
  PassoOrcamento,
  PassoEmConstrucao,
]
```

- [ ] **Step 5: Rodar a suíte inteira e commit**

Run: `docker compose run --rm web npm test`
Expected: todos os testes passam.

```bash
git add web/src/paginas/questionario/PassoOrcamento.tsx web/src/paginas/questionario/PassoOrcamento.test.tsx web/src/paginas/Questionario.tsx
git commit -m "feat(front): passo 5 do questionário (orçamento)

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

### Task 8: Passo 6 — Primeiro filho, envio e fim a fim

**Files:**
- Create: `web/src/paginas/questionario/PassoPrimeiroFilho.tsx`, `web/src/paginas/questionario/PassoPrimeiroFilho.test.tsx`
- Modify: `web/src/paginas/Questionario.tsx` (troca o 6º item de `PASSOS`; remove `PassoEmConstrucao`, que fica sem uso), `web/src/paginas/Questionario.test.tsx` (acrescenta os testes de fim a fim)

**Interfaces:**
- Consumes: `GrupoOpcoes` (Tarefa 5), `criarEnxoval`/`ErroApi` (Tarefa 2), `todosPassosValidos` (Tarefa 1).
- Produces: `PassoPrimeiroFilho`; fecha o fluxo completo do questionário.

- [ ] **Step 1: Escrever o teste do `PassoPrimeiroFilho` que falha**

`web/src/paginas/questionario/PassoPrimeiroFilho.test.tsx`:
```tsx
import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import PassoPrimeiroFilho from './PassoPrimeiroFilho'

describe('PassoPrimeiroFilho', () => {
  it('registra a resposta como booleano', () => {
    const onChange = vi.fn()
    render(<PassoPrimeiroFilho respostas={{}} onChange={onChange} />)

    fireEvent.click(screen.getByText('Não'))

    expect(onChange).toHaveBeenCalledWith({ primeiro_filho: false })
  })
})
```

Run: `docker compose run --rm web npm test`
Expected: FAIL.

- [ ] **Step 2: Implementar `PassoPrimeiroFilho.tsx`**

`web/src/paginas/questionario/PassoPrimeiroFilho.tsx`:
```tsx
import { GrupoOpcoes } from './GrupoOpcoes'
import type { PassoProps } from './tipos'

const OPCOES = [
  { valor: 'sim', rotulo: 'Sim' },
  { valor: 'nao', rotulo: 'Não' },
] as const

export default function PassoPrimeiroFilho({ respostas, onChange }: PassoProps) {
  return (
    <div className="space-y-4">
      <h2 className="text-xl">Este é o primeiro filho?</h2>
      <GrupoOpcoes
        nome="Primeiro filho"
        opcoes={OPCOES}
        valor={
          respostas.primeiro_filho === undefined
            ? undefined
            : respostas.primeiro_filho
              ? 'sim'
              : 'nao'
        }
        onEscolher={(v) => onChange({ primeiro_filho: v === 'sim' })}
      />
    </div>
  )
}
```

- [ ] **Step 3: Rodar e ver passar**

Run: `docker compose run --rm web npm test`
Expected: passa.

- [ ] **Step 4: Ligar o passo 6 e remover o placeholder**

Em `web/src/paginas/Questionario.tsx`, importe `PassoPrimeiroFilho`, troque o 6º item e apague a função `PassoEmConstrucao` (não é mais usada):
```ts
import PassoPrimeiroFilho from './questionario/PassoPrimeiroFilho'
```
```ts
const PASSOS: ComponentType<PassoProps>[] = [
  PassoCidade,
  PassoDataPrevista,
  PassoFrequenciaLavagem,
  PassoMoradia,
  PassoOrcamento,
  PassoPrimeiroFilho,
]
```

- [ ] **Step 5: Escrever os testes de fim a fim que falham**

Acrescente em `web/src/paginas/Questionario.test.tsx` (topo do arquivo, com os outros imports e mocks):
```tsx
import { criarEnxoval } from '../api/enxovais'
import { ErroApi } from '../api/cliente'
```
```ts
const { mockNavigate } = vi.hoisted(() => ({ mockNavigate: vi.fn() }))

vi.mock('react-router-dom', async () => {
  const real = await vi.importActual<typeof import('react-router-dom')>('react-router-dom')
  return { ...real, useNavigate: () => mockNavigate }
})
```

E ao final do `describe('Questionario', ...)`:
```tsx
  it('completa as 6 perguntas e cria o enxoval', async () => {
    vi.mocked(buscarMunicipios).mockResolvedValue([
      { codigo_ibge: 4106902, nome: 'Curitiba', uf: 'PR', perfil_sugerido: 'frio' },
    ])
    vi.mocked(criarEnxoval).mockResolvedValue({ id: 'id-teste' })
    renderEm('/questionario/1')

    fireEvent.change(screen.getByLabelText('Cidade'), { target: { value: 'curitiba' } })
    await waitFor(() => screen.getByText('Curitiba - PR'))
    fireEvent.click(screen.getByText('Curitiba - PR'))
    fireEvent.click(screen.getByText('Avançar'))

    fireEvent.change(screen.getByLabelText('Data prevista'), { target: { value: '2027-06-15' } })
    fireEvent.click(screen.getByText('Avançar'))

    fireEvent.click(screen.getByText('Lavo a cada 2 dias'))
    fireEvent.click(screen.getByText('Avançar'))

    fireEvent.click(screen.getByText('Apartamento'))
    fireEvent.click(screen.getByText('Sim'))
    fireEvent.click(screen.getByText('Avançar'))

    fireEvent.click(screen.getByText('Intermediário'))
    fireEvent.click(screen.getByText('Avançar'))

    fireEvent.click(screen.getByText('Sim'))
    fireEvent.click(screen.getByText('Concluir'))

    await waitFor(() =>
      expect(criarEnxoval).toHaveBeenCalledWith({
        municipio_codigo: 4106902,
        data_prevista: '2027-06-15',
        dias_entre_lavagens: 2,
        moradia: 'apartamento',
        tem_carro: true,
        orcamento: 'intermediario',
        primeiro_filho: true,
        correcao_perfil: null,
      }),
    )
    await waitFor(() => expect(mockNavigate).toHaveBeenCalledWith('/enxoval/id-teste/planilha'))
  })

  it('mostra o erro da API e mantém as respostas quando falha ao concluir', async () => {
    vi.mocked(buscarMunicipios).mockResolvedValue([
      { codigo_ibge: 4106902, nome: 'Curitiba', uf: 'PR', perfil_sugerido: 'frio' },
    ])
    vi.mocked(criarEnxoval).mockRejectedValue(
      new ErroApi('dados_invalidos', 'Confira os dados enviados.', 422),
    )
    renderEm('/questionario/1')

    fireEvent.change(screen.getByLabelText('Cidade'), { target: { value: 'curitiba' } })
    await waitFor(() => screen.getByText('Curitiba - PR'))
    fireEvent.click(screen.getByText('Curitiba - PR'))
    fireEvent.click(screen.getByText('Avançar'))
    fireEvent.change(screen.getByLabelText('Data prevista'), { target: { value: '2027-06-15' } })
    fireEvent.click(screen.getByText('Avançar'))
    fireEvent.click(screen.getByText('Lavo a cada 2 dias'))
    fireEvent.click(screen.getByText('Avançar'))
    fireEvent.click(screen.getByText('Apartamento'))
    fireEvent.click(screen.getByText('Sim'))
    fireEvent.click(screen.getByText('Avançar'))
    fireEvent.click(screen.getByText('Intermediário'))
    fireEvent.click(screen.getByText('Avançar'))
    fireEvent.click(screen.getByText('Sim'))
    fireEvent.click(screen.getByText('Concluir'))

    await waitFor(() =>
      expect(screen.getByRole('alert')).toHaveTextContent('Confira os dados enviados.'),
    )
    expect(screen.getByText('Concluir')).toBeEnabled()
    expect(screen.getByText('Passo 6 de 6')).toBeInTheDocument()
  })

  it('entrar direto no passo 6 pela URL sem completar os passos anteriores mantém Concluir desabilitado', () => {
    renderEm('/questionario/6')
    expect(screen.getByText('Passo 6 de 6')).toBeInTheDocument()

    fireEvent.click(screen.getByText('Sim'))

    expect(screen.getByText('Concluir')).toBeDisabled()
  })
```

Run: `docker compose run --rm web npm test`
Expected: FAIL até o Step 4 estar completo — depois disso, só os dois testes novos acima ainda podem falhar se algum texto de botão não bater exatamente; confira contra o Step 2 desta tarefa e as Tarefas 5-7.

- [ ] **Step 6: Rodar a suíte inteira e ver passar**

Run: `docker compose run --rm web npm test`
Expected: todos os testes passam.

- [ ] **Step 7: Verificar o build e o typecheck**

Run:
```bash
docker compose run --rm web npm run typecheck
docker compose run --rm web npm run build
```
Expected: os dois rodam sem erro (confirma que `PassoEmConstrucao` foi mesmo removido sem deixar import morto).

- [ ] **Step 8: Verificar manualmente o fluxo completo**

Com `docker compose up -d --build` (api + web), abra `http://localhost:${WEB_PORT:-5180}/questionario/1` e complete as 6 perguntas. Confirme que o navegador termina em `/enxoval/<uuid>/planilha` (ainda a página placeholder "Planilha" da Etapa 5a) e que `GET http://localhost:${API_PORT:-8010}/api/v1/enxovais/<uuid>` devolve o enxoval criado.

- [ ] **Step 9: Commit**

```bash
git add web/src/paginas/questionario/PassoPrimeiroFilho.tsx web/src/paginas/questionario/PassoPrimeiroFilho.test.tsx web/src/paginas/Questionario.tsx web/src/paginas/Questionario.test.tsx
git commit -m "feat(front): passo 6 do questionário (primeiro filho), envio e navegação final

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

## Ao terminar a Etapa 5b

- `docker compose run --rm web npm test` passa por inteiro.
- `docker compose run --rm web npm run build` e `npm run typecheck` compilam sem erro.
- O fluxo `/` → `/questionario/1..6` → `POST /enxovais` → `/enxoval/:id/planilha` funciona de ponta a ponta no navegador.
- Próximo passo: plano da **Etapa 5c (planilha)**, que consome `GET /enxovais/{id}` e os contadores otimistas sobre as linhas calculadas.
