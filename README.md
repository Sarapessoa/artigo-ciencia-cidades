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

## Figura

A figura do artigo (`figuras/conectividade.pdf`, gerada pelo notebook) tem três painéis:

- **(a)** Mapa da rede, destacando os cinco maiores componentes e as ligações conferidas.
- **(b)** Moradores a até 300 m da rede pelas ruas, por décimo de renda, com o índice de concentração de cada curva.
- **(c)** Curva das ligações faltantes.

O gráfico ordenado da extensão dos componentes, que ocupava o painel (b), saiu para dar lugar ao recorte de renda.

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

Instale o Git LFS e execute `git lfs pull` ap?s clonar para obter as bases grandes
e as imagens preservadas. Consulte [o invent?rio dos dados](dados/README.md)
para fontes, hashes e limites do acervo.

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

## População atendida

O script [analise/populacao_atendida.py](analise/populacao_atendida.py) cruza a rede com os setores censitários do **Censo 2022** (IBGE), usando os moradores (`v0001`) e o rendimento nominal médio dos responsáveis pelos domicílios (`V06004`). A população de cada setor é tratada como uniforme na sua área e repartida numa grade de 50 m. Um morador é considerado atendido por um componente se algum trecho dele estiver a até 300 m **pelas ruas**. Os resultados ficam em `resultados/populacao_*.csv` e em `figuras/populacao_renda.png`.

A distância pelas ruas usa a malha viária do OSM de `conferir_lacunas.py`, com as arestas divididas a cada 20 m. Ela é a soma de três partes:

1. a distância em linha reta da célula até o vértice mais próximo;
2. o menor caminho pelas ruas;
3. a chegada ao componente por um vértice a até 15 m dele.

Na mediana, o caminho pelas ruas é 1,27 vez a distância em linha reta. A medida em linha reta foi mantida para comparação (coluna `medida`).

| Distância | Medida | Perto de algum trecho | Perto de C1 | Perto de C1 + C2 | Extensão alcançável média |
|---|---|---|---|---|---|
| 200 m | ruas | 34,0% | 19,9% | 26,8% | 55 km |
| **300 m** | **ruas** | **48,3%** | **27,7%** | **37,9%** | **76 km** |
| 500 m | ruas | 68,0% | 37,8% | 52,9% | 105 km |
| 300 m | linha reta | 60,3% | 34,0% | 46,8% | 94 km |

A extensão alcançável é a do maior componente a até essa distância de cada morador, ou zero se não houver nenhum. C1 + C2 é o cenário em que a ligação já registrada no OSM (ver acima) entra na rede. Entre os moradores perto de algum trecho, só 57% estão perto de C1.

Por décimo de renda dos setores, a até 300 m pelas ruas:

| Décimo | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|---|
| Perto de algum trecho | 35% | 32% | 36% | 44% | 48% | 47% | 47% | 54% | 63% | 78% |
| Perto de C1 | 11% | 9% | 14% | 15% | 25% | 25% | 27% | 39% | 46% | 66% |
| Perto de C1 + C2 | 26% | 22% | 28% | 33% | 40% | 37% | 36% | 44% | 46% | 66% |
| Extensão alcançável (km) | 37 | 32 | 45 | 51 | 71 | 70 | 73 | 101 | 119 | 166 |

A desigualdade aparece de duas formas. A primeira é de cobertura: os mais pobres têm menos trechos por perto. A segunda é de conectividade: a infraestrutura perto deles pertence com mais frequência a componentes pequenos. No décimo mais rico, 84% dos atendidos estão perto de C1. No mais pobre, só 32%. A ligação de C2 é a que mais beneficia a baixa renda: no primeiro décimo, o atendimento por C1 passa de 11% para 26%.

A curva das ligações faltantes foi refeita com o ganho medido em **população atendida** pelas ruas, em vez de extensão (`resultados/ligacoes_faltantes_populacao.csv`). C2 vem primeiro: com 477 m de ligação, o maior componente passa de 57% para 78% da população atendida. Depois vêm C4 e C3. Com 1,6 km de ligações, chega a 90%; com 3,0 km, a 95%.

Limites:

- A malha viária não inclui calçadas nem caminhos de pedestres (`footway`, `path`). Em áreas onde esses são o acesso principal, a distância pode estar superestimada.
- A renda é a média do setor, então a análise é ecológica e não descreve indivíduos.
- A data de referência dos setores (2022) coincide com a da base cicloviária.

### Robustez e índice de concentração

**Calçadas e caminhos de pedestres.** Em áreas de vielas, eles podem ser o acesso principal, e a malha viária usada não os inclui. Para testar, a medida `ruas_e_caminhos` acrescenta à malha os caminhos de pedestres do OSM (`footway`, `path`, `steps` e `corridor`), que somam 17 mil vias. Os resultados quase não mudam. A até 300 m, o atendimento por C1 passa de 27,7% para 27,9%. O gradiente por renda se mantém: de 11% no décimo mais pobre a 66% no mais rico. A ressalva é que o teste depende do quanto as vielas estão mapeadas no OSM.

**Índice de concentração.** O índice resume a desigualdade por renda num número só. É o dobro da covariância entre o indicador e a posição de cada morador na distribuição de renda, dividido pela média do indicador. Vale 0 quando o indicador se distribui por igual entre ricos e pobres e fica positivo quando se concentra nos de maior renda. Para 300 m pelas ruas, ficam assim:

| Indicador | Índice de concentração |
|---|---|
| Perto de algum trecho | 0,15 |
| Perto de C1 | 0,33 |
| Perto de C1 + C2 | 0,17 |
| Extensão alcançável | 0,28 |
| Extensão alcançável, com C2 ligado | 0,17 |

