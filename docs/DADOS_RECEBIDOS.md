# Dados da prefeitura: o que cada arquivo é e como usar

## Resumo
| Arquivo | O que é | Uso no projeto |
|---|---|---|
| `Logradouro_gerais.zip` (LOGRADOUROS_ATIVOS.shp) | 23.450 trechos de rua, cerca de 2.160 km, 6.431 nomes, com tipo de pavimento (pedra, asfalto, sem pavimento). Sistema SIRGAS 2000 UTM 25S | **Base oficial das ruas**. Substitui o OpenStreetMap, dá o nome das ruas (busca por rua) e permite cruzar com o pavimento |
| `Logradouro_gerais.csv` | Tabela de um conjunto parecido, com colunas de nome diferentes das do shapefile | Não precisa. Use o shapefile |
| `bairros.zip` | 64 bairros (só o nome, coluna `N_BAIRRO`) | Ranking por bairro |
| `bairros.csv` | Área em hectares e densidade por bairro | Futuro: árvores por hectare e por habitante |
| `favela_comunidade_urbana.zip` | 157 polígonos de comunidades urbanas (nome, bairro, fonte) | **Equidade**: sombra nas comunidades x resto da cidade |
| `comunidades.csv` | 91 comunidades com área, sem mapa | Não precisa (o shapefile é mais completo) |
| `hidrografia.zip` | Rios e córregos | Futuro: faixas de preservação e áreas de plantio ao longo dos rios |
| `pracas.csv` | 215 praças com bairro, situação de reforma, lei e área, **sem coordenadas** | Só tabela. Peça o shapefile de praças para medir a sombra de cada uma |
| `MapaJoaoPessoa90x90_ParquesPracas.pdf` | Mapa de parques e praças (fev/2021) | Só consulta (não tem dados vetoriais) |
| `GEOVIAS_PDF_A3.zip` | Imagens A3 de mapas por bairro | Só consulta visual. Não foi usado |
| Anexos do Plano Diretor (macrozoneamento, eixos de transporte público) | Mapas da lei | Argumentos e priorização (veja abaixo) |
| `CARTILHA_LACESSE...pdf` | Cartilha de acessibilidade das calçadas (Seplan e UFPB, 2025) | Regras de largura da calçada e de plantio |
| `2946-2090.tif`, `2952-2079.tif`, `2963-2079.tif` | **Ortofotos de 10 cm**, cada uma com 575 m x 575 m, RGB | Piloto de detecção de copas (veja abaixo) |

O anexo do Sistema Viário (`A0_P_MUN_ANEXO_ANEXO_I_DA_LEI_DO_SISTEMA_VIARIO.pdf`) não chegou legível para mim. Se quiser que eu o use, envie de novo ou me diga a página que importa.

## As três ortofotos
- São **ortofotos reais**: 5.750 x 5.750 pixels, 10 cm por pixel, georreferenciadas em SIRGAS 2000 UTM 25S. Os arquivos são de julho de 2022; confirme com a prefeitura a data do voo.
- `2946-2090`: dentro da Mata do Buraquinho (floresta, sem ruas). `2952-2079`: borda de Água Fria e Cidade dos Colibris (mata, prédios públicos e casas). `2963-2079`: Jardim Cidade Universitária (bairro residencial).
- Juntas cobrem cerca de 1 km². É um **piloto**, não a cidade.
- Resultado do piloto (`ortofoto_piloto.py`): nos trechos medidos, a cobertura de copa foi de 68% perto da mata e de 27% no bairro residencial. As ruas oficiais ficam alinhadas com as fotos.
- O método usa cor, brilho e textura. Separa bem copas de telhados e ruas, mas ainda pode incluir grama alta como copa. Valide uma amostra em campo antes de divulgar números.

## SIGWeb (mapa de árvores da prefeitura)
Eu não consegui abrir o portal daqui (ele bloqueia acesso automático), então não sei qual é a base técnica dele. Caminhos corretos para obter os dados:
1. **Pedido pela Lei de Acesso à Informação** à Seplan e à Semam: a camada de árvores do SIGWeb em shapefile ou GeoJSON, com data do levantamento, espécie, porte e a metodologia.
2. Pergunte se o SIGWeb publica **serviços de mapa** (WMS/WFS/REST). Se publicar, o QGIS lê esses serviços direto e dá para exportar a camada.
3. Se a camada for só visual, peça também as ortofotos e o levantamento original.
Com essa camada, dá para comparar o Sentinel-2 com o cadastro e mostrar no site as árvores mapeadas pela prefeitura.

