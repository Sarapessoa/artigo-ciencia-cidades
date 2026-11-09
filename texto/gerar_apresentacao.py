"""Gera os slides em PDF a partir do artigo e das tabelas locais.

Uso: python texto/gerar_apresentacao.py
"""
from pathlib import Path
import csv
import math
import pymupdf
from PIL import Image, ImageDraw
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output/pdf'
TMP = ROOT / 'tmp/pdfs/apresentacao'
OUT.mkdir(parents=True, exist_ok=True)
TMP.mkdir(parents=True, exist_ok=True)
DEST = OUT / 'apresentacao_artigo_cicloviaria_fortaleza_academica.pdf'
pdfmetrics.registerFont(TTFont('Arial', 'C:/Windows/Fonts/arial.ttf'))
pdfmetrics.registerFont(TTFont('Arial-Bold', 'C:/Windows/Fonts/arialbd.ttf'))
pdfmetrics.registerFontFamily('Arial', normal='Arial', bold='Arial-Bold', italic='Arial', boldItalic='Arial-Bold')
W, H = 1280, 720
INK, BLUE, ORANGE, GREEN = '#202020', '#287DCC', '#C56032', '#168B70'
MUTED, GRID, BG = '#454545', '#CDD5DF', '#FFFFFF'
NAVY = '#173C69'
c = canvas.Canvas(str(DEST), pagesize=(W,H))
c.setTitle('Além dos quilômetros | Apresentação do artigo')
c.setAuthor('Sara Pessoa Silva')
page = 0

def txt(text, x, top, width=1152, size=24, color=INK, bold=False, leading=None, font=None):
    # Uma única família tipográfica em toda a apresentação.
    if font in ('Georgia', 'Georgia-Italic'): font = 'Arial-Bold' if bold else 'Arial'
    style = ParagraphStyle('p', fontName=font or ('Arial-Bold' if bold else 'Arial'), fontSize=size,
                           leading=leading or size*1.25, textColor=HexColor(color))
    p = Paragraph(text, style)
    _, h = p.wrap(width, 2000)
    if top+h > 663:
        raise ValueError(f'Slide {page}: text below content limit: {text[:60]} ({top+h})')
    p.drawOn(c,x,H-top-h)
    return h

def line(x1,y1,x2,y2,color=GRID,width=1):
    c.setStrokeColor(HexColor(color)); c.setLineWidth(width)
    c.line(x1,H-y1,x2,H-y2)

def start(title, source, section=''):
    global page
    page += 1
    c.setFillColor(HexColor('#FFFFFF' if '44 componentes' in title else BG)); c.rect(0,0,W,H,fill=1,stroke=0)
    if title:
        txt(title,64,47,1152,36,NAVY,True,44)
        line(64,108,1216,108,NAVY,2)
    # Footers are intentionally outside the content area.
    line(64,674,1216,674,GRID,.7)
    c.setFont('Arial',11); c.setFillColor(HexColor(MUTED))
    c.drawString(64,25,source)
    c.drawRightString(1216,25,f'{page:02d}')

def end(): c.showPage()

def note(text, top=590):
    txt(text,64,top,1152,23,INK)

def rows(items, x=64, top=165, width=1152, step=112):
    for i,(head,body) in enumerate(items):
        y=top+i*step
        txt('•',x,y,28,25,NAVY,True)
        h=txt(head,x+30,y,width-30,25,INK,True)
        txt(body,x+30,y+h+10,width-30,24,MUTED)

def table(headers, data, widths, top=190, x=64, rowh=76, size=23):
    c.setFillColor(HexColor('#E8EEF5'))
    c.rect(x,H-top-43,sum(widths),53,fill=1,stroke=0)
    xx=x
    for h,w in zip(headers,widths):
        txt(h,xx+12,top,w-24,19,NAVY,True); xx+=w
    line(x,top+43,x+sum(widths),top+43)
    for j,row in enumerate(data):
        xx=x; y=top+55+j*rowh
        if j%2==1:
            c.setFillColor(HexColor('#F5F7FA'))
            c.rect(x,H-(y+rowh-15),sum(widths),rowh,fill=1,stroke=0)
        for v,w in zip(row,widths):
            txt(str(v),xx+12,y,w-24,size,INK); xx+=w
        line(x,y+rowh-15,x+sum(widths),y+rowh-15)

