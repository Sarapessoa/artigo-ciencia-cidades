"""Confere as lacunas entre o maior componente (C1) e os componentes C2..C{N_COMPONENTES+1}.

Para cada componente, calcula:

- a lacuna em linha reta até C1 (par de pontos mais próximo);
- se a infraestrutura cicloviária registrada hoje no OpenStreetMap liga o componente a C1 e quantos
  metros de vias do OSM, ausentes da base, isso exige. Pontes e túneis do OSM só se ligam a outras
  vias pelas próprias extremidades (rampas), nunca pelo meio;
- a menor ligação possível pelas ruas (malha viária do OSM), isto é, quantos metros de
  infraestrutura nova seriam necessários seguindo vias existentes.

Saídas: resultados/lacunas.csv, as geometrias das ligações em resultados/lacunas.geojson e, para conferência visual, recortes de satélite em
resultados/lacunas/. Caches do OSM em dados/brutos/ (osm_ruas_fortaleza.json fica fora do git).

Uso: python conferir_lacunas.py
"""
import json
import time
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import geopandas as gpd
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from pyproj import Transformer
from shapely import get_point
from shapely.geometry import LineString, Point
from shapely.ops import nearest_points

from rede import BRUTOS, CRS_METRICO, RESULTADOS, TOL_PRINCIPAL, cenario_principal
from triagem_conexoes import mosaico

N_COMPONENTES = 4
RAIO_RUAS_M = 15  # distância máxima entre um componente e um vértice da malha viária
MARGEM_M = 150
ZOOM = 18
PASTA_IMG = RESULTADOS / "lacunas"
ARQ_CICLO = BRUTOS / "osm_ciclovias_fortaleza.json"
ARQ_RUAS = BRUTOS / "osm_ruas_fortaleza.json"
SERVIDORES_OVERPASS = ["https://overpass-api.de/api/interpreter",
                       "https://overpass.kumi.systems/api/interpreter"]

# Vias com infraestrutura cicloviária no OSM: ciclovias, ciclofaixas e vias de uso
# compartilhado sinalizado para bicicletas.
FILTROS_CICLO = [
    'way["highway"="cycleway"]',
    'way["cycleway"~"lane|track|opposite_lane|opposite_track"]',
    'way["cycleway:left"~"lane|track"]',
    'way["cycleway:right"~"lane|track"]',
    'way["cycleway:both"~"lane|track"]',
    'way["bicycle"="designated"]',
]
# Vias por onde uma ligação cicloviária poderia passar.
TIPOS_RUA = ("primary|primary_link|secondary|secondary_link|tertiary|tertiary_link|unclassified|"
             "residential|living_street|service|cycleway|pedestrian|track")
CORES = {1: "#2a78d6", 2: "#eb6834", 3: "#1baf7a", 4: "#eda100", 5: "#e87ba4"}


def overpass(arquivo, filtros, caixa):
    """Baixa (uma vez) o resultado da consulta Overpass para a caixa (o, s, l, n)."""
    if not arquivo.exists():
        o, s, l, n = caixa
        partes = "".join(f"{f}({s},{o},{n},{l});" for f in filtros)
        consulta = f"[out:json][timeout:240];({partes});out geom tags;"
        for tentativa in range(3):
            url = SERVIDORES_OVERPASS[tentativa % len(SERVIDORES_OVERPASS)]
            try:
                req = Request(url, data=urlencode({"data": consulta}).encode(),
                              headers={"User-Agent": "artigo-ciclovias-fortaleza"})
                arquivo.write_bytes(urlopen(req, timeout=300).read())
                break
            except OSError as erro:
                print(f"{url}: {erro}")
                time.sleep(15)
        else:
            raise RuntimeError("nenhum servidor Overpass respondeu")
    return json.loads(arquivo.read_text(encoding="utf-8"))["elements"]


def vias_osm(elementos):
    linhas = [{"osm_id": e["id"], "tags": e["tags"],
               "geometry": LineString([(p["lon"], p["lat"]) for p in e["geometry"]])}
              for e in elementos if len(e.get("geometry", [])) > 1]
    return (gpd.GeoDataFrame(linhas, crs=4326).drop_duplicates("osm_id")
            .to_crs(CRS_METRICO).reset_index(drop=True))


def lacuna_reta(rede, k):
    maior, outro = rede[rede["componente"] == 1], rede[rede["componente"] == k]
    d, i, j = min((a.distance(b), i, j)
                  for i, a in maior.geometry.items() for j, b in outro.geometry.items())
    return d, LineString(nearest_points(rede.geometry[i], rede.geometry[j])), i, j


