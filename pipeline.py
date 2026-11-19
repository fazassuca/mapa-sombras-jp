"""Mapa de sombras de João Pessoa, ano a ano (2019 até hoje).
Sentinel-2 (Planetary Computer) + ruas do OpenStreetMap. Gera em data/:
  segments.geojson   trechos de rua (geometria, nome, bairro, comunidade), criado uma única vez
                     (usa data/shp/ com os shapefiles da prefeitura; sem eles, usa o OpenStreetMap)
  cov_ANO.json       cobertura de copa (0 a 1) de cada trecho naquele ano
  trees_ANO.json     manchas de copa [lon, lat, raio_m] para o zoom da rua
  anos.json          lista de anos disponíveis
  escolas.json       sombra no entorno (150 m) de escolas e creches (se houver data/shp/equipamento_educacao.shp)
Anos já calculados são pulados; só o ano atual é refeito a cada execução."""
import json, os, sys, warnings
from datetime import date
import numpy as np, geopandas as gpd, osmnx as ox
import planetary_computer as pc, pystac_client, stackstac
from pyproj import Transformer
from rasterio import features
from rasterio.enums import Resampling
from rasterstats import zonal_stats
from shapely.ops import substring

CIDADE = "João Pessoa, Paraíba, Brazil"
BBOX = (-34.99, -7.25, -34.76, -7.03)   # oeste, sul, leste, norte
HOJE = date.today()
ANOS = list(range(2019, HOJE.year + 1))
JANELA = ("09-01", "12-31")             # mesma época todo ano (menos nuvem, comparação justa)
MAX_NUVEM, N_CENAS = 20, 12
EPSG = 32725                            # UTM 25S
SEG, BUFFER = 80, 12                    # metros: tamanho do trecho, largura de cada lado da rua
NDVI_MIN, NDVI_MAX = 0.25, 0.65         # NDVI que vira 0% e 100% de copa
NDVI_ARVORE = 0.45                      # acima disso o pixel vira mancha de árvore
os.environ.setdefault("SHAPE_RESTORE_SHX", "YES")   # recria o .shx quando o shapefile vem sem ele
D = "data"; os.makedirs(D, exist_ok=True)
cat = pystac_client.Client.open("https://planetarycomputer.microsoft.com/api/stac/v1", modifier=pc.sign_inplace)

SHP = f"{D}/shp"   # coloque aqui os shapefiles descompactados da prefeitura

