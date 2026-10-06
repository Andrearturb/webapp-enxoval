# Enxoval Inteligente: desenho do MVP

Data: 2026-10-05 · Status: aprovado · Última revisão: 2026-10-06

**Estado da implementação:** Etapa 1 (Docker, banco, seed, admin) e Etapa 2 (motor) prontas e na `main`. Etapas 3 (API) e 4 (telas) pendentes; deploy fora deste ciclo. As seções abaixo descrevem o que existe; onde ainda é intenção, está dito. · Conteúdo de produto: [`docs/plano-enxoval.md`](../../plano-enxoval.md)

## 1. Objetivo e contexto

O site responde **o que comprar, quando comprar e quanto comprar** para um bebê do nascimento aos 12 meses. A família responde 6 perguntas e recebe uma planilha personalizada, um roteiro por fase, um guia de itens e as regras de segurança por idade. O conteúdo (itens, quantidades, marcas, regras) está no plano aprovado.

Decisões de enquadramento:

- **É a base de um produto real**, não uma demonstração. Todos os dados da família ficam no backend; o front não guarda dado importante.
- **Sem usuários neste MVP.** O login virá depois com um realm do **Keycloak**. Nada de usuário é desenhado agora, mas há um ponto único de encaixe (seção 7).
- **Sem deploy neste ciclo.** Tudo é testado localmente em Docker Compose. O deploy na Oracle Cloud (provavelmente ARM/Ampere, a confirmar) é um ciclo futuro, e nenhum comando roda no servidor sem aprovação prévia.

Regras permanentes do projeto:

- Mobile first, acessível (contraste AA, alvos de toque ≥ 44 px), todo o texto em português do Brasil.
- Itens e alertas de segurança **nunca** são removidos por orçamento ou preferência.
- Conteúdo próprio; nada copiado de influenciadoras.
- Marcas e regras de segurança ainda serão validadas, então são editáveis e têm campos de validação.
- Segredos só em variáveis de ambiente, nunca no repositório.

### Critérios de sucesso

1. Uma família conclui o questionário no celular em cerca de 2 minutos e vê a planilha calculada para a sua cidade, data e rotina.
2. A família marca quantidades compradas, ganhas e que já tinha; os dados persistem no servidor e reaparecem ao abrir o link em outro aparelho.
3. A planilha é exportada em PDF, XLSX e CSV.
4. O conteúdo (itens, marcas, cidades, regras) é editável no `/admin` sem mexer em código, e as correções aparecem para todas as famílias na próxima leitura.
5. O teste "segurança nunca sai" passa para todas as combinações de respostas.

## 2. Arquitetura

Abordagem escolhida: **API e SPA separados**.

```
navegador → Caddy ─┬─ /            → build estático do React
                   ├─ /api/*       → FastAPI (api:8000)
                   └─ /admin/*     → FastAPI/SQLAdmin (api:8000)
                         FastAPI → PostgreSQL (rede interna, sem porta publicada)
```

| Camada | Tecnologia |
|---|---|
| Backend | Python, FastAPI, SQLAlchemy 2, Alembic, Pydantic, pydantic-settings, SQLAdmin, WeasyPrint, openpyxl |
| Banco | PostgreSQL |
| Front | Vite, React, TypeScript, Tailwind CSS, shadcn/ui, Lucide, TanStack Query, React Router |
| Infra | Docker Compose (serviços `db`, `api`, `web`); Caddy serve o front e faz proxy; imagens oficiais multi-arquitetura (x86 e ARM) |

Em desenvolvimento, o front roda no servidor do Vite (hot reload) com proxy para a API.

### Estrutura de pastas

```
webapp-enxoval/
├─ docker-compose.yml          # base + overrides de dev
├─ .env.example                # só nomes de variáveis
├─ api/
│  ├─ app/
│  │  ├─ main.py               # cria o app, monta /api/v1 e /admin
│  │  ├─ config.py             # configurações via ambiente
│  │  ├─ db/                   # engine, sessão, modelos
│  │  ├─ motor/                # personalização: funções puras
│  │  ├─ servicos/             # banco ↔ motor
│  │  ├─ rotas/                # endpoints e schemas Pydantic
│  │  ├─ exportar/             # PDF, XLSX, CSV
│  │  ├─ admin/                # SQLAdmin
│  │  └─ acesso.py             # ponto de encaixe do Keycloak
│  ├─ alembic/
│  ├─ seed/                    # YAML de conteúdo, municípios IBGE, script
│  └─ tests/
├─ web/
│  ├─ src/ (paginas/, componentes/, api/, tema/)
│  └─ Caddyfile
└─ docs/
```

