import pandas as pd

# Caminhos para os arquivos de entrada e saída
caminho_arquivo1 = r"C:\SH Prime\Analise de Dados\Captações\Novembro\leads ultimo mes - ver leads de imoveis atualizados.xlsx"
caminho_arquivo2 = r"C:\SH Prime\Analise de Dados\Captações\Novembro\Imoveis atualizados nos ultimos 30 dias nao puc.csv"
caminho_saida = r"C:\SH Prime\Analise de Dados\Resultados\intersecao_resultado.xlsx"

# Ler as duas planilhas fora da função
df1 = pd.read_excel(caminho_arquivo1)
df2 = pd.read_csv(caminho_arquivo2)

def intersecao_planilhas(df1, df2, caminho_saida):
    # Realizar a intersecção usando as colunas 'Referencia' e 'Código do Imóvel '
    df_intersecao = pd.merge(df2, df1, left_on='Referencia', right_on='Código do Imóvel', how='inner')
    
    # Salvar o resultado em um novo arquivo CSV na pasta Resultados
    df_intersecao.to_excel(caminho_saida, index=False)

# Executar a função com os DataFrames lidos
intersecao_planilhas(df1, df2, caminho_saida)
