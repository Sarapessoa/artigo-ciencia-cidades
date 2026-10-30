"""População atendida pela rede cicloviária, pelo maior componente e por cada componente.

Usa os setores censitários do Censo 2022 (IBGE): moradores (v0001) e rendimento nominal médio
mensal dos responsáveis pelos domicílios (V06004). A população de cada setor é suposta uniforme
na sua área e repartida numa grade de GRADE_M metros; cada célula é representada pelo seu
centroide. Uma célula é "atendida" por um componente se algum trecho dele estiver a até D metros
em linha reta.

Indicadores, para cada D em DISTANCIAS:
- fração da população perto de qualquer trecho, do maior componente (C1) e de C1 + C2, a união
  que o OpenStreetMap atual já registra (ver conferir_lacunas.py);
- extensão alcançável: a extensão do maior componente a até D de cada morador (0 se nenhum);
- os mesmos indicadores por décimo de renda dos setores, ponderado pela população.

Também refaz a curva das ligações faltantes com o ganho medido em população atendida em vez de
extensão (estratégia "maior ganho" de ligacoes_faltantes.py).

Saídas:
- resultados/populacao_atendida.csv: indicadores gerais por distância;
- resultados/populacao_por_renda.csv: indicadores por décimo de renda;
- resultados/populacao_por_setor.csv: indicadores por setor censitário;
- resultados/ligacoes_faltantes_populacao.csv: passos da estratégia ponderada por população;
- figuras/populacao_renda.png: atendimento por décimo de renda.

Uso: python populacao_atendida.py
"""
import io
import urllib.request
import zipfile

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from shapely.geometry import box

from conferir_lacunas import ARQ_RUAS, TIPOS_RUA, malha_viaria, overpass, vertices_perto
from ligacoes_faltantes import ESTRATEGIAS, crescer
from rede import BRUTOS, CRS_METRICO, FIGURAS, RESULTADOS, cenario_principal

FTP = "https://ftp.ibge.gov.br/Censos/Censo_Demografico_2022"
URL_SETORES = (f"{FTP}/Agregados_por_Setores_Censitarios/malha_com_atributos/setores/gpkg/UF/CE/"
               "CE_setores_CD2022.gpkg")
URL_RENDA = (f"{FTP}/Agregados_por_Setores_Censitarios_Rendimento_do_Responsavel/"
             "Agregados_por_setores_renda_responsavel_BR_20260508_csv.zip")
ARQ_SETORES = BRUTOS / "CE_setores_CD2022.gpkg"
ARQ_RENDA = BRUTOS / "renda_setores_fortaleza.csv"
COD_FORTALEZA = "2304400"

GRADE_M = 50
DISTANCIAS = [200, 300, 500]  # metros
D_PRINCIPAL = 300


def baixar(url, arquivo):
    if not arquivo.exists():
        print("baixando", url)
        urllib.request.urlretrieve(url, arquivo)


def setores():
    """Setores de Fortaleza em coordenadas métricas, com moradores e renda média dos responsáveis."""
    baixar(URL_SETORES, ARQ_SETORES)
    s = gpd.read_file(ARQ_SETORES, where=f"CD_MUN='{COD_FORTALEZA}'",
                      columns=["CD_SETOR", "NM_BAIRRO", "v0001"])
    if not ARQ_RENDA.exists():
        # o arquivo nacional tem 30 MB; guarda-se só o recorte de Fortaleza
        print("baixando", URL_RENDA)
        with urllib.request.urlopen(URL_RENDA) as r, zipfile.ZipFile(io.BytesIO(r.read())) as z:
            renda = pd.read_csv(z.open(z.namelist()[0]), sep=";", dtype=str)
        renda[renda["CD_SETOR"].str.startswith(COD_FORTALEZA)].to_csv(ARQ_RENDA, index=False)
    renda = pd.read_csv(ARQ_RENDA, dtype={"CD_SETOR": str})
    renda["renda"] = pd.to_numeric(renda["V06004"], errors="coerce")  # "X" = sigilo
    s = s.merge(renda[["CD_SETOR", "renda"]], on="CD_SETOR", how="left")
    s["moradores"] = pd.to_numeric(s["v0001"], errors="coerce").fillna(0)
    return s.drop(columns="v0001").to_crs(CRS_METRICO)