## Plano Diretor: como usar os anexos
- **Macrozoneamento**: Macrozona de Proteção Ambiental, Macrozonas Adensáveis 1 a 3, bordas de tabuleiro e faixa de 500 m das praias. Dá para cruzar com as ruas e mostrar, por exemplo, a sombra nas áreas que o plano manda adensar.
- **Eixos de estruturação do transporte público** (troncais e complementares): são as ruas por onde o plano quer concentrar gente e ônibus. Argumento: caminhar até o ponto precisa de sombra. Peça o shapefile desse anexo para cruzar com as ruas.

## Cartilha de acessibilidade: o que ela muda na proposta
- Calçada nova: faixa livre de pelo menos 1,20 m mais faixa de serviço de pelo menos 0,75 m, ou seja, 1,95 m ou mais. A árvore entra na faixa de serviço.
- Árvore de pequeno porte: calçadas a partir de cerca de 1,9 m. Médio porte: mais de 2,2 m. Grande porte não se aplica a calçadas.
- A cartilha afirma que calçadas acessíveis devem ser confortáveis, inclusive sob o sol, e podem ser arborizadas. Use essa frase como apoio.
- Efeito prático: em ruas de calçada estreita, a prefeitura só consegue plantar se alargar a calçada. Dá um bom argumento para o projeto de requalificação.

## Como montar tudo
1. Descompacte `Logradouro_gerais.zip`, `bairros.zip` e `favela_comunidade_urbana.zip` na pasta `data/shp/` (mantenha todos os arquivos de cada conjunto).
2. Apague `data/segments.geojson` e `data/cov_*.json` se já existirem (as ruas mudaram de fonte).
3. `python pipeline.py`
4. Para refazer o piloto de ortofoto: coloque os `.tif` em `data/ortofotos/` e rode `python ortofoto_piloto.py`.

---

# Segunda remessa de dados

| Arquivo | O que é | Uso no projeto |
|---|---|---|
| `Censo_2022_-_João_Pessoa.csv` | Só totais da cidade, sem divisão por bairro: 833.932 moradores, 162.069 com até 14 anos, 123.614 com 60 anos ou mais, 377.756 domicílios | Argumento "quem sente mais o calor" (34% da população está nessas faixas de idade). Para equidade por bairro falta o dado por setor censitário, que o IBGE publica |
| `equipamento_educacao.zip` | 247 pontos da rede municipal (CMEI 113, EMAI 105, EMEI 3, EM 3, anexos 7 e outros), 230 em funcionamento | **Módulo de escolas e creches**: sombra nas ruas em volta, num raio de 150 m |
| `115_2022_02_25_P5b_DIRETRIZES_E_PROPOSTAS_V02.pdf` | Diretrizes e propostas do Plano Diretor (fev/2022) | Proposta 1.6 (plantio de árvores) e 24.9 (ampliar a arborização das vias) |
| `115_2022_11_21_P6b_PAI_R07.pdf` | Plano de Ação e Investimentos, versão R07 (nov/2022) | Ações com prioridade, prazo, custo, responsável e indicador (veja abaixo) |
| `115_CARTILHA-DO-PDMJP_R10-2.pdf` | Cartilha do Plano Diretor (2023) | Metas do plano (áreas verdes e permeáveis contra ilhas de calor; fruição pública para calçadas) |
| Mapas Educação, Saúde e SEJER (PDF) | Mapas de 2021 e 2023. Saúde: 163 unidades com bairro e distrito sanitário. SEJER: 44 unidades (campos, ginásios, poeirões, centros de juventude) | Só consulta, sem coordenadas. Peça os shapefiles de saúde e SEJER para repetir o módulo de escolas |

## O que o PAI diz sobre árvores
Leitura das páginas 27, 30 e 76 do PAI (R07). Prazos: curto até 3 anos, médio de 4 a 7 anos.

