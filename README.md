# Artigo de Ciência de Dados em Cidades

## Tema definido

**Além dos quilômetros: análise da conectividade da rede cicloviária de Fortaleza.**

O artigo investigará a continuidade espacial da infraestrutura cicloviária, usando exclusivamente dados públicos. O recorte inclui ciclovias e ciclofaixas, preservando a classificação de cada trecho. A inclusão das duas modalidades evita interpretar a ligação por uma ciclovia como uma interrupção entre ciclofaixas.

## Pergunta de pesquisa

A infraestrutura cicloviária de Fortaleza forma uma rede contínua ou apresenta conjuntos de trechos desconectados entre si?

## Objetivo

Caracterizar a conectividade da rede cicloviária e identificar suas principais descontinuidades. A análise distinguirá extensão disponível de conexão entre trechos, sem presumir previamente que a rede é fragmentada.

## Relação com a disciplina

O tema articula mobilidade, redes espaciais e acessibilidade urbana. A representação da infraestrutura como grafo permite estudar componentes conectados e a distribuição de seus tamanhos. A conectividade estrutural é uma dimensão da acessibilidade, mas não mede sozinha segurança, conforto ou possibilidade efetiva de realizar todos os deslocamentos.

## Dados públicos

- Fonte inicial: [catálogo de malha cicloviária da Prefeitura de Fortaleza](https://dados.fortaleza.ce.gov.br/dataset/?_license_id_limit=0&_tags_limit=0&organization=amc&q=&tags=malha+cicloviaria), que lista dados em GeoJSON.
- Fonte complementar para conferência: [Fortaleza em Mapas](https://mapas.fortaleza.ce.gov.br/catalogo).
- Recorte espacial: município de Fortaleza.
- Recorte temporal: retrato correspondente à versão disponível do arquivo, com data de atualização e de obtenção registradas na análise.
- Seleção principal: ciclovias e ciclofaixas existentes. Ciclorrotas, passeios compartilhados e trechos apenas planejados não entram automaticamente; eventual inclusão deve ser justificada e apresentada separadamente.

Antes da análise, verificar licença ou condições de uso, disponibilidade do arquivo, campos, categorias, cobertura e data de atualização. A base ainda não foi baixada nem validada para este artigo.

## Método proposto

1. Obter a base pública e registrar sua origem e versão.
2. Inspecionar e filtrar as geometrias; conferir duplicidades, segmentos inválidos e classificação da infraestrutura.
3. Usar um sistema de coordenadas projetadas adequado para medir comprimentos em metros.
4. Construir um grafo em que os nós representem extremidades e conexões reais, e as arestas representem os trechos cicloviários.
5. Conferir cruzamentos, passagens em níveis diferentes e pequenas lacunas cartográficas antes de definir conexões. Proximidade geométrica não comprova passagem entre trechos.
6. Calcular componentes conectados e seus comprimentos. Como análise estrutural inicial, usar grafo não direcionado; isso não representa restrições de sentido de circulação.
7. Verificar a sensibilidade dos resultados à tolerância usada para unir extremidades próximas, justificando o parâmetro adotado.
8. Examinar no mapa as principais descontinuidades e discutir os limites da representação.

## Indicadores principais

- Número de componentes conectados.
- Extensão de cada componente, em quilômetros.
- Proporção da extensão total pertencente ao maior componente: comprimento do maior componente dividido pelo comprimento total da rede analisada.
- Localização dos principais conjuntos desconectados.

O tamanho dos componentes será comparado principalmente por extensão, pois a quantidade de segmentos depende de como o arquivo foi desenhado e subdividido.

## Figura planejada

Uma figura composta por dois painéis:

- **(a)** Mapa da rede, destacando o maior componente e os demais conjuntos conectados.
- **(b)** Gráfico ordenado da extensão dos componentes, destacando a participação do maior no total.

## Exigências do professor

Conforme [instrucoes.pdf](instrucoes.pdf), o artigo deve:

- Ter no máximo três páginas.
- Incluir pelo menos uma figura contendo um gráfico.
- Analisar dados ou um modelo relacionado a cidades usando temas e técnicas da disciplina.
- Explicar o problema e contextualizá-lo com referências.
- Descrever a metodologia.
- Apresentar resultados, conclusões e limitações.

O texto será escrito no Overleaf a partir do template [Modelo Unifor](https://www.overleaf.com/latex/templates/modelo-unifor/gscygbjpxjmw). Esse template usa classe `article`, folha A4, fonte Helvetica e espaçamento 1,5, além de referências manuais com `thebibliography`.

Os slides e a bibliografia fornecidos estão em [material](material/). A seleção das referências específicas será feita durante a preparação do artigo.

## Limites de interpretação

Uma desconexão na infraestrutura cicloviária selecionada não significa necessariamente que seja impossível circular de bicicleta entre os trechos: pode existir ligação por vias comuns. Da mesma forma, continuidade no mapa não garante segurança, conservação, sinalização ou travessia adequada.

Erros geométricos e desatualização cadastral podem produzir descontinuidades artificiais. O artigo analisará a rede representada na base, com conferência dos casos relevantes, sem afirmar efeitos causais sobre uso da bicicleta ou acidentes.

## Como reproduzir

```
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
cd analise && ../.venv/Scripts/python -m nbconvert --to notebook --execute --inplace conectividade.ipynb
```

O notebook [analise/conectividade.ipynb](analise/conectividade.ipynb) baixa os dados para `dados/brutos/`, se ainda não estiverem lá, grava as tabelas em `resultados/` e gera a figura em `figuras/conectividade.pdf`.

## Triagem das conexões incertas

O cenário principal usa tolerância de 10 m e conta os cruzamentos como conexões. Há 275 conexões incertas: cruzamentos sem extremidade próxima e uniões que só existem com tolerância acima de 0 m. Uma amostra foi conferida em imagem de satélite (Esri World Imagery) com [analise/triagem_conexoes.py](analise/triagem_conexoes.py). A amostra tem 77 conexões:

- as 39 **críticas**, cuja remoção separa parte da rede;
- as 18 restantes a até 20 m de ponte, viaduto ou túnel no OpenStreetMap;
- um sorteio de 20 entre as demais.

Os vereditos estão em `resultados/triagem_conexoes.csv`:

| Veredito | Críticas | Perto de estrutura (OSM) | Sorteio | Total |
|---|---|---|---|---|
| Confirmada (travessia ou continuidade visível) | 12 | 0 | 3 | 15 |
| Em nível (encontro em nível, sem sinalização visível) | 26 | 7 | 15 | 48 |
| Desnível (viaduto, túnel ou passagem inferior) | 1 | 9 | 1 | 11 |
| Inconclusiva | 0 | 2 | 1 | 3 |

As 11 passagens em desnível são removidas do cenário principal. Só uma delas era crítica: a Av. Dep. Paulino Rocha sob a Rotatória do Castelão, que separa 0,8 km. Com isso, a rede fica com 44 componentes, e o maior soma 241,0 km (56,1%). Sem as 3 inconclusivas, o maior componente cai para 236,4 km (55,1%).

A data das imagens não é informada e pode ser diferente da data de referência da base (2022). Uma travessia "em nível" indica apenas que as vias se encontram, não que haja sinalização cicloviária.

## Conferência das lacunas

O script [analise/conferir_lacunas.py](analise/conferir_lacunas.py) examina as separações entre o maior componente (C1) e os quatro seguintes. A tabela resultante é `resultados/lacunas.csv`. Para cada componente, ele calcula:

- a lacuna em **linha reta**;
- se a infraestrutura cicloviária do **OpenStreetMap atual** (19/10/2026, em `dados/brutos/osm_ciclovias_fortaleza.json`) já liga o componente a C1. Pontes e túneis do OSM só se ligam a outras vias pelas próprias extremidades;
- a menor ligação **pelas ruas**, na malha viária do OSM.

| | Extensão | Linha reta | Pelo OSM atual | Pelas ruas |
|---|---|---|---|---|
| C2 (oeste) | 66,6 km | 344 m | ligado, com 785 m de vias ausentes da base | 455 m |
| C3 (sudeste) | 64,0 km | 686 m | sem ligação | 799 m |
| C4 | 11,2 km | 62 m | sem ligação | 56 m |
| C5 | 4,6 km | 2 197 m | sem ligação | 2 780 m |

O que a conferência mostrou:

- **C2.** A linha reta de 344 m cai num cruzamento em desnível: a ciclovia de C1 na Av. Mister Hull passa sob o Viaduto Antônio Bezerra. No OSM, a ciclofaixa do viaduto e das ruas Dr. Catunda Gondim e Coronel Matos Dourado liga C2 a C1. Essas vias receberam a marcação de ciclofaixa em 30/08/2024 e 22/11/2024, segundo o histórico do OSM, e a faixa aparece na imagem de satélite. A ligação é posterior ao ano de referência da base (2022) ou foi omitida nela.
- **C3.** A linha reta de 686 m atravessa a mata do Parque do Cocó e não corresponde a uma ligação possível. Pelas ruas, a menor ligação tem 799 m, pela Av. Eng. Santana Júnior (ponte sobre o Rio Cocó) e pela Av. Rogaciano Leite. Nenhuma das duas tem infraestrutura cicloviária, nem na base nem no OSM atual.
- **C4.** A ligação de 56 m passa por uma viela, ao lado da Av. Sen. Carlos Jereissati.

## Ligações faltantes

O script [analise/ligacoes_faltantes.py](analise/ligacoes_faltantes.py) adapta a estratégia gulosa de Natera Orozco et al. (2020). A cada passo, o maior componente é ligado a outro pelo menor caminho na malha viária do OSM, e o caminho passa a fazer parte dele. O custo inclui o acesso de cada trecho à via. São comparadas duas regras de escolha do próximo componente: o **mais próximo** e o de **maior ganho**, isto é, mais extensão por metro de ligação. Os passos ficam em `resultados/ligacoes_faltantes.csv`, e os caminhos em `.geojson`.

| Fração da rede no maior componente | 75% | 80% | 90% | 95% | 100% |
|---|---|---|---|---|---|
| Maior ganho | 0,56 km | 1,38 km | 1,40 km | 3,5 km | 18,2 km |
| Mais próximo | 3,7 km | 3,7 km | 5,5 km | 5,5 km | 17,2 km |

Pela regra de maior ganho, os três primeiros passos relevantes ligam C4 (68 m), C2 (477 m) e C3 (818 m). A análise usa só a base de 2022: a ligação de C2, que o OSM já registra, entra aqui como se ainda fosse necessária.

## Texto

O artigo é escrito em LaTeX em [texto/artigo.tex](texto/artigo.tex), com as referências em [texto/referencias.bib](texto/referencias.bib), e compilado localmente com o MiKTeX. O PDF resultante é [texto/artigo.pdf](texto/artigo.pdf).

O formato, em duas colunas e com as seções nomeadas pelas três perguntas do manual do professor, segue o artigo de [skaduhs5232/Tese](https://github.com/skaduhs5232/Tese/blob/main/artigo/main.tex). Desse arquivo foi aproveitado apenas o layout; o conteúdo é deste trabalho. As referências usam `texto/unsrt-pt.bst`, uma cópia do estilo `unsrt` que liga os autores com "e" em vez de "and".

A logo da Unifor do cabeçalho está em `texto/figs/unifor_logo.png`.

O texto final é compilado no **Overleaf**. Para criar o projeto:

1. Gere o pacote com `python texto/gerar_overleaf.py`. O resultado é `texto/overleaf.zip`, que fica fora do git. Ele contém `main.tex`, `referencias.bib`, `unsrt-pt.bst`, `figuras/conectividade.pdf` e `figs/unifor_logo.png`.
2. No Overleaf, use **New Project → Upload Project** e escolha o zip.
3. Confirme que o compilador é **pdfLaTeX** (Menu → Compiler). O Overleaf roda o BibTeX automaticamente.

Para compilar localmente, sem Overleaf, use `powershell -File texto/compilar.ps1`. O script roda `pdflatex`, `bibtex` e `pdflatex` mais duas vezes, com os auxiliares em `texto/build/`. O LaTeX Workshop do VS Code usa a mesma sequência (`.vscode/settings.json`).

## Próxima etapa

Criar o projeto no Overleaf e revisar o rascunho.
