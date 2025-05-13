import pandas as pd
import streamlit as st
import datetime
import plotly.express as px
from datetime import timedelta
import plotly.graph_objects as go
import os
import requests
import json

current_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.abspath(os.path.join(current_dir, ".."))

# Caminho para o arquivo
file_path = os.path.join(base_dir, "Ativos", "report-leads-31-12-2024.xlsx")
file_path_df1 = os.path.join(base_dir, "Ativos", "report-leads-30-06-2024.xlsx")
file_path_df2 = os.path.join(base_dir, "Ativos", "report-leads-jan,fev,mar,abr.xlsx")

pd.options.display.date_yearfirst = False
pd.options.display.date_dayfirst = True

st.set_page_config(layout="wide")

pd.set_option("styler.render.max_elements", 10000000)

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
df_leads_c2s = pd.read_excel(file_path)
df_leads_c2s_df2 = pd.read_excel(file_path_df1)
df_leads_c2s_df3 = pd.read_excel(file_path_df2)

df_leads_c2s = pd.concat([df_leads_c2s, df_leads_c2s_df2, df_leads_c2s_df3], ignore_index = True)

df_leads_c2s["Data de chegada"] = pd.to_datetime(df_leads_c2s["Data de chegada"], format='%d/%m/%Y %H:%M', errors='coerce')
df_leads_c2s["Data de chegada"] = df_leads_c2s["Data de chegada"].dt.date


#Funções:

def padrão_lead(valor):
    
    if valor < 1000000:
       return 'Baixo Padrão'
    elif valor >= 1000000:
        return 'Médio Padrão'
    elif valor >=1900000:
        return ''

def capitalize(input):
    return input.title()

def formatar_valor(val):
    return f'R$ {val:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')

#Função que transforma a data(val) em string formatada para %d/%m/Y
def formatar_datas(val):
    return val.strftime('%d/%m/%Y') if not pd.isnull(val) else ''

def grafico_torta(data):
    grafico_bairros_torta = go.Figure(go.Pie(
        labels=data.index,
        values=data,
    ))
    grafico_bairros_torta.update_traces(
        
        textfont_size=12,
        marker=dict(line=dict(color='black', width=1))
    )
    return grafico_bairros_torta


renomeação_equipes = {
    'SH Prime - ZN Tiger': 'Tiger',
    'SH Prime - ZN PUMA': 'Puma',
    'SH Prime - ZN Wolf': 'Wolf',
    'SH Prime - ZN Lion': 'Lion',
    'SH Prime - SH Albatroz': 'Albatroz',
    'SH Prime - SH Falcão': 'Falcão',
    'Sh Prime - SH Gavião': 'Gavião',
    'SH Prime - SH Carcará': 'Carcará',
    'SH Prime - SH Faisão': 'Faisão',
    'SH Prime - SH Azor': 'Azor',
    'SH Prime - SH Fenix': 'Fênix',
    'SH Prime - SH Sabiá': 'Sabiá',
    'SH Prime - SH Canário': 'Canário',
    'SH Prime - SH Gold': 'Gold',
    'SH Prime - SH Infinity': 'Infinity',
    'SH Prime Imóveis': 'Sem equipe vinculada',
    'SH Prime - Diretoria Perdizes': 'Sem equipe vinculada',
    'SH Prime - Diretoria Santana': 'Sem equipe vinculada',
    'SH Prime - Diretoria Pacaembu': 'Sem Equipe vinculada',
}
colunas_excluir = ["Canal", "Telefone apenas dígitos", "Cidade", 'Status da atividade atual', "Negócio fechado em", "Valor real do fechamento", "Etiquetas", "Código do imóvel negociado"]