O que os índices mostram:

- **Conectividade e cobertura.** A desigualdade no acesso à parte conectada da rede (0,33) é o dobro da desigualdade em ter algum trecho por perto (0,15). A rede chega aos bairros pobres, mas em pedaços desconectados.
- **Efeito de C2.** A ligação de C2 reduz a concentração do acesso a C1 de 0,33 para 0,17, quase o nível da simples cobertura.
- **Outras distâncias e medidas.** O padrão se repete a 200 m e a 500 m e também em linha reta. Os valores estão nas colunas `ic_*` de `resultados/populacao_atendida.csv`.

### Mapa por setor

O script [analise/mapa_populacao.py](analise/mapa_populacao.py) classifica cada setor pela situação da maioria dos seus moradores, a até 300 m pelas ruas. O mapa fica em `figuras/mapa_populacao.png`, com a renda ao lado, e o resumo por bairro em `resultados/populacao_por_bairro.csv`.

| Situação da maioria | Setores | Moradores |
|---|---|---|
| perto do maior componente | 1 225 | 690 mil (28%) |
| perto só de componentes menores | 903 | 517 mil (21%) |
| sem rede por perto | 2 178 | 1,22 milhão (50%) |

O que o mapa mostra:

- **Componentes menores.** A população perto só de componentes menores se concentra em dois blocos. O primeiro é o oeste (C2), de baixa renda: Bom Jardim (85% dos moradores nessa situação), Bonsucesso, Canindezinho, Genibaú, Granja Lisboa e Granja Portugal, todos com renda média abaixo de R$ 1.700. O segundo é o sudeste (C3), de renda média e alta: Eng. Luciano Cavalcante (R$ 6.899), Cidade dos Funcionários e Messejana. A fragmentação não atinge só a baixa renda, mas é no oeste que ela pesa sobre mais gente.
- **Sem rede por perto.** Os maiores contingentes estão nas bordas da cidade, sobretudo ao sul: Jangurussu (59 mil moradores, 83%), Mondubim, Siqueira, Planalto Ayrton Senna e Lagoa Redonda. No noroeste, aparece Vila Velha.

## Texto

O artigo é escrito em LaTeX em [texto/artigo.tex](texto/artigo.tex), com as referências em [texto/referencias.bib](texto/referencias.bib), e compilado localmente com o MiKTeX. O PDF resultante é [texto/artigo.pdf](texto/artigo.pdf).

O formato, em duas colunas e com as seções nomeadas pelas três perguntas do manual do professor, segue o artigo de [skaduhs5232/Tese](https://github.com/skaduhs5232/Tese/blob/main/artigo/main.tex). Desse arquivo foi aproveitado apenas o layout; o conteúdo é deste trabalho. As referências usam `texto/unsrt-pt.bst`, uma cópia do estilo `unsrt` que liga os autores com "e" em vez de "and".

A logo da Unifor do cabeçalho está em `texto/figs/unifor_logo.png`.

O texto final é compilado no **Overleaf**. Para criar o projeto:

1. Gere o pacote com `python texto/gerar_overleaf.py`. O resultado é `texto/overleaf.zip`, que fica fora do git. Ele contém `main.tex`, `referencias.bib`, `unsrt-pt.bst`, `figuras/conectividade.pdf` e `figs/unifor_logo.png`.
2. No Overleaf, use **New Project → Upload Project** e escolha o zip.
3. Confirme que o compilador é **pdfLaTeX** (Menu → Compiler). O Overleaf roda o BibTeX automaticamente.

Com um plano que inclua a integração Git, os envios seguintes dispensam o upload manual:

```
python texto/gerar_overleaf.py --enviar https://git.overleaf.com/<id-do-projeto>
```

O endereço aparece em Menu → Integrations → Git e só é necessário na primeira vez. O script clona o projeto em `texto/overleaf/`, que fica fora do git, copia os arquivos, faz o commit e envia. Na clonagem, o Git pede usuário `git` e, como senha, um token gerado nas configurações da conta do Overleaf; o gerenciador de credenciais guarda o token, que não fica no repositório. Se houver edições feitas direto no Overleaf, o script as baixa para `texto/overleaf/` e para sem sobrescrevê-las; passe-as para `texto/artigo.tex` e rode de novo.

Para compilar localmente, sem Overleaf, use `powershell -File texto/compilar.ps1`. O script roda `pdflatex`, `bibtex` e `pdflatex` mais duas vezes, com os auxiliares em `texto/build/`. O LaTeX Workshop do VS Code usa a mesma sequência (`.vscode/settings.json`).

## Apresentação do artigo

A versão acadêmica, com 23 slides, está em
[apresentacao_artigo_cicloviaria_fortaleza_academica.pdf](output/pdf/apresentacao_artigo_cicloviaria_fortaleza_academica.pdf).
Inclui contexto, fontes dos dados, método, exemplos didáticos, resultados e limitações.

Para gerar novamente no Windows, com as fontes Arial instaladas:

```powershell
python -m pip install -r texto/requirements-apresentacao.txt
python texto/gerar_apresentacao.py
```

O gerador usa os resultados e a figura já existentes no repositório. Ele verifica
as 23 páginas e os limites dos textos, e salva imagens de conferência em
`tmp/pdfs/apresentacao/`. Essas imagens são temporárias, não são versionadas e
podem ser removidas após a revisão visual.

## Próxima etapa do artigo

Criar o projeto no Overleaf e revisar o rascunho.
