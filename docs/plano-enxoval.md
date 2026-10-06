# Enxoval Inteligente: planejamento do site

Versão aprovada como MVP em 2026-10-05. Fonte viva: https://claude.ai/code/artifact/d551683f-918d-4c96-b18b-6f1621b6eef7

## Visão geral

O site responde três perguntas para quem espera um bebê: **o que comprar, quando comprar e quanto comprar** nos primeiros 12 meses. A pessoa preenche um questionário curto e recebe uma planilha personalizada, um roteiro de compras por fase e um guia de cada item.

A personalização parte de dois dados principais e três secundários:

- **Cidade** define o perfil de clima (quente o ano todo, inverno moderado ou inverno frio).
- **Mês previsto de nascimento** define em que estação o bebê vai usar cada tamanho de roupa.
- **Rotina** (frequência de lavar roupa, apartamento ou casa, tem carro) ajusta quantidades e itens de passeio.
- **Orçamento** (econômico, intermediário ou investir mais) muda as marcas sugeridas, não os itens de segurança.
- **Primeiro filho ou não** permite marcar o que já existe em casa.

O site é demonstrativo na primeira versão: sem login, sem loja, com os dados salvos no navegador e opção de exportar a planilha. O conteúdo é próprio; o perfil de uma influenciadora serviu só como inspiração do formato.

## Estrutura do site

Fluxo: Página inicial → Questionário (6 perguntas, ~2 minutos) → Meu enxoval (resultado), que se divide em 4 abas: Planilha, Roteiro, Guia dos itens, Segurança.

| Página | O que mostra | Interação principal |
| --- | --- | --- |
| Página inicial | Proposta do site, exemplo de planilha pronta, botão Começar | Ir para o questionário |
| Questionário | Cidade, data prevista, rotina de lavagem, moradia e carro, orçamento, primeiro filho | Uma pergunta por tela, com barra de progresso |
| Planilha | Itens por categoria com tamanho, quantidade, prioridade e status | Marcar como comprado, ganhado ou já tenho; filtrar; exportar em PDF ou Excel |
| Roteiro | Linha do tempo do 5º mês de gestação aos 12 meses do bebê | Ver o que comprar agora e o que pode esperar |
| Guia dos itens | Uma ficha por item: para que serve, a partir de que idade, marcas, como escolher | Abrir a ficha a partir da planilha |
| Segurança | Regras de sono, transporte, banho e brinquedos por idade | Alertas que também aparecem nas fichas |

Na planilha, cada linha mostra um selo de prioridade: **essencial** (precisa estar pronto antes do parto), **útil** (facilita a rotina) e **pode esperar** (só vale comprar depois de conhecer o bebê).

## Lógica de personalização

A lista nasce de uma base única de itens, e cada resposta do questionário aplica uma regra simples sobre ela.

| Pergunta | O que muda na lista |
| --- | --- |
| Cidade | Escolhe o perfil de clima e quais meses contam como frios |
| Mês previsto | Diz em que estação cada tamanho de roupa será usado |
| Frequência de lavar roupa | Define quantos dias a lista precisa cobrir sem lavar; a conta parte das trocas do bebê, não da rotina de hoje (veja Quantas roupas por dia) |
| Tem carro | Com carro, bebê conforto é essencial desde a saída da maternidade; sem carro, sling e carrinho leve ganham prioridade |
| Apartamento ou casa | Apartamento pequeno sugere berço mais compacto e cômoda com trocador; casa com escada adiciona portão de segurança aos 6 meses |
| Orçamento | Troca a faixa de marcas sugeridas; itens de segurança nunca são cortados |
| Primeiro filho | Se não for, a planilha abre com a coluna Já tenho para marcar |

### Perfis de clima

O site traz uma tabela com as capitais e as principais cidades, e a pessoa pode corrigir o perfil se a cidade dela for mais fria ou mais quente que o padrão.