@st.cache_data
def leads_cleaner(dataframe):
    df_leads_clean = dataframe.drop(columns=colunas_excluir)
    df_leads_clean["Equipe"] = df_leads_clean["Equipe"].replace(renomeação_equipes)
    df_leads_clean["Data de chegada"] = pd.to_datetime(df_leads_clean["Data de chegada"], format='%d/%m/%Y %H:%M', errors='coerce')
    df_leads_clean['Data Chegada'] = df_leads_clean['Data de chegada'].dt.strftime('%d/%m/%Y')
    df_leads_clean["Mês Chegada"] = df_leads_clean["Data de chegada"].dt.to_period("M")
    # Extrair o texto após " - ", mas manter o valor original se não houver " - "
    df_leads_clean['Bairro'] = (
    df_leads_clean['Bairro']
    .str.extract(r'-\s*(.+)$', expand=False)  # Extrai o texto após "-"
    .fillna(df_leads_clean['Bairro'])        # Preenche valores nulos com o original
    .str.replace(r'[^\w\s]', '', regex=True) # Remove caracteres especiais como []()
    .str.replace(r'\s+', ' ', regex=True)    # Substitui múltiplos espaços por um único
    .str.strip()                             # Remove espaços em branco no início e no fim
)

    df_leads_clean['Código do Imóvel'] = df_leads_clean['Código do Imóvel'].astype(str)
    # Atualizando o bairro para produtos com "Nenhum", usando "Código do Imóvel" como chave
    #leads_sem_bairro =  (df_leads_clean['Bairro'] == "Nenhum") | (df_leads_clean['Bairro'].isna())
    return  df_leads_clean

df_leads_clean = leads_cleaner(df_leads_c2s)

@st.cache_data
def atualizar_bairros(dataframe):
    # Defina a chave de acesso e a URL base
    api_key = '5747309ef69f4dfec03b87133c9b0b83'  # Substitua pela sua chave
    base_url = 'http://shprime2-rest.vistahost.com.br'

    # Identifica os imóveis sem bairro
    #imoveis_sem_bairro = dataframe[['Código do Imóvel', 'Bairro']]
    imoveis_sem_bairro = dataframe[
        dataframe['Bairro'].isnull() |
        (dataframe['Bairro'] == '') |
        (dataframe['Bairro'] == 'Nenhum') |
        (dataframe['Bairro'] == 'SP') | (dataframe['Bairro'] == '0')
    ]
    imoveis_sem_bairro_bol = imoveis_sem_bairro.index
    # Coleta os códigos dos imóveis sem bairro e converte para string
    codigos_imoveis = imoveis_sem_bairro['Código do Imóvel'].astype(str).tolist()

    # Define o tamanho do lote para as requisições (ajuste conforme necessário)
    tamanho_lote = 50

    # Dicionário para armazenar os bairros retornados pela API
    dicionario_codigos_bairros = {}

    # Percorre os códigos em lotes
    for i in range(0, len(codigos_imoveis), tamanho_lote):
        lote_codigos = codigos_imoveis[i:i + tamanho_lote]
        # Configura os parâmetros de pesquisa
        fields = ['Codigo', 'BairroComercial']
        filter = {'Codigo': lote_codigos}
        paginacao = {"pagina": 1, "quantidade": tamanho_lote}
        pesquisa = {'fields': fields, 'filter': filter, "paginacao": paginacao}
        pesquisa_json = json.dumps(pesquisa)

        # Realiza a requisição GET
        response = requests.get(
            f'{base_url}/imoveis/listar',
            headers={'Accept': 'application/json'},
            params={'key': api_key, 'pesquisa': pesquisa_json, 'showSuspended': 1, 'showInternal': 1}
        )

        # Verifica o status da resposta
        if response.status_code == 200:
            # Converte a resposta para JSON
            data = response.json()

            # Verifica se há resultados
            if data:
                # Itera sobre os itens do dicionário retornado
                for codigo_imovel, imovel in data.items():
                    codigo = imovel.get('Codigo')
                    bairro = imovel.get('BairroComercial')
                    if codigo and bairro:
                        # Remove espaços e padroniza para maiúsculas
                        codigo = codigo.strip().upper()
                        bairro = bairro.strip()
                        dicionario_codigos_bairros[codigo] = bairro
        else:
            print(f'Erro na requisição: {response.status_code}, Detalhes: {response.text}')

    # Imprime o dicionário para verificação
    print("Dicionário de códigos e bairros obtidos da API:")
    print(dicionario_codigos_bairros)

    # Converte 'Código do Imóvel' para string, remove espaços e padroniza
    dataframe['Código do Imóvel'] = dataframe['Código do Imóvel'].astype(str).str.strip().str.upper()

    # Atualiza o dataframe original com os bairros obtidos usando 'map'
    dataframe.loc[imoveis_sem_bairro_bol, 'Bairro'] = dataframe.loc[imoveis_sem_bairro_bol, 'Código do Imóvel'].map(dicionario_codigos_bairros)

    return dataframe

