"""Piloto em alta resolução: detecta copas nas ortofotos (10 cm) da prefeitura, desenha cada copa como um
círculo e mede a cobertura por trecho de rua. Só precisa de numpy, opencv-python-headless e tifffile.

Uso:  python ortofoto_piloto.py [pasta_com_tifs] [caminho_do_shapefile_de_logradouros_sem_extensao]
Padrões: data/ortofotos  e  data/shp/LOGRADOUROS_ATIVOS
Gera:  data/trees_ortho.json   [[lon, lat, raio_m, tipo], ...]  tipo 0 = árvore provável, 1 = vegetação baixa/mato
       data/ortho_ruas.json    cobertura de copa medida por trecho de rua (para validar o Sentinel-2)
       data/ortho_areas.json   retângulos das áreas cobertas pelas fotos

Como separa árvore de mato (sem dados de altura): copas de árvore são mais escuras que gramados e matos.
Vegetação verde e textura (ExG, textura local) define "vegetação"; o brilho médio de cada mancha decide se é
árvore (escura) ou vegetação baixa (clara). Sombras de prédios são descartadas pela cor. É uma estimativa:
com LiDAR/modelo de altura, ou com o cadastro de árvores do SIGWeb, a separação fica muito melhor."""
import glob, json, os, sys
import cv2, numpy as np, tifffile
from geo_basico import le_shp, le_dbf, utm25s_para_lonlat

PASTA = sys.argv[1] if len(sys.argv) > 1 else "data/ortofotos"
SHP = sys.argv[2] if len(sys.argv) > 2 else "data/shp/LOGRADOUROS_ATIVOS"
LARG = 15          # metros de cada lado do eixo da rua
SEG = 40           # metros por trecho medido
MIN_M2 = 8         # menor mancha guardada (m²)
V_ARVORE = int(os.environ.get("V_ARVORE", 95))  # brilho médio (0-255) abaixo do qual a mancha é tratada como árvore
os.makedirs("data", exist_ok=True)

def vegetacao(rgb):
    f = rgb.astype(np.float32); R, G, B = f[..., 0], f[..., 1], f[..., 2]
    exg = (2 * G - R - B) / (R + G + B + 1e-6)
    v = f.max(2)
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY).astype(np.float32)
    mu = cv2.blur(gray, (11, 11)); sd = np.sqrt(np.maximum(cv2.blur(gray * gray, (11, 11)) - mu * mu, 0))
    m = ((exg > 0.12) & (sd > 6) & (v > 35) & (v < 150)).astype(np.uint8)   # v > 35 descarta sombras
    el = lambda d: cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (d, d))
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, el(5)); m = cv2.morphologyEx(m, cv2.MORPH_OPEN, el(9))
    return m, v

def circulos(mask, px):
    """Transforma manchas em círculos (centros = máximos da transformada de distância)."""
    dist = cv2.distanceTransform(mask, cv2.DIST_L2, 5)
    pico = (dist == cv2.dilate(dist, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (25, 25)))) & (dist >= 0.8 / px)
    ys, xs = np.nonzero(pico)
    rs = dist[ys, xs] * 1.15
    ordem = np.argsort(-rs); mantidos = []
    for i in ordem:
        x, y, r = xs[i], ys[i], rs[i]
        if r * px > 9: r = 9 / px
        if any((x - a) ** 2 + (y - b) ** 2 < (0.65 * max(r, c)) ** 2 for a, b, c in mantidos[-400:]) or \
           any((x - a) ** 2 + (y - b) ** 2 < (0.65 * max(r, c)) ** 2 for a, b, c in mantidos if abs(a - x) < 200 and abs(b - y) < 200):
            continue
        mantidos.append((x, y, r))
    return mantidos

def trechos(partes, passo):
    for p in partes:
        if len(p) < 2: continue
        d = np.r_[0, np.cumsum(np.hypot(*np.diff(p, axis=0).T))]
        if d[-1] < 5: continue
        n = max(1, round(d[-1] / passo))
        cortes = np.linspace(0, d[-1], n + 1)
        for a, b in zip(cortes[:-1], cortes[1:]):
            t = np.unique(np.r_[a, d[(d > a) & (d < b)], b])
            yield np.c_[np.interp(t, d, p[:, 0]), np.interp(t, d, p[:, 1])]

