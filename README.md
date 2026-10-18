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

Os slides e a bibliografia fornecidos estão em [material](material/). A seleção das referências específicas será feita durante a preparação do artigo.

## Limites de interpretação

Uma desconexão na infraestrutura cicloviária selecionada não significa necessariamente que seja impossível circular de bicicleta entre os trechos: pode existir ligação por vias comuns. Da mesma forma, continuidade no mapa não garante segurança, conservação, sinalização ou travessia adequada.

Erros geométricos e desatualização cadastral podem produzir descontinuidades artificiais. O artigo analisará a rede representada na base, com conferência dos casos relevantes, sem afirmar efeitos causais sobre uso da bicicleta ou acidentes.

## Próxima etapa

Baixar e inspecionar a base pública para confirmar a viabilidade do recorte e definir as regras de construção da rede. Ainda não há resultados calculados.
