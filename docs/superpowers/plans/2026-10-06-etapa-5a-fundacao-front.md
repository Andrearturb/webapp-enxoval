# Etapa 5a — Fundação do front · Plano de implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Criar o esqueleto do front (Vite + React + TypeScript), rodando dentro do `docker compose` como o serviço `web`, com tema (cores e fontes da spec), as 7 rotas da Etapa 5 como páginas vazias, o provider do TanStack Query e o cliente gerado da API — tudo sem conteúdo real de tela, que entra nas sub-etapas 5b–5e.

**Architecture:** SPA servida pelo próprio servidor de desenvolvimento do Vite, que faz proxy de `/api` para o container `api` (sem Caddy nesta etapa — Caddy só existe no ciclo de deploy). Tailwind CSS v4 (plugin do Vite, sem `tailwind.config.js` nem PostCSS separados) define os tokens de cor e fonte da seção 6 da spec como utilitários (`bg-fundo`, `text-texto`, `font-titulo` etc.). As peças do shadcn/ui (`components.json`, `cn()`) são escritas à mão nesta etapa — nenhum componente de UI é instalado ainda, só a base que os componentes das sub-etapas seguintes vão precisar.

**Tech Stack:** Vite, React 18+, TypeScript, Tailwind CSS v4 (`@tailwindcss/vite`), React Router (API declarativa, sem loaders), TanStack Query, Fontsource (`@fontsource/lora`, `@fontsource/dm-sans`), openapi-typescript, Vitest + Testing Library + jsdom. Node 22 (imagem `node:22-alpine`).

**Spec:** [`docs/superpowers/specs/2026-10-05-enxoval-inteligente-design.md`](../specs/2026-10-05-enxoval-inteligente-design.md) (seções 2, 6 e 10)

## Global Constraints

- Mobile first, acessível (contraste AA, alvos de toque ≥ 44 px), todo texto visível ao usuário em português do Brasil (regra permanente do projeto, spec seção 1). Nesta etapa isso vale para os textos dos placeholders de página.
- Caddy **não entra em nenhuma sub-etapa de front** — só no ciclo de deploy. Em dev, o Vite fala direto com a API via proxy do próprio `vite.config.ts`.
- Os tipos da API (`src/api/tipos.ts`) são **gerados por um script manual e commitados** — nunca gerados a cada build. Build e testes não podem depender da API estar no ar.
- Fontes **auto-hospedadas** (Fontsource, arquivos no bundle) — nenhuma requisição a CDN externo em tempo de execução.
- Segredos só em variáveis de ambiente (regra já em vigor no projeto; nesta etapa não há segredo novo, mas nenhum passo pode introduzir um).
- Testes: `docker compose run --rm web npm test`. Build de produção: `docker compose run --rm web npm run build` (precisa compilar limpo, mesmo sem uso até o deploy).

## Review Focus

1. **`docker compose up -d --build web` sobe sem erro e `http://localhost:5174` mostra algo no navegador** (não uma tela branca). Nenhum teste automatizado prova isso — jsdom não é um navegador real. Verificação manual na Tarefa 1.
2. **Uma rota totalmente desconhecida** (ex.: `/isso-nao-existe`) não pode deixar a tela branca ou travada — precisa de uma rota de fallback "página não encontrada". Teste na Tarefa 4.
3. **`/enxoval/<qualquer-coisa>/guia/<qualquer-coisa>`** cai na página de guia do item com **qualquer** valor de `:id` e `:item` — o roteador não pode exigir um item ou enxoval conhecido ainda (isso só chega na 5d). Teste na Tarefa 4.
4. **`npm run build` (build de produção) compila sem erro de tipos**, mesmo que não seja usado até o deploy — garante que a 5a não deixa a árvore de tipos quebrada para as sub-etapas seguintes. Verificação na Tarefa 3 e novamente na Tarefa 5.
5. **Editar um arquivo em `web/src` com os containers no ar reaparece no navegador via hot reload** (bind mount + Vite funcionando, incluindo no Windows). Nenhum teste automatizado prova isso. Verificação manual na Tarefa 1.