def ligacao_pelo_osm(rede, ciclo):
    """Para cada componente, o caminho até C1 que usa o mínimo de vias cicloviárias do OSM."""
    todos = gpd.GeoDataFrame(pd.concat(
        [rede[["geometry"]].assign(fonte="base", comp=rede["componente"]),
         ciclo[["geometry"]].assign(fonte="osm", comp=0)], ignore_index=True), crs=CRS_METRICO)
    elevada = np.r_[np.zeros(len(rede), bool),
                    [any(k in t for k in ("bridge", "tunnel", "layer")) for t in ciclo["tags"]]]
    G = nx.Graph()
    G.add_nodes_from(range(len(todos)))
    pontas = [get_point(g, k) for g in todos.geometry for k in (0, -1)]
    dono = np.repeat(np.arange(len(todos)), 2)
    ip, jt = todos.sindex.query(gpd.GeoSeries(pontas, crs=CRS_METRICO),
                                predicate="dwithin", distance=TOL_PRINCIPAL)
    for a, b in zip(ip, jt):
        if dono[a] == b:
            continue
        if elevada[b] and min(pontas[a].distance(get_point(todos.geometry[b], k))
                              for k in (0, -1)) > TOL_PRINCIPAL:
            continue
        G.add_edge(int(dono[a]), int(b))
    ia, ib = todos.sindex.query(todos.geometry, predicate="intersects")
    G.add_edges_from((int(a), int(b)) for a, b in zip(ia, ib)
                     if a != b and not (elevada[a] or elevada[b]))

    custo = todos.length.where(todos["fonte"] == "osm", 0).to_numpy()
    H = nx.Graph()
    H.add_edges_from((a, b, {"w": (custo[a] + custo[b]) / 2}) for a, b in G.edges)
    H.add_edges_from(("C1", x, {"w": 0}) for x in todos.index[todos["comp"] == 1])
    resultado = {}
    for k in range(2, N_COMPONENTES + 2):
        H.add_edges_from(("alvo", x, {"w": 0}) for x in todos.index[todos["comp"] == k])
        try:
            caminho = nx.shortest_path(H, "C1", "alvo", weight="w")
            usados = [x - len(rede) for x in caminho[1:-1] if todos.at[x, "fonte"] == "osm"]
            resultado[k] = ciclo.loc[usados]
        except nx.NetworkXNoPath:
            resultado[k] = None
        H.remove_node("alvo")
    return resultado


def ligacao_pelas_ruas(rede, ruas_elementos):
    """Para cada componente, o menor caminho pela malha viária até C1."""
    tr = Transformer.from_crs(4326, CRS_METRICO, always_xy=True)
    R = nx.Graph()
    nome = {}
    for e in ruas_elementos:
        pts = [tuple(round(c, 1) for c in tr.transform(p["lon"], p["lat"])) for p in e["geometry"]]
        for a, b in zip(pts, pts[1:]):
            R.add_edge(a, b, w=float(np.hypot(a[0] - b[0], a[1] - b[1])))
            nome[frozenset((a, b))] = e["tags"].get("name", "(sem nome)")
    lista = list(R.nodes)
    vertices = gpd.GeoSeries([Point(n) for n in lista], crs=CRS_METRICO)

    def perto(k):
        g = rede[rede["componente"] == k].union_all()
        return {lista[i] for i in vertices.sindex.query(g, predicate="dwithin", distance=RAIO_RUAS_M)}

    dist, caminhos = nx.multi_source_dijkstra(R, perto(1), weight="w")
    resultado = {}
    for k in range(2, N_COMPONENTES + 2):
        alcancados = [n for n in perto(k) if n in dist]
        if not alcancados:
            resultado[k] = None
            continue
        fim = min(alcancados, key=dist.get)
        cam = caminhos[fim]
        ruas = {}
        for a, b in zip(cam, cam[1:]):
            ruas[nome[frozenset((a, b))]] = ruas.get(nome[frozenset((a, b))], 0) + R[a][b]["w"]
        resultado[k] = (dist[fim], LineString(cam) if len(cam) > 1 else Point(cam[0]), ruas)
    return resultado


