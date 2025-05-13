import pandas as pd
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.abspath(os.path.join(current_dir))

# Caminho para o arquivo
arquivo_excel = os.path.join(base_dir, "Ativos", "report-leads-28-11-2024")
arquivo_parquet = "pinto.parquet"

def excel_para_parquet(arquivo_excel, arquivo_parquet, nome_aba=None):
    """
    Lê um arquivo Excel (xlsx) e salva como arquivo Parquet.
    
    :param arquivo_excel: Caminho para o arquivo Excel de entrada.
    :param arquivo_parquet: Caminho para o arquivo Parquet de saída.
    :param nome_aba: Nome ou índice da planilha (aba) a ser lida. Se None, lê a primeira.
    """
    # Lê a(s) planilha(s) do arquivo Excel
    df = pd.read_excel(arquivo_excel, sheet_name=nome_aba)
    
    # Salva o DataFrame em Parquet
    df.to_parquet(arquivo_parquet, engine='pyarrow', index=False)
    print(f"Arquivo Parquet salvo em: {arquivo_parquet}")

# Exemplo de uso
if __name__ == "__main__":
    caminho_excel = arquivo_excel        # Caminho do arquivo Excel de entrada
    caminho_parquet = arquivo_parquet   # Caminho do arquivo Parquet de saída
    nome_planilha = "leads-15-12-2024"                 # Pode ser o nome (ex: 'Planilha1') ou índice (ex: 0)

    excel_para_parquet(caminho_excel, caminho_parquet, nome_planilha)