---

### Task 1: Scaffold do Vite, Tailwind e o serviço `web` no Docker

**Files:**
- Create: `web/` (gerado pelo scaffold do Vite), `web/Dockerfile`, `web/.dockerignore`, `web/.gitignore`
- Modify: `web/vite.config.ts`, `web/src/index.css`, `web/package.json` (script `dev`)
- Modify: `docker-compose.yml`, `docker-compose.override.yml`

**Interfaces:**
- Produces: serviço `web` acessível em `http://localhost:5174` com hot reload; `web/vite.config.ts` com `server.proxy["/api"]` apontando para `http://api:8000`.

Esta tarefa é só scaffold/configuração — não há comportamento para testar com antecedência (a skill de TDD lista arquivos de configuração como exceção). A prova é rodar o container e ver a página no navegador.

- [ ] **Step 1: Gerar o scaffold do Vite num container Node descartável**

Não precisa de Node instalado no host — roda dentro de um container que some depois:

Run (na raiz do repositório):
```bash
docker run --rm -v "$(pwd)/web:/app" -w /app node:22-alpine \
  npm create vite@latest . -- --template react-ts
```
Expected: cria `web/package.json`, `web/vite.config.ts`, `web/tsconfig.json`, `web/index.html`, `web/src/main.tsx`, `web/src/App.tsx`, `web/src/index.css`, `web/public/`.

- [ ] **Step 2: Instalar as dependências do scaffold e as do nosso stack**

```bash
docker run --rm -v "$(pwd)/web:/app" -w /app node:22-alpine sh -c \
  "npm install && npm install tailwindcss @tailwindcss/vite react-router-dom @tanstack/react-query @fontsource/lora @fontsource/dm-sans"
```
Expected: `web/node_modules/` e `web/package-lock.json` aparecem; `web/package.json` ganha `tailwindcss`, `@tailwindcss/vite`, `react-router-dom`, `@tanstack/react-query`, `@fontsource/lora`, `@fontsource/dm-sans`.

- [ ] **Step 3: `web/Dockerfile`**

```dockerfile
FROM node:22-alpine
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm install
COPY . .
EXPOSE 5173
CMD ["npm", "run", "dev"]
```

- [ ] **Step 4: `web/.dockerignore`**

```
node_modules
dist
.git
```

- [ ] **Step 5: `web/.gitignore`**

```
node_modules
dist
*.local
```

- [ ] **Step 6: Ligar o Tailwind v4 no `web/vite.config.ts`**

Substitua o conteúdo gerado pelo scaffold por:
```ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    watch: {
      // O Docker Desktop no Windows não propaga eventos de inotify para
      // bind mounts; sem polling, o Vite nunca percebe um arquivo mudado.
      usePolling: true,
    },
    proxy: {
      '/api': {
        target: 'http://api:8000',
        changeOrigin: true,
      },
    },
  },
})
```
(O bloco `test` do Vitest entra na Tarefa 2, quando o Vitest for instalado.)

- [ ] **Step 7: Substituir `web/src/index.css`**

O scaffold do Vite cria um CSS de demonstração; troque todo o conteúdo por:
```css
@import "tailwindcss";
```
(Os tokens de tema entram na Tarefa 3.)

- [ ] **Step 8: Script `dev` ouvindo em todas as interfaces**

Em `web/package.json`, no bloco `"scripts"`, troque:
```json
"dev": "vite",
```
por:
```json
"dev": "vite --host 0.0.0.0",
```
(Sem isso, o Vite só escuta em `localhost` dentro do container, inacessível do host.)

- [ ] **Step 9: Acrescentar o serviço `web` ao `docker-compose.yml`**

Depois do serviço `api`, antes de `volumes:`:
```yaml
  web:
    build: ./web
    restart: unless-stopped
    depends_on:
      - api
```

No bloco `volumes:` do final do arquivo (que já tem `dados_db`), acrescente:
```yaml
  node_modules_web:
```
(Volume **nomeado**, não anônimo — um volume anônimo leva um nome novo e vazio a cada `docker compose run`, então um `npm install` feito num `run` não apareceria no `run` seguinte. Um volume nomeado é o mesmo em toda chamada, igual a `dados_db`.)

