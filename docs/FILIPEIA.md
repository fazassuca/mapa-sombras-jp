# O que baixar no portal Filipeia (filipeia.joaopessoa.pb.gov.br)

Observação: lista montada a partir do que outras fontes documentam sobre o portal (camadas de bairros, praças, parques, rios, comunidades, corredores e ciclovias; shapefiles de logradouros e curvas de nível; ortofoto e nuvem de pontos de áreas específicas; Atlas Municipal com perfil de bairro). Confirme os nomes exatos dentro do portal.

## Prioridade 1 (baixe agora)
| Camada | Para que serve no projeto | Onde entra |
|---|---|---|
| Bairros (shapefile) | Ranking por bairro e relatórios | salvar como `data/bairros.geojson` (coluna `nome`) |
| Limite municipal | Recortar a área de análise | conferir o `BBOX` do `pipeline.py` |
| Comunidades / favelas / ZEIS | Mostrar desigualdade: ruas sem sombra em áreas vulneráveis (o Plano Diretor dá prioridade a elas) | cruzar com os trechos |
| Praças e parques | Medir sombra em espaços públicos (praças acima de 5.000 m² são zona de proteção na minuta do PDM) | camada extra |
| Logradouros / faces de quadra | Nomes de ruas para listar "as 50 ruas mais quentes" nos relatórios | cruzar com os trechos |

## Prioridade 2
- Corredores de ônibus, faixas exclusivas e ciclovias: são os eixos que o Plano Diretor quer adensar; defender "corredor sombreado" para pedestres.
- Rios (e faixas de preservação): onde plantar sem conflito e onde há APP.
- Escolas públicas (INEP) e unidades de saúde: sombra no entorno de escolas e postos.
- Atlas Municipal (perfil de bairro, PDF): área em hectares, comunidades e ZEIS por bairro; ajuda a calcular árvores por hectare.

## Prioridade 3 (mudam a qualidade do mapa)
- **Ortofoto e nuvem de pontos (LiDAR)**, se existirem para sua região de interesse: com elas dá para detectar árvores individuais (`detecta_arvores.py`). Pergunte à Seplan a data, a resolução e a cobertura. Verifique a licença de uso antes de publicar.
- Curvas de nível: só se for cruzar com drenagem e alagamentos.

## Pedidos formais à Prefeitura (Lei de Acesso à Informação)
1. Cadastro georreferenciado de árvores de vias públicas (Semam), com espécie e data.
2. Plano de Arborização Urbana de 2012 e relatório de execução.
3. Lista das ações de arborização no Plano de Ação e Investimentos do Plano Diretor, com status, custo e responsável.
4. Ortofotos ou imagens aéreas mais recentes, com resolução e data.
5. Saldo, prazo e possibilidade de realocação de recursos do Programa João Pessoa Sustentável (UEP/Segov).

## Também útil fora do Filipeia
- IBGE: setores censitários (população e renda) para análise de equidade.
- Plano Diretor: documentos em planodiretor.joaopessoa.pb.gov.br/documentos (Cartilha, P5b Diretrizes e Propostas e P6b Plano de Ação e Investimentos são os mais úteis).