Regra de fronteira: `motor/` não importa banco, HTTP nem SQLAlchemy. `servicos/` é a única camada que lê o banco e chama o motor.

## 3. Modelo de dados

### Catálogo (editável no admin)

| Tabela | Campos principais |
|---|---|
| `categoria` | id, slug, nome, ordem |
| `fase_roteiro` | código, nome, início e fim (referência: semana de gestação ou mês do bebê), texto, ordem |
| `item` | id, slug, categoria, nome, para_que_serve, como_escolher, idade_inicio_meses, fase_compra (→ `fase_roteiro`), prioridade_base (`essencial`, `util`, `pode_esperar`), `e_seguranca`, uso_clima (`neutro`, `divide`, `so_frio`), variante_frio e variante_calor (rótulos, para `divide`), `escala_lavagem` (a quantidade segue a fórmula de lavagem), quantidade e unidade_texto (itens sem tamanho), ordem |
| `item_tamanho` | item, tamanho (`RN`, `P`, `M`, `G`, `GG`), quantidade_base (calibrada para lavar a cada 2 dias), fase_compra opcional (ex.: roupas M compradas de 0 a 3 meses) |
| `item_regra` | item, condição (`com_carro`, `sem_carro`, `apartamento`, `casa_sem_escada`, `casa_com_escada`, `perfil_quente`, `perfil_moderado`, `perfil_frio`), efeito (`incluir_so_se`, `mudar_prioridade`, `dica`), valor (texto livre; **falta** restringir ao enum quando o efeito é `mudar_prioridade`) |
| `janela_tamanho` | tamanho, idade_inicio_dias, idade_fim_dias, peso_referencia. **Falta** `CHECK (idade_fim_dias > idade_inicio_dias)` |
| `perfil_clima` | código (`quente`, `moderado`, `frio`), nome, descrição, meses_frios, meses_frescos |
| `estado` | uf, nome, perfil_padrao |
| `municipio` | código IBGE, nome, nome_busca (sem acento), uf, perfil_excecao (opcional) |
| `marca` | id, nome, faixa_padrao, `validado`, fonte, revisado_em |
| `item_marca` | item, marca, faixa (`economico`, `intermediario`, `investir`), ordem |
| `regra_seguranca` | id, código, tema (`sono`, `transporte`, `banho`, `alimentacao`, `casa`, `brinquedos`, `geral`), idade_inicio_meses, idade_fim_meses, texto, base (SBP, INMETRO, CONTRAN…), `validado`, fonte, revisado_em |
| `item_regra_seguranca` | item, regra_seguranca (N:N, para mostrar o alerta na ficha) |

### Família

| Tabela | Campos |
|---|---|
| `enxoval` | id (UUID v4), criado_em, atualizado_em, municipio, perfil_clima (o usado), perfil_corrigido, data_prevista, dias_entre_lavagens, moradia (`apartamento`, `casa_sem_escada`, `casa_com_escada`), tem_carro, orcamento, primeiro_filho |
| `enxoval_linha` | enxoval, chave (item, tamanho, variante), qtd_comprada, qtd_ganhada, qtd_ja_tinha, atualizado_em. PK (enxoval, chave). Exclusão em cascata com o enxoval |

### Decisões de modelo

- **A lista é recalculada a cada leitura.** Só as respostas e as quantidades marcadas são gravadas, então correções de conteúdo chegam a todos. A opção futura de ajuste manual acrescenta `qtd_ajustada` (nula) em `enxoval_linha`, sem outra mudança.
- **Chave da linha** estável e legível: `<slug>:<tamanho>:<variante>`, com partes vazias quando não se aplicam (ex.: `body:P:frio`, `berco::`).
- **Linhas órfãs:** se uma mudança de respostas tira uma linha da lista, o registro continua. Ela aparece em "fora da lista atual" enquanto tiver alguma quantidade maior que zero.
- **Sem usuário/dono.** A coluna de dono entra numa migração futura, junto com o Keycloak.
- **Duas travas em falta.** `janela_tamanho` aceita fim ≤ início e `item_regra.valor` aceita qualquer texto. Ambas são editáveis no `/admin`, e um erro de digitação ali chegava ao motor. O motor hoje degrada com aviso em vez de quebrar (seção 4), mas as travas ainda devem entrar numa migração.

### Carga inicial (seed)

