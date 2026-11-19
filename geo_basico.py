"""Leitor mínimo de shapefile/DBF e conversão UTM 25S -> lon/lat, só com numpy.
Usado pelos scripts de ortofoto para não exigir GDAL."""
import os, struct
import numpy as np

def le_shp(caminho):
    """Retorna lista (uma por registro) de listas de partes (arrays Nx2) ou None."""
    d = open(caminho, "rb").read()
    out, pos = [], 100
    while pos + 8 <= len(d):
        _, clen = struct.unpack(">ii", d[pos:pos + 8]); pos += 8
        rec = d[pos:pos + clen * 2]; pos += clen * 2
        st = struct.unpack("<i", rec[:4])[0]
        if st in (3, 5, 13, 15, 23, 25):
            nparts, npts = struct.unpack("<ii", rec[36:44])
            parts = np.frombuffer(rec, "<i4", nparts, 44)
            pts = np.frombuffer(rec, "<f8", npts * 2, 44 + 4 * nparts).reshape(-1, 2)
            idx = list(parts) + [npts]
            out.append([pts[idx[i]:idx[i + 1]] for i in range(nparts)])
        elif st in (1, 11, 21):
            x, y = struct.unpack("<dd", rec[4:20]); out.append([np.array([[x, y]])])
        else:
            out.append(None)
    return out

def le_dbf(caminho):
    """Retorna lista de dicts (None para registros apagados)."""
    enc = "latin-1"
    for ext in (".cpg", ".CPG"):
        p = os.path.splitext(caminho)[0] + ext
        if os.path.exists(p):
            c = open(p).read().strip().upper()
            enc = "utf-8" if "UTF" in c else "cp1252"
    d = open(caminho, "rb").read()
    n, hlen, rlen = struct.unpack("<IHH", d[4:12])
    campos, p = [], 32
    while d[p] != 0x0D:
        campos.append((d[p:p + 11].split(b"\0")[0].decode("ascii"), chr(d[p + 11]), d[p + 16])); p += 32
    regs = []
    for i in range(n):
        r = d[hlen + i * rlen: hlen + (i + 1) * rlen]
        if r[:1] == b"*":
            regs.append(None); continue
        off, row = 1, {}
        for nome, tipo, tam in campos:
            v = r[off:off + tam].decode(enc, "replace").strip(); off += tam
            if tipo in "NF":
                try: v = float(v.replace(",", "."))
                except ValueError: v = None
            row[nome] = v
        regs.append(row)
    return regs

def utm25s_para_lonlat(E, N):
    """SIRGAS 2000 / UTM 25S (EPSG:31985) -> lon, lat em graus (séries de Krüger)."""
    E, N = np.asarray(E, float), np.asarray(N, float)
    a, f, k0 = 6378137.0, 1 / 298.257222101, 0.9996
    n = f / (2 - f)
    A = a / (1 + n) * (1 + n**2 / 4 + n**4 / 64)
    beta = [n / 2 - 2 * n**2 / 3 + 37 * n**3 / 96, n**2 / 48 + n**3 / 15, 17 * n**3 / 480]
    delta = [2 * n - 2 * n**2 / 3 - 2 * n**3, 7 * n**2 / 3 - 8 * n**3 / 5, 56 * n**3 / 15]
    x, y = (E - 500000) / (k0 * A), (N - 10000000) / (k0 * A)
    xi = y - sum(beta[j] * np.sin(2 * (j + 1) * y) * np.cosh(2 * (j + 1) * x) for j in range(3))
    eta = x - sum(beta[j] * np.cos(2 * (j + 1) * y) * np.sinh(2 * (j + 1) * x) for j in range(3))
    chi = np.arcsin(np.sin(xi) / np.cosh(eta))
    lat = chi + sum(delta[j] * np.sin(2 * (j + 1) * chi) for j in range(3))
    lon = np.radians(-33.0) + np.arctan2(np.sinh(eta), np.cos(xi))
    return np.degrees(lon), np.degrees(lat)

def ponto_em_poligono(px, py, partes):
    """Regra par-ímpar (suporta buracos). px, py: arrays."""
    px, py = np.atleast_1d(px).astype(float), np.atleast_1d(py).astype(float)
    dentro = np.zeros(len(px), bool)
    for ring in partes:
        x1, y1 = ring[:, 0], ring[:, 1]
        x2, y2 = np.roll(x1, -1), np.roll(y1, -1)
        for a, b, c, d in zip(x1, y1, x2, y2):
            if b == d: continue
            cruza = ((b > py) != (d > py)) & (px < (c - a) * (py - b) / (d - b) + a)
            dentro ^= cruza
    return dentro