| Perfil | Exemplos | Meses frios considerados |
| --- | --- | --- |
| Quente o ano todo | Manaus, Belém, Fortaleza, Recife, Salvador, Rio de Janeiro, Cuiabá | Nenhum; só noites mais frescas em junho e julho |
| Inverno moderado | São Paulo, Belo Horizonte, Brasília, Campo Grande | Junho a agosto |
| Inverno frio | Curitiba, Porto Alegre, Florianópolis, cidades de serra | Maio a setembro |

### Como o mês de nascimento entra na conta

Cada tamanho de roupa cobre uma janela de idade: RN até cerca de 1 mês, P de 0 a 3 meses, M de 3 a 6, G de 6 a 9 e GG ou 1 de 9 a 12. A grade muda entre marcas, então o site mostra a regra do peso junto (RN costuma servir até cerca de 4 kg).

O site cruza cada janela com os meses frios do perfil e divide o kit de roupas daquele tamanho em peças de frio e de calor na mesma proporção. Peças só de frio, como casaco, gorro e saco de dormir, aparecem apenas nas janelas com mês frio.

Exemplo com nascimento em junho:

| Tamanho | Meses de uso | Curitiba (inverno frio) | Salvador (quente) |
| --- | --- | --- | --- |
| RN e P | junho a agosto | Quase tudo manga longa, macacão com pé, manta, gorro, saco de dormir | Body manga curta e longa meio a meio, manta leve |
| M | setembro a novembro | Metade manga longa, casaco leve | Body manga curta, shorts e macacão curto |
| G | dezembro a fevereiro | Peças de calor | Peças de calor |
| GG | março a maio | Metade de frio, casaco e meia-calça | Peças de calor |

### Quantas roupas por dia

A quantidade de roupa parte de quantas vezes o bebê costuma ser trocado por dia em cada fase, e não de quantas vezes a casa lava roupa hoje.

    peças = trocas por dia × (dias entre lavagens + 1)

O dia a mais cobre a secagem e os imprevistos. O site mostra o resultado como "com esta lista você fica até 3 dias sem lavar".

| Fase | Trocas de roupa por dia | Por que muda | Peças de cima (lavando a cada 2 dias) |
| --- | --- | --- | --- |
| 0 a 3 meses (RN e P) | 3 a 5 | Regurgitação e vazamento de fralda | 12 (8 bodies e 4 macacões) |
| 3 a 6 meses (M) | 3 a 4 | Menos regurgitação, mais baba | 11 |
| 6 a 9 meses (G) | 2 a 3 | Introdução alimentar suja, mas o babador ajuda | 9 |
| 9 a 12 meses (GG) | 2 a 3 | Engatinhar e brincar no chão | 9 |

As trocas por dia são estimativas a validar com pediatras e famílias. Quem lava 2 vezes por semana precisa de cerca de uma vez e meia a lista; o site avisa quando a quantidade fica alta demais para guardar.

## Roteiro de compras

As compras grandes ficam entre o 5º e o 7º mês de gestação; tudo que depende do tamanho ou da fase do bebê fica para depois do nascimento. No site, as fases viram datas reais a partir da data prevista, e a fase atual aparece destacada.

1. **Até o 5º mês (gestação):** definir orçamento, pesquisar marcas e montar a lista de presentes. Comprar pouco.
2. **5º ao 7º mês (gestação):** itens grandes (berço, colchão, cômoda com trocador), carrinho e bebê conforto.
3. **7º ao 8º mês (gestação):** roupas RN e P, roupa de berço, higiene e fraldas; lavar tudo. Mala da maternidade pronta e bebê conforto instalado até 34 semanas.
4. **Parto.**
5. **0 a 3 meses:** repor fraldas e comprar só o que faltou (sling, bomba de leite). Roupas M para a estação certa.
6. **3 a 6 meses:** roupas G, mordedores, tapete de atividades. No 5º mês: cadeira de alimentação, pratos, colheres, babadores.
7. **6 a 9 meses:** início da introdução alimentar, copo de transição, roupas GG. Antes de engatinhar: protetor de tomada, trava de gaveta, portão.
8. **9 a 12 meses:** primeiro sapato de sola flexível, roupas tamanho 1. Trocar a cadeirinha do carro só quando passar o limite do bebê conforto.