def figura(k, rede, linhas, destino, titulo):
    """Recorte de satélite com a base, a lacuna em linha reta, o caminho pelas ruas e o OSM usado."""
    rede = rede.to_crs(3857)
    camadas = {nome: gpd.GeoSeries([g], crs=CRS_METRICO).to_crs(3857)
               for nome, g in linhas.items() if g is not None}
    x0, y0, x1, y1 = pd.concat(camadas.values()).buffer(MARGEM_M).total_bounds
    lado = max(x1 - x0, y1 - y0) / 2
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    caixa = (cx - lado, cy - lado, cx + lado, cy + lado)
    img, extensao = mosaico(caixa, zoom=ZOOM)

    estilo = {"OSM usado": dict(color="white", linewidth=3.5, alpha=0.9),
              "pelas ruas": dict(color="yellow", linewidth=1.6, linestyle="--"),
              "linha reta": dict(color="red", linewidth=1.2, linestyle=":")}
    fig, eixos = plt.subplots(1, 2, figsize=(10, 5))
    for ax, sobrepor in zip(eixos, (False, True)):
        ax.imshow(img, extent=extensao)
        if sobrepor:
            for nome, g in camadas.items():
                g.plot(ax=ax, **estilo[nome])
            for c in (1, k):
                rede[rede["componente"] == c].plot(ax=ax, color=CORES[c], linewidth=1.8)
        ax.set_xlim(caixa[0], caixa[2])
        ax.set_ylim(caixa[1], caixa[3])
        ax.set_axis_off()
    legenda = [Line2D([], [], color=CORES[1], lw=2, label="C1 (base)"),
               Line2D([], [], color=CORES[k], lw=2, label=f"C{k} (base)")]
    legenda += [Line2D([], [], label=nome, **{a: v for a, v in estilo[nome].items() if a != "alpha"})
                for nome in camadas]
    eixos[1].legend(handles=legenda, loc="lower right", fontsize=7, facecolor="#333333",
                    labelcolor="white", framealpha=0.8)
    fig.suptitle(titulo, fontsize=9)
    fig.tight_layout()
    fig.savefig(destino, dpi=110, bbox_inches="tight")
    plt.close(fig)


def main():
    PASTA_IMG.mkdir(parents=True, exist_ok=True)
    rede, comp = cenario_principal()
    caixa = tuple(rede.to_crs(4326).total_bounds)
    ciclo = vias_osm(overpass(ARQ_CICLO, FILTROS_CICLO, caixa))
    ruas = overpass(ARQ_RUAS, [f'way["highway"~"^({TIPOS_RUA})$"]'], caixa)
    pelo_osm = ligacao_pelo_osm(rede, ciclo)
    pelas_ruas = ligacao_pelas_ruas(rede, ruas)

    linhas, geometrias = [], []
    for k in range(2, N_COMPONENTES + 2):
        d_reta, g_reta, i, j = lacuna_reta(rede, k)
        osm_k, ruas_k = pelo_osm[k], pelas_ruas[k]
        geometrias.append({"componente": k, "tipo": "linha reta", "geometry": g_reta})
        if ruas_k:
            geometrias.append({"componente": k, "tipo": "pelas ruas", "geometry": ruas_k[1]})
        if osm_k is not None and len(osm_k):
            geometrias.append({"componente": k, "tipo": "OSM atual", "geometry": osm_k.union_all()})
        linhas.append({
            "componente": k,
            "km_componente": round(comp.at[k, "km"], 1),
            "reta_m": round(d_reta),
            "reta_entre": f"{rede.at[i, 'Nome']} x {rede.at[j, 'Nome']}",
            "ligado_pelo_osm": osm_k is not None,
            "osm_m": round(osm_k.length.sum()) if osm_k is not None else None,
            "osm_vias": "; ".join(sorted({t.get("name", "(sem nome)") for t in osm_k["tags"]}))
                        if osm_k is not None else "",
            "osm_ids": " ".join(str(x) for x in osm_k["osm_id"]) if osm_k is not None else "",
            "ruas_m": round(ruas_k[0]) if ruas_k else None,
            "ruas_vias": "; ".join(f"{n} ({m:.0f} m)" for n, m in
                                   sorted(ruas_k[2].items(), key=lambda x: -x[1])) if ruas_k else "",
        })
        figura(k, rede,
               {"linha reta": g_reta,
                "pelas ruas": ruas_k[1] if ruas_k else None,
                "OSM usado": osm_k.union_all() if osm_k is not None and len(osm_k) else None},
               PASTA_IMG / f"lacuna_C1_C{k}.png",
               f"C1 x C{k}: linha reta {round(d_reta)} m; pelas ruas "
               f"{round(ruas_k[0]) if ruas_k else '-'} m")

    tab = pd.DataFrame(linhas)
    tab.to_csv(RESULTADOS / "lacunas.csv", index=False, encoding="utf-8-sig")
    gpd.GeoDataFrame(geometrias, crs=CRS_METRICO).to_crs(4326).to_file(
        RESULTADOS / "lacunas.geojson", driver="GeoJSON")
    print(tab.drop(columns=["osm_ids"]).to_string(index=False))


if __name__ == "__main__":
    main()