def image_box(path,x,top,w,h):
    im=Image.open(path)
    iw,ih=im.size; scale=min(w/iw,h/ih)
    dw,dh=iw*scale,ih*scale
    c.drawImage(ImageReader(im),x+(w-dw)/2,H-top-dh,dw,dh,mask='auto')

def data(name):
    with open(ROOT/'resultados'/name,encoding='utf-8-sig') as f: return list(csv.DictReader(f))

def chart_lines(series, xmin,xmax,ymin,ymax,xticks,yticks,xlabel,ylabel,x=100,top=210,w=760,h=345):
    def X(v):return x+(v-xmin)/(xmax-xmin)*w
    def Y(v):return top+h-(v-ymin)/(ymax-ymin)*h
    txt(ylabel,x,top-45,w,19,MUTED)
    for v in yticks:
        line(x,Y(v),x+w,Y(v),GRID)
        txt(str(v).replace('.',','),x-55,Y(v)-12,48,17,MUTED)
    for v in xticks:
        txt(str(v).replace('.',','),X(v)-10,top+h+13,60,17,MUTED)
    line(x,top,x,top+h,MUTED); line(x,top+h,x+w,top+h,MUTED)
    txt(xlabel,x,top+h+45,w,19,MUTED)
    for points,color,label in series:
        c.setStrokeColor(HexColor(color)); c.setLineWidth(4)
        p=c.beginPath(); p.moveTo(X(points[0][0]),H-Y(points[0][1]))
        for xx,yy in points[1:]:p.lineTo(X(xx),H-Y(yy))
        c.drawPath(p)
        if len(points)<15:
            for xx,yy in points:
                c.setFillColor(HexColor(color));c.circle(X(xx),H-Y(yy),5,stroke=0,fill=1)

def bars(labels,values,colors,maxval=100,unit='%',top=205,x=64,w=780,step=116):
    for i,(lab,val,col) in enumerate(zip(labels,values,colors)):
        y=top+i*step
        txt(lab,x,y,w,22,INK,True)
        line(x,y+63,x+w,y+63,GRID,.8)
        c.setFillColor(HexColor(col));c.rect(x,H-y-71,w*val/maxval,20,fill=1,stroke=0)
        txt(f'{val:g}'.replace('.',',')+unit,x+w+22,y+34,280,29,col,True)

# Crop only the existing map panel; all numeric charts below remain vector PDF content.
fig=pymupdf.open(ROOT/'figuras/conectividade.pdf')
r=fig[0].rect
fig[0].get_pixmap(matrix=pymupdf.Matrix(3,3),clip=pymupdf.Rect(0,0,r.width*.465,r.height*.88)).save(TMP/'mapa.png')

start('','Artigo de Sara Pessoa Silva, versão local de 3 de novembro de 2026')
image_box(ROOT/'texto/figs/unifor_logo.png',64,38,220,94)
txt('Universidade de Fortaleza<br/>Programa de Pós-Graduação em Informática Aplicada',330,54,870,25,NAVY,True,34)
line(64,154,1216,154,NAVY,2)
txt('Além dos quilômetros',64,212,1152,46,NAVY,True,55)
txt('Fragmentação da rede cicloviária de Fortaleza<br/>e desigualdade no acesso',64,295,1152,32,INK,True,42)
txt('<b>Autora:</b> Sara Pessoa Silva',64,429,1152,25)
txt('<b>Disciplina:</b> Ciência de Dados Aplicado à Ciência de Cidades',64,482,1152,25)
txt('<b>Professor:</b> Hygor P. M. Melo',64,535,1152,25)
txt('Fortaleza, 9 de novembro de 2026',64,606,1152,23,MUTED)
end()

start('Contexto e problema','Fonte: artigo, seção “Qual é o problema?”; Hansen (1959), Natera Orozco et al. (2020).')
rows([
 ('Contexto','A base municipal reúne 429 km de ciclovias e ciclofaixas. A extensão é uma medida frequente de expansão da infraestrutura.'),
 ('Problema','A soma dos quilômetros não informa se os trajetos são contínuos nem quais grupos da população estão próximos da rede.'),
 ('Exemplo','Dois trechos de 5 km somam 10 km mesmo quando estão separados e não permitem um percurso contínuo pela infraestrutura.'),
],top=153,step=124)
txt('Pergunta de pesquisa',64,547,1152,26,NAVY,True)
txt('As ciclovias e ciclofaixas formam uma rede contínua? Como a proximidade do maior componente varia por renda?',64,591,1152,25,INK,False,31)
end()