## Planilha base

Quantidades pensadas para quem lava roupa a cada 2 dias. As marcas são exemplos do varejo brasileiro, ainda não conferidos; validar antes de publicar.

### Roupas por tamanho

| Peça | RN | P | M | G | GG |
| --- | --- | --- | --- | --- | --- |
| Body (manga curta ou longa conforme o clima) | 4 | 8 | 7 | 6 | 6 |
| Calça ou mijão | 3 | 6 | 5 | 5 | 5 |
| Macacão | 2 | 4 | 4 | 3 | 3 |
| Casaquinho | 1 | 2 | 2 | 2 | 2 |
| Meias (pares) | 3 | 6 | 5 | 4 | 4 |
| Gorro (só em mês frio) | 1 | 2 | 1 | 1 | 1 |

Peças de qualquer tamanho: 2 mantas, 3 toalhas com capuz, 10 fraldas de pano ou paninhos de boca e, em clima frio, 2 sacos de dormir. Marcas de exemplo: Hering Kids, Carter's, Tip Top, Up Baby, Brandili, linhas de C&A, Renner e Riachuelo. Como escolher: algodão, botões ou zíper na frente, sem laços, fitas ou peças soltas.

### Sono e quarto

| Item | Para que serve | Qtd | Quando · prioridade | Marcas de exemplo | Como escolher |
| --- | --- | --- | --- | --- | --- |
| Berço | Lugar seguro de sono desde o 1º dia | 1 | 5º–7º mês · essencial | Tcil, Reller, Matic; portáteis Burigotto e Galzerano | Selo INMETRO, grades com vão de no máximo 6,5 cm, estrado com regulagem de altura |
| Colchão de berço | Base firme para dormir | 1 | 5º–7º mês · essencial | Ortobom, Castor, Fom | Firme, do tamanho exato do berço, sem vão nas laterais |
| Lençol com elástico | Forrar o colchão | 4 | 7º–8º mês · essencial | Papi, Hering, linhas de loja | Bem justo; nada de edredom, travesseiro ou protetor de berço |
| Cômoda com trocador | Guardar roupas e trocar fralda na altura certa | 1 | 5º–7º mês · útil | Mesmas marcas do berço | Trocador com bordas elevadas, cômoda fixada na parede |
| Babá eletrônica | Ouvir ou ver o bebê de outro cômodo | 1 | 7º–8º mês · útil | Motorola, Philips Avent, Multikids Baby | Alcance para a casa, fio longe do berço |
| Mosquiteiro | Proteger de insetos | 1 | 7º–8º mês · só clima quente | Linhas de loja | Bem preso, sem sobras de tecido dentro do berço |

### Higiene e banho