- [ ] **Step 10: Acrescentar o `web` ao `docker-compose.override.yml`**

No bloco `services:`, depois de `api:`:
```yaml
  web:
    volumes:
      - ./web:/app
      - node_modules_web:/app/node_modules
    ports:
      - "127.0.0.1:5174:5173"
    command: npm run dev
```
O volume `node_modules_web` impede que o bind mount de `./web:/app` esconda o `node_modules` instalado dentro da imagem — essencial no Windows, onde um `node_modules` do host (se existir) traria binários da plataforma errada. Por ser nomeado (não anônimo), `docker compose run --rm web npm install <pacote>` nas próximas tarefas grava nele, e o próximo `run` vê o pacote instalado.

- [ ] **Step 11: Subir e verificar manualmente**

Run:
```bash
docker compose up -d --build web
```
Expected: os serviços `db`, `api` e `web` sobem sem erro.

Abra `http://localhost:5174` no navegador.
Expected: a página padrão do scaffold do Vite aparece (logos do Vite/React, contador).

Edite `web/src/App.tsx` (qualquer mudança de texto visível) com os containers no ar.
Expected: a mudança aparece no navegador em 1–2 segundos, sem recarregar a página manualmente (hot reload).

- [ ] **Step 12: Commit**

```bash
git add web docker-compose.yml docker-compose.override.yml
git commit -m "feat(front): scaffold do Vite+React+TS, Tailwind v4 e o serviço web no compose

Co-Authored-By: <modelo da sessão> <noreply@anthropic.com>"
```

---

### Task 2: Vitest, Testing Library e a primeira página (placeholder de Início)

**Files:**
- Modify: `web/vite.config.ts` (bloco `test`), `web/package.json` (scripts `test`, `test:watch`)
- Create: `web/src/tests/setup.ts`, `web/src/paginas/Inicio.tsx`, `web/src/paginas/Inicio.test.tsx`

**Interfaces:**
- Consumes: nada das tarefas anteriores além do projeto scaffolded.
- Produces: `Inicio` (componente default export de `web/src/paginas/Inicio.tsx`), usado pela Tarefa 4 no roteamento.

- [ ] **Step 1: Instalar o Vitest e a Testing Library**

```bash
docker compose run --rm web npm install -D vitest jsdom @testing-library/react @testing-library/jest-dom
```

- [ ] **Step 2: Escrever o teste que falha**

`web/src/paginas/Inicio.test.tsx`:
```tsx
import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import Inicio from './Inicio'

describe('Inicio', () => {
  it('mostra o título da página', () => {
    render(<Inicio />)
    expect(screen.getByText('Início')).toBeInTheDocument()
  })
})
```

- [ ] **Step 3: Configurar o Vitest**

`web/src/tests/setup.ts`:
```ts
import '@testing-library/jest-dom/vitest'
```

Em `web/vite.config.ts`, acrescente o bloco `test` ao objeto de configuração (depois de `server`):
```ts
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/tests/setup.ts'],
  },
```
No topo do arquivo, acrescente a referência de tipos do Vitest (linha 1, antes dos imports):
```ts
/// <reference types="vitest/config" />
```

Em `web/package.json`, no bloco `"scripts"`:
```json
"test": "vitest run",
"test:watch": "vitest",
```

- [ ] **Step 4: Rodar e ver falhar**

Run: `docker compose run --rm web npm test`
Expected: FAIL — `Inicio.tsx` não existe (`Cannot find module './Inicio'` ou equivalente).

- [ ] **Step 5: Implementar `Inicio.tsx`**

`web/src/paginas/Inicio.tsx`:
```tsx
export default function Inicio() {
  return <h1>Início</h1>
}
```

- [ ] **Step 6: Rodar e ver passar**

Run: `docker compose run --rm web npm test`
Expected: `1 passed`.

- [ ] **Step 7: Commit**