df_bairros_atualizado = df_leads_clean

df_bairros_atualizado['Bairro'] = df_bairros_atualizado['Bairro'].astype(str).apply(capitalize)
print(df_bairros_atualizado['Bairro'].value_counts())


# Merge leads c2s e canal pro (criar no futuro)
#df_leads_c2s["Chamadas"] = df_leads_c2s["Corretores do Imovel"].fillna("").str.split(",").str[-1]

#Título e Subtítlo Sidebar 
st.sidebar.title("Dashboard - Leads")
st.sidebar.subheader("Menu Principal")

tipos_lead = ("Compra", "Aluguel", "Ambos")

seleção_tipo_leads = st.sidebar.segmented_control("Tipo de Leads", options=tipos_lead, selection_mode="single", default = tipos_lead[2])

seleção_agencia_ou_equipes = st.sidebar.toggle("Por Equipes", value = False)


# Dicionário de equipes por agência
equipes_agencias = {
"Todas Agências": [],
"Perdizes":["Albatroz", "Carcará", "Azor", "Gavião", "Falcão", "Faisão"],
"Pacaembu":["Fênix", "Canário", "Sabiá"],
"Santana": ["Lion", "Puma", "Wolf"],
"Jardins": ["Gold"],
"Itaim Bibi": ["Infinity"]
}

#Conversão para formato de Datas Válido

data_minima = df_leads_clean["Data de chegada"].min()
data_maxima = df_leads_clean["Data de chegada"].max()
data_hoje = datetime.datetime.now()
data_mes_passado = data_maxima - timedelta(days=31)
data_mes_retrasado = data_maxima - timedelta(days=61)


#Menu de seleção por Data
seleção_data_cadastro = st.sidebar.date_input("Data de Chegada", [data_minima, data_maxima],data_minima, data_hoje, format="DD/MM/YYYY")

data_inicial = pd.to_datetime(seleção_data_cadastro[0]) + pd.Timedelta(days=1)
data_final = pd.to_datetime(seleção_data_cadastro[1]) # + pd.Timedelta(days=1)

#Botão equipe OFF
if seleção_agencia_ou_equipes == False:
    
    #Menu de seleção Agência
    seleção_agencia = st.sidebar.selectbox("Selecione a Agência",options=list(equipes_agencias.keys()))  # Lista de agências para selecionar
    equipes_da_agencia = equipes_agencias[seleção_agencia]
    regex_equipes = '|'.join(equipes_da_agencia)  # Cria uma regex_equipes para as equipes (ex: 'Carcará|Azor|Gavião|Falcão|Faisão')
#Botão Equipe ON
else:
    #Menu de seleção de equipe
    seleção_equipe = st.sidebar.selectbox("Selecione a Equipe", 
    ("Azor", "Faisão", "Falcão", "Gavião","Carcará", "Albatroz", "Gold", "Sabiá", "Fênix", "Canário", "Lion", "Puma", "Wolf", "Infinity", "Sem Equipe Vinculada"))

tabela_resultados = df_bairros_atualizado[
    (df_bairros_atualizado["Data de chegada"] >= data_inicial - timedelta(days=1)) &
    (df_bairros_atualizado["Data de chegada"] <= data_final)
]

if seleção_tipo_leads == tipos_lead[2]:
    filtro_tipo = ["Compra", "Aluguel"]
else:
    filtro_tipo = [seleção_tipo_leads]

# Aplicar o filtro
tabela_resultados = tabela_resultados[tabela_resultados["Natureza da negociação"].isin(filtro_tipo)]

if seleção_agencia_ou_equipes == True:
    tabela_resultados = tabela_resultados[tabela_resultados["Equipe"].str.contains(seleção_equipe, case=False)]
    
else:
    if seleção_agencia != "Todas Agências":
        tabela_resultados = tabela_resultados[tabela_resultados["Equipe"].str.contains(regex_equipes)] 


contagem_leads = len(tabela_resultados)

st.subheader(f"Total de Leads:  {contagem_leads}")

coluna1, coluna2 = st.columns([1,1])