def carrega_segmentos():
    f = f"{D}/segments.geojson"
    if os.path.exists(f):
        s = gpd.read_file(f)
        if "n" in s.columns:
            print("Usando segments.geojson existente (apague-o, e os cov_*.json, para refazer as ruas)")
            s = s.to_crs(EPSG)
            for c, v in (("b", ""), ("k", 0)):
                if c not in s.columns: s[c] = v
            return s
        print("segments.geojson antigo, sem nome de rua: vou refazer as ruas e os arquivos que dependem dele.")
        for x in [f] + glob.glob(f"{D}/cov_*.json") + glob.glob(f"{D}/trees_[0-9]*.json") + [f"{D}/escolas.json"]:
            if os.path.exists(x): os.remove(x)
    oficial = f"{SHP}/LOGRADOUROS_ATIVOS.shp"
    if os.path.exists(oficial):
        print("Usando os logradouros oficiais da prefeitura...")
        ruas = gpd.read_file(oficial).to_crs(EPSG).explode(index_parts=False)
        ruas = ruas[ruas.geometry.geom_type == "LineString"]
        col = "nome_logr" if "nome_logr" in ruas.columns else "NOME_LOGR"
        nomes = ruas[col].fillna("").astype(str).str.split().str.join(" ")
    else:
        print("Baixando ruas do OpenStreetMap (sem shapefile da prefeitura em data/shp)...")
        G = ox.convert.to_undirected(ox.graph_from_place(CIDADE, network_type="drive"))
        ruas = ox.graph_to_gdfs(G, nodes=False).to_crs(EPSG)
        nomes = ruas["name"].fillna("").astype(str).str.upper() if "name" in ruas.columns else [""] * len(ruas)
    partes, nm = [], []
    for g, n_ in zip(ruas.geometry, nomes):
        n = max(1, round(g.length / SEG))
        for k in range(n):
            p = substring(g, g.length * k / n, g.length * (k + 1) / n)
            if p.geom_type == "LineString" and p.length > 1:
                partes.append(p); nm.append(n_)
    seg = gpd.GeoDataFrame({"n": nm}, geometry=partes, crs=EPSG).reset_index(drop=True)
    seg["b"], seg["k"] = "", 0
    pts = gpd.GeoDataFrame(geometry=seg.geometry.interpolate(0.5, normalized=True), crs=EPSG)
    bf = next((x for x in (f"{SHP}/bairros.shp", f"{D}/bairros.geojson") if os.path.exists(x)), None)
    if bf:
        b = gpd.read_file(bf).to_crs(EPSG)
        col = next((c for c in ("N_BAIRRO", "nome", "NOME") if c in b.columns), [c for c in b.columns if c != "geometry"][0])
        j = gpd.sjoin(pts, b[[col, "geometry"]], how="left", predicate="within")
        seg["b"] = j[~j.index.duplicated()][col].fillna("").astype(str).str.title().values
    cf = f"{SHP}/favela_comunidade_urbana.shp"
    if os.path.exists(cf):                      # comunidades urbanas: base para olhar equidade
        c = gpd.read_file(cf).to_crs(EPSG)
        c["geometry"] = c.buffer(15)
        j = gpd.sjoin(pts, c[["geometry"]], how="left", predicate="within")
        seg["k"] = j[~j.index.duplicated()]["index_right"].notna().astype(int).values
    out = seg.to_crs(4326)
    feats = [{"type": "Feature", "properties": {"n": n, "b": b, "k": int(k)},
              "geometry": {"type": "LineString", "coordinates": [[round(x, 5), round(y, 5)] for x, y in g.coords]}}
             for g, n, b, k in zip(out.geometry, out.n, out.b, out.k)]
    json.dump({"type": "FeatureCollection", "features": feats}, open(f, "w"), separators=(",", ":"))
    return seg

def ndvi_do_ano(ano):
    fim = min(HOJE, date(ano, 12, 31))
    itens = list(cat.search(collections=["sentinel-2-l2a"], bbox=BBOX, datetime=f"{ano}-{JANELA[0]}/{fim}",
                            query={"eo:cloud_cover": {"lt": MAX_NUVEM}}).items())
    itens = sorted(itens, key=lambda i: i.properties["eo:cloud_cover"])[:N_CENAS]
    if not itens:
        return None, None
    print(f"   {len(itens)} cenas")
    ndvis, transform = [], None
    try:   # leitura mais paciente: tenta de novo quando o servidor corta a resposta no meio
        env = stackstac.DEFAULT_GDAL_ENV.updated(always=dict(
            GDAL_HTTP_MAX_RETRY="6", GDAL_HTTP_RETRY_DELAY="3", GDAL_HTTP_TIMEOUT="90",
            GDAL_HTTP_VERSION="1.1", CPL_VSIL_CURL_USE_HEAD="NO"))
    except Exception:
        env = None
    extra = {"gdal_env": env} if env is not None else {}
    for k, it in enumerate(itens, 1):          # uma cena por vez: usa pouca memória e evita travar
        print(f"   cena {k}/{len(itens)}")
        nd = None
        for tentativa in range(1, 4):
            try:
                item = it if tentativa == 1 else pc.sign(it)      # renova o acesso na nova tentativa
                cubo = stackstac.stack([item], assets=["B04", "B08", "SCL"], epsg=EPSG, resolution=10,
                                       bounds_latlon=BBOX, resampling=Resampling.nearest,
                                       dtype="float64", rescale=False, chunksize=1024, **extra)
                ruim = cubo.sel(band="SCL").isin([0, 1, 3, 8, 9, 10])
                # cenas com baseline >= 04.00 (a partir de 2022) têm offset de 1000; as anteriores não
                desl = 1000 if float(it.properties.get("s2:processing_baseline", "4")) >= 4.0 else 0
                red = ((cubo.sel(band="B04") - desl) / 10000).where(~ruim)
                nir = ((cubo.sel(band="B08") - desl) / 10000).where(~ruim)
                nd = ((nir - red) / (nir + red)).isel(time=0).compute(scheduler="synchronous").values
                transform = cubo.attrs["transform"]
                break
            except Exception as e:
                print(f"   falha na cena {k} (tentativa {tentativa}/3): {str(e)[:110]}")
                time.sleep(4 * tentativa)
        if nd is None:
            print(f"   cena {k} ignorada depois de 3 tentativas")
            continue
        ndvis.append(nd)
    if len(ndvis) < 3:
        print(f"   atenção: só {len(ndvis)} cenas lidas; o resultado deste ano fica menos confiável")
    if not ndvis:
        return None, None
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        ndvi = np.nanmedian(np.stack(ndvis), axis=0)
    return ndvi, transform