```bash
git add web/vite.config.ts web/package.json web/package-lock.json web/src/tests web/src/paginas
git commit -m "feat(front): configura Vitest + Testing Library e a página de Início

Co-Authored-By: <modelo da sessão> <noreply@anthropic.com>"
```

---

### Task 3: Tema — cores, fontes e a base do shadcn/ui

**Files:**
- Modify: `web/src/index.css` (tokens de tema), `web/src/main.tsx` (imports das fontes)
- Create: `web/components.json`, `web/src/lib/utils.ts`

**Interfaces:**
- Consumes: nada novo.
- Produces: utilitários Tailwind `bg-fundo`, `text-texto`, `text-texto-suave`, `bg-superficie`, `bg-principal`, `bg-principal-suave`, `bg-areia`, `text-terracota`, `text-rosa`, `bg-selo-essencial-fundo`/`text-selo-essencial-texto` (e os equivalentes `-util-`/`-espera-`), `bg-alerta-fundo`/`text-alerta-texto`, `font-titulo` (Lora), `font-texto` (DM Sans). `cn(...)` exportado de `web/src/lib/utils.ts`, para as sub-etapas que instalarem componentes do shadcn/ui.

Tokens de cor e tipografia não têm comportamento para testar no Vitest — jsdom não executa o pipeline real do Tailwind, então um teste que só checasse o nome de uma classe não provaria a cor renderizada. A prova real é visual (navegador) e o build (garante que o CSS compila).

- [ ] **Step 1: Instalar as dependências que os componentes do shadcn/ui vão esperar**

```bash
docker compose run --rm web npm install clsx tailwind-merge class-variance-authority lucide-react
```

- [ ] **Step 2: `web/src/lib/utils.ts`**

```ts
import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...entradas: ClassValue[]) {
  return twMerge(clsx(entradas))
}
```

- [ ] **Step 3: `web/components.json`**

```json
{
  "$schema": "https://ui.shadcn.com/schema.json",
  "style": "default",
  "rsc": false,
  "tsx": true,
  "tailwind": {
    "config": "",
    "css": "src/index.css",
    "baseColor": "neutral",
    "cssVariables": true
  },
  "aliases": {
    "components": "@/componentes",
    "utils": "@/lib/utils"
  }
}
```
Este arquivo é escrito à mão (não via `npx shadcn init`) para não depender de flags de uma CLI que muda com frequência. Nenhuma tarefa desta etapa instala um componente do shadcn/ui de verdade, então um campo de schema levemente desatualizado aqui não quebra nada agora; a primeira sub-etapa que rodar `npx shadcn add <componente>` deve confirmar que o arquivo está no formato que a versão instalada da CLI espera, e ajustar se não estiver.

- [ ] **Step 4: Alias `@/` no TypeScript e no Vite**

O scaffold do Vite pode gerar um único `tsconfig.json` com `"compilerOptions"`, ou (em versões mais novas) um `tsconfig.json` que só referencia `tsconfig.app.json` e `tsconfig.node.json`, com as opções de verdade dentro de `tsconfig.app.json`. Abra `web/tsconfig.json`: se ele tiver um bloco `"references"` em vez de `"compilerOptions"`, edite `tsconfig.app.json` (o que inclui `src/`); senão, edite o próprio `tsconfig.json`. Dentro de `"compilerOptions"` do arquivo certo, acrescente:
```json
"baseUrl": ".",
"paths": {
  "@/*": ["./src/*"]
},
```

Em `web/vite.config.ts`, importe `fileURLToPath` e acrescente `resolve.alias`:
```ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { fileURLToPath } from 'node:url'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
```
(mantenha o resto do arquivo igual; só acrescente o bloco `resolve` entre `plugins` e `server`. Não use `__dirname` aqui — o scaffold do Vite gera um projeto `"type": "module"`, e `__dirname` não existe em ESM nativo; `import.meta.url` é o equivalente correto.)

- [ ] **Step 5: Tokens de tema em `web/src/index.css`**

