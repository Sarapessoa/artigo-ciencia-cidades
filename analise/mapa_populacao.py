"""Mapa da população atendida por setor censitário, ao lado da renda, e resumo por bairro.

Lê resultados/populacao_por_setor.csv (gerado por populacao_atendida.py, a até 300 m pelas ruas)
e classifica cada setor pela situação da maior parte dos moradores:

- "maior componente": a maioria está perto de C1;
- "só componentes menores": a maioria está perto de algum trecho, mas não de C1;
- "sem rede por perto": a maioria não está perto de nenhum trecho.

Saídas:
- figuras/mapa_populacao.png: (a) situação dos setores e a rede; (b) renda dos setores;
- resultados/populacao_por_bairro.csv: moradores em cada situação, por bairro.

Uso: python mapa_populacao.py
"""
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Patch

from populacao_atendida import ARQ_SETORES, COD_FORTALEZA
from rede import BRUTOS, CRS_METRICO, FIGURAS, RESULTADOS, cenario_principal

CLASSES = {"maior componente": "#2a78d6", "só componentes menores": "#eda100",
           "sem rede por perto": "#d3d0c6"}
CINZA_REDE = "#6b6b6b"


def classe(st):
    menores = st["pct_qualquer"] - st["pct_c1"]
    sem = 100 - st["pct_qualquer"]
    return np.select([(st["pct_c1"] >= menores) & (st["pct_c1"] >= sem), menores >= sem],
                     list(CLASSES)[:2], list(CLASSES)[2])


def por_bairro(st):
    st = st.assign(c1=st["moradores"] * st["pct_c1"] / 100,
                   menores=st["moradores"] * (st["pct_qualquer"] - st["pct_c1"]) / 100,
                   sem=st["moradores"] * (100 - st["pct_qualquer"]) / 100,
                   renda_x=st["renda"] * st["moradores"])
    b = st.groupby("bairro").agg(moradores=("moradores", "sum"), c1=("c1", "sum"),
                                 menores=("menores", "sum"), sem=("sem", "sum"),
                                 renda_x=("renda_x", "sum"))
    return pd.DataFrame({
        "moradores": b["moradores"].round(0),
        "renda_media": (b["renda_x"] / b["moradores"]).round(0),
        "moradores_c1": b["c1"].round(0), "moradores_so_menores": b["menores"].round(0),
        "moradores_sem_rede": b["sem"].round(0),
        "pct_c1": (100 * b["c1"] / b["moradores"]).round(1),
        "pct_so_menores": (100 * b["menores"] / b["moradores"]).round(1),
        "pct_sem_rede": (100 * b["sem"] / b["moradores"]).round(1),
    }).sort_values("moradores", ascending=False)


def main():
    rede, _ = cenario_principal()
    geo = gpd.read_file(ARQ_SETORES, where=f"CD_MUN='{COD_FORTALEZA}'",
                        columns=["CD_SETOR"]).to_crs(CRS_METRICO)
    st = pd.read_csv(RESULTADOS / "populacao_por_setor.csv", dtype={"CD_SETOR": str})
    st["classe"] = classe(st)
    setores = geo.merge(st, on="CD_SETOR", how="left")
    limite = gpd.read_file(BRUTOS / "limite_fortaleza_ibge.geojson").to_crs(CRS_METRICO)

    bairros = por_bairro(st)
    bairros.to_csv(RESULTADOS / "populacao_por_bairro.csv", encoding="utf-8-sig")
    total = st["moradores"].sum()
    for c in CLASSES:
        m = st.loc[st["classe"] == c, "moradores"].sum()
        print(f"{c}: {(st['classe'] == c).sum()} setores, {m:,.0f} moradores ({100 * m / total:.1f}%)")
    grandes = bairros[bairros["moradores"] >= 10000]
    for col, titulo in [("moradores_so_menores", "só componentes menores"),
                        ("moradores_sem_rede", "sem rede por perto")]:
        print(f"\nBairros com mais moradores em '{titulo}':")
        print(bairros.sort_values(col, ascending=False).head(10)[
            ["moradores", "renda_media", col, "pct_c1", "pct_so_menores", "pct_sem_rede"]].to_string())
    print("\nBairros (>= 10 mil moradores) com mais extensão por perto mas fora de C1:")
    print(grandes.sort_values("pct_so_menores", ascending=False).head(10)[
        ["moradores", "renda_media", "pct_c1", "pct_so_menores", "pct_sem_rede"]].to_string())

    fig, (a, b) = plt.subplots(1, 2, figsize=(10, 5.2), layout="constrained")
    for ax in (a, b):
        limite.plot(ax=ax, facecolor="#f4f3ef", edgecolor="#c9c8c1", linewidth=0.6)
    sem_moradores = setores["moradores"].isna() | (setores["moradores"] < 1)
    for c, cor in CLASSES.items():
        setores[(setores["classe"] == c) & ~sem_moradores].plot(ax=a, color=cor, linewidth=0)
    rede[rede["componente"] > 1].plot(ax=a, color=CINZA_REDE, linewidth=0.7)
    rede[rede["componente"] == 1].plot(ax=a, color="#174a87", linewidth=0.9)
    a.legend(handles=[Patch(color=cor, label=f"maioria: {c}") for c, cor in CLASSES.items()],
             loc="lower left", frameon=False, fontsize=7)
    a.set_title("(a) moradores a até 300 m da rede, pelas ruas", fontsize=9, loc="left")

    com_renda = setores[~sem_moradores & setores["renda"].notna()].sort_values("renda")
    # quintis ponderados pela população, como os décimos de populacao_atendida.py
    acum = com_renda["moradores"].cumsum() / com_renda["moradores"].sum()
    quintil = np.minimum(np.ceil(acum * 5), 5).astype(int)
    cores = plt.get_cmap("YlGn")(np.linspace(0.15, 0.9, 5))
    legenda = []
    for q in range(1, 6):
        sel = com_renda[quintil == q]
        sel.plot(ax=b, color=cores[q - 1], linewidth=0)
        legenda.append(Patch(color=cores[q - 1],
                             label=f"R$ {sel['renda'].min():,.0f} a {sel['renda'].max():,.0f}"
                             .replace(",", ".")))
    b.legend(handles=legenda, loc="lower left", frameon=False, fontsize=7,
             title="quintis de população", title_fontsize=7)
    rede.plot(ax=b, color=CINZA_REDE, linewidth=0.5)
    b.set_title("(b) rendimento médio dos responsáveis", fontsize=9, loc="left")
    for ax in (a, b):
        ax.set_axis_off()
    fig.savefig(FIGURAS / "mapa_populacao.png", dpi=200)


if __name__ == "__main__":
    main()