start('A origem dos dados','Fontes: artigo, referencias.bib e resultados/fonte.json','01 / Fontes')
table(['Fonte','Dados utilizados','Referência e obtenção'],[
 ['Prefeitura de Fortaleza','Traçado e tipologia dos trechos<br/>Arquivo GeoJSON','Referência predominante: 2022<br/>Obtido em 19/10/2026'],
 ['IBGE','Setores, população e renda<br/>média dos responsáveis','Censo Demográfico 2022<br/>Acesso em 30/10/2026'],
 ['OpenStreetMap','Malha viária e conferência<br/>das ligações','Extração citada no artigo:<br/>19/10/2026'],
], [300,410,442],top=173,rowh=110,size=24)
note('O traçado vem da Prefeitura; os moradores próximos vêm do IBGE.',574)
txt('Atualização do catálogo municipal em 2024 não significa que todos os trechos retratem 2024.',64,625,1152,17,MUTED)
end()

start('Quais trechos entram na análise?','Fontes: dados/brutos/malha_cicloviaria.geojson; analise/rede.py; artigo','02 / Preparação')
table(['Categoria no arquivo','Registros','Decisão'],[
 ['Ciclofaixas','313','Incluir'],['Ciclovias','93','Incluir'],
 ['Ciclorrotas e passeios compartilhados','41','Excluir: cerca de 17 km'],
], [650,180,322],top=159,rowh=78)
txt('406 trechos selecionados',64,475,600,34,INK,False,font='Georgia')
txt('429 km de infraestrutura',700,475,510,34,INK,False,font='Georgia')
note('Exemplo real: “Via Expressa”, classificada como ciclovia, permanece na base.',559)
txt('Comprimentos calculados em metros no sistema SIRGAS 2000 / UTM 24S (EPSG:31984).',64,622,1152,18,MUTED)
end()

start('Como os trechos viram um grafo','Fonte: artigo e analise/rede.py. Valores A–D abaixo são exemplos didáticos.','03 / Representação')
txt('<b>Nó:</b> um trecho cadastrado. <b>Aresta:</b> uma conexão entre dois trechos.',64,151,1152,26)
table(['Par de trechos','Situação geométrica','Regra inicial'],[
 ['A e B','Eles se intersectam','Conectar'],
 ['B e C','Extremidade a 8 m do outro trecho','Conectar: tolerância de 10 m'],
 ['C e D','Extremidade a 18 m do outro trecho','Manter separados'],
], [210,510,432],top=220,rowh=80,size=23)
note('Resultado do exemplo: {A, B, C} formam um componente; {D} forma outro.',580)
txt('O grafo é não direcionado: o modelo não representa os sentidos permitidos de circulação.',64,625,1152,18,MUTED)
end()

start('Uma interseção no mapa pode ser um viaduto','Fontes: artigo; resultados/triagem_conexoes.csv; README, triagem das conexões','04 / Conferência')
txt('77 conexões incertas inspecionadas em imagens de satélite',64,157,1130,28,INK,True)
table(['Classificação','Quantidade','Tratamento'],[
 ['Confirmada ou em nível','63','Manter no cenário principal'],
 ['Passagem em desnível','11','Remover a conexão do grafo'],
 ['Inconclusiva','3','Manter e testar sua exclusão'],
], [505,180,467],top=224,rowh=74,size=23)
note('Exemplo real: Av. Dep. Paulino Rocha sob a Rotatória do Castelão.',555)
txt('Excluir essa conexão separa 0,8 km. A amostra não representa uma auditoria de toda a rede.',64,610,1152,22,MUTED)
end()

start('Os 429 km formam 44 componentes','Fonte: artigo, Figura 1a. Cores preservadas do mapa original.','05 / Resultado da rede')
image_box(TMP/'mapa.png',55,144,610,500)
txt('241 km',735,169,440,48,BLUE,True)
txt('C1: 56% da extensão total<br/>Centro, orla e eixo ao sul',735,233,460,24)
txt('67 km no oeste',735,328,460,31,ORANGE,True)
txt('C2: segundo maior componente',735,376,460,23,MUTED)
txt('64 km no sudeste',735,445,460,31,GREEN,True)
txt('C3: terceiro maior componente',735,493,460,23,MUTED)
txt('Exemplo de leitura: trechos laranja se conectam entre si, mas ficam separados de C1 na base.',735,560,460,21)
end()