Substitua o conteúdo (que hoje só tem `@import "tailwindcss";`) por:
```css
@import "tailwindcss";

@theme {
  --color-fundo: #F7F5EE;
  --color-superficie: #FFFFFF;
  --color-texto: #2F3A33;
  --color-texto-suave: #5A6660;
  --color-principal: #4F6B57;
  --color-principal-suave: #EEF1EA;
  --color-areia: #EDE4D3;
  --color-terracota: #D9967A;
  --color-rosa: #D8A9A0;
  --color-selo-essencial-fundo: #F5DDD2;
  --color-selo-essencial-texto: #874129;
  --color-selo-util-fundo: #E1EAE2;
  --color-selo-util-texto: #36513D;
  --color-selo-espera-fundo: #EDE4D3;
  --color-selo-espera-texto: #5E4B2A;
  --color-alerta-fundo: #F7E4DF;
  --color-alerta-texto: #6E2F2A;

  --font-titulo: "Lora", serif;
  --font-texto: "DM Sans", sans-serif;
}

@layer base {
  body {
    @apply bg-fundo text-texto font-texto;
  }
  h1, h2, h3 {
    @apply font-titulo;
  }
}
```
(Nomes dos tokens iguais aos da tabela da seção 6 da spec, trocando espaço/maiúscula por `-`: "pode esperar" virou `espera` para caber num nome de utilitário Tailwind válido.)

- [ ] **Step 6: Importar as fontes em `web/src/main.tsx`**

No topo do arquivo, antes do `import './index.css'` (ou da linha equivalente que o scaffold gerou):
```ts
import '@fontsource/dm-sans/400.css'
import '@fontsource/lora/600.css'
```

- [ ] **Step 7: Rodar o build e verificar manualmente**

Run: `docker compose run --rm web npm run build`
Expected: compila sem erro (prova que o `@theme` e os imports de fonte são válidos).

Edite `web/src/paginas/Inicio.tsx` temporariamente para usar os tokens:
```tsx
export default function Inicio() {
  return <h1 className="text-principal">Início</h1>
}
```
Abra `http://localhost:5174` no navegador.
Expected: o fundo da página é o bege claro (`#F7F5EE`), o título "Início" está em Lora e na cor verde principal (`#4F6B57`). Depois de confirmar visualmente, pode manter ou remover o `className` de teste — ele não faz parte do contrato desta tarefa.

- [ ] **Step 8: Commit**

```bash
git add web/components.json web/tsconfig*.json web/vite.config.ts web/src/index.css web/src/main.tsx web/src/lib web/package.json web/package-lock.json
git commit -m "feat(front): tokens de tema (cores e fontes da spec) e base do shadcn/ui

Co-Authored-By: <modelo da sessão> <noreply@anthropic.com>"
```

---

### Task 4: Roteamento — as 7 rotas vazias + fallback de não encontrada

**Files:**
- Create: `web/src/paginas/Questionario.tsx`, `web/src/paginas/Planilha.tsx`, `web/src/paginas/Roteiro.tsx`, `web/src/paginas/Guia.tsx`, `web/src/paginas/GuiaItem.tsx`, `web/src/paginas/Seguranca.tsx`, `web/src/paginas/Ajustes.tsx`, `web/src/paginas/NaoEncontrada.tsx`
- Create: `web/src/App.tsx` (substitui o gerado pelo scaffold), `web/src/App.test.tsx`
- Modify: `web/src/main.tsx` (providers + roteador)

**Interfaces:**
- Consumes: `Inicio` (Tarefa 2).
- Produces: `AppRoutes` (export nomeado de `web/src/App.tsx`), usado por `main.tsx` e pelos testes de rota.

- [ ] **Step 1: Escrever o teste que falha**

