"""Compara o Sentinel-2 com as fotos aéreas de 10 cm nos trechos de rua das áreas piloto.
Serve para decidir se as cores do mapa (verde/amarelo/vermelho) estão calibradas.

Uso (depois de rodar pipeline.py e ortofoto_piloto.py):  python calibra.py [ano]
Mostra: média do Sentinel x média da foto, correlação e o limite do Sentinel que equivale a 30% de copa real.
Gera data/calibracao.json. Use o número final nos campos de limite do site ("Como ler as cores")."""
import json, sys, unicodedata
import numpy as np

def norm(s):
    return " ".join(unicodedata.normalize("NFD", s or "").encode("ascii", "ignore").decode().lower().split())

anos = json.load(open("data/anos.json"))["anos"]
ano = int(sys.argv[1]) if len(sys.argv) > 1 else anos[-1]
cov = np.array(json.load(open(f"data/cov_{ano}.json")))
seg = json.load(open("data/segments.geojson"))["features"]
ortho = json.load(open("data/ortho_ruas.json"))
meio = np.array([np.mean(f["geometry"]["coordinates"], axis=0) for f in seg])      # lon, lat do meio de cada trecho
nomes = [norm(f["properties"].get("n", "")) for f in seg]
x, y = [], []
for o in ortho:
    d = np.hypot((meio[:, 0] - o["lon"]) * 110540 * np.cos(np.radians(o["lat"])), (meio[:, 1] - o["lat"]) * 110540)
    cand = np.nonzero(d < 60)[0]
    mesmo = [i for i in cand if nomes[i] and nomes[i] == norm(o["n"])]
    cand = mesmo or list(cand)
    if cand:
        x.append(float(np.mean(cov[cand]))); y.append(o["cob"])
x, y = np.array(x), np.array(y)
if len(x) < 8:
    sys.exit(f"Só {len(x)} trechos casaram. Rode o pipeline com as ruas oficiais (data/shp) e o ortofoto_piloto.py.")
r = float(np.corrcoef(x, y)[0, 1]); a, b = np.polyfit(x, y, 1)
eq = float((0.30 - b) / a) if a > 0 else float("nan")
print(f"Ano {ano}: {len(x)} trechos comparados")
print(f"  copa média no Sentinel: {x.mean():.0%}   copa média na foto aérea: {y.mean():.0%}")
print(f"  correlação: {r:.2f}   reta: foto = {a:.2f} x Sentinel + {b:+.2f}")
print(f"  30% de copa real equivalem a cerca de {eq:.0%} no Sentinel")
print("  Leitura: se a foto mostra mais copa que o Sentinel, o satélite subestima e vale baixar os limites do mapa.")
json.dump({"ano": ano, "n": len(x), "r": round(r, 3), "a": round(float(a), 3), "b": round(float(b), 3),
           "sentinel_30pct_equiv": round(eq, 3)}, open("data/calibracao.json", "w"))