if data_final > data_mes_passado:
    with coluna1:
        contatos_lead = tabela_resultados[['Nome do cliente', 'Telefone formatado']].value_counts().reset_index().rename(columns={'count': 'Contatos'})
        leads_contato_maior_que_1 = contatos_lead[contatos_lead['Contatos']>1]
        # contatos_lead
        if len(leads_contato_maior_que_1) > 0:
            média_contatos_lead = contatos_lead['Contatos'].mean().round(2)

        leads_último_mês = tabela_resultados[tabela_resultados['Data de chegada'] >= data_mes_passado]
        leads_penúltimo_mês = tabela_resultados[(tabela_resultados['Data de chegada'] >= data_mes_retrasado) & 
        (tabela_resultados['Data de chegada'] <= data_mes_passado)]
        delta_último_mês = int(len(leads_último_mês) - len(leads_penúltimo_mês))

        if len(leads_contato_maior_que_1) > 0:
            leads_Reincidência = round((len(leads_contato_maior_que_1) / contagem_leads)*100, 2)
        else:
            leads_Reincidência = 0

        leads_por_dia_último_mês = leads_último_mês['Data de chegada'].value_counts()
        média_leads_por_dia_último_mês = int(leads_por_dia_último_mês.mean())


        with st.expander('Leads por dia'):
            leads_por_dia_último_mês 
        with st.expander('Contatos Leads'):
            contatos_lead
        with st.expander('Leads contato maior que 1'):
            leads_contato_maior_que_1

    
        média_leads_por_dia_ultimo_mês =int(leads_por_dia_último_mês.mean())

        with coluna2:
            with st.container(height=300):
                coluna1, coluna2 = st.columns([1,1])
                with coluna1:
                    metrica_leads_ultimos_30_dias = st.metric('Total de Leads últimos 30 dias',len(leads_último_mês), delta_último_mês,help='A média de vezes que o mesmo lead entrou em contato')

                with coluna1:
                    metrica_leads_reincidencia = st.metric('%Leads Reincidência',f'{leads_Reincidência}%', delta_último_mês,help='A média de vezes que o mesmo lead entrou em contato')
                
                with coluna2:
                    metrica_media_leads_por_dia = st.metric('Média de leads por dia:',média_leads_por_dia_ultimo_mês, média_leads_por_dia_último_mês)
            
            
# =============================================================================
# INICIO GRÁFICOS
# =============================================================================

st.header("Estatísticas:")

#Separa leads venda de leads locação

tabela_leads_compra= tabela_resultados[tabela_resultados['Natureza da negociação'] == 'Compra']
tabela_leads_aluguel = tabela_resultados[tabela_resultados['Natureza da negociação'] == 'Aluguel']

Leads_compra_por_mes = tabela_leads_compra.groupby("Mês Chegada").size().reset_index(name="Quantidade Leads")
Leads_aluguel_por_mes = tabela_leads_aluguel.groupby("Mês Chegada").size().reset_index(name="Quantidade Leads")

if seleção_agencia_ou_equipes == True:
    titulo_grafico = f'Leads por mês equipe {seleção_equipe}'
elif seleção_agencia != "Todas Agências" :
    titulo_grafico = f'Leads por mês agência {seleção_agencia}'
else:
    titulo_grafico = 'Leads por mês'