def grade(s):
    """Células de GRADE_M m recortadas pelos setores, com a população proporcional à área."""
    x0, y0, x1, y1 = s.total_bounds
    xs = np.arange(np.floor(x0 / GRADE_M) * GRADE_M, x1, GRADE_M)
    ys = np.arange(np.floor(y0 / GRADE_M) * GRADE_M, y1, GRADE_M)
    celulas = gpd.GeoDataFrame(geometry=[box(x, y, x + GRADE_M, y + GRADE_M) for x in xs for y in ys],
                               crs=CRS_METRICO)
    s = s[s["moradores"] > 0].assign(area_setor=lambda d: d.area)
    g = gpd.overlay(celulas, s, how="intersection", keep_geom_type=True)
    g["pop"] = g["moradores"] * g.area / g["area_setor"]
    g["geometry"] = g.centroid
    return g[["CD_SETOR", "NM_BAIRRO", "renda", "pop", "geometry"]].reset_index(drop=True)


def perto(pontos, rede, d):
    """Matriz booleana pontos x componentes: há trecho do componente a até d metros do ponto?"""
    ip, it = rede.sindex.query(pontos.geometry, predicate="dwithin", distance=d)
    n_comp = rede["componente"].max()
    m = np.zeros((len(pontos), n_comp + 1), dtype=bool)
    m[ip, rede["componente"].to_numpy()[it]] = True
    return m


def decimos(pontos):
    """Décimo de renda de cada ponto, ponderado pela população (1 = mais pobre)."""
    ok = pontos["renda"].notna()
    ordem = pontos[ok].sort_values("renda")
    acum = ordem["pop"].cumsum() / ordem["pop"].sum()
    dec = pd.Series(np.nan, index=pontos.index)
    dec[ordem.index] = np.minimum(np.ceil(acum * 10), 10)
    return dec


def figura(por_renda):
    t = por_renda[por_renda["distancia_m"] == D_PRINCIPAL]
    fig, (a, b) = plt.subplots(1, 2, figsize=(9, 3.4), layout="constrained")
    x = t["decimo"]
    a.plot(x, t["pct_qualquer"], "o-", color="#888888", label="qualquer trecho")
    a.plot(x, t["pct_c1_c2"], "o--", color="#eb6834", label="C1 + C2 (ligação já no OSM)")
    a.plot(x, t["pct_c1"], "o-", color="#2a78d6", label="maior componente (C1)")
    a.set(ylim=(0, 100), ylabel=f"% dos moradores a até {D_PRINCIPAL} m",
          xlabel="décimo de renda do setor (1 = mais pobre)", xticks=range(1, 11))
    a.legend(frameon=False, fontsize=8)
    b.bar(x, t["km_alcance_medio"], color="#2a78d6")
    b.set(ylabel="extensão alcançável média (km)", xlabel="décimo de renda do setor (1 = mais pobre)",
          xticks=range(1, 11))
    for ax in (a, b):
        ax.spines[["top", "right"]].set_visible(False)
    fig.savefig(FIGURAS / "populacao_renda.png", dpi=200)


