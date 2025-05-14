import os
import sys
import pandas as pd
import re

condutores_presentes = ""

# Função para validar e consolidar dados das planilhas
def valida_card(diretorio_card, name_card, data_consolidada):
    conteudo_card = os.listdir(diretorio_card)
    if 'arquivos_gps' in conteudo_card:
        planilhas_dir = f'{diretorio_card}/arquivos_gps'
        planilhas = os.listdir(planilhas_dir)
        print(f'{name_card} ({diretorio_card}) tem {len(planilhas)} planilhas')
        
        for planilha in planilhas:
            viagem_planilha_dir = f'{planilhas_dir}/{planilha}'
            
            if planilha.endswith('.csv'):
                try:
                    df = pd.read_csv(viagem_planilha_dir, sep=';')
                    data_consolidada.append(df)
                except Exception as e:
                    print(f'Erro ao processar {viagem_planilha_dir}: {e}')


# Recursão para buscar os arquivos de GPS independente do diretório passado
def destrincha_diretorio(caminho_atual, data_consolidada, condutores_presentes):
    dirs = os.listdir(caminho_atual)
    dirs.sort()
    for dir in dirs:
        oficial_dir = f'{caminho_atual}/{dir}'

        if os.path.isdir(oficial_dir):
            if "Card" in dir:
                parts = oficial_dir.split('/')
                for part in parts:
                    if re.search(r'[A-Z]{2,}', part):
                        condutores_presentes.append(part)
                    
                valida_card(oficial_dir, dir, data_consolidada)
            destrincha_diretorio(oficial_dir, data_consolidada, condutores_presentes)


# Função principal para iniciar a busca e salvar o CSV final
def busca_cards(caminho_atual):
    data_consolidada = []
    condutores_presentes = []
    
    try:
        destrincha_diretorio(caminho_atual, data_consolidada, condutores_presentes)
        # Consolida todos os dados em um único DataFrame e salva no arquivo CSV final
        if data_consolidada:
            condutores_presentes = list(sorted(set(condutores_presentes)))
            name_condutores = "_".join(condutores_presentes)
            df_final = pd.concat(data_consolidada, ignore_index=True)
            df_final.to_csv(f'FullTable_{name_condutores}.csv', index=False, sep=';')
            print(f'Arquivo "FullTable_{name_condutores}.csv" salvo com sucesso.')
        else:
            print('Nenhum dado foi consolidado.')
    except Exception as e:
        print(f'Erro: {e}')

# Chamada principal
if __name__ == "__main__":
    if len(sys.argv) > 1:
        caminho_atual = sys.argv[1]
        busca_cards(caminho_atual)
    else:
        print('Nenhum argumento foi passado na chamada do script')
