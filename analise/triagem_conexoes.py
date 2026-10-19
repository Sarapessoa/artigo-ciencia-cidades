"""Prepara a triagem das conexões incertas do cenário principal.

Conexão incerta: cruzamento sem extremidade próxima, ou união que só existe
com tolerância acima de 0 m. Para cada uma, o script calcula:

- se é crítica, isto é, se removê-la separa a rede (ponte no grafo) e quantos km se separam;
- se há viaduto, passarela ou túnel do OpenStreetMap a até 20 m do ponto.

A amostra conferida reúne todas as críticas e um sorteio das demais. Para cada conexão
da amostra é gerado um recorte de imagem de satélite com os dois trechos sobrepostos.
O veredito de cada caso é registrado à mão em `resultados/triagem_conexoes.csv`.

Uso: python triagem_conexoes.py
"""
import json
from io import BytesIO
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import geopandas as gpd
import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd
from PIL import Image
from shapely.geometry import LineString
from shapely.ops import nearest_points

from rede import BRUTOS, CRS_METRICO, RESULTADOS, TOL_PRINCIPAL, conexoes, grafo, ler_bruto, selecionar

N_SORTEIO = 20
SEMENTE = 42
RAIO_OSM_M = 20
MEIA_JANELA_M = 70
PASTA_IMG = RESULTADOS / "triagem"
ARQ_OSM = BRUTOS / "osm_viadutos_tuneis.json"
URL_OVERPASS = "https://overpass-api.de/api/interpreter"
URL_TILE = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
ZOOM = 19
ORIGEM_MERCATOR = 20037508.342789244


def estruturas_osm(rede):
    """Vias do OSM marcadas como ponte ou túnel na área da rede (cache local)."""
    if not ARQ_OSM.exists():
        o, s, l, n = rede.to_crs(4326).total_bounds
        consulta = (f"[out:json][timeout:120];"
                    f"(way[highway][bridge]({s},{o},{n},{l});"
                    f"way[highway][tunnel]({s},{o},{n},{l});"
                    f"way[railway][bridge]({s},{o},{n},{l}););out geom tags;")
        req = Request(URL_OVERPASS, data=urlencode({"data": consulta}).encode(),
                      headers={"User-Agent": "artigo-ciclovias-fortaleza"})
        ARQ_OSM.write_bytes(urlopen(req, timeout=180).read())
    elementos = json.loads(ARQ_OSM.read_text(encoding="utf-8"))["elements"]
    linhas = [{"osm_id": e["id"],
               "tipo": "túnel" if "tunnel" in e["tags"] else "ponte/viaduto",
               "nome": e["tags"].get("name", ""),
               "geometry": LineString([(p["lon"], p["lat"]) for p in e["geometry"]])}
              for e in elementos if len(e.get("geometry", [])) > 1
              and e["tags"].get("bridge", e["tags"].get("tunnel")) not in ("no",)]
    return gpd.GeoDataFrame(linhas, crs=4326)