start('Duas desconexões com diagnósticos distintos','Fonte: artigo, seção de fragmentação; conferência com OSM e imagens de satélite','06 / Verificação das lacunas')
txt('C1 e C2 • Antônio Bezerra',64,168,550,28,ORANGE,True)
txt('Uma ciclofaixa de cerca de 0,8 km aparece no OSM desde 2024 e na imagem de satélite.',64,232,520,26)
txt('Sua inclusão elevaria C1 a cerca de 72% da extensão.',64,364,520,26,ORANGE,True)
txt('Exemplo de desatualização cadastral.',64,485,520,24,MUTED)
txt('C1 e C3 • Rio Cocó',700,168,516,28,GREEN,True)
txt('A menor ligação viária tem 799 m pela Av. Eng. Santana Júnior, em percurso sem ciclofaixa.',700,232,516,26)
txt('C3 permanece separado nas fontes consultadas.',700,364,516,26,GREEN,True)
txt('Exemplo de lacuna a avaliar em campo.',700,485,516,24,MUTED)
note('A data do registro no OSM não determina a data de implantação.',590)
end()

start('Como escolher a próxima ligação','Fonte do método: artigo e Natera Orozco et al. (2020). Números abaixo são didáticos.','07 / Simulação')
txt('A cada etapa, comparar os candidatos e atualizar o componente principal.',64,155,1140,25)
table(['Candidato','Ligação pelas ruas','Rede incorporada','Ganho por metro'],[
 ['A','100 m','1 km = 1.000 m','10 m de rede / m'],
 ['B','500 m','20 km = 20.000 m','40 m de rede / m'],
], [210,315,300,327],top=227,rowh=88,size=23)
rows([
 ('Menor distância escolhe A','Prioriza a conexão mais curta disponível.'),
 ('Maior ganho por metro escolhe B','Prioriza a extensão original incorporada em relação ao comprimento da ligação.'),
],top=457,step=96)
end()

start('As primeiras ligações concentram o ganho','Fonte: resultados/ligacoes_faltantes.csv e artigo, Figura 1c','08 / Resultado da simulação')
sim=data('ligacoes_faltantes.csv')
series=[]
for strategy,col in [('maior ganho',INK),('mais próximo','#9C9C96')]:
    points=[(float(r['acumulado_m'])/1000,float(r['pct_gigante'])) for r in sim if r['estrategia']==strategy]
    # Degraus: uma nova parcela da rede só entra ao concluir cada ligação.
    clipped=[]
    for i,p in enumerate(points):
        if p[0]<=6:
            if clipped:clipped.append((p[0],clipped[-1][1]))
            clipped.append(p)
        elif clipped:
            clipped.append((6,clipped[-1][1]));break
    series.append((clipped,col,strategy))
chart_lines(series,0,6,50,100,range(7),[50,60,70,80,90,100],'Comprimento acumulado de ligações (km)','Extensão original no maior componente (%)',w=740,h=340)
txt('90% da rede',920,190,295,29,INK,True)
txt('1,4 km',920,265,295,43,INK,True)
txt('Maior ganho por metro',920,321,295,21)
txt('5,5 km',920,390,295,43,'#81817B',True)
txt('Menor distância',920,446,295,21)
txt('Cerca de 18 km para integrar toda a rede pelo maior ganho.',920,527,295,21,MUTED)
txt('A simulação parte da base municipal e inclui a conexão de C2. Esses quilômetros não equivalem a obras pendentes nem a custo financeiro.',64,628,1152,17,MUTED)
end()

