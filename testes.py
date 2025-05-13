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
base_dir = os.path.abspath(os.path.join(current_dir))

# Caminho para o arquivo
file_path = os.path.join(base_dir, "Ativos", "report-leads-28-11-2024.xlsx")

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


df_leads_c2s["Data de chegada"] = pd.to_datetime(df_leads_c2s["Data de chegada"], format='%d/%m/%Y %H:%M', errors='coerce')
df_leads_c2s["Data de chegada"] = df_leads_c2s["Data de chegada"].dt.date


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
colunas_excluir = ["Canal", "Telefone apenas dígitos", "Cidade", 'Status da atividade atual', "Negócio fechado em", "Valor real do fechamento", "Etiquetas", "Código do imóvel negociado"]

@st.cache_data
def leads_cleaner(dataframe):
    df_leads_clean = dataframe.drop(columns=colunas_excluir)
    df_leads_clean["Equipe"] = df_leads_clean["Equipe"].replace(renomeação_equipes)
    df_leads_clean["Data de chegada"] = pd.to_datetime(df_leads_clean["Data de chegada"], format='%d/%m/%Y %H:%M', errors='coerce')
    df_leads_clean['Data Chegada'] = df_leads_clean['Data de chegada'].dt.strftime('%d/%m/%Y')
    df_leads_clean["Mês chegada"] = df_leads_clean["Data de chegada"].dt.to_period("M")
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


data_minima = df_leads_clean["Data de chegada"].min()
data_maxima = df_leads_clean["Data de chegada"].max()
data_hoje = datetime.datetime.now()
data_mes_passado = data_maxima - timedelta(days=31)
data_mes_retrasado = data_maxima - timedelta(days=61)


leads_último_mês = df_leads_clean[(df_leads_clean['Data de chegada'] >= data_mes_passado) &
(df_leads_clean['Natureza da negociação'].isin(["Compra", "Aluguel"]))]
leads_penúltimo_mês = df_leads_clean[(df_leads_clean['Data de chegada'] >= data_mes_retrasado) & 
(df_leads_clean['Data de chegada'] <= data_mes_passado)]
delta_último_mês = int(len(leads_último_mês) - len(leads_penúltimo_mês))