seg = carrega_segmentos()
zona = seg.buffer(BUFFER, cap_style=2)
area25 = seg.buffer(25).union_all()
para_lonlat = Transformer.from_crs(EPSG, 4326, always_xy=True).transform

for ano in ANOS:
    cf = f"{D}/cov_{ano}.json"
    if os.path.exists(cf) and ano < HOJE.year:
        print(f"{ano}: já calculado, pulando"); continue
    print(f"{ano}: processando...")
    ndvi, transform = ndvi_do_ano(ano)
    if ndvi is None:
        print(f"{ano}: sem cenas boas, pulando"); continue
    copa = np.clip((ndvi - NDVI_MIN) / (NDVI_MAX - NDVI_MIN), 0, 1)
    zs = zonal_stats(zona, copa, affine=transform, stats=["mean"], nodata=np.nan)
    json.dump([round(z["mean"] or 0, 2) for z in zs], open(cf, "w"), separators=(",", ":"))
    perto = features.rasterize([(area25, 1)], out_shape=copa.shape, transform=transform,
                               fill=0, dtype="uint8").astype(bool)
    r, c = np.where(perto & (ndvi > NDVI_ARVORE))
    xs, ys = transform * (c + 0.5, r + 0.5)
    lon, lat = para_lonlat(xs, ys)
    raio = 4 + 5 * copa[r, c]                  # raio da copa em metros (4 a 9 m)
    json.dump([[round(a, 5), round(b, 5), round(float(d), 1)] for a, b, d in zip(lon, lat, raio)],
              open(f"{D}/trees_{ano}.json", "w"), separators=(",", ":"))
    print(f"{ano}: {len(r)} manchas")

anos = sorted(int(f[4:8]) for f in os.listdir(D) if f.startswith("cov_"))
json.dump({"anos": anos, "atualizado": str(HOJE)}, open(f"{D}/anos.json", "w"))
try:
    esc = f"{SHP}/equipamento_educacao.shp"
    if os.path.exists(esc) and anos:                  # escolas e creches municipais: sombra no entorno (150 m)
        e = gpd.read_file(esc).to_crs(EPSG)
        e = e[e.geometry.geom_type == "Point"]
        if "SITUACAO" in e.columns:
            e = e[e["SITUACAO"].astype(str).str.upper().str.contains("FUNCION")]
        if "TIPO2" in e.columns:
            e = e[e["TIPO2"].isin(["CMEI", "EMAI", "EMEI", "EM", "ANEXO"])]
        covs = {a: json.load(open(f"{D}/cov_{a}.json")) for a in anos}
        e4326 = e.to_crs(4326)
        saida = []
        for (_, row), pt in zip(e.iterrows(), e4326.geometry):
            ix = seg.sindex.query(row.geometry.buffer(150), predicate="intersects")
            if len(ix) == 0:
                continue
            bairros = seg.iloc[ix]["b"].replace("", np.nan).dropna()
            saida.append({"n": str(row.get("EQUIPAME_1") or row.get("EQUIPAMENT") or ""),
                          "t": str(row.get("TIPO2", "")), "b": str(bairros.mode().iat[0]) if len(bairros) else "",
                          "lon": round(pt.x, 5), "lat": round(pt.y, 5),
                          "c": {str(a): round(float(np.mean([covs[a][j] for j in ix])), 2) for a in anos}})
        json.dump(saida, open(f"{D}/escolas.json", "w"), ensure_ascii=False, separators=(",", ":"))
        print(f"{len(saida)} escolas e creches medidas")
except Exception as erro:
    print("Aviso: não consegui medir as escolas:", str(erro)[:160])
print("Pronto. Anos:", anos)