- O conteúdo do plano é transcrito para YAML em `api/seed/` (`categorias`, `fases`, `itens`, `marcas`, `perfis`, `estados`, `excecoes_municipios`, `seguranca`). A lista de municípios vem do arquivo público do IBGE, versionado no repositório.
- O comando `python -m seed` carrega cada grupo **só se a tabela estiver vazia**, e nunca apaga dados de famílias. Assim, item ou marca apagado ou renomeado no admin não volta numa nova execução. `python -m seed --forcar` repõe o que estiver faltando, sem sobrescrever o que existe.
- Depois da carga, **o banco é a fonte da verdade** e a edição é feita no `/admin`. Toda marca e regra de segurança nasce com `validado = false`.

## 4. Motor de personalização (`api/app/motor/`)

Funções puras sobre dataclasses. A data de hoje (`hoje`) sempre entra como parâmetro.

Entrada: `Respostas` + `Catalogo` + `hoje`. Saída: `EnxovalCalculado` (linhas por categoria, fichas, roteiro, alertas, resumo, avisos).

Contas com fração usam `fractions.Fraction`, nunca `float`. Um teste garante que o pacote não importa banco nem HTTP.

| Função | Regra |
|---|---|
| `resolver_perfil(municipio, estado, correcao)` | correção da família > exceção do município > padrão do estado |
| `proporcao_frio(data_prevista, inicio_dias, fim_dias, perfil, incluir_frescos=True)` | percorre cada dia da janela (`fim_dias` exclusivo); dia em mês frio vale 1, em mês fresco vale 0,5, nos demais vale 0. Devolve a média (0 a 1). Recebe dias, e não o objeto janela, para servir também a itens sem tamanho (ano inteiro) |
| `fator_lavagem(dias)` | `(dias + 1) / 3`. Opções de resposta: todo dia = 1, a cada 2 dias = 2, a cada 3 dias = 3, 2× por semana = 4 |
| `quantidade(base, fator)` | `ceil(base × fator)` |
| `dividir_variantes(qtd, p)` | frio = `floor(qtd × p + ½)` (meio para cima; não é o `round()` do Python, que arredonda para o par), calor = `qtd − frio`. O total é preservado por construção |
| `avaliar_regras(item, respostas)` | inclusão, prioridade final, dicas e avisos de catálogo. Item de segurança só sai por condição física (`incluir_so_se` com moradia, carro ou clima); orçamento e preferências nunca o removem |
| `marcas_para(marcas, orcamento)` | marcas da faixa, na ordem do catálogo; se vazia, a faixa mais próxima (empate: a mais barata), com `fallback=True` na ficha |
| `montar_roteiro(fases, data_prevista, hoje)` | fases em datas reais (gestação a partir de DPP − 40 semanas; fases do bebê em meses completos, com fim de mês ajustado) e a fase atual |
| `alertas_por_idade(regras, data_prevista)` | regras com a data em que passam a valer |
| `montar_enxoval(respostas, catalogo, hoje, limite_volume=40)` | orquestra tudo e gera o resumo ("fica até N dias sem lavar", total de unidades, aviso de volume alto, destacar "já tinha") |
| `progresso(linhas, marcadas)` | o quanto já está atendido: total, atendidas, faltam, % pronto e as linhas marcadas que saíram da lista. Fica **fora** do `montar_enxoval`, porque o cálculo da lista não conhece o que a família marcou; uma linha nunca conta além da própria quantidade |

Itens `so_frio` entram apenas quando a janela tem ao menos um dia em **mês frio de verdade**; mês "fresco" não basta, e é isso que mantém o gorro fora de Salvador. Itens com `uso_clima = divide` geram até duas linhas (frio e calor); a linha com quantidade 0 é omitida. Itens sem tamanho usam o primeiro ano inteiro (0 a 365 dias) para decidir o clima.

**Fase atual quando as fases se sobrepõem** (a reta final vai até a 42ª semana e invade os primeiros meses do bebê): antes da data prevista vale a primeira fase na ordem, porque a gestação pode passar da data; a partir dela vale a mais avançada, já que arrumar a mala deixou de ser o próximo passo.

**Alertas de segurança** nunca são filtrados nem alterados por resposta alguma. Só os *links* do alerta para itens fora deste enxoval são removidos, para a ficha não apontar para um item que a família não tem (ex.: o portão de escada no alerta da casa, para quem mora em apartamento).