`web/src/App.test.tsx`:
```tsx
import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'
import { AppRoutes } from './App'

function renderEm(caminho: string) {
  const queryClient = new QueryClient()
  render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[caminho]}>
        <AppRoutes />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('AppRoutes', () => {
  it.each([
    ['/', 'Início'],
    ['/questionario/1', 'Questionário'],
    ['/enxoval/abc123/planilha', 'Planilha'],
    ['/enxoval/abc123/roteiro', 'Roteiro'],
    ['/enxoval/abc123/guia', 'Guia dos itens'],
    ['/enxoval/abc123/guia/berco', 'Guia do item'],
    ['/enxoval/abc123/seguranca', 'Segurança'],
    ['/enxoval/abc123/ajustes', 'Ajustes'],
  ])('a rota %s mostra a página certa', (caminho, texto) => {
    renderEm(caminho)
    expect(screen.getByText(texto)).toBeInTheDocument()
  })

  it('uma rota desconhecida mostra a página de não encontrada, não tela branca', () => {
    renderEm('/isso-nao-existe')
    expect(screen.getByText('Página não encontrada')).toBeInTheDocument()
  })

  it('aceita qualquer valor de :id e :item na rota de guia do item', () => {
    renderEm('/enxoval/qualquer-coisa/guia/qualquer-item')
    expect(screen.getByText('Guia do item')).toBeInTheDocument()
  })
})
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `docker compose run --rm web npm test`
Expected: FAIL — `./App` não exporta `AppRoutes` (ou o arquivo ainda tem o conteúdo do scaffold).

- [ ] **Step 3: Criar as páginas placeholder**

`web/src/paginas/Questionario.tsx`:
```tsx
export default function Questionario() {
  return <h1>Questionário</h1>
}
```

`web/src/paginas/Planilha.tsx`:
```tsx
export default function Planilha() {
  return <h1>Planilha</h1>
}
```

`web/src/paginas/Roteiro.tsx`:
```tsx
export default function Roteiro() {
  return <h1>Roteiro</h1>
}
```

`web/src/paginas/Guia.tsx`:
```tsx
export default function Guia() {
  return <h1>Guia dos itens</h1>
}
```

`web/src/paginas/GuiaItem.tsx`:
```tsx
export default function GuiaItem() {
  return <h1>Guia do item</h1>
}
```

`web/src/paginas/Seguranca.tsx`:
```tsx
export default function Seguranca() {
  return <h1>Segurança</h1>
}
```

`web/src/paginas/Ajustes.tsx`:
```tsx
export default function Ajustes() {
  return <h1>Ajustes</h1>
}
```

`web/src/paginas/NaoEncontrada.tsx`:
```tsx
export default function NaoEncontrada() {
  return <h1>Página não encontrada</h1>
}
```

- [ ] **Step 4: `web/src/App.tsx`**

Substitui o arquivo gerado pelo scaffold por:
```tsx
import { Route, Routes } from 'react-router-dom'
import Ajustes from './paginas/Ajustes'
import Guia from './paginas/Guia'
import GuiaItem from './paginas/GuiaItem'
import Inicio from './paginas/Inicio'
import NaoEncontrada from './paginas/NaoEncontrada'
import Planilha from './paginas/Planilha'
import Questionario from './paginas/Questionario'
import Roteiro from './paginas/Roteiro'
import Seguranca from './paginas/Seguranca'

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<Inicio />} />
      <Route path="/questionario/:passo" element={<Questionario />} />
      <Route path="/enxoval/:id/planilha" element={<Planilha />} />
      <Route path="/enxoval/:id/roteiro" element={<Roteiro />} />
      <Route path="/enxoval/:id/guia" element={<Guia />} />
      <Route path="/enxoval/:id/guia/:item" element={<GuiaItem />} />
      <Route path="/enxoval/:id/seguranca" element={<Seguranca />} />
      <Route path="/enxoval/:id/ajustes" element={<Ajustes />} />
      <Route path="*" element={<NaoEncontrada />} />
    </Routes>
  )
}
```

- [ ] **Step 5: Ligar os providers em `web/src/main.tsx`**

Substitua o conteúdo por (mantendo os imports de fonte e `./index.css` já criados na Tarefa 3):
```tsx
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter } from 'react-router-dom'
import '@fontsource/dm-sans/400.css'
import '@fontsource/lora/600.css'
import './index.css'
import { AppRoutes } from './App'

