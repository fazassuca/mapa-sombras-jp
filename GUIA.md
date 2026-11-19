# Guia: publicar o Mapa de Sombras no seu GitHub

## Conteúdo da pasta
- `pipeline.py`: lê o Sentinel-2 de cada ano (2019 até hoje), mede a cobertura de copa nas ruas e gera os dados.
- `index.html`: o site (mapa interativo; círculos de sombra aparecem a partir do zoom 16).
- `requirements.txt`: bibliotecas Python.
- `.github/workflows/atualizar.yml`: atualiza os dados sozinho todo mês.
- `data/`: onde os arquivos gerados ficam.

## 1. Preparar o computador
1. Instale **Python 3.11 ou 3.12** (python.org; evite versões muito novas, como 3.14 ou 3.15, porque as bibliotecas de mapas ainda não funcionam bem nelas) e **Git** (git-scm.com).
2. Crie uma conta no **github.com**, se ainda não tiver.

## 2. Gerar os dados (1ª vez)
No terminal, dentro da pasta do projeto:

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python pipeline.py
```
Leva de 10 a 20 minutos por ano (a 1ª execução, com todos os anos, pode passar de 1 hora) e precisa de internet. Ao final, `data/` terá `segments.geojson` (ruas), `cov_ANO.json` e `trees_ANO.json` (um par por ano) e `anos.json`.
Anos já calculados são pulados nas próximas execuções; só o ano atual é refeito.
Não precisa de conta nem chave de API (o Planetary Computer é aberto).

**Opcional, ranking por bairro:** baixe os limites de bairros de João Pessoa (portal de dados abertos da prefeitura ou IBGE), salve como `data/bairros.geojson` com uma coluna `nome` apague `data/segments.geojson` e os `data/cov_*.json` e rode o `pipeline.py` de novo (as ruas são recriadas com o bairro).

### No Mac: se aparecer "command not found: python"
O Mac usa `python3` no lugar de `python` (fora do ambiente virtual). Rode:

```bash
python3 --version
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python pipeline.py
```
Depois do `source .venv/bin/activate` (o terminal passa a mostrar `(.venv)` no início da linha), `python` e `pip` já funcionam normalmente.
Se `python3 --version` pedir para instalar as "ferramentas de linha de comando", aceite e espere terminar. Se disser que não encontra o `python3`, instale pelo python.org ou com `brew install python`, e abra um terminal novo.
Para o teste local (passo 3), com o ambiente ativo, `python -m http.server 8000` funciona; fora dele, use `python3 -m http.server 8000`.

### Se aparecer "python não é reconhecido como comando" (Windows)
1. Teste primeiro com `py` no lugar de `python`: digite `py --version`. Se mostrar a versão, use `py` em todos os comandos (`py -m venv .venv`, `py pipeline.py`).
2. Se `py` também falhar, reinstale o Python em python.org e, **na primeira tela do instalador, marque "Add python.exe to PATH"** antes de clicar em Install. Feche e abra o terminal depois.
3. Se abrir a Microsoft Store ao digitar `python`: em **Configurações → Aplicativos → Configurações avançadas de aplicativos → Aliases de execução de aplicativo**, desligue os itens "python.exe" e "python3.exe".
4. No Windows, ative o ambiente com `.venv\Scripts\activate` (o `source` é só para Mac e Linux). Se o PowerShell reclamar de "execução de scripts desabilitada", rode antes: `Set-ExecutionPolicy -Scope Process Bypass`.

## 3. Testar localmente
```bash
python -m http.server 8000
```
Abra http://localhost:8000. Aproxime até o zoom da rua para ver as copas redondas.

## 4. Subir para o GitHub
1. No GitHub: **New repository**, nome `mapa-sombras-jp`, público, sem README.
2. No terminal:
```bash
git init
git add .
git commit -m "Primeira versão"
git branch -M main
git remote add origin https://github.com/SEU_USUARIO/mapa-sombras-jp.git
git push -u origin main
```
(Garanta que `.venv/` não suba: crie um arquivo `.gitignore` com a linha `.venv/`.)

## 5. Colocar o site no ar (GitHub Pages)
1. No repositório: **Settings → Pages**.
2. Em *Source*, escolha **Deploy from a branch**, branch `main`, pasta `/ (root)`. Salve.
3. Em ~2 minutos o site abre em `https://SEU_USUARIO.github.io/mapa-sombras-jp/`.

## 6. Atualização automática
O arquivo `atualizar.yml` já refaz o mapa todo dia 1. Para rodar na hora: aba **Actions → Atualizar mapa → Run workflow**.
Se o Actions der erro de permissão: **Settings → Actions → General → Workflow permissions → Read and write**.

## 7. Ver o mapa em anos anteriores
No site há dois modos:
- **Sombra:** use o controle de ano (ou o ▶ para animar) e toque nas barras do gráfico para ver cada ano.
- **Mudança no tempo:** compara dois anos. Azul = ganhou sombra, laranja = perdeu, cinza = estável. O ranking mostra os bairros que mais perderam sombra.