| Item | Para que serve | Qtd | Quando · prioridade | Marcas de exemplo | Como escolher |
| --- | --- | --- | --- | --- | --- |
| Fraldas descartáveis | Uso diário, de 8 a 12 trocas por dia no início | RN: 2 pacotes; P: cerca de 1 mês de estoque | 7º–8º mês · essencial | Pampers, Huggies, MamyPoko, Turma da Mônica Baby, Personal Baby | Pouco RN; testar marcas antes de estocar |
| Algodão e lenço umedecido | Limpeza na troca | 4 pacotes de algodão, 2 de lenço | 7º–8º mês · essencial | Cremer, Huggies, Pampers | Primeiras semanas: algodão com água; lenço sem perfume e sem álcool |
| Pomada para assadura | Prevenir e tratar assaduras | 2 | 7º–8º mês · essencial | Bepantol Baby, Hipoglós, Desitin | Óxido de zinco ou dexpantenol; confirmar com o pediatra |
| Sabonete e xampu de bebê | Banho | 1 de cada | 7º–8º mês · essencial | Johnson's Baby, Granado Bebê, Mustela, Dove Baby, Natura Mamãe e Bebê | pH neutro, sem perfume forte |
| Banheira com suporte | Banho seguro na altura certa | 1 | 7º–8º mês · essencial | Burigotto, Safety 1st | Estável, com apoio anatômico; balde de banho é alternativa |
| Termômetro corporal digital | Medir febre | 1 | 7º–8º mês · essencial | G-Tech, Omron | Digital, nunca de mercúrio |
| Kit unha e escova macia | Cortar unhas e pentear | 1 | 7º–8º mês · útil | Lillo, Kuka | Tesoura de ponta redonda ou lixa de bebê |
| Aspirador nasal e soro fisiológico | Desentupir o nariz | 1 | 7º–8º mês · útil | NoseFrida, Lillo | Fácil de lavar |

### Passeio e transporte

| Item | Para que serve | Qtd | Quando · prioridade | Marcas de exemplo | Como escolher |
| --- | --- | --- | --- | --- | --- |
| Bebê conforto | Transporte no carro, obrigatório por lei | 1 | 5º–7º mês · essencial com carro | Maxi-Cosi, Cybex, Chicco, Burigotto, Safety 1st, Infanti | Selo INMETRO, voltado para trás, testar no carro; evitar usado sem histórico |
| Carrinho | Passeios do dia a dia | 1 | 5º–7º mês · essencial | Burigotto, Galzerano, Chicco, ABC Design, Cybex | Encosto que deita totalmente, cinto de 5 pontos, cabe no porta-malas |
| Sling ou canguru | Carregar o bebê com as mãos livres | 1 | 0–3 meses · útil | Ergobaby, Infanti, Chicco | Posição M (joelhos acima do bumbum), rosto sempre visível |
| Bolsa maternidade e trocador portátil | Levar o necessário nas saídas | 1 | 7º–8º mês · essencial | Masterbag, linhas de loja | Bolsos separados e trocador lavável |

### Alimentação

| Item | Para que serve | Qtd | Quando · prioridade | Marcas de exemplo | Como escolher |
| --- | --- | --- | --- | --- | --- |
| Almofada de amamentação | Apoiar o bebê e a coluna de quem amamenta | 1 | 7º–8º mês · útil | Linhas de loja | Capa removível; nunca usar para o bebê dormir |
| Bomba tira-leite | Tirar e guardar leite | 1 | 0–3 meses · pode esperar | Medela, Philips Avent | Só se precisar; manual basta para uso ocasional |
| Mamadeira | Leite tirado ou fórmula | 2 | 0–3 meses · pode esperar | Philips Avent, MAM, NUK, Lillo, Kuka | Livre de BPA; só comprar se houver indicação |
| Cadeira de alimentação | Comer sentado e seguro | 1 | 5º mês · essencial | Burigotto, Chicco, Safety 1st, Galzerano | Cinto de 5 pontos, base larga, bandeja lavável |
| Pratos, colheres e babadores | Introdução alimentar | 2 pratos, 3 colheres, 4 babadores | 5º mês · essencial | MAM, NUK, Buba, Lillo | Silicone ou plástico livre de BPA, colher macia |
| Copo de transição | Oferecer água a partir dos 6 meses | 1 | 6–9 meses · essencial | NUK, MAM, Lillo | Alça e bico macio ou borda 360 |

### Segurança da casa