start('Como distribuir a população no espaço','Fonte: artigo e analise/populacao_atendida.py. Exemplo numérico didático.','09 / População')
rows([
 ('1. Ler a população de cada setor do Censo','A unidade de origem é o setor censitário, não o endereço de cada morador.'),
 ('2. Recortar o setor com células de 50 m','Cada célula recebe população proporcional à área que ocupa dentro do setor.'),
 ('3. Representar cada parcela pelo centro da célula','Esse ponto permite calcular a distância até a infraestrutura cicloviária.'),
],top=158,step=115)
note('Exemplo: setor com 1.000 moradores e 20 células de mesma área = 50 por célula.',548)
txt('Uma célula com metade dessa área recebe 25 moradores. A hipótese é de distribuição uniforme.',64,610,1152,22,MUTED)
end()

start('O que significa estar a até 300 metros?','Fonte do método: artigo e analise/populacao_atendida.py. Percursos abaixo são didáticos.','10 / Distância de acesso')
txt('Somar o acesso até a rua, o percurso viário e o acesso até o trecho cicloviário.',64,154,1152,26)
table(['Parcela do percurso','Morador A','Morador B'],[
 ['Da célula até a rua, em linha reta','30 m','40 m'],
 ['Pelas ruas','220 m','290 m'],
 ['Da rua até a infraestrutura','20 m','20 m'],
 ['Total','270 m: dentro do limite','350 m: fora do limite'],
], [580,286,286],top=220,rowh=70,size=23)
note('O trajeto de acesso segue as ruas; ele pode ser maior que a distância em linha reta.',590)
end()

start('Cobertura e acesso ao maior componente','Fonte: resultados/populacao_atendida.csv, medida ruas e distância de 300 m','11 / Proximidade')
bars(['Próximos de qualquer trecho','Próximos de C1','Próximos de C1 com C2 integrado'],[48.3,27.7,37.9],['#949A9D',BLUE,ORANGE],top=170,step=124)
note('A cada 100 moradores: cerca de 48 perto de algum trecho, mas só 28 perto de C1.',585)
txt('Os grupos se sobrepõem: quem está perto de C1 também está perto de algum trecho.',64,632,1152,18,MUTED)
end()

start('Como comparar a proximidade por renda','Fonte: artigo e analise/populacao_atendida.py. Exemplo de agrupamento didático.','12 / Décimos de renda')
rows([
 ('Ordenar pela renda média do setor','O indicador é o rendimento nominal médio dos responsáveis pelos domicílios.'),
 ('Dividir os moradores em dez grupos de igual população','O 1º décimo reúne os moradores de setores de menor renda; o 10º, de maior renda.'),
 ('Calcular a proporção próxima da rede em cada grupo','Usar o mesmo limite de distância permite comparar os grupos.'),
],top=155,step=114)
note('Exemplo: com 1.000 moradores, cada décimo teria aproximadamente 100 pessoas.',550)
txt('Não são dez grupos com o mesmo número de bairros. A renda do setor não é a renda de cada pessoa.',64,612,1152,21,MUTED)
end()

start('A proximidade de C1 cresce com a renda','Fonte: resultados/populacao_por_renda.csv, medida ruas e distância de 300 m','13 / Resultado por renda')
inc=[r for r in data('populacao_por_renda.csv') if r['medida']=='ruas' and r['distancia_m']=='300']
series=[]
for key,col,label in [('pct_qualquer','#949A9D','Qualquer trecho'),('pct_c1_c2',ORANGE,'C1 + C2'),('pct_c1',BLUE,'C1')]:
    series.append(([(int(r['decimo']),float(r[key])) for r in inc],col,label))
chart_lines(series,1,10,0,100,range(1,11),range(0,101,20),'Décimo de renda setorial: menor (1) a maior (10)','Moradores a até 300 m pelas ruas (%)',w=750,h=345)
for j,(_,col,label) in enumerate(series):txt(label,930,220+58*j,280,25,col,True)
txt('C1',930,446,280,23,BLUE,True)
txt('11% no 1º décimo<br/>66% no 10º décimo',930,487,280,26)
txt('Leitura: em 100 moradores de setores de menor renda, cerca de 11 estão perto de C1.',64,632,1152,20,MUTED)
end()

start('A ligação de C2 muda o diagnóstico','Fonte: artigo e resultados/populacao_atendida.csv e populacao_por_renda.csv','14 / Cenário com C2')
table(['Indicador a até 300 m pelas ruas','Base municipal','Com C2 integrado'],[
 ['Proximidade de C1 no 1º décimo','11%','26%'],
 ['Proximidade do principal na cidade','28%','38%'],
 ['Índice de concentração','0,33','0,17'],
], [650,245,257],top=185,rowh=91,size=25)
note('Exemplo: no 1º décimo, aproximadamente 15 pessoas a mais em cada 100.',560)
txt('É uma mudança de cenário cadastral. O estudo não mede uma mudança de comportamento após uma obra.',64,615,1152,22,MUTED)
end()

start('Como interpretar o índice de concentração','Fonte: artigo; Wagstaff, Paci e van Doorslaer (1991); resultados/populacao_atendida.csv','15 / Desigualdade')
txt('Valor positivo: proximidade concentrada nos grupos de maior renda.',64,153,1152,25)
bars(['Qualquer trecho','C1','C1 com C2 integrado'],[.15,.33,.17],['#949A9D',BLUE,ORANGE],maxval=.4,unit='',top=215,w=730,step=109)
txt('Zero indica ausência de concentração por renda medida pelo índice.',940,245,270,23,MUTED)
txt('Não significa que todos estejam próximos da rede.',940,382,270,23,MUTED)
note('Exemplo de leitura: 0,33 é um índice; não significa “33% da população”.',594)
end()

start('Os resultados dependem do limite escolhido?','Fontes: artigo; resultados/populacao_atendida.csv; sensibilidade_tolerancia.csv','16 / Sensibilidade')
pop=[r for r in data('populacao_atendida.csv') if r['medida']=='ruas']
ss=[]
for key,col,label in [('pct_qualquer','#949A9D','Qualquer trecho'),('pct_c1',BLUE,'C1')]:
    ss.append(([(int(r['distancia_m']),float(r[key])) for r in pop],col,label))
chart_lines(ss,200,500,0,80,[200,300,500],[0,20,40,60,80],'Limite de distância pelas ruas (m)','Moradores próximos (%)',w=700,h=330)
txt('Cinza: qualquer trecho<br/>Azul: C1',910,184,305,23,MUTED)
txt('200 m: 20% perto de C1<br/>500 m: 38% perto de C1',910,285,305,24,BLUE,True)
txt('O gradiente por renda permanece nos dois limites.',910,388,305,23)
txt('Tolerância geométrica de 5 a 50 m: C1 fica entre 52% e 57% da extensão.',910,487,305,22)
txt('O acesso de 300 m e a tolerância de conexão de 10 m são parâmetros diferentes.',64,626,1152,21,MUTED)
end()

start('Um exemplo completo do procedimento','Exemplo didático de interpretação; os valores 50, 270 e 350 não são observações individuais.','17 / Retomada do método')
table(['Etapa','Exemplo de uma célula da grade'],[
 ['População','A célula representa 50 moradores do mesmo setor.'],
 ['Distância','Um trecho de C2 está a 270 m; C1 está a 350 m.'],
 ['Cenário municipal','Os 50 contam como próximos de algum trecho, mas não de C1.'],
 ['Cenário com C2 integrado','Os 50 passam a estar próximos do componente principal.'],
 ['Comparação por renda','O ganho entra no décimo correspondente à renda do setor.'],
], [300,852],top=175,rowh=76,size=23)
note('A posição dos moradores é a mesma; a conexão entre os componentes muda.',618)
end()

start('Limites da interpretação','Fonte: artigo, limitações e metodologia','18 / Limitações')
rows([
 ('Proximidade não mede segurança nem viagens realizadas','Exemplo: um trecho próximo pode ter uma travessia difícil ou não atender ao destino desejado.'),
 ('A população é estimada dentro de cada setor','Exemplo: uma célula pode receber moradores no modelo mesmo contendo uma área não residencial.'),
 ('A renda é setorial, e as fontes têm datas diferentes','Exemplo: um morador de baixa renda pode viver em um setor de renda média alta.'),
 ('A estratégia gulosa escolhe o melhor passo disponível','Exemplo: uma boa ligação agora não garante o melhor conjunto final nem viabilidade de obra.'),
],top=155,step=116)
end()

start('O que o estudo permite concluir','Fonte: artigo, resultados e conclusão','19 / Conclusão')
rows([
 ('Fragmentação da rede cadastrada','Os 429 km estão distribuídos em 44 componentes. O maior componente concentra 56% da extensão.'),
 ('Desigualdade na proximidade','C1 está a até 300 m de 11% dos moradores do décimo de menor renda setorial, contra 66% no de maior renda.'),
 ('Implicações para a avaliação da infraestrutura','Atualizar a ligação de C2 na base municipal e avaliar a conexão de C3 sobre o Rio Cocó.'),
 ('Integração e cobertura','A conexão dos componentes deve acompanhar a expansão da cobertura: cerca de metade dos moradores está além de 300 m da rede.'),
],top=153,step=124)
end()

start('Distâncias que não devem ser confundidas','Fonte: artigo; resultados/ligacoes_faltantes.csv; analise/rede.py','Apoio / Perguntas')
table(['Medida','O que representa'],[
 ['10 m','Tolerância geométrica para conectar trechos próximos.'],
 ['300 m','Limite de acesso da população até a infraestrutura pelas ruas.'],
 ['Cerca de 0,8 km','Extensão da ciclofaixa observada no OSM na ligação C1–C2.'],
 ['477 m na simulação','Ligação até C2 calculada pelo algoritmo após atualizar o componente principal.'],
 ['1,4 km acumulados','Ligações para atingir 90% da extensão original pelo critério de maior ganho.'],
], [320,832],top=163,rowh=78,size=22)
txt('A ligação observada e o menor caminho simulado não descrevem necessariamente o mesmo trajeto.',64,625,1152,19,MUTED)
end()

start('Fontes e reprodução da análise','Referências completas no artigo. Links clicáveis neste PDF.','Apoio / Referências')
txt('Dados e código',64,154,1152,27,INK,True)
txt('Prefeitura de Fortaleza: <link href="https://dados.fortaleza.ce.gov.br" color="#287DCC">dados.fortaleza.ce.gov.br</link><br/>IBGE: <link href="https://ftp.ibge.gov.br/Censos/Censo_Demografico_2022" color="#287DCC">Censo Demográfico 2022, agregados por setores</link><br/>OpenStreetMap: <link href="https://www.openstreetmap.org" color="#287DCC">openstreetmap.org</link> (contribuidores, ODbL)<br/>Repositório: <link href="https://github.com/Sarapessoa/artigo-ciencia-cidades" color="#287DCC">github.com/Sarapessoa/artigo-ciencia-cidades</link>',64,203,1152,23,INK,False,37)
txt('Referências centrais do método',64,392,1152,27,INK,True)
txt('Natera Orozco et al. (2020). Data-driven strategies for optimal bicycle network growth.<br/>Royal Society Open Science, 7, 201130.<br/><br/>Wagstaff, Paci e van Doorslaer (1991). On the measurement of inequalities in health.<br/>Social Science &amp; Medicine, 33(5), 545–557.',64,439,1152,21,MUTED,False,28)
txt('Exemplos didáticos identificados nos slides não são dados individuais observados.',64,625,1152,18,MUTED)
end()

c.save()
doc=pymupdf.open(DEST)
assert len(doc)==23, len(doc)
for i,p in enumerate(doc):
    assert p.rect.width==1280 and p.rect.height==720
    assert len(p.get_text())>100
    p.get_pixmap(matrix=pymupdf.Matrix(1,1)).save(TMP/f'slide-{i+1:02d}.png')
    for block in p.get_text('dict')['blocks']:
        if block['type']!=0:continue
        for ln in block['lines']:
            for sp in ln['spans']:
                x0,y0,x1,y1=sp['bbox']
                assert x0>=0 and x1<=W+1 and y0>=0 and y1<=H+1,(i+1,sp['text'],sp['bbox'])
# Contact sheets for visual review; these do not become part of the deliverable.
for batch in range(math.ceil(len(doc)/6)):
    sheet=Image.new('RGB',(1280,3*390),'#CCD3D8')
    draw=ImageDraw.Draw(sheet)
    for k in range(6):
        n=batch*6+k
        if n>=len(doc):break
        im=Image.open(TMP/f'slide-{n+1:02d}.png').resize((620,349))
        xx=10+(k%2)*640; yy=25+(k//2)*390
        sheet.paste(im,(xx,yy));draw.text((xx,yy-18),f'Slide {n+1}',fill='black')
    sheet.save(TMP/f'contato-{batch+1}.png')
print(f'PDF: {DEST}\nSlides: {len(doc)}\nVerificação: texto dentro das páginas; renderização concluída.')