Para mudar os anos, edite `ANOS` no topo do `pipeline.py` (o Sentinel-2 em nível L2A cobre bem a partir de 2019). A época do ano é fixa (`JANELA`, setembro a dezembro) para comparar situações iguais.

## 8. Ajustes úteis (topo do `pipeline.py`)
- `NDVI_ARVORE`: sobe para 0.5 se aparecerem manchas em gramados ou terrenos.
- `MAX_NUVEM` e `DIAS`: mais cenas ajudam na estação chuvosa.
- Cores verde/amarelo/vermelho: limites de 40% e 20% na função `cls` do `index.html`.

## Limites a declarar ao apresentar ao governo
- Na comparação entre anos, mudanças pequenas (abaixo de 10 pontos de cobertura) podem ser ruído de nuvem, chuva ou calibração do satélite; por isso são mostradas como estáveis. Mudanças grandes e concentradas valem confirmar com imagem de alta resolução.
- O Sentinel-2 tem **10 m por pixel**: mede cobertura de copa, não conta árvores individuais. Em ruas estreitas, árvores de quintais vizinhos podem entrar na conta.
- As manchas redondas são uma **representação visual** da copa, não a sombra exata (que varia com hora e estação).
- Para o relatório final, valide uma amostra de ruas em campo ou com imagens de drone/ortofoto.

## 9. Satélite, árvores individuais e argumentos
- O botão **Satélite** do site mostra imagens de satélite de fundo (Esri World Imagery) para o público conferir as árvores a olho. Confira os termos de uso da Esri ao publicar.
- Não use o Google Maps para extrair dados das imagens (os termos proíbem). Para detectar árvores individuais, use ortofoto da prefeitura ou de drone e o `detecta_arvores.py`. O resultado (`data/trees_ortho.json`) aparece no site como uma camada opcional.
- `docs/FILIPEIA.md`: o que baixar no portal da prefeitura e quais pedidos fazer pela Lei de Acesso à Informação.
- O painel do site traz os argumentos ligados ao Programa João Pessoa Sustentável e ao Plano Diretor. O botão **Imprimir relatório** gera uma versão para PDF com os dados da tela. Revise os textos com um advogado ou urbanista antes de protocolar.

## 10. Dados da prefeitura, busca por rua e piloto de ortofoto
- Leia `docs/DADOS_RECEBIDOS.md`: ele explica cada arquivo enviado pela prefeitura e a ordem para usar.
- Coloque os shapefiles descompactados em `data/shp/`. Com eles, o `pipeline.py` usa as ruas oficiais, o nome de cada rua e as comunidades urbanas. **Apague `data/segments.geojson` e `data/cov_*.json` antes de rodar de novo**, porque a fonte das ruas mudou.
- No site, a caixa **Veja a sua rua** busca pelo nome da rua, mostra a sombra ano a ano e leva ao pedido de plantio. No `index.html`, troque a constante `URL_SOLICITAR` (no começo do script) pelo link exato do serviço no portal do cidadão.
- O piloto de ortofoto (`ortofoto_piloto.py`) já vem com resultados em `data/ortho_*.json` para três áreas. As fotos (`.tif`, cerca de 130 MB cada) **não** vão para o GitHub: deixe-as só no seu computador, em `data/ortofotos/`, e coloque `data/ortofotos/` e `data/shp/` no `.gitignore` se não tiver autorização para publicá-los.
- Confirme com a prefeitura a licença de uso das ortofotos e dos shapefiles antes de publicar qualquer derivado.

## 11. Escolas e creches, PAI e portal do cidadão
- Copie `equipamento_educacao.*` (descompactado) para `data/shp/` e rode `python pipeline.py`. O site passa a mostrar a lista das escolas e creches com menos sombra no entorno e os pontos no mapa. Esse trecho do `pipeline.py` não foi testado com os seus dados; se der erro, me envie a mensagem.
- O botão "Solicitar uma árvore na minha calçada" aponta para o Portal do Cidadão (`https://prefeituraconectada.joaopessoa.pb.gov.br/portal/`). Se descobrir o link direto do serviço, troque a constante `URL_SOLICITAR` no `index.html`.
- As ações do PAI citadas no painel estão resumidas em `docs/DADOS_RECEBIDOS.md`, com a página de cada uma.

## 12. Painel novo, calibração e limiares
- O `index.html` agora é um painel: menu lateral, indicadores, mapa, gráfico de evolução, rosca de distribuição, ranking de bairros, escolas, equidade, CAU e argumentos. Pedir uma árvore tem cartão fixo e botão no topo.
- Para conferir as cores do mapa contra as fotos aéreas: `python calibra.py` (depois do `pipeline.py` e do `ortofoto_piloto.py`). Use o limite sugerido nos campos "Boa" e "Parcial" do cartão "Como ler as cores".
- Fotos aéreas: `python ortofoto_piloto.py` gera `data/trees_ortho.json` (círculos). Com `PREVIA=1` ele salva imagens de conferência (`previa_*.jpg`). Se aparecer árvore demais ou de menos, mude `V_ARVORE`.
- Se a busca por rua disser que não encontra nada, rode `python pipeline.py` com os shapefiles em `data/shp/`; o script refaz as ruas sozinho quando o arquivo é antigo.