if len(Leads_compra_por_mes) >1 or len(Leads_aluguel_por_mes) >1:
    fig = go.Figure()
    # Adicionar a linha ao gráfico
    fig.add_trace(go.Scatter(
    x=Leads_compra_por_mes['Mês Chegada'].astype(str),  # Convertendo o período para string para o eixo X
    y=Leads_compra_por_mes['Quantidade Leads'],
    mode='lines+markers+text',  # Mostrar linha e pontos
    name='Leads Compra',
    text = Leads_compra_por_mes["Quantidade Leads"] ,
    textposition="top center",
    line=dict(color='#008DD9', width=2),# Configurações da linha
    marker=dict(size=4),
    ))

    # Adicionar a linha para "Aluguel"
    fig.add_trace(go.Scatter(
        x=Leads_aluguel_por_mes['Mês Chegada'].astype(str),  # Convertendo o período para string para o eixo X
        y=Leads_aluguel_por_mes['Quantidade Leads'],
        textposition="top center",
        mode='lines+markers+text',  # Mostrar linha e pontos
        text = Leads_aluguel_por_mes["Quantidade Leads"],
        name='Leads Aluguel',
        line=dict(color='#E68100', width=2),  # Configurações da linha
        marker=dict(size=4)  # Configurações dos marcadores
    ))
    # Adicionar títulos e ajustar layout
    
    fig.update_layout(
    title= titulo_grafico,
    xaxis_title='Mês',
    yaxis_title='Quantidade Leads', 
     xaxis=dict(
        tickmode='array',  # Mostra rótulos em um intervalo definido
        tickvals=Leads_compra_por_mes['Mês Chegada'].astype(str).tolist(),  # Garantir que todos os meses aparecem
        ticktext=Leads_compra_por_mes['Mês Chegada'].astype(str).tolist(),
        tickangle=45,  # Rotaciona os rótulos do eixo X para evitar sobreposição
        tickformat="%b" # Formato para exibir as datas (dia-mês-ano)
    ),
    template='plotly_white'  # Tema branco para melhor visualização
    )
    # Mostrar o gráfico no Streamlit
    st.plotly_chart(fig)


else:
    st.write("Seleciona um intervalo maior que 1 mês para exibir o gráfico de captações por mês")


coluna1, coluna2 = st.columns([1, 3])

with coluna1:

    leads_venda_por_fonte = tabela_resultados["Fonte"].value_counts()
    leads_venda_por_fonte

with coluna2:
    # Mapeamento de cores específicas
    color_map = {
    "Placa":"#363530",
    "Site":"#EDB32B",
    "Site Próprio (SH Prime)":"#EDB32B",
    "Site SH Prime Imóveis":"#EDB32B",
    "ImovelWeb":"e64d00",
    " Instagram": "d03059",
    "Instagram Leads":"d03059",
    "Chaves na Mão": "ff0d36",
    "Loft": "#d9562b",
    "LOFT 40%":"#d9562b",
    "LOFT 80%":"#d9562b",
    "Grupo Zap" : "#CEE000",
    "Zap Imóveis": "#CEE000",  # Verde limão
    "Facebook": "#0866ff",     # Azul Facebook
    "Facebook Leads":"0866ff",
    "Google": "#DB4437",       # Vermelho Google
    "Indicação": "#FF9900"}     # Laranja

    # Criando o gráfico de torta com mapeamento correto
    grafico_fonte = px.pie(
    data_frame=leads_venda_por_fonte.reset_index(),
    names=leads_venda_por_fonte.index,               # Nome da coluna com as categorias (Fonte)
    values=leads_venda_por_fonte.values,              # Nome da coluna com os valores (quantidade)
    title="Distribuição de Leads por Fonte",
    color=leads_venda_por_fonte.index,               # Base para o mapeamento
    color_discrete_map=color_map) # Aplicando cores personalizadas corretamente

    # Exibindo o gráfico (em Streamlit, use st.plotly_chart(fig))
    st.plotly_chart(grafico_fonte)

leads_por_bairro = tabela_resultados["Bairro"].value_counts().dropna().reset_index().rename(columns={'count': 'Leads'})

def topo_tabela(tabela, tamanho):
    return tabela.head(tamanho)

coluna1, coluna2 = st.columns([1, 3])

with coluna1:
    leads_por_bairro

with coluna2:
    # Criar gráfico de barras
    grafico_leads_por_bairro = px.bar(topo_tabela(leads_por_bairro, 20),
    x="Bairro",  # Linha horizontal (eixo X)
    y="Leads",   # Linha vertical (eixo Y)
    text="Leads",  # Exibe os valores nos topos das barras
    )

    # Personalizar a cor das barras
    grafico_leads_por_bairro.update_traces(marker_color="#0140FF")  # Cor customizada (laranja)

    # Títulos e layout
    grafico_leads_por_bairro.update_layout(
    title="Leads por Bairro",
    xaxis_title="Bairros",
    yaxis_title="Número de Leads",
    template="plotly_white",  # Fundo claro
    )
    grafico_leads_por_bairro

leads_por_imovel = tabela_resultados['Código do Imóvel'].value_counts().reset_index().rename(columns={'count': 'Leads'})
leads_por_imovel

tabela_resultados