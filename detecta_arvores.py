"""Detecta copas de árvores em uma ortofoto RGB de alta resolução (GeoTIFF) com DeepForest
e gera data/trees_ortho.json ([lon, lat, raio_m]) para o site.
Fontes de ortofoto: prefeitura (Filipeia/SEPLAN), voo de drone ou outro aerolevantamento autorizado.
Uso: python detecta_arvores.py caminho/ortofoto.tif
Instalação extra: pip install deepforest   (instala PyTorch; é pesado)"""
import json, sys
import rasterio
from pyproj import Transformer
from deepforest import main

caminho = sys.argv[1]
modelo = main.deepforest()
try:
    modelo.load_model("weecology/deepforest-tree")   # versões recentes
except Exception:
    modelo.use_release()                              # versões antigas
try:
    df = modelo.predict_tile(raster_path=caminho, patch_size=400, patch_overlap=0.25)
except TypeError:
    df = modelo.predict_tile(path=caminho, patch_size=400, patch_overlap=0.25)
if "score" in df.columns:
    df = df[df["score"] > 0.3]
with rasterio.open(caminho) as src:
    t, crs = src.transform, src.crs
    metros_px = abs(t.a) * (111320 if crs.is_geographic else 1)
    para_lonlat = Transformer.from_crs(crs, 4326, always_xy=True).transform
    saida = []
    for r in df.itertuples():
        x, y = t * ((r.xmin + r.xmax) / 2, (r.ymin + r.ymax) / 2)
        lon, lat = para_lonlat(x, y)
        raio = max(r.xmax - r.xmin, r.ymax - r.ymin) / 2 * metros_px
        saida.append([round(lon, 6), round(lat, 6), round(float(raio), 1)])
json.dump(saida, open("data/trees_ortho.json", "w"), separators=(",", ":"))
print(f"{len(saida)} copas detectadas -> data/trees_ortho.json")
