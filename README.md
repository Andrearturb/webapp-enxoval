# Enxoval Inteligente

O que comprar, quando e quanto para o bebê, do nascimento aos 12 meses.
Documentação: `docs/plano-enxoval.md` (produto) e `docs/superpowers/specs/` (desenho).

## Rodar localmente

Requisitos: Docker Desktop.

```bash
cp .env.example .env        # PowerShell: Copy-Item .env.example .env
# edite o .env e troque a senha
docker compose up -d --build
```

- API: http://localhost:8010/api/v1/saude
- Documentação da API: http://localhost:8010/api/docs

Portas 8010 ou 5180 em uso? Troque `API_PORT`/`WEB_PORT` no `.env`.

## Login com Keycloak

O provedor de identidade fica no repositório separado [keycloak-server](https://github.com/Andrearturb/keycloak-server).
Suba esse projeto seguindo seu README e, no `.env` deste app, configure:

```env
KEYCLOAK_HABILITADO=true
KEYCLOAK_URL=http://host.docker.internal:8080
KEYCLOAK_PUBLIC_URL=http://localhost:8080
KEYCLOAK_ISSUER=http://localhost:8080/realms/enxoval
KEYCLOAK_REALM=enxoval
KEYCLOAK_CLIENT_ID=webapp
```

`KEYCLOAK_URL` é o endereço usado pelo container da API para buscar as chaves;
`KEYCLOAK_PUBLIC_URL` é o endereço acessível pelo navegador. `KEYCLOAK_ISSUER`
deve corresponder ao issuer público do realm, mesmo quando a URL interna é diferente.
Para outro realm, ajuste também o sufixo de `KEYCLOAK_ISSUER`.

No `.env` do `keycloak-server`, fixe `KC_HOSTNAME=http://localhost:8080` e
`APP_ENXOVAL_URL=http://localhost:5180`. Se mudar uma porta, atualize as URLs
correspondentes nos dois projetos. Confira o campo `issuer` em
http://localhost:8080/realms/enxoval/.well-known/openid-configuration antes de
ativar o app; ele deve ser igual a `KEYCLOAK_ISSUER`.

Rode `docker compose run --rm api alembic upgrade head` e recrie API/frontend com
`docker compose up -d --build api web`. A página inicial passa a exibir os enxovais
da conta autenticada. As exportações também exigem token.

Em uma janela anônima, http://localhost:5180 deve abrir o login. Use **Cadastre-se**
para criar sua conta de família (a conta administrativa do Keycloak é separada).
Após o cadastro/login, a aplicação abre **Meus enxovais**. **Sair** encerra a sessão
e retorna ao login. Uma sessão já autenticada pode entrar diretamente pelo SSO.

O cadastro agora exige confirmação do e-mail antes de liberar a aplicação.
No desenvolvimento, os e-mails são capturados pela caixa local do projeto
Keycloak em http://localhost:8026. Abra a mensagem e clique no link de confirmação.
Essa caixa não entrega mensagens para endereços reais; em produção, configure
um SMTP de entrega no Keycloak. Contas existentes sem e-mail verificado também
precisam confirmar seu endereço. A API rejeita tokens não verificados, inclusive
tokens emitidos antes dessa configuração.

Em **Minha conta** (`/minha-conta`), a pessoa pode escolher um dos seis avatares
(ursinho, coelhinho, elefantinho, patinho, nuvem e lua) ou suas iniciais, consultar
nome e e-mail, editar dados pessoais, alterar senha e sair. A edição de nome e
senha abre o fluxo do Keycloak e retorna ao perfil. A escolha é vinculada ao `sub`
da conta e armazenada no PostgreSQL (`perfil_usuario`). Clicar no avatar atual
abre um modal com os seis avatares e **Usar minhas iniciais**; escolher uma opção
salva e fecha o modal. Contas sem escolha usam o ursinho. Fotos não são exibidas.
A API aceita os seis códigos ou `avatar: null` para iniciais em
`PUT /api/v1/perfil/avatar`; o envio de arquivos foi
retirado. As ilustrações são arquivos WebP locais em `web/public/avatares`.
O perfil retorna apenas `avatar`; não existe operação para remover a escolha.
A coluna legada `foto` não é exposta nem usada para a imagem do perfil.
Execute `docker compose exec api alembic upgrade head` antes de usar o perfil
em um banco existente. Faça backup do banco para preservar os perfis e fotos antigas.

Enxovais criados antes da autenticação têm `dono_id` vazio e não aparecem nas contas
até que sejam associados ao proprietário correto. Com `KEYCLOAK_HABILITADO=false`,
o desenvolvimento local continua sem login. Em um build estático do frontend,
forneça as variáveis `VITE_KEYCLOAK_*` durante `npm run build`.

A ativação não associa enxovais antigos automaticamente e não apaga respostas ou
marcações. A conta nova começa com sua própria lista vazia; uma associação futura
deve conferir o proprietário correto antes de alterar `dono_id`.

## Banco e conteúdo

```bash
docker compose run --rm api alembic upgrade head   # cria/atualiza as tabelas
docker compose run --rm api python -m seed         # carrega o conteúdo (só o que falta)
```

O conteúdo inicial fica em `api/seed/dados/`. Depois da primeira carga, edite pelo admin
(`/admin`): o seed só carrega uma tabela que ainda esteja vazia, então o que você apagar ou
renomear lá não volta. Para repor de propósito o que estiver faltando (sem sobrescrever o
que existe), rode `python -m seed --forcar`.

## API

Documentação interativa em http://localhost:8010/api/docs (só com `DOCS_HABILITADO=true`).

```bash
# busca de cidade
curl "http://localhost:8010/api/v1/municipios?busca=curitiba"
# cria um enxoval e lê o resultado
curl -X POST http://localhost:8010/api/v1/enxovais -H 'Content-Type: application/json' \
  -d '{"municipio_codigo":4106902,"data_prevista":"2027-06-15","dias_entre_lavagens":2,
       "moradia":"apartamento","tem_carro":true,"orcamento":"intermediario","primeiro_filho":true}'
curl http://localhost:8010/api/v1/enxovais/<id>
```

## Front

```bash
docker compose up -d --build web
```

- http://localhost:5180

Gerar os tipos da API a partir do OpenAPI (a API precisa estar no ar, com `DOCS_HABILITADO=true`):
```bash
docker compose run --rm web npm run gen:api
```

### Testes

```bash
docker compose run --rm web npm test
```

## Testes

```bash
docker compose run --rm api pytest
docker compose run --rm web npm test
```
