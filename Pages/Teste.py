import pandas as pd
import datetime
import plotly.express as px
import plotly.graph_objects as go


pd.options.display.date_yearfirst = False
pd.options.display.date_dayfirst = True


df_imoveis = pd.read_csv("Ativos/imoveis 22-11-2024.csv")


data_hoje = datetime.datetime.now()

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
    df_imoveis_ativos['Data atualizacao'] = pd.to_datetime(df_imoveis_ativos['Data atualizacao'], format='%d/%m/%Y')
    df_imoveis_ativos["Data cadastro"] = pd.to_datetime(df_imoveis_ativos["Data cadastro"],format="%d/%m/%Y")
    df_imoveis_ativos["Chamadas"] = df_imoveis_ativos["Corretores do Imovel"].fillna("").str.split(",").str[-1]
    df_imoveis_ativos["Captador Imóvel"] = df_imoveis_ativos["Corretores do Imovel"].str.split(",").str[0]
    df_imoveis_ativos['Padrão Imovel'] = df_imoveis_ativos['Valor venda'].apply(padrao_imovel)
    df_imoveis_ativos[["Vagas", "Suite", "Endereco Numero"]] = df_imoveis_ativos[["Vagas", "Suite", "Endereco Numero"]].fillna(0).astype(int)
    df_imoveis_ativos['Status Atualização'] = df_imoveis_ativos['Data atualizacao'].apply(classificar_atualizacao)
    return df_imoveis_ativos

df_imoveis_ativos = imoveis_ativos(df_imoveis)

@st.cache_data
def df_imoveis_cleaner(dataframe):

    df_imoveis_clean = dataframe[["Referencia", "Bairro Comercial", "Data cadastro", "Data atualizacao", "Empreendimento"]] 
    return df_imoveis_clean
    
df_imoveis_clean = df_imoveis_cleaner(df_imoveis_ativos)

df_imoveis_clean