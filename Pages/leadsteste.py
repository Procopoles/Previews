import os
import json
import requests
import datetime
from datetime import timedelta
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# Configurações iniciais do Streamlit e CSS
st.set_page_config(layout="wide")
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Rubik:wght@400;700&display=swap');
    html, body, [class*="css"] {
        font-family: 'Rubik', sans-serif;
    }
    </style>
    """, unsafe_allow_html=True)

# =============================================================================
# FUNÇÕES AUXILIARES
# =============================================================================

def padrão_lead(valor):
    if valor < 1000000:
        return 'Baixo Padrão'
    elif valor >= 1000000:
        return 'Médio Padrão'
    elif valor >= 1900000:
        return ''
    
def capitalize(texto):
    return texto.title()

def formatar_valor(val):
    return f'R$ {val:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')

def formatar_datas(val):
    return val.strftime('%d/%m/%Y') if not pd.isnull(val) else ''

def grafico_torta(data):
    fig = go.Figure(go.Pie(
        labels=data.index,
        values=data,
    ))
    fig.update_traces(
        textfont_size=12,
        marker=dict(line=dict(color='black', width=1))
    )
    return fig

# Dicionário de renomeação de equipes
renomeação_equipes = {
    'SH Prime - ZN Tiger': 'Tiger',
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

colunas_excluir = [
    "Canal", "Telefone apenas dígitos", "Cidade",
    'Status da atividade atual', "Negócio fechado em",
    "Valor real do fechamento", "Etiquetas",
    "Código do imóvel negociado"
]

# =============================================================================
# FUNÇÕES DE CARREGAMENTO E LIMPEZA DOS DADOS
# =============================================================================

@st.cache_data(show_spinner=False)
def carregar_dados():
    """Carrega e concatena os arquivos Excel."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.abspath(os.path.join(current_dir, ".."))
    file_path = os.path.join(base_dir, "Ativos", "report-leads-31-12-2024.xlsx")
    file_path_df2 = os.path.join(base_dir, "Ativos", "report-leads-30-06-2024.xlsx")
    file_path_df3 = os.path.join(base_dir, "Ativos", "report-leads-jarneiro-2024.xlsx")
    file_path_df4 = os.path.join(base_dir, "Ativos", "report-leads-31-01-2025.xlsx")
    
    df1 = pd.read_excel(file_path)
    df2 = pd.read_excel(file_path_df2)
    df3 = pd.read_excel(file_path_df3)
    df4 = pd.read_excel(file_path_df4)
    
    df_leads_c2s = pd.concat([df1, df2, df3, df4], ignore_index=True)
    
    # Converter "Data de chegada" para datetime e extrair só a data
    df_leads_c2s["Data de chegada"] = pd.to_datetime(
        df_leads_c2s["Data de chegada"], format='%d/%m/%Y %H:%M', errors='coerce'
    ).dt.date
    return df_leads_c2s

@st.cache_data(show_spinner=False)
def leads_cleaner(dataframe):
    """Limpa e padroniza o DataFrame de leads."""
    df_leads_clean = dataframe.drop(columns=colunas_excluir, errors="ignore").copy()
    df_leads_clean["Equipe"] = df_leads_clean["Equipe"].replace(renomeação_equipes)
    
    # Converter "Data de chegada" para datetime (para filtros e agrupamentos)
    df_leads_clean["Data de chegada"] = pd.to_datetime(
        df_leads_clean["Data de chegada"], format='%Y-%m-%d', errors='coerce'
    )
    df_leads_clean['Data Chegada'] = df_leads_clean['Data de chegada'].dt.strftime('%d/%m/%Y')
    df_leads_clean["Mês Chegada"] = df_leads_clean["Data de chegada"].dt.to_period("M")
    
    # Limpar a coluna "Bairro"
    df_leads_clean['Bairro'] = (
        df_leads_clean['Bairro']
        .str.extract(r'-\s*(.+)$', expand=False)
        .fillna(df_leads_clean['Bairro'])
        .str.replace(r'[^\w\s]', '', regex=True)
        .str.replace(r'\s+', ' ', regex=True)
        .str.strip()
    )
    # Garantir que o código do imóvel seja string
    df_leads_clean['Código do Imóvel'] = df_leads_clean['Código do Imóvel'].astype(str)
    
    return df_leads_clean

# =============================================================================
# EXECUÇÃO PRINCIPAL DA APLICAÇÃO
# =============================================================================

def main():
    # Carregar e limpar os dados
    df_leads_c2s = carregar_dados()
    df_leads_clean = leads_cleaner(df_leads_c2s)
    
    # Atualização simples do bairro (apenas capitaliza)
    df_bairros_atualizado = df_leads_clean.copy()
    df_bairros_atualizado['Bairro'] = df_bairros_atualizado['Bairro'].astype(str).apply(capitalize)
    st.sidebar.title("Dashboard - Leads")
    st.sidebar.subheader("Menu Principal")
    
    # Seletor de Tipo de Lead
    tipos_lead = ("Compra", "Aluguel", "Ambos")
    # Utilizando radio (o segmented_control não é padrão)
    seleção_tipo_leads = st.sidebar.radio("Tipo de Leads", options=tipos_lead, index=2)
    
    # Seleção: Por Equipes ou por Agência
    seleção_agencia_ou_equipes = st.sidebar.checkbox("Por Equipes", value=False)
    
    # Dicionário de equipes por agência
    equipes_agencias = {
        "Todas Agências": [],
        "Perdizes": ["Albatroz", "Carcará", "Azor", "Gavião", "Falcão", "Faisão"],
        "Pacaembu": ["Fênix", "Canário", "Sabiá"],
        "Santana": ["Lion", "Tiger", "Wolf"],
        "Jardins": ["Gold"],
        "Itaim Bibi": ["Infinity"]
    }
    
    if seleção_agencia_ou_equipes:
        seleção_equipe = st.sidebar.selectbox(
            "Selecione a Equipe", 
            ["Azor", "Faisão", "Falcão", "Gavião", "Carcará", "Albatroz",
             "Gold", "Sabiá", "Fênix", "Canário", "Lion", "Tiger", "Wolf", "Infinity", "Sem Equipe Vinculada"]
        )
    else:
        seleção_agencia = st.sidebar.selectbox("Selecione a Agência", options=list(equipes_agencias.keys()))
        if seleção_agencia != "Todas Agências":
            equipes_da_agencia = equipes_agencias[seleção_agencia]
            regex_equipes = '|'.join(equipes_da_agencia)
    
    # Seletor de Data de Chegada
    data_minima = df_bairros_atualizado["Data de chegada"].min().date()
    data_maxima = df_bairros_atualizado["Data de chegada"].max().date()
    seleção_data_cadastro = st.sidebar.date_input(
        "Data de Chegada", 
        value=[data_minima, data_maxima],
        min_value=data_minima, max_value=data_maxima,
        format="DD/MM/YYYY"
    )
    if len(seleção_data_cadastro) != 2:
        st.error("Selecione um intervalo de datas válido!")
        return
    data_inicial = pd.to_datetime(seleção_data_cadastro[0])
    data_final = pd.to_datetime(seleção_data_cadastro[1])
    
    # Filtragem dos dados
    tabela_resultados = df_bairros_atualizado[
        (df_bairros_atualizado["Data de chegada"] >= data_inicial) &
        (df_bairros_atualizado["Data de chegada"] <= data_final)
    ]
    
    if seleção_tipo_leads == "Ambos":
        filtro_tipo = ["Compra", "Aluguel"]
    else:
        filtro_tipo = [seleção_tipo_leads]
    tabela_resultados = tabela_resultados[tabela_resultados["Natureza da negociação"].isin(filtro_tipo)]
    
    if seleção_agencia_ou_equipes:
        tabela_resultados = tabela_resultados[tabela_resultados["Equipe"].str.contains(seleção_equipe, case=False, na=False)]
    else:
        if seleção_agencia != "Todas Agências":
            tabela_resultados = tabela_resultados[tabela_resultados["Equipe"].str.contains(regex_equipes, case=False, na=False)]
    
    contagem_leads = len(tabela_resultados)
    st.subheader(f"Total de Leads: {contagem_leads}")
    
    # =============================================================================
    # Métricas e Indicadores (últimos 30 dias)
    # =============================================================================
    data_mes_passado = data_final - timedelta(days=31)
    data_mes_retrasado = data_final - timedelta(days=61)
    
    if data_final > data_mes_passado:
        leads_ultimo_mes = tabela_resultados[tabela_resultados['Data de chegada'] >= data_mes_passado]
        leads_penultimo_mes = tabela_resultados[
            (tabela_resultados['Data de chegada'] >= data_mes_retrasado) &
            (tabela_resultados['Data de chegada'] < data_mes_passado)
        ]
        delta_ultimo_mes = int(len(leads_ultimo_mes) - len(leads_penultimo_mes))
        
        # Contatos duplicados
        contatos_lead = tabela_resultados[['Nome do cliente', 'Telefone formatado']].value_counts().reset_index().rename(columns={0: 'Contatos'})
        leads_contato_maior_que_1 = contatos_lead[contatos_lead['Contatos'] > 1]
        leads_Reincidência = round((len(leads_contato_maior_que_1) / contagem_leads)*100, 2) if contagem_leads > 0 else 0
        
        leads_por_dia = leads_ultimo_mes['Data de chegada'].value_counts()
        média_leads_por_dia = int(leads_por_dia.mean()) if not leads_por_dia.empty else 0
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric('Leads últimos 30 dias', len(leads_ultimo_mes), delta_ultimo_mes, help='Diferença em relação ao penúltimo mês')
            st.metric('%Leads Reincidência', f'{leads_Reincidência}%', delta_ultimo_mes, help='Percentual de leads com múltiplos contatos')
        with col2:
            st.metric('Média de leads por dia', média_leads_por_dia)
    
    # =============================================================================
    # Gráfico: Leads por Mês
    # =============================================================================
    
    tabela_leads_compra = tabela_resultados[tabela_resultados['Natureza da negociação'] == 'Compra']
    tabela_leads_aluguel = tabela_resultados[tabela_resultados['Natureza da negociação'] == 'Aluguel']
    
    Leads_compra_por_mes = tabela_leads_compra.groupby("Mês Chegada").size().reset_index(name="Quantidade Leads")
    Leads_aluguel_por_mes = tabela_leads_aluguel.groupby("Mês Chegada").size().reset_index(name="Quantidade Leads")
    
    if (len(Leads_compra_por_mes) > 1) or (len(Leads_aluguel_por_mes) > 1):
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=Leads_compra_por_mes['Mês Chegada'].astype(str),
            y=Leads_compra_por_mes['Quantidade Leads'],
            mode='lines+markers+text',
            name='Leads Compra',
            text=Leads_compra_por_mes["Quantidade Leads"],
            textposition="top center",
            line=dict(color='#008DD9', width=2),
            marker=dict(size=4)
        ))
        fig.add_trace(go.Scatter(
            x=Leads_aluguel_por_mes['Mês Chegada'].astype(str),
            y=Leads_aluguel_por_mes['Quantidade Leads'],
            mode='lines+markers+text',
            name='Leads Aluguel',
            text=Leads_aluguel_por_mes["Quantidade Leads"],
            textposition="top center",
            line=dict(color='#E68100', width=2),
            marker=dict(size=4)
        ))
        
        if seleção_agencia_ou_equipes:
            titulo_grafico = f'Leads por mês - Equipe {seleção_equipe}'
        elif seleção_agencia != "Todas Agências":
            titulo_grafico = f'Leads por mês - Agência {seleção_agencia}'
        else:
            titulo_grafico = 'Leads por mês'
            
        fig.update_layout(
            title=titulo_grafico,
            xaxis_title='Mês',
            yaxis_title='Quantidade Leads',
            xaxis=dict(tickmode='array', tickangle=45),
            template='plotly_white'
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.write("Selecione um intervalo maior que 1 mês para exibir o gráfico de captações por mês.")
    
    # =============================================================================
    # Gráfico: Distribuição de Leads por Fonte
    # =============================================================================
    leads_por_fonte = tabela_resultados["Fonte"].value_counts()
    if not leads_por_fonte.empty:
        color_map = {
            "Placa": "#363530",
            "Site": "#EDB32B",
            "Site Próprio (SH Prime)": "#EDB32B",
            "Site SH Prime Imóveis": "#EDB32B",
            "ImovelWeb": "#e64d00",
            " Instagram": "#d03059",
            "Instagram Leads": "#d03059",
            "Chaves na Mão": "#ff0d36",
            "Loft": "#d9562b",
            "LOFT 40%": "#d9562b",
            "LOFT 80%": "#d9562b",
            "Grupo Zap": "#CEE000",
            "Zap Imóveis": "#CEE000",
            "Facebook": "#0866ff",
            "Facebook Leads": "#0866ff",
            "Google": "#DB4437",
            "Indicação": "#FF9900"
        }
        grafico_fonte = px.pie(
            data_frame=leads_por_fonte.reset_index(),
            names='index',
            values='Fonte',
            title="Distribuição de Leads por Fonte",
            color='index',
            color_discrete_map=color_map
        )
        st.plotly_chart(grafico_fonte, use_container_width=True)
    
    # =============================================================================
    # Gráfico: Leads por Bairro (Top 20)
    # =============================================================================
    leads_por_bairro = tabela_resultados["Bairro"].value_counts().dropna().reset_index().rename(columns={'index': 'Bairro', 'Bairro': 'Leads'})
    if not leads_por_bairro.empty:
        top_bairros = leads_por_bairro.head(20)
        grafico_leads_por_bairro = px.bar(
            top_bairros,
            x="Bairro",
            y="Leads",
            text="Leads",
            title="Leads por Bairro"
        )
        grafico_leads_por_bairro.update_traces(marker_color="#0140FF")
        grafico_leads_por_bairro.update_layout(
            xaxis_title="Bairros",
            yaxis_title="Número de Leads",
            template="plotly_white"
        )
        st.plotly_chart(grafico_leads_por_bairro, use_container_width=True)
    
    # =============================================================================
    # Exibição da Tabela Final
    # =============================================================================
    st.dataframe(tabela_resultados.reset_index(drop=True))
    
if __name__ == "__main__":
    main()