| Item | Para que serve | Qtd | Quando · prioridade | Marcas de exemplo | Como escolher |
| --- | --- | --- | --- | --- | --- |
| Protetor de tomada | Evitar choque | Uma por tomada baixa | 6–9 meses · essencial | Safety 1st, Multikids Baby | Difícil de remover pela criança |
| Trava de gaveta e armário | Afastar produtos de limpeza e objetos cortantes | 6 a 10 | 6–9 meses · essencial | Safety 1st, Multikids Baby | Adesiva ou magnética |
| Portão de segurança | Bloquear escada e cozinha | 1 por acesso | 6–9 meses · só casa com escada | Safety 1st, Burigotto | Parafusado no topo de escadas |
| Protetor de quina | Amortecer batidas | 1 kit | 9–12 meses · útil | Safety 1st, Multikids Baby | Silicone bem aderido |

### Para a mãe

| Item | Para que serve | Qtd | Quando · prioridade | Marcas de exemplo | Como escolher |
| --- | --- | --- | --- | --- | --- |
| Absorvente pós-parto | Sangramento das primeiras semanas | 2 a 3 pacotes | 7º–8º mês · essencial | Intimus, Always, linhas de farmácia | Noturno de fluxo intenso, sem perfume |
| Calcinha pós-parto | Conforto e apoio do absorvente | 5 | 7º–8º mês · essencial | Linhas de loja | Cintura alta, algodão |
| Sutiã de amamentação | Amamentar sem tirar a peça | 3 | 8º mês · essencial | Linhas de lingerie e de loja | Comprar perto do parto, um número acima, sem aro |
| Protetor de seios | Absorver vazamento de leite | 1 caixa ou 3 pares laváveis | 8º mês · útil | Lansinoh, Philips Avent, Lillo | Trocar sempre que úmido |
| Pomada para mamilo | Aliviar fissuras | 1 | 8º mês · útil | Lansinoh, Medela | Lanolina pura; confirmar com quem acompanha a amamentação |
| Camisola ou pijama com abertura | Amamentar na maternidade e em casa | 3 | 8º mês · essencial | Linhas de loja | Botões na frente |
| Chinelo e itens de banho | Mala da maternidade | 1 kit | 8º mês · essencial | Qualquer | Chinelo antiderrapante |
| Garrafa de água grande | Hidratação na amamentação | 1 | 8º mês · útil | Qualquer | Com canudo, para usar com uma mão |
| Cinta pós-parto | Apoio abdominal | 1 | Depois do parto · só com indicação médica | Linhas de farmácia | Só se o médico indicar |

## Segurança por idade

Segurança é regra fixa: nenhum orçamento ou preferência remove um item ou alerta. Referências (SBP, INMETRO, CONTRAN) vieram de conhecimento geral e precisam ser conferidas nas fontes.

| Idade | Regras que o site destaca | Base |
| --- | --- | --- |
| Sempre | Produtos infantis com selo INMETRO; nada de cordão no pescoço ou prendedor de chupeta longo | INMETRO |
| 0 a 12 meses | Dormir de barriga para cima, no berço, colchão firme, sem travesseiro, edredom, protetor de berço ou pelúcias | SBP |
| 0 a 12 meses | No carro, sempre no bebê conforto voltado para trás, banco traseiro, desde a maternidade | CONTRAN |
| 0 a 6 meses | Nunca deixar o bebê sozinho no trocador ou na banheira; água entre 36 e 37 °C | SBP |
| 0 a 6 meses | Sling com rosto visível e queixo longe do peito | Carregamento ergonômico |
| 6 a 9 meses | Introdução alimentar a partir dos 6 meses, sentado com cinto; sem mel até 1 ano, sem açúcar até 2 anos | SBP |
| 6 a 12 meses | Proteger tomadas, gavetas e escadas antes de engatinhar; móveis fixados na parede | SBP |
| 6 a 12 meses | Andador não é recomendado; brinquedos 0–3 anos sem peças pequenas | SBP, INMETRO |

## Em aberto

- Mostrar faixas de preço ou só quantidades (sugestão: começar só com quantidades).
- Nome do site.
- Links de afiliados ficam fora da primeira versão.
