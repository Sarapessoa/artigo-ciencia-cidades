# Dados preservados

As bases consumidas pela análise estão em `brutos/`. As três bases grandes e
os recortes de conferência são armazenados com Git LFS. Após clonar:

```sh
git lfs install
git lfs pull
```

Em 09/11/2026, foram recuperados do checkout local original
`D:/Mestrado/ciencia-cidades/artigo` os arquivos de ruas e caminhos do OSM,
o GeoPackage do IBGE e 81 imagens de conferência (77 de triagem e 4 de lacunas).
Não houve nova consulta às fontes para substituir esses arquivos.
`manifesto.json` registra caminhos, tamanhos e SHA-256 de todas as bases,
das imagens, dos vereditos e dos metadados da fonte. Para os JSONs do OSM,
registra também a data da base informada na resposta Overpass.
A recuperação local não comprova, por si só, qual execução produziu cada resultado.

## Fontes e entradas

- `brutos/malha_cicloviaria.geojson`: Prefeitura de Fortaleza; URL e datas
  registradas em `../resultados/fonte.json`.
- `brutos/limite_fortaleza_ibge.geojson`: API de malhas municipais do IBGE;
  URL em `../resultados/fonte.json`.
- `brutos/osm_ciclovias_fortaleza.json` e `brutos/osm_ruas_fortaleza.json`:
  OpenStreetMap via Overpass; filtros e consulta em `../analise/conferir_lacunas.py`.
- `brutos/osm_viadutos_tuneis.json`: OpenStreetMap via Overpass;
  consulta em `../analise/triagem_conexoes.py`.
- `brutos/osm_caminhos_fortaleza.json`: OpenStreetMap via Overpass;
  consulta em `../analise/populacao_atendida.py`.
- `brutos/CE_setores_CD2022.gpkg`: malha com atributos do Censo 2022 do IBGE;
  endereço completo em `URL_SETORES`, em `../analise/populacao_atendida.py`.
- `brutos/renda_setores_fortaleza.csv`: recorte dos setores de Fortaleza do
  arquivo nacional `Agregados_por_setores_renda_responsavel_BR_20260508_csv.zip`;
  endereço completo em `URL_RENDA` no mesmo script.
- `../resultados/triagem_conexoes.csv`: vereditos manuais utilizados como
  entrada do cenário principal, embora estejam na pasta de resultados.
- `../resultados/triagem/*.png` e `../resultados/lacunas/*.png`: imagens de
  conferência com sobreposições da análise, obtidas de Esri World Imagery.
  O endereço do serviço está em `URL_TILE`, em `../analise/triagem_conexoes.py`.

## Limites do acervo

O ZIP nacional de renda não foi preservado pelo código original e não foi
encontrado no checkout original; o recorte efetivamente usado está preservado.
As imagens são os recortes produzidos pela análise, não os tiles originais
sem sobreposição. A data de captura das imagens não é conhecida.
Assim, o acervo reúne as entradas locais da análise e sua evidência visual,
mas não todos os arquivos originais integrais dos provedores.

Os scripts ainda podem baixar bases ausentes e consultar imagens ao gerar
novamente a conferência. Para reproduzir com as cópias preservadas, primeiro
baixe os objetos LFS e mantenha esses arquivos. Uma consulta nova ao OSM ou à
Esri pode retornar conteúdo diferente. Os hashes permitem detectar alterações.