geoms, attrs = le_shp(SHP + ".shp"), le_dbf(SHP + ".dbf")
ruas_saida, arvores, areas = [], [], []
for tif in sorted(glob.glob(os.path.join(PASTA, "*.tif"))):
    nome_tile = os.path.basename(tif)[:-4]
    with tifffile.TiffFile(tif) as t:
        pg = t.pages[0]
        px = float(pg.tags["ModelPixelScaleTag"].value[0])
        _, _, _, x0, y0, _ = pg.tags["ModelTiepointTag"].value
        img = pg.asarray()
    H, W = img.shape[:2]
    valido = (img[..., 3] > 127) if img.shape[2] == 4 else np.ones((H, W), bool)
    veg, v = vegetacao(np.ascontiguousarray(img[..., :3]))
    n, lab, st, _ = cv2.connectedComponentsWithStats(veg)
    area = st[:, cv2.CC_STAT_AREA]
    vmed = np.bincount(lab.ravel(), weights=v.ravel(), minlength=n) / np.maximum(area, 1)
    grande = area >= MIN_M2 / px**2; grande[0] = False
    eh_arvore = grande & (vmed < V_ARVORE)
    m_arv = (eh_arvore[lab] & valido).astype(np.uint8)
    m_mato = ((grande & ~eh_arvore)[lab] & valido).astype(np.uint8)
    x1, y1 = x0 + W * px, y0 - H * px
    perto = np.zeros((H, W), np.uint8); r = int(LARG / px); novos = []
    for g, a in zip(geoms, attrs):
        if not g or not a: continue
        bb = np.vstack(g)
        if bb[:, 0].max() < x0 or bb[:, 0].min() > x1 or bb[:, 1].max() < y1 or bb[:, 1].min() > y0: continue
        for seg in trechos(g, SEG):
            pp = np.c_[(seg[:, 0] - x0) / px, (y0 - seg[:, 1]) / px]
            if (pp[:, 0] < 0).any() or (pp[:, 0] >= W).any() or (pp[:, 1] < 0).any() or (pp[:, 1] >= H).any(): continue
            ja, jb = int(max(pp[:, 0].min() - r - 2, 0)), int(min(pp[:, 0].max() + r + 2, W))
            ia, ib = int(max(pp[:, 1].min() - r - 2, 0)), int(min(pp[:, 1].max() + r + 2, H))
            loc = np.zeros((ib - ia, jb - ja), np.uint8)
            cv2.polylines(loc, [np.round(pp - [ja, ia]).astype(np.int32).reshape(-1, 1, 2)], False, 1, 2 * r)
            perto[ia:ib, ja:jb] |= loc
            val = (loc.astype(bool) & valido[ia:ib, ja:jb]).sum()
            if val < 0.5 * loc.sum(): continue
            cobre = (loc.astype(bool) & m_arv[ia:ib, ja:jb].astype(bool)).sum() / max(val, 1)
            mato = (loc.astype(bool) & m_mato[ia:ib, ja:jb].astype(bool)).sum() / max(val, 1)
            mid = seg[len(seg) // 2]; lon, lat = utm25s_para_lonlat(mid[0], mid[1])
            novos.append({"n": " ".join(str(a["nome_logr"]).split()), "lon": round(float(lon), 6), "lat": round(float(lat), 6),
                          "cob": round(float(cobre), 2), "mato": round(float(mato), 2), "tile": nome_tile})
    ruas_saida += novos
    nc = 0
    previa = img[..., :3].copy() if os.environ.get("PREVIA") else None
    for mascara, tipo in ((m_arv & perto, 0), (m_mato & perto, 1)):
        for cx, cy, cr in circulos(mascara, px):
            if previa is not None:
                cv2.circle(previa, (int(cx), int(cy)), int(cr), (0, 255, 0) if tipo == 0 else (255, 0, 255), 6)
            lon, lat = utm25s_para_lonlat(x0 + cx * px, y0 - cy * px)
            arvores.append([round(float(lon), 6), round(float(lat), 6), round(float(cr * px), 1), tipo]); nc += tipo == 0
    if previa is not None:
        cv2.imwrite(f"previa_{nome_tile}.jpg", cv2.cvtColor(cv2.resize(previa, (1400, 1400), interpolation=cv2.INTER_AREA), cv2.COLOR_RGB2BGR))
    if novos:
        (lo1, lo2), (la1, la2) = utm25s_para_lonlat([x0, x1], [y1, y0])
        areas.append([[round(float(la1), 6), round(float(lo1), 6)], [round(float(la2), 6), round(float(lo2), 6)]])
    cob = np.mean([s["cob"] for s in novos]) if novos else float("nan")
    print(f"{nome_tile}: {len(novos)} trechos, copa de árvore {cob:.0%} nas ruas, {nc} copas")

json.dump(arvores, open("data/trees_ortho.json", "w"), separators=(",", ":"))
json.dump(ruas_saida, open("data/ortho_ruas.json", "w"), ensure_ascii=False, separators=(",", ":"))
json.dump(areas, open("data/ortho_areas.json", "w"))
print("Pronto:", len(arvores), "círculos e", len(ruas_saida), "trechos")