def main():
    rede, comp = cenario_principal()
    km = comp["km"].to_dict()
    pontos = grade(setores())
    pop = pontos["pop"].to_numpy()
    total = pop.sum()
    pontos["decimo"] = decimos(pontos)
    km_comp = np.zeros(rede["componente"].max() + 1)
    for k, v in km.items():
        km_comp[k] = v
    print(f"{len(pontos)} células, {total:,.0f} moradores; "
          f"{pontos.loc[pontos['renda'].isna(), 'pop'].sum():,.0f} sem renda informada")

    gerais, por_renda, por_setor = [], [], {}
    for d in DISTANCIAS:
        m = perto(pontos, rede, d)
        qualquer, c1, c12 = m.any(axis=1), m[:, 1], m[:, 1] | m[:, 2]
        alcance = (m * km_comp).max(axis=1)  # extensão do maior componente ao alcance
        alcance_c12 = np.where(c12, km[1] + km[2], alcance)
        linha = {"distancia_m": d,
                 "pct_qualquer": 100 * pop[qualquer].sum() / total,
                 "pct_c1": 100 * pop[c1].sum() / total,
                 "pct_c1_c2": 100 * pop[c12].sum() / total,
                 "pct_c1_entre_atendidos": 100 * pop[c1].sum() / pop[qualquer].sum(),
                 "km_alcance_medio": (pop * alcance).sum() / total,
                 "km_alcance_medio_c1_c2": (pop * alcance_c12).sum() / total}
        gerais.append(linha)
        df = pd.DataFrame({"decimo": pontos["decimo"], "renda": pontos["renda"], "pop": pop,
                           "qualquer": qualquer * pop, "c1": c1 * pop, "c12": c12 * pop,
                           "alcance": alcance * pop})
        g = df.groupby("decimo").agg(pop=("pop", "sum"), qualquer=("qualquer", "sum"),
                                     c1=("c1", "sum"), c12=("c12", "sum"),
                                     alcance=("alcance", "sum"),
                                     renda_min=("renda", "min"), renda_max=("renda", "max"))
        por_renda.append(pd.DataFrame({
            "distancia_m": d, "decimo": g.index.astype(int),
            "renda_min": g["renda_min"].round(0), "renda_max": g["renda_max"].round(0),
            "moradores": g["pop"].round(0),
            "pct_qualquer": 100 * g["qualquer"] / g["pop"], "pct_c1": 100 * g["c1"] / g["pop"],
            "pct_c1_c2": 100 * g["c12"] / g["pop"], "km_alcance_medio": g["alcance"] / g["pop"]}))
        if d == D_PRINCIPAL:
            st = pd.DataFrame({"CD_SETOR": pontos["CD_SETOR"], "NM_BAIRRO": pontos["NM_BAIRRO"],
                               "renda": pontos["renda"], "pop": pop, "qualquer": qualquer * pop,
                               "c1": c1 * pop, "alcance": alcance * pop})
            st = st.groupby(["CD_SETOR", "NM_BAIRRO"]).agg(
                renda=("renda", "first"), moradores=("pop", "sum"), qualquer=("qualquer", "sum"),
                c1=("c1", "sum"), alcance=("alcance", "sum")).reset_index()
            por_setor = pd.DataFrame({
                "CD_SETOR": st["CD_SETOR"], "bairro": st["NM_BAIRRO"], "renda": st["renda"],
                "moradores": st["moradores"].round(1),
                "pct_qualquer": 100 * st["qualquer"] / st["moradores"],
                "pct_c1": 100 * st["c1"] / st["moradores"],
                "km_alcance_medio": st["alcance"] / st["moradores"]})
            m_principal = m

    gerais = pd.DataFrame(gerais).round(2)
    por_renda = pd.concat(por_renda, ignore_index=True).round(2)
    gerais.to_csv(RESULTADOS / "populacao_atendida.csv", index=False, encoding="utf-8-sig")
    por_renda.to_csv(RESULTADOS / "populacao_por_renda.csv", index=False, encoding="utf-8-sig")
    por_setor.round(2).to_csv(RESULTADOS / "populacao_por_setor.csv", index=False,
                              encoding="utf-8-sig")
    figura(por_renda)
    print(gerais.to_string(index=False))
    print(por_renda[por_renda["distancia_m"] == D_PRINCIPAL].to_string(index=False))

    # Ligações faltantes com ganho em população atendida (a até D_PRINCIPAL de algum trecho)
    pop_comp = m_principal * pop[:, None]

    def valor(conjunto):
        return pop[m_principal[:, sorted(conjunto)].any(axis=1)].sum()

    atendida = pop[m_principal.any(axis=1)].sum()
    R, nome = malha_viaria(overpass(ARQ_RUAS, [f'way["highway"~"^({TIPOS_RUA})$"]'],
                                    tuple(rede.to_crs(4326).total_bounds)))
    acesso = vertices_perto(R, rede, com_distancia=True)
    passos = pd.DataFrame(crescer(R, nome, acesso, km, atendida, ESTRATEGIAS["maior ganho"],
                                  valor=valor)).drop(columns="geometry")
    passos = passos.rename(columns={"pct_gigante": "pct_pop_gigante"})
    passos["pop_componente"] = [pop_comp[:, k].sum() for k in passos["componente"]]
    for c in ("km_componente", "ligacao_m", "acumulado_m", "pop_componente"):
        passos[c] = passos[c].round(1)
    passos["pct_pop_gigante"] = passos["pct_pop_gigante"].round(2)
    passos.to_csv(RESULTADOS / "ligacoes_faltantes_populacao.csv", index=False,
                  encoding="utf-8-sig")
    print(passos[["passo", "componente", "km_componente", "pop_componente", "ligacao_m",
                  "acumulado_m", "pct_pop_gigante", "absorvidos"]].head(12).to_string(index=False))
    for alvo in (75, 80, 90, 95):
        ok = passos[passos["pct_pop_gigante"] >= alvo]
        print(f"  {alvo}% da população atendida: "
              + (f"{ok['acumulado_m'].iloc[0] / 1000:.2f} km" if len(ok) else "não alcançado"))


if __name__ == "__main__":
    main()
