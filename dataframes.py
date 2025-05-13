import pandas as pd
import datetime
import requests
import json

# Defina a chave de acesso e a URL base
api_key = '5747309ef69f4dfec03b87133c9b0b83'
base_url = 'http://shprime2-rest.vistahost.com.br'

listar_campos = f'{base_url}/imoveis/listarcampos?key={api_key}'

# Configure os parâmetros de pesquisa

codigo_imovel = ['1178709', '1178710', 'SH123663', 'SH129381', 'SH78168', 'SH123866'] #diversos códigos em uma lista

fields = ['Codigo', 'BairroComercial', 'Status', 'VivaRealPublicationType', 'VivaRealPublicationType2']
filter = {'Codigo': codigo_imovel}
#filter = {'Status': ['Venda', 'Vendido Terceiros', 'Pendente', 'Alugado Terceiros', 'Aluguel']}  # Exemplo: mínimo de 2 dormitórios'} 
paginação = {"pagina":1,"quantidade":50}
pesquisa = {'fields': fields, 'filter': filter, "paginacao": paginação}

pesquisa_json = json.dumps(pesquisa)

# Construa a URL completa com os parâmetros
endpoint = f'/imoveis/listar?key={api_key}&pesquisa={pesquisa_json}&showSuspended=1'
url = base_url + endpoint

# Realize a requisição GET
response = requests.get(f'{base_url}/imoveis/listar',headers={'Accept': 'application/json'},params={'key': api_key, 'pesquisa': json.dumps(pesquisa), 'showSuspended': 1, 'showInternal': 1 })


# Verifique o status da resposta
if response.status_code == 200:
    # Converta a resposta para JSON
    data = response.json()
    # Exiba os dados
    print(json.dumps(data, indent=4, ensure_ascii=False))
else:
    print(f'Erro: {response.status_code}, Detalhes: {response.text}')

