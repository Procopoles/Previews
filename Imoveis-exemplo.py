import pandas as pd
import streamlit as st
import datetime
from datetime import timedelta
import plotly.express as px
import plotly.graph_objects as go
import os



pd.options.display.date_yearfirst = False
pd.options.display.date_dayfirst = True

st.set_page_config(layout="wide")

pd.set_option("styler.render.max_elements", 10000000)
#Logo SH
st.sidebar.image("Ativos/Logo-Lopes.png", use_container_width=True)

# Injetando o CSS da fonte do Google Fonts
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Rubik:wght@400;700&display=swap');

    html, body, [class*="css"]  {
        font-family: 'Rubik', sans-serif;
    }
    </style>
    """, unsafe_allow_html=True)

#Setando o dataframe
df_imoveis = pd.read_csv("Ativos/excluir3.csv", delimiter=';')


data_hoje = datetime.datetime.now()


#Funções:

def capitalize(input):
    return input.title()
""

def formatar_valor(val):
    # Verifica se o valor é 0 ou "Na"
    if val == 0 or val == "":
        return val
    # Formata os valores numéricos restantes
    return f'R$ {val:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')


#Função que transforma a data(val) em string formatada para %d/%m/Y
def formatar_datas(val):
    return val.strftime('%d/%m/%Y') if not pd.isnull(val) else ''

#Função de Classificação do Padrão do Imóvel
def padrao_imovel(valor):
    if valor <= 1000000:
        return 'Baixo Padrão'
    elif 1000000 < valor <= 1900000:
        return 'Médio Padrão'
    elif 1900000 < valor <= 3000000:
        return 'Alto Padrão'
    else:
        return 'Altíssimo Padrão'


#Função de Classificação de Status de Atualização do Imóvel
def classificar_atualizacao(data_atualizacao):
    dias_desde_atualizacao = (data_hoje - data_atualizacao).days
    if 60 < dias_desde_atualizacao < 365:
        return 'Desatualizados +60 dias'
    elif dias_desde_atualizacao <= 60:
        return "Atual. nos últimos 60 dias"
    else:
        return 'Desatualizados +1 ano'


@st.cache_data
def imoveis_ativos(dataframe):
    df_imoveis_ativos = dataframe.drop(columns=["Valor M2 Aluguel", "Valor M2 venda", "Nome", "Valor total aluguel", "Endereco Complemento"])
    df_imoveis_ativos = df_imoveis_ativos[df_imoveis_ativos["Status"].isin(["Venda","Aluguel"])]
    df_imoveis_ativos = df_imoveis_ativos[df_imoveis_ativos["Lançamento"] != "Sim"]
    df_imoveis_ativos['Data atualizacao'] = pd.to_datetime(df_imoveis_ativos['Data atualizacao'], errors='coerce')
    df_imoveis_ativos["Data cadastro"] = pd.to_datetime(df_imoveis_ativos["Data cadastro"],errors='coerce')
    df_imoveis_ativos['Chamadas'] = df_imoveis_ativos["Corretores do Imovel"].fillna("").str.split(",").str[-1]
    df_imoveis_ativos["Captador Imóvel"] = df_imoveis_ativos["Corretores do Imovel"].str.split(",").str[0]
    df_imoveis_ativos['Padrão Imovel'] = df_imoveis_ativos['Valor venda'].apply(padrao_imovel)
    df_imoveis_ativos[["Vagas", "Suite", "Endereco Numero"]] = df_imoveis_ativos[["Vagas", "Suite", "Endereco Numero"]].fillna(0).astype(int)
    df_imoveis_ativos['Status Atualização'] = df_imoveis_ativos['Data atualizacao'].apply(classificar_atualizacao)
    df_imoveis_ativos['Bairro Comercial'] = df_imoveis_ativos['Bairro Comercial'].astype(str).apply(capitalize)
    df_imoveis_ativos["Mês Cadastro"] =  df_imoveis_ativos["Data cadastro"].dt.to_period("M")
    return df_imoveis_ativos

df_imoveis_ativos = imoveis_ativos(df_imoveis)

data_minima = df_imoveis_ativos["Data cadastro"].min()
data_maxima = df_imoveis_ativos["Data cadastro"].max()


@st.cache_data
def tabela_equipes(dataframe):
    tabela_equipes = dataframe[['Equipes do Imovel', 'Data cadastro']]
    return tabela_equipes

#@st.cache_data
def captações_equipe(equipe, data_inicial, data_final):
    tabela_equipes_filtrada = tabela_equipes[(tabela_equipes['Equipes do Imovel'].str.contains(equipe, case=False, na=False)) & 
    (tabela_equipes['Data cadastro']>= data_inicial) & 
    (tabela_equipes['Data cadastro']<= data_final)]
    return tabela_equipes_filtrada['Equipes do Imovel'].count()

#@st.cache_data
def captações_equipe_último_mês(equipe, captações):
    return int(captações - (captações_equipe(equipe, data_minima, data_delta_30)))

#st.cache_data
def captações_equipe_mês_retrasado(equipe):
    return int((captações_equipe(equipe, data_minima, data_delta_30)) - (captações_equipe(equipe, data_minima, data_delta_60)))


#df_anuncios = pd.read_csv("Ativos/Anuncios Canal Pro.csv") #DataFrame Anúncios Canal Pro


# Merge de df chamadas, ultilando colunas "Referencia"

 # 2. Merge com df Anuncios, utilizando as colunas 'Referencia' e 'Código do Imóvel' como base

#df_anuncios = df_anuncios.drop_duplicates(subset='Código do Imóvel')
#df_imoveis_ativos = pd.merge(df_imoveis_ativos, df_anuncios[['Código do Imóvel', 'Tipo do anúncio', 'CEP']], left_on='Referencia', right_on='Código do Imóvel', how='left')
#df_imoveis_ativos = df_imoveis_ativos.drop(columns=["Código do Imóvel"])


# =============================================================================
# PAINEL LATERAL
# =============================================================================


#Título e Subtítlo Sidebar 
st.sidebar.title("Dashboard - Captações Lopes")
st.sidebar.subheader("Menu Principal")

coluna1, coluna2 = st.columns([1, 1])

with coluna1:
    seleção_apenas_publicados = st.sidebar.toggle("Publicados em Portais", value =True)

with coluna2:
    seleção_agencia_ou_equipes = st.sidebar.toggle("Por Equipes", value = False)

#Conversor de boleano para Sim e Não:
conversor_apenas_publicados_portais = {True: "Sim", False: "Nao"}

# Dicionario de publicados nos portais

# Dicionário de equipes por agência
# Dicionário base sem "Todas Agências"
equipes_agencias = {
    "Perdizes": ["Albatroz", "Carcará", "Azor", "Gavião", "Falcão", "Faisão"],
    "Pacaembu": ["Fênix", "Canário", "Sabiá"],
    "Santana": ["Lion", "Wolf"],
    "Jardins": ["Gold", "Infinity"]
}

# Gerar "Todas Agências" como a união de todos os valores
todas_equipes = [equipe for lista in equipes_agencias.values() for equipe in lista]

# Montar o dicionário final
equipes_agencias = {"Todas Agências": todas_equipes, **equipes_agencias}


if seleção_agencia_ou_equipes == False:
    
    #Menu de seleção Agência
    seleção_agencia = st.sidebar.selectbox("Selecione a Agência",options=list(equipes_agencias.keys()))  # Lista de agências para selecionar
    
    equipes_da_agencia = equipes_agencias[seleção_agencia]
    regex = '|'.join(equipes_da_agencia)  # Cria uma regex para as equipes (ex: 'Carcará|Azor|Gavião|Falcão|Faisão')
    equipes = equipes_da_agencia

else:
    #Menu de seleção de equipe
    seleção_equipe = st.sidebar.selectbox("Selecione a Equipe", 
    ("Azor", "Faisão", "Falcão", "Gavião","Carcará", "Albatroz", "Gold", "Sabiá", "Fênix", "Canário", "Lion", "Tiger", "Wolf", "Infinity", "Sem Equipe Vinculada"))

# Filtro de Datas:

seleção_data_cadastro = st.sidebar.date_input("Data do Cadastro", [datetime.datetime(2008, 1, 1), data_maxima],data_minima, data_hoje, format="DD/MM/YYYY")

data_inicial = pd.to_datetime(seleção_data_cadastro[0])
data_final = pd.to_datetime(seleção_data_cadastro[1])

data_delta_30 = data_final - timedelta(days=31)
data_delta_60 = data_final - timedelta(days=61)

#Slider de Valor
#seleção_valores = st.sidebar.slider("Valor Venda", valor_minimo, valor_maximo, [valor_minimo, valor_maximo])

# =============================================================================
# PROCESSAMENTO TABELA
# =============================================================================


#Tabela com aplicação dos filtros da sidebar
tabela_resultados = df_imoveis_ativos[
    (df_imoveis_ativos["Data cadastro"] >= data_inicial) &
    (df_imoveis_ativos["Data cadastro"] <= data_final) &
    (df_imoveis_ativos["Publicar Viva Real VRSync"] == conversor_apenas_publicados_portais[seleção_apenas_publicados]) | 
    (df_imoveis_ativos["Publicar Viva Real VRSync 2"] == conversor_apenas_publicados_portais[seleção_apenas_publicados])

]


tabela_equipes = tabela_equipes(tabela_resultados)

#>>>>Botão Equipe ON<<<<
if seleção_agencia_ou_equipes == True:
    if seleção_equipe != "Sem Equipe Vinculada":
        tabela_resultados = tabela_resultados[tabela_resultados["Equipes do Imovel"].str.contains(seleção_equipe, case=False, na=False)
        ]
    #Tabela resultados para caso seja selecionado "Geral"
    else:tabela_resultados = tabela_resultados[
    (tabela_resultados["Equipes do Imovel"].isna() | tabela_resultados["Equipes do Imovel"].str.strip().eq(""))  # Verificar células vazias/nulas
    ]
#>>>>Botão equipe OFF<<<<
else: 
    if seleção_agencia != "Todas Agências":
        tabela_resultados = tabela_resultados[tabela_resultados["Equipes do Imovel"].str.contains(regex, case=False, na=False)]

total_imoveis = len(tabela_resultados)


if seleção_agencia_ou_equipes == False:
    coluna1, coluna2= st.columns([1, 1])
    with coluna1:
        st.header(f"Captações Lopes {seleção_agencia}")
        st.subheader(f"Total de imóveis: {total_imoveis}")        
        seleção_ultimos_30_dias = st.toggle("**últimos 30 dias**")

else:
    st.header(f"Captações equipe {seleção_equipe}")
    st.subheader(f"Total de imóveis: {total_imoveis}")

if seleção_agencia_ou_equipes == False:
    colunas = st.columns(13)
    captações = {}
    captações_ultimo_mes = {}
    captações_mes_retrasado = {}
    classificar_atualizacaoaptações_mes_retrasado = {}
    meta_cap_mensal = 20

    # Processando captações para todas as equipes
    for equipe in equipes:
        captações[equipe] = captações_equipe(equipe, data_inicial, data_final)
        captações_ultimo_mes[equipe] = captações_equipe_último_mês(equipe, captações[equipe])


    if seleção_ultimos_30_dias == False:
        
        # Criando métricas dinamicamente
        for i, equipe in enumerate(equipes):
            delta_color = "off" if captações_ultimo_mes[equipe] < meta_cap_mensal else "normal"
            colunas[i].metric(
                f"**{equipe}**",
                captações[equipe],
                captações_ultimo_mes[equipe],
                delta_color=delta_color
            )
    else:
        #Processando captações para todas as equipes
        for equipe in equipes:
            captações_mes_retrasado[equipe] = captações_equipe_mês_retrasado(equipe)

        #Criando métricas dinamicamente
        
        for i, equipe in enumerate(equipes):
            delta_color = "off" if captações_ultimo_mes[equipe] < meta_cap_mensal else "normal"
            colunas[i].metric(
                f"**{equipe}**",
                captações_ultimo_mes[equipe],
                captações_ultimo_mes[equipe] - captações_mes_retrasado[equipe],
                delta_color=delta_color
            )

        

st.divider()

#Usa o método style.format na coluna "Data cadastro" e aplica 
# a função de formatação "formatar data". Ou seja não altera os valores reais do DataFrame.
df_formatado = tabela_resultados.style.format({"Data cadastro": formatar_datas,
                                               "Data atualizacao": formatar_datas,
                                               "Valor venda": formatar_valor,
                                               "Valor Aluguel": formatar_valor,
                                               "Area Privativa": "{:.2f}"})

st.header("Estatísticas:")


# =============================================================================
# INICIO GRÁFICOS
# =============================================================================

@st.cache_data
def imoveis_venda(dataframe):
    tabela_venda = dataframe[dataframe["Status"]== "Venda"]
    #Agrupamento por mês
    tabela_venda["Mês Cadastro"] = tabela_resultados["Data cadastro"].dt.to_period("M")
    return tabela_venda

@st.cache_data
def imoveis_aluguel(dataframe):
    tabela_aluguel = dataframe[dataframe["Status"]== "Aluguel"]
    #Agrupamento por mês
    return tabela_aluguel

tabela_venda = imoveis_venda(tabela_resultados)
tabela_aluguel = imoveis_aluguel(tabela_resultados)


captações_mensais_venda = tabela_venda.groupby("Mês Cadastro").size().reset_index(name="Quantidade")
captações_mensais_aluguel = tabela_aluguel.groupby("Mês Cadastro").size().reset_index(name = "Quantidade")

if len(captações_mensais_venda)>1:
    # Criar o gráfico de linha com Plotly
    fig = go.Figure()
    # Adicionar a linha ao gráfico
    fig.add_trace(go.Scatter(
    x=captações_mensais_venda['Mês Cadastro'].astype(str),  # Convertendo o período para string para o eixo X
    y=captações_mensais_venda['Quantidade'],
    textposition="top center",
    mode='lines+markers+text',
    text=captações_mensais_venda['Quantidade'],  # Mostrar linha e pontos
    name='Captações - Venda',
    line=dict(color='#0062D9', width=2),  # Configurações da linha
    marker=dict(size=4)  # Configurações dos marcadores
    ))  
    # Adicionar a linha para "Aluguel"
    fig.add_trace(go.Scatter(
        x=captações_mensais_aluguel['Mês Cadastro'].astype(str),  # Convertendo o período para string para o eixo X
        y=captações_mensais_aluguel['Quantidade'],
        textposition="top center",
        text=captações_mensais_aluguel['Quantidade'],
        mode='lines+markers+text',  # Mostrar linha e pontos
        name='Captações - Aluguel',
        line=dict(color='#B4D900', width=2),  # Configurações da linha
        marker=dict(size=4)  # Configurações dos marcadores
    ))
    # Adicionar títulos e ajustar layout
    fig.update_layout(
    title='Quantidade de Captações por Mês',
    xaxis_title='Mês',
    yaxis_title='Número de Captações',
    xaxis=dict(tickmode='linear', type='category'),
    template='plotly_white'  # Tema branco para melhor visualização
    )
    # Mostrar o gráfico no Streamlit
    st.plotly_chart(fig)
else:
    st.warning("Seleciona um intervalo maior que 1 mês para exibir o gráfico de captações por mês")

captações_por_corretor = tabela_resultados["Captador Imóvel"].value_counts()

chamadas_por_corretor = tabela_resultados["Chamadas"].value_counts()

# Combinar as duas séries em um DataFrame
tabela_corretores = pd.concat([captações_por_corretor, chamadas_por_corretor], axis=1, keys=['Captações', 'Chamadas']).fillna(0)

# Resetar o índice para ter uma coluna com o nome do corretor
tabela_corretores = tabela_corretores.reset_index().rename(columns={'index': 'Corretor'})

# Converter as colunas para inteiros
tabela_corretores[['Captações', 'Chamadas']] = tabela_corretores[['Captações', 'Chamadas']].astype(int)

# Ordenar a tabela por Captações em ordem decrescente
tabela_corretores = tabela_corretores.sort_values(by='Captações', ascending=False).reset_index(drop=True)
top_20_chamadas = chamadas_por_corretor.head(20).sort_values(ascending=True)
top_20_corretores = captações_por_corretor.head(20).sort_values(ascending=True)
total_captações_por_corretor = top_20_corretores.sum()

# Recriar os DataFrames filtrados para os corretores
chamadas_e_captações = top_20_corretores.index.intersection(top_20_chamadas.index)


# Supondo que captações_intersecção e chamadas_intersecção sejam Series com o mesmo índice
captações_intersecção = top_20_corretores.loc[chamadas_e_captações]
chamadas_intersecção = top_20_chamadas.loc[chamadas_e_captações]

# Criar o DataFrame com os dados dos corretores
tabela_top_20_corretores = pd.DataFrame({
    'Corretor': captações_intersecção.index,
    'Captações': captações_intersecção.values,
    'Chamadas': chamadas_intersecção.values
})

# Ordenar pela quantidade de captações em ordem decrescente
tabela_top_20_corretores = tabela_top_20_corretores.sort_values(by='Captações', ascending=False).reset_index(drop=True)

st.divider()

# Dividir o layout em duas colunas
coluna1, coluna2 = st.columns([1, 3])

with coluna1:
    tabela_corretores

with coluna2:

    # Transformar os dados para o formato longo
    df_melted = tabela_top_20_corretores.melt(id_vars='Corretor', value_vars=['Captações', 'Chamadas'],
                                              var_name='Tipo', value_name='Quantidade')

    cores_grafico_corretores = {'Captações': '#0062D9','Chamadas': '#D98C00'}      

    # Criar o gráfico de barras agrupadas com Plotly Express
    fig = px.bar(
        df_melted,
        x='Quantidade',
        y='Corretor',
        color='Tipo',
        orientation='h',
        barmode='group',
        title='Captações e Chamadas por Corretor',
        template='plotly_white',
        color_discrete_map=cores_grafico_corretores  # Mapeamento de cores personalizado
    )

    # Atualizar o layout do gráfico
    fig.update_layout(
        xaxis_title='Quantidade',
        yaxis_title='Corretor',
        autosize=True,
        margin=dict(l=0, r=0, t=30, b=0)
    )

    # Inverter a ordem das categorias no eixo Y para que os maiores valores fiquem em cima
    fig.update_yaxes(autorange='reversed')

    # Ajustar o espaçamento entre os ticks do eixo X, se necessário
    fig.update_xaxes(dtick=2000, automargin=True)

    # Exibir o gráfico no Streamlit
    st.plotly_chart(fig, use_container_width=True)



st.divider()

#Divide em 2 colunas
coluna1, coluna2 = st.columns([1,3])

#Dataframes dos bairros
caps_por_bairro = tabela_resultados["Bairro Comercial"].value_counts()
top_30_caps_por_bairro = caps_por_bairro.head(30)


def grafico_torta(data, title):
    grafico_bairros_torta = go.Figure(go.Pie(
        labels=data.index,
        values=data,
        showlegend=False,
        title=title,
        textinfo='label+percent',
        hoverinfo='label+percent+value',
    ))
    grafico_bairros_torta.update_layout(
    title={
        'text': 'Distribuição dos Imóveis por Categoria de Padrão',
        'font': {'size': 18},  # Aumentar o tamanho da fonte
        'x': 0.5,  # Centralizar o título horizontalmente
        'xanchor': 'center'})  # Ancorar o título no centro
    # Adiciona destaque para as fatias
   # grafico_bairros_torta.update_traces(
       # marker=dict(line=dict(color='black', width=1)))
    return grafico_bairros_torta

def grafico_barra(data, title):
    grafico_bairros_barra = px.bar(data, title= title,  color_discrete_sequence=["#0140FF"])   
    grafico_bairros_barra.update_layout(
        margin=dict(l=0, r=0, t=30, b=0),  # Remover margens para ocupar mais espaço
        title=dict(x=0.5))  # Centralizar o título 
    return grafico_bairros_barra

st.divider()

with coluna1:
    st.write("Captações por Bairro")
    caps_por_bairro

with coluna2:
    
    col1, col2, col3 = st.columns([1,2,1])
    with col3:
        seletor_grafico = st.toggle("Alterar tipo de Gráfico", value = True)

    grafico_bairros_barra = grafico_barra(top_30_caps_por_bairro, "Top 30 bairros")
    grafico_bairros_torta = grafico_torta(top_30_caps_por_bairro, "Top 30 bairros")
        

with coluna2:
    if seletor_grafico == False:
        st.plotly_chart(grafico_bairros_torta, use_container_width=True)
    
    else:
        st.plotly_chart(grafico_bairros_barra, use_container_width=True)


# Contar o número de imóveis em cada categoria
contagem_padrao = tabela_resultados['Padrão Imovel'].value_counts()

categoria_captação = tabela_resultados["Categoria"].value_counts()

grafico_categoria = grafico_torta(categoria_captação, "Categorias")


coluna1, coluna2 = st.columns([2,3])

cores_grafico_padrao = {"Baixo Padrão": "#FAAF2D", 
"Médio Padrão": "#FADF14",
"Alto Padrão": "#00E06C", 
"Altíssimo Padrão": "#00DFEB"}

ordem_categorias = ["Baixo Padrão", "Médio Padrão", "Alto Padrão", "Altíssimo Padrão"]
contagem_padrao = contagem_padrao.reindex(ordem_categorias, fill_value=0)

# Mapear as cores com base nas categorias de contagem_padrao.index

with coluna1:

    
    grafico_padrao_imoveis = go.Figure(go.Bar(
    x=contagem_padrao.index,
    y=contagem_padrao.values,
    marker=dict(color=["#A6F5EE", "#14EBFF", "#23CAFF", "#8100CC"]),
    text=contagem_padrao.values,  # Mostrar os valores nas barras
    textposition='auto'
    ))

    # Atualizar o layout do gráfico
    grafico_padrao_imoveis.update_layout(
    title='Distribuição dos Imóveis por Padrão',
    xaxis_title='Distribuição por Ticket do Imóvel',
    xaxis = dict(type='category'),
    yaxis_title='Número de Imóveis',
    legend=dict(
        title='Legenda',  # Título da legenda
        orientation='h',
        y=-0.2)  # Posição vertical da legenda)  # Coloca a legenda na horizontal
    )
    st.plotly_chart(grafico_padrao_imoveis)

with coluna2:
    st.plotly_chart(grafico_categoria)
    

# Grafico Atualização


# Contar a quantidade de imóveis em cada categoria
contagem_status = tabela_resultados['Status Atualização'].value_counts()

# Lista com a ordem desejada das categorias
desired_order = ['Atual. nos últimos 60 dias', 'Desatualizados +60 dias', 'Desatualizados +1 ano']

# Reindexar contagem_status para garantir a ordem das categorias
contagem_status = contagem_status.reindex(desired_order, fill_value=0)

tabela_atualização = tabela_resultados[["Referencia", "Data atualizacao", "Status Atualização"]]
tabela_atualização_formatada = tabela_atualização.style.format({"Data atualizacao": formatar_datas})

st.divider()

coluna1, coluna2 = st.columns([2, 3])

with coluna1:
    st.write(tabela_atualização_formatada)

with coluna2:
    # Mapeamento de cores para cada categoria
    category_colors = {
        'Atual. nos últimos 60 dias': '#00F080',
        'Desatualizados +60 dias': '#FF8800',
        'Desatualizados +1 ano': '#F00000'
    }

    # Obter a lista de cores correspondente às categorias na ordem desejada
    colors = [category_colors[category] for category in desired_order]

    # Criar o gráfico de barras com as categorias na ordem correta
    fig = go.Figure(go.Bar(
        x=contagem_status.index,
        y=contagem_status.values,
        marker=dict(color=colors),
        text=contagem_status.values,  # Mostrar os valores nas barras
        textposition='auto'
    ))

    # Adicionar título e rótulos
    fig.update_layout(
        title='Quantidade de Imóveis por Status de Atualização',
        xaxis_title='Status de Atualização',
        yaxis_title='Quantidade de Imóveis',
        template='plotly_white'
    )

    # Mostrar o gráfico no Streamlit
    st.plotly_chart(fig)

df_formatado