**`avisos` é canal de defeito de catálogo**, não de situação normal: item sem tamanhos nem quantidade, janela de tamanho ausente ou inválida, regra de prioridade com valor inválido. O motor não quebra em nenhum desses casos: devolve o que consegue e avisa, em português. O uso de uma faixa de marca vizinha **não** é aviso, porque é rotineiro (muitos itens só têm marca genérica); isso viaja por item em `Ficha.marcas.fallback` e `Ficha.marcas.faixa`, que é a granularidade que a tela usa.

Os exemplos do plano (ex.: "metade manga longa" no M em Curitiba) são aproximações; o motor segue a conta dia a dia, e os números podem diferir um pouco do texto.

**Bebê conforto sem carro:** continua na lista com prioridade `util` (táxi, carro de aplicativo, carona). Portão de segurança: `incluir_so_se casa_com_escada`.

## 5. API (`/api/v1`)

| Método e rota | Função |
|---|---|
| `GET /saude` | verificação de saúde |
| `GET /municipios?busca=` | até 10 resultados, busca sem acento, com perfil sugerido |
| `GET /perfis-clima` | os 3 perfis com descrição |
| `POST /enxovais` | cria a partir das 6 respostas e devolve `201 {id}` |
| `GET /enxovais/{id}` | respostas + linhas calculadas mescladas com as quantidades + roteiro + fichas + segurança + resumo |
| `PATCH /enxovais/{id}` | edita respostas |
| `PUT /enxovais/{id}/linhas/{chave}` | grava `{comprada, ganhada, ja_tinha}` (inteiros ≥ 0) |
| `POST /enxovais/{id}/linhas/{chave}/completar` | completa o que falta com a origem informada (`comprada`, `ganhada`, `ja_tinha`) |
| `GET /enxovais/{id}/exportar.{pdf,xlsx,csv}` | arquivos gerados no servidor |
| `DELETE /enxovais/{id}` | apaga o enxoval e suas linhas definitivamente |

- Validação: data prevista entre `hoje − 1 ano` e `hoje + 10 meses`; somas acima do sugerido são permitidas.
- Formato de erro: `{"erro": "<codigo>", "mensagem": "<texto pt-BR>"}`; 404 para enxoval inexistente, 422 para validação, 500 genérico (o detalhe vai só para o log).
- OpenAPI em `/api/docs`, desligável por variável de ambiente. Os tipos TypeScript do front são gerados com `openapi-typescript`.

## 6. Front

### Rotas

| Rota | Conteúdo |
|---|---|
| `/` | proposta, como funciona, exemplo de planilha, botão "Começar meu enxoval" |
| `/questionario/:passo` | 6 passos com barra de progresso; respostas parciais só em memória; um único `POST` no fim |
| `/enxoval/:id/planilha` | resumo, filtros (todos, faltando, tamanho, prioridade), linhas por categoria com contadores −/+ e "marcar tudo" |
| `/enxoval/:id/roteiro` | linha do tempo com datas reais e fase atual |
| `/enxoval/:id/guia`, `/enxoval/:id/guia/:item` | fichas: para que serve, idade, como escolher, marcas da faixa, alertas |
| `/enxoval/:id/seguranca` | regras por idade e tema, com datas |
| `/enxoval/:id/ajustes` | editar respostas, exportar, copiar link, apagar meus dados |

### As 6 perguntas

1. Cidade (autocompletar) com perfil sugerido e "Não é isso? Corrigir".
2. Data prevista (dia/mês/ano).
3. Frequência de lavar roupa.
4. Moradia (apartamento / casa sem escada / casa com escada) e carro (sim/não).
5. Orçamento (econômico / intermediário / investir mais).
6. Primeiro filho (sim/não). Se não for, a coluna "já tinha" abre em destaque.

### Comportamento e acessibilidade

- Os dados vêm todos de `GET /enxovais/{id}` em cache do TanStack Query.
- Contadores com atualização otimista, gravação agrupada em ~400 ms e desfazer em caso de erro.
- Mobile first, com abas fixas no topo; no desktop, a planilha vira tabela.
- Contraste AA, foco visível, rótulos em todos os campos, selos com texto e respeito a `prefers-reduced-motion`.
- Telas para "enxoval não encontrado" e "sem conexão".
- Aviso permanente no rodapé: marcas e regras em validação, confirme com o pediatra.

### Identidade visual (paleta B, Sálvia e linho)