| Ação | Meta | Prioridade | Prazo | Responsável |
|---|---|---|---|---|
| Eixo Ambiental, diretriz 1, ação f: plantio de árvores em vias, parques e canteiros | Aumentar em até 50% a arborização do município. Custo estimado: R$ 3.139.600.000. Indicador: número de árvores plantadas por ano | Média | Médio | Semam (com Sedest, Emlur, Seduc, Setur, Seplan, Semob e Sedurb) |
| Eixo de Mobilidade, diretriz 24, ação h: programa de arborização das vias públicas | Criar o programa. Custo administrativo. Indicador: criação do programa | **Alta** | **Longo** | Semam, Semob e Seplan |
| Eixo Ambiental, diretriz 3, ação c: Plano de Arborização Municipal | Indicar espécies e tornar o plantio condição do habite-se | Média | Longo | Semam e Seplan |
| Eixo de Mobilidade, diretriz 24: programa de implantação e revitalização de calçadas, e norma de padronização de calçadas | Acessibilidade universal, com foco nos grandes eixos e no Centro Histórico | Alta | Curto | Seplan, Semob e Sedurb |

**Como usar:** o programa de arborização das vias é de prioridade alta, mas está no longo prazo e custa só trabalho administrativo. O pedido natural é antecipá-lo para o curto prazo e fazê-lo andar junto com o programa de calçadas, que já é de curto prazo. O indicador "árvores plantadas por ano" dá uma régua pública para cobrar.

Cuidados: a versão do PAI é de nov/2022, anterior à lei sancionada. O custo de R$ 3,14 bilhões está assim no documento e parece cobrir o conjunto da ação, não só o plantio; vale perguntar à Seplan o que ele inclui.

## Pedidos adicionais à Prefeitura (Lei de Acesso à Informação)
6. Série anual do indicador "número de árvores plantadas por ano" (PAI, ação 1.f), e o estágio do programa de arborização das vias (ação 24.h) e do Plano de Arborização Municipal (ação 3.c).
7. Cronograma oficial dos prazos curto, médio e longo do PAI, com datas de início.
8. Os shapefiles de unidades de saúde e da SEJER (mesma base dos mapas em PDF).

## Como montar o módulo de escolas
Coloque `equipamento_educacao.*` em `data/shp/` e rode `python pipeline.py`. Ele gera `data/escolas.json`. O site mostra a lista das escolas com menos sombra no entorno e, com a caixa marcada, os pontos no mapa.

---

# Terceira remessa: CAU e ajustes

## Cadastro Ambiental Urbano (CAU)
- O arquivo público tem 12.437 registros (set/2020 a jan/2026), sem coordenadas. **O campo município vem em branco em 96% das linhas** (só 501 informam UF e município), então não dá para filtrar "João Pessoa" só por esse campo.
- Só um registro traz João Pessoa no campo município (uma nascente em rascunho). Para achar os demais, li o nome, a descrição e as palavras-chave de cada linha e guardei apenas os que ligam claramente a João Pessoa: **15 registros, 11 publicados, 126 ha de área verde demarcada** (Parque Linear Parahyba, Arruda Câmara, Sólon de Lucena, Augusto dos Anjos e sete praças). Cada um tem a evidência no campo `evid` de `data/cau_joao_pessoa.json`.
- Pode haver outros registros de João Pessoa sem o município preenchido e sem citar a cidade no texto. Peça à administração do CAU (ou à Semam) a exportação **por município**, com coordenadas.
- Leitura: perto das 215 praças do cadastro da Prefeitura, só 8 praças aparecem no CAU. Dá um argumento: a cidade quase não usa a plataforma federal de planejamento da arborização.

## O que mudou no site
- **Busca por rua e bairro**: a causa mais provável da mensagem "não existe" é um `data/segments.geojson` antigo, sem nome de rua. O `pipeline.py` agora detecta isso, apaga e refaz as ruas; o site mostra um aviso claro quando os dados não têm nomes.
- **Cores**: os limites passaram de 40% e 20% para **30% (boa) e 15% (parcial)**, com base na referência 3-30-300 (30% de copa por bairro), e podem ser mudados no próprio site. O satélite de 10 m tende a subestimar árvores em ruas estreitas. Para medir isso, rode `python calibra.py` (compara o satélite com as fotos aéreas das áreas piloto e diz que limite do satélite equivale a 30% de copa real).
- **Fotos aéreas**: cada copa agora é um **círculo**. A separação entre árvore e vegetação baixa usa o brilho da mancha (copa escura = árvore). É uma estimativa sem dados de altura. Ajuste `V_ARVORE` (padrão 95) se precisar: `V_ARVORE=85 python ortofoto_piloto.py`. A previa com os círculos sai com `PREVIA=1`.
- **Pedir árvore**: botão no topo e cartão fixo no painel, sem depender de escolher uma rua.
