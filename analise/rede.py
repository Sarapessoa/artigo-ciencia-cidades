"""Construção da rede cicloviária e cálculo de componentes conectados.

Usado por `conectividade.ipynb` e `triagem_conexoes.py`.
"""
from pathlib import Path

import geopandas as gpd
import networkx as nx
import numpy as np
import pandas as pd
from shapely import get_point

RAIZ = Path(__file__).resolve().parent.parent
BRUTOS = RAIZ / "dados" / "brutos"
RESULTADOS = RAIZ / "resultados"
FIGURAS = RAIZ / "figuras"

CRS_METRICO = 31984  # SIRGAS 2000 / UTM zona 24S
TIPOLOGIAS = ["Ciclovias", "Ciclofaixas"]
TOLERANCIAS = [0, 1, 2, 5, 10, 20, 50]  # metros
TOL_PRINCIPAL = 10


def ler_bruto():
    bruto = gpd.read_file(BRUTOS / "malha_cicloviaria.geojson")
    return bruto.apply(lambda s: s.str.strip() if s.dtype == object else s)


def selecionar(bruto):
    """Ciclovias e ciclofaixas em coordenadas métricas, com extensão em km."""
    rede = bruto[bruto["Tipologia"].isin(TIPOLOGIAS)].to_crs(CRS_METRICO).reset_index(drop=True)
    rede["km"] = rede.length / 1000
    return rede


def conexoes(rede, tol):
    """Pares de trechos conectados, com o tipo de conexão."""
    pares = {}
    pontas = gpd.GeoSeries(
        [get_point(g, k) for g in rede.geometry for k in (0, -1)], crs=rede.crs)
    dono = np.repeat(np.arange(len(rede)), 2)
    if tol == 0:
        ip, jt = rede.sindex.query(pontas, predicate="intersects")
    else:
        ip, jt = rede.sindex.query(pontas, predicate="dwithin", distance=tol)
    for i, j in zip(dono[ip], jt):
        if i != j:
            pares[tuple(sorted((int(i), int(j))))] = "extremidade"
    ia, ib = rede.sindex.query(rede.geometry, predicate="intersects")
    for i, j in zip(ia, ib):
        if i < j and (int(i), int(j)) not in pares:
            pares[(int(i), int(j))] = "cruzamento"
    return pares


def grafo(rede, tol, cruzamentos=True, excluir=()):
    G = nx.Graph()
    G.add_nodes_from(range(len(rede)))
    G.add_edges_from(par for par, tipo in conexoes(rede, tol).items()
                     if (cruzamentos or tipo == "extremidade") and par not in excluir)
    return G


def componentes(rede, G):
    linhas = []
    for nos in nx.connected_components(G):
        nos = sorted(nos)
        linhas.append({"trechos": nos, "n_trechos": len(nos),
                       "km": rede.loc[nos, "km"].sum()})
    comp = pd.DataFrame(linhas).sort_values("km", ascending=False, ignore_index=True)
    comp.index = comp.index + 1
    comp.index.name = "ordem"
    return comp