| Token | Cor | Uso |
|---|---|---|
| `fundo` | `#F7F5EE` | fundo da página |
| `superficie` | `#FFFFFF` | cartões |
| `texto` | `#2F3A33` | texto principal |
| `texto-suave` | `#5A6660` | texto secundário |
| `principal` | `#4F6B57` | botões, aba ativa, barras de progresso (texto branco) |
| `principal-suave` | `#EEF1EA` | abas inativas, botões secundários |
| `areia` | `#EDE4D3` | ilustrações, selo "pode esperar" |
| `terracota` | `#D9967A` | acento |
| `rosa` | `#D8A9A0` | acento |
| selo essencial | fundo `#F5DDD2`, texto `#874129` | |
| selo útil | fundo `#E1EAE2`, texto `#36513D` | |
| selo pode esperar | fundo `#EDE4D3`, texto `#5E4B2A` | |
| alerta de segurança | fundo `#F7E4DF`, texto `#6E2F2A` | |

Títulos em **Lora** (600) e texto em **DM Sans**. Cantos arredondados de 14 a 26 px, sombras leves, muito respiro. As ilustrações em traço fino começam como espaços reservados em SVG simples.

## 7. Acesso e segurança

- Todas as rotas `/enxovais` dependem de `acesso.py` (dependência FastAPI), que hoje não faz nada. Com o Keycloak, ela vai validar o token do realm e filtrar pelo dono.
- Até lá, o UUID v4 funciona como chave de acesso: `Referrer-Policy: no-referrer`, `noindex` nas páginas de enxoval, IDs fora dos logs de acesso e limite de requisições por IP em `POST /enxovais`.
- `/admin` só existe com `ADMIN_HABILITADO=true` (ligado no local, desligado por padrão em produção).
- Cabeçalhos de segurança no Caddy (CSP incluída). Postgres sem porta publicada. API como usuário não-root.
- Dados mínimos: sem nome, e-mail ou telefone. A exclusão é definitiva.

**Bloqueios de deploy** (precisam estar resolvidos antes de produção): `/admin` protegido pelo papel de admin do Keycloak; conferência de marcas e regras de segurança; política de privacidade (LGPD); confirmação da arquitetura do servidor; as duas travas de banco em falta (seção 3).

**Pendências de qualidade anotadas nas revisões** (não bloqueiam a Etapa 3, mas devem entrar antes do deploy): o aviso de volume alto olha um tamanho por vez e ignora que RN e P convivem na gaveta no primeiro mês; `condicao_vale` não falha alto diante de uma condição nova; falta teste para a regra "nunca chamar `date.today()`"; `Alerta.ativo_ate` e `FaseCalculada.fim` usam convenções de fim diferentes; apagar categoria, fase ou estado em uso mostra erro 500 no admin; a busca de cidade não casa apóstrofo tipográfico nem hífen (corrigir junto com a busca da Etapa 3, movendo `normalizar_busca` para `app/`).

## 8. Testes

| Camada | Ferramenta | Cobertura |
|---|---|---|
| Motor | pytest puro (94 testes) | cada função da seção 4; Curitiba e Salvador com nascimento em junho; virada de ano; 29 de fevereiro; fator de lavagem; preservação do total na divisão; catálogo incompleto; pureza de imports; propriedade "segurança nunca sai" sobre as 432 combinações de respostas |
| Serviços e API | pytest + httpx + Postgres em container | ciclo de vida do enxoval, linhas, órfãs, erros 404/422, exportações válidas |
| Seed | pytest (51 testes, com Postgres) | carga única por tabela, preservação de edições do admin, erro nomeando o item em YAML inválido, municípios homônimos e integridade referencial |
| Front | Vitest + Testing Library | questionário, contadores otimistas com desfazer |
| Ponta a ponta | Playwright + axe | inicial → questionário → planilha → exportação, no celular e no desktop |

Desenvolvimento orientado a testes (TDD) em todas as camadas.

## 9. Fora deste MVP

Login e contas (Keycloak), ajuste manual de quantidade, faixas de preço, links de afiliados, compartilhamento só para leitura, deploy na Oracle Cloud, nome final do site.

**Conteúdo a validar** (editável no `/admin`, sem mexer em código): marcas e suas faixas de orçamento, regras de segurança e suas fontes, perfil de clima padrão por estado e as exceções por cidade. Dois pontos já identificados: os perfis frio e moderado estão sem "meses frescos", o que deixa o tamanho M de Curitiba com menos peças de frio do que o plano descreve; e o casaquinho está neutro ao clima, enquanto o texto do plano trata casaco como peça só de frio.

## 10. Ordem de implementação

1. Docker Compose com o banco, modelos, migrações e seed.
2. Motor de personalização com testes.
3. API.
4. Telas.
5. Deploy (ciclo futuro, não planejado agora).