const queryClient = new QueryClient()

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AppRoutes />
      </BrowserRouter>
    </QueryClientProvider>
  </StrictMode>,
)
```

- [ ] **Step 6: Rodar e ver passar**

Run: `docker compose run --rm web npm test`
Expected: todos os testes passam (1 de `Inicio` + 10 de `AppRoutes` — 8 do `it.each` mais os 2 casos de borda —, 11 no total).

- [ ] **Step 7: Verificar manualmente**

Com `docker compose up -d web` no ar, abra no navegador:
- `http://localhost:5174/` → "Início"
- `http://localhost:5174/enxoval/qualquer/planilha` → "Planilha"
- `http://localhost:5174/rota-que-nao-existe` → "Página não encontrada"

- [ ] **Step 8: Commit**

```bash
git add web/src
git commit -m "feat(front): as 7 rotas da Etapa 5 como páginas vazias + fallback de não encontrada

Co-Authored-By: <modelo da sessão> <noreply@anthropic.com>"
```

---

### Task 5: Tipos da API gerados e README

**Files:**
- Create: `web/src/api/tipos.ts` (gerado, commitado)
- Modify: `web/package.json` (script `gen:api`, `typecheck`), `README.md`

**Interfaces:**
- Produces: `web/src/api/tipos.ts` exportando `paths` (tipo gerado pelo `openapi-typescript` a partir de `/api/openapi.json`), consumido pelas sub-etapas que chamarem a API de verdade (5b em diante).

Um arquivo de tipos gerado não tem comportamento de runtime para um teste de Vitest provar — a verificação real é o TypeScript aceitar o arquivo e compilar o projeto (`tsc --noEmit` e `npm run build`).

- [ ] **Step 1: Instalar o gerador e criar o script**

```bash
docker compose run --rm web npm install -D openapi-typescript
```

Em `web/package.json`, no bloco `"scripts"`, acrescente:
```json
"typecheck": "tsc --noEmit",
"gen:api": "openapi-typescript http://api:8000/api/openapi.json -o src/api/tipos.ts",
```

- [ ] **Step 2: Garantir que a API está no ar e com a documentação habilitada**

Run:
```bash
docker compose up -d db api
```
Confira que `DOCS_HABILITADO=true` está no `.env` (sem isso `/api/openapi.json` não existe e o Step 3 falha com 404).

- [ ] **Step 3: Gerar os tipos**

Run:
```bash
docker compose run --rm web npm run gen:api
```
Expected: cria `web/src/api/tipos.ts` com os tipos de todas as rotas de `/api/v1` (ex.: `paths["/api/v1/enxovais"]`, `paths["/api/v1/municipios"]`).

- [ ] **Step 4: Verificar que o projeto inteiro continua compilando**

Run:
```bash
docker compose run --rm web npm run typecheck
docker compose run --rm web npm run build
```
Expected: os dois rodam sem erro.

- [ ] **Step 5: Rodar a suíte inteira do front**

Run: `docker compose run --rm web npm test`
Expected: todos os testes continuam passando (nada nesta tarefa toca em componentes).

- [ ] **Step 6: Atualizar o README**

Acrescente ao `README.md`, depois da seção "## API":
````markdown
## Front

```bash
docker compose up -d --build web
```

- http://localhost:5174

Gerar os tipos da API a partir do OpenAPI (a API precisa estar no ar, com `DOCS_HABILITADO=true`):
```bash
docker compose run --rm web npm run gen:api
```

### Testes

```bash
docker compose run --rm web npm test
```
````

- [ ] **Step 7: Commit**

```bash
git add web/package.json web/package-lock.json web/src/api README.md
git commit -m "feat(front): gera os tipos da API (openapi-typescript) e documenta o front no README

Co-Authored-By: <modelo da sessão> <noreply@anthropic.com>"
```

---

## Ao terminar a Etapa 5a

- `docker compose run --rm web npm test` passa por inteiro.
- `docker compose run --rm web npm run build` compila sem erro.
- As 7 rotas (+ fallback) respondem com a página certa no navegador.
- Próximo passo: plano da **Etapa 5b (questionário)**, que já pode consumir `src/api/tipos.ts` e o tema desta etapa.