def mosaico(caixa):
    """Junta os tiles de imagem (Web Mercator) que cobrem a caixa; devolve imagem e extensão."""
    passo = 2 * ORIGEM_MERCATOR / 2 ** ZOOM
    c0, c1 = int((caixa[0] + ORIGEM_MERCATOR) // passo), int((caixa[2] + ORIGEM_MERCATOR) // passo)
    l0, l1 = int((ORIGEM_MERCATOR - caixa[3]) // passo), int((ORIGEM_MERCATOR - caixa[1]) // passo)
    img = Image.new("RGB", ((c1 - c0 + 1) * 256, (l1 - l0 + 1) * 256))
    for c in range(c0, c1 + 1):
        for l in range(l0, l1 + 1):
            req = Request(URL_TILE.format(z=ZOOM, y=l, x=c),
                          headers={"User-Agent": "artigo-ciclovias-fortaleza"})
            img.paste(Image.open(BytesIO(urlopen(req, timeout=60).read())),
                      ((c - c0) * 256, (l - l0) * 256))
    extensao = (c0 * passo - ORIGEM_MERCATOR, (c1 + 1) * passo - ORIGEM_MERCATOR,
                ORIGEM_MERCATOR - (l1 + 1) * passo, ORIGEM_MERCATOR - l0 * passo)
    return img, extensao


def recorte_satelite(ponto, rede, i, j, destino):
    # Os tiles estão em Web Mercator, que distorce menos de 0,3% em Fortaleza.
    rede = rede.to_crs(3857)
    ponto = gpd.GeoSeries([ponto], crs=CRS_METRICO).to_crs(3857)[0]
    x, y = ponto.x, ponto.y
    caixa = (x - MEIA_JANELA_M, y - MEIA_JANELA_M, x + MEIA_JANELA_M, y + MEIA_JANELA_M)
    img, extensao = mosaico(caixa)
    fig, eixos = plt.subplots(1, 2, figsize=(8, 4))
    for ax, sobrepor in zip(eixos, (False, True)):
        ax.imshow(img, extent=extensao)
        if sobrepor:
            rede.plot(ax=ax, color="white", linewidth=0.8, alpha=0.5)
            rede.iloc[[i]].plot(ax=ax, color="#2a78d6", linewidth=1.6, alpha=0.8)
            rede.iloc[[j]].plot(ax=ax, color="#eb6834", linewidth=1.6, alpha=0.8)
        ax.plot(x, y, marker="o", markersize=14, markerfacecolor="none",
                markeredgecolor="yellow", markeredgewidth=1)
        ax.set_xlim(caixa[0], caixa[2])
        ax.set_ylim(caixa[1], caixa[3])
        ax.set_axis_off()
    fig.tight_layout()
    fig.savefig(destino, dpi=110, bbox_inches="tight")
    plt.close(fig)


def main():
    PASTA_IMG.mkdir(parents=True, exist_ok=True)
    rede = selecionar(ler_bruto())
    pares = conexoes(rede, TOL_PRINCIPAL)
    exatos = conexoes(rede, 0)
    G = grafo(rede, TOL_PRINCIPAL)
    pontes = {tuple(sorted(e)) for e in nx.bridges(G)}
    osm = estruturas_osm(rede).to_crs(rede.crs)

    linhas = []
    for (i, j), tipo in pares.items():
        if tipo == "extremidade" and (i, j) in exatos:
            continue
        a, b = rede.geometry[i], rede.geometry[j]
        pa, pb = nearest_points(a, b)
        ponto = pa.union(pb).centroid
        km_separados = 0.0
        if (i, j) in pontes:
            H = G.copy()
            H.remove_edge(i, j)
            lado = min(nx.node_connected_component(H, i), nx.node_connected_component(H, j),
                       key=lambda c: rede.loc[sorted(c), "km"].sum())
            km_separados = rede.loc[sorted(lado), "km"].sum()
        perto = osm[osm.distance(ponto) <= RAIO_OSM_M]
        geo = gpd.GeoSeries([ponto], crs=rede.crs).to_crs(4326)[0]
        linhas.append({
            "i": i, "j": j, "tipo": tipo,
            "trecho_a": rede.at[i, "Nome"], "trecho_b": rede.at[j, "Nome"],
            "tipologia_a": rede.at[i, "Tipologia"], "tipologia_b": rede.at[j, "Tipologia"],
            "distancia_m": round(a.distance(b), 1),
            "critica": (i, j) in pontes, "km_separados": round(km_separados, 2),
            "osm_estrutura": "; ".join(sorted(set(perto["tipo"] + " " + perto["nome"]))).strip(),
            "lat": round(geo.y, 6), "lon": round(geo.x, 6), "_ponto": ponto,
        })
    tab = pd.DataFrame(linhas)

    resto = tab[~tab["critica"]]
    sorteio = resto.sample(n=min(N_SORTEIO, len(resto)), random_state=SEMENTE)
    tab["amostra"] = ""
    tab.loc[tab["critica"], "amostra"] = "crítica"
    tab.loc[sorteio.index, "amostra"] = "sorteio"
    tab.loc[(tab["amostra"] == "") & (tab["osm_estrutura"] != ""), "amostra"] = "osm"
    tab = tab.sort_values(["amostra", "km_separados"], ascending=[True, False], ignore_index=True)

    tab["imagem"] = ""
    for k, lin in tab[tab["amostra"] != ""].iterrows():
        nome = f"{lin['i']}_{lin['j']}.png"
        destino = PASTA_IMG / nome
        if not destino.exists():
            recorte_satelite(lin["_ponto"], rede, lin["i"], lin["j"], destino)
        tab.at[k, "imagem"] = nome

    tab.drop(columns="_ponto").to_csv(RESULTADOS / "triagem_candidatos.csv",
                                      index_label="id", encoding="utf-8-sig")
    print(len(tab), "conexões incertas;", int(tab["critica"].sum()), "críticas;",
          int((tab["osm_estrutura"] != "").sum()), "perto de ponte/túnel no OSM;",
          int((tab["amostra"] != "").sum()), "na amostra")


if __name__ == "__main__":
    main()
