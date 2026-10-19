"""Curva das ligações faltantes: quantos metros de ligação pelas ruas conectam qual fração da rede.

Adapta a estratégia gulosa de Natera Orozco et al. (2020): a cada passo, o componente gigante é
ligado a outro componente pelo menor caminho na malha viária do OSM, e o caminho passa a fazer
parte do gigante. Duas regras de escolha do próximo componente:

- "mais próximo": o de menor ligação (como em Natera Orozco et al.);
- "maior ganho": o que acrescenta mais extensão por metro de ligação.

O custo de uma ligação é o caminho pelas ruas mais a distância de cada ponta até o componente
que ela toca (o acesso do trecho à via). Um componente a até RAIO_RUAS_M do caminho escolhido é
absorvido pagando apenas esse acesso.

Saídas: resultados/ligacoes_faltantes.csv (um passo por linha) e
resultados/ligacoes_faltantes.geojson (o caminho de cada passo).

Uso: python ligacoes_faltantes.py
"""
import geopandas as gpd
import networkx as nx
from shapely.geometry import LineString

from conferir_lacunas import (ARQ_RUAS, TIPOS_RUA, malha_viaria, overpass, ruas_do_caminho,
                              vertices_perto)
from rede import CRS_METRICO, RESULTADOS, cenario_principal

ESTRATEGIAS = {
    "mais próximo": lambda km, d: -d,
    "maior ganho": lambda km, d: km / max(d, 1.0),
}
ORIGEM = "__gigante__"


def crescer(R, nome, acesso, km, total_km, escolha):
    """Executa a estratégia gulosa a partir de C1; devolve uma linha por passo.

    `acesso[k]` é {vértice da malha: distância até o componente k}."""
    R = R.copy()
    # nó artificial ligado ao gigante; o peso de cada aresta é o acesso do gigante ao vértice
    R.add_weighted_edges_from(((ORIGEM, n, d) for n, d in acesso[1].items()), weight="w")
    restantes = {k for k in km if k != 1 and acesso.get(k)}
    no_gigante, acumulado = km[1], 0.0
    passos = [{"passo": 0, "componente": 1, "km_componente": km[1], "ligacao_m": 0.0,
               "acumulado_m": 0.0, "pct_gigante": 100 * no_gigante / total_km,
               "absorvidos": "", "ruas": "", "geometry": None}]
    while restantes:
        dist, caminhos = nx.single_source_dijkstra(R, ORIGEM, weight="w")
        candidatos = {}
        for k in restantes:
            custos = {n: dist[n] + d for n, d in acesso[k].items() if n in dist}
            if custos:
                fim = min(custos, key=custos.get)
                candidatos[k] = (custos[fim], fim)
        if not candidatos:
            break
        k = max(candidatos, key=lambda c: escolha(km[c], candidatos[c][0]))
        d, fim = candidatos[k]
        cam = caminhos[fim][1:]  # sem o nó artificial
        nos_caminho = set(cam)
        # o caminho passa a fazer parte do gigante (acesso zero)
        R.add_weighted_edges_from(((ORIGEM, n, 0.0) for n in cam), weight="w")
        # componentes que o caminho toca são absorvidos pagando o próprio acesso
        absorvidos = {c for c in restantes - {k} if nos_caminho & acesso[c].keys()}
        custo_absorvidos = sum(min(acesso[c][n] for n in nos_caminho & acesso[c].keys())
                               for c in absorvidos)
        for c in {k} | absorvidos:
            R.add_weighted_edges_from(((ORIGEM, n, dd) for n, dd in acesso[c].items()), weight="w")
            no_gigante += km[c]
        restantes -= {k} | absorvidos
        acumulado += d + custo_absorvidos
        ruas = ruas_do_caminho(R, nome, cam)
        passos.append({
            "passo": len(passos), "componente": k, "km_componente": km[k],
            "ligacao_m": d + custo_absorvidos, "acumulado_m": acumulado,
            "pct_gigante": 100 * no_gigante / total_km,
            "absorvidos": " ".join(f"C{c}" for c in sorted(absorvidos)),
            "ruas": "; ".join(f"{n} ({m:.0f} m)" for n, m in sorted(ruas.items(), key=lambda x: -x[1])),
            "geometry": LineString(cam) if len(cam) > 1 else None,
        })
    return passos


def main():
    rede, comp = cenario_principal()
    R, nome = malha_viaria(overpass(ARQ_RUAS, [f'way["highway"~"^({TIPOS_RUA})$"]'],
                                    tuple(rede.to_crs(4326).total_bounds)))
    acesso = vertices_perto(R, rede, com_distancia=True)
    km = comp["km"].to_dict()
    total_km = comp["km"].sum()

    linhas = []
    for estrategia, escolha in ESTRATEGIAS.items():
        for p in crescer(R, nome, acesso, km, total_km, escolha):
            linhas.append({"estrategia": estrategia, **p})
    tab = gpd.GeoDataFrame(linhas, geometry="geometry", crs=CRS_METRICO)
    meio = tab.geometry.interpolate(0.5, normalized=True).to_crs(4326)
    tab["lat"], tab["lon"] = meio.y.round(6), meio.x.round(6)
    for c in ("km_componente", "ligacao_m", "acumulado_m"):
        tab[c] = tab[c].round(1)
    tab["pct_gigante"] = tab["pct_gigante"].round(2)

    tab.drop(columns="geometry").to_csv(RESULTADOS / "ligacoes_faltantes.csv", index=False,
                                        encoding="utf-8-sig")
    tab[tab.geometry.notna()].to_crs(4326).to_file(RESULTADOS / "ligacoes_faltantes.geojson",
                                                   driver="GeoJSON")
    for estrategia, t in tab.groupby("estrategia", sort=False):
        print(f"\n{estrategia}:")
        print(t[["passo", "componente", "km_componente", "ligacao_m", "acumulado_m", "pct_gigante",
                 "absorvidos"]].head(12).to_string(index=False))
        for alvo in (75, 80, 90, 95):
            ok = t[t["pct_gigante"] >= alvo]
            print(f"  {alvo}%: " + (f"{ok['acumulado_m'].iloc[0] / 1000:.2f} km de ligações, "
                                    f"{int(ok['passo'].iloc[0])} passos" if len(ok) else "não alcançado"))
        print(f"  final: {t['pct_gigante'].iloc[-1]:.1f}% com {t['acumulado_m'].iloc[-1] / 1000:.1f} km"
              f" em {int(t['passo'].iloc[-1])} passos")


if __name__ == "__main__":
    main()
