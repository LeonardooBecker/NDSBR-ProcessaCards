import pandas as pd
import cv2
import datetime

import os
import sys
import re
import shutil

import subprocess
import sys
import multiprocessing
import random

from retorna_primeiro_segundo import retorna_tempo
from retorna_primeiro_segundo import retorna_velocidade
from retorna_primeiro_segundo import retorna_coordenada
    


headerTXT = ['TIMESTAMP', 'HOVER', 'LATITUDE', 'LONGITUDE', 'A1', 'VELOCIDADE', 'A2', 'A3', 'A4', 'GPS_FILE', 'A5', 'A6', 'A7']

headerCSV = ['DRIVER', 'LONG', 'LAT', 'DAY', 'DAY_CORRIGIDO', '03:00:00', 'TRIP', 'ID',
             'PR', 'H', 'M', 'S', 'TIME_ACUM', 'SPD_MPH', 'SPD_KMH', 'ACEL_MS2', 'HEADING', 'ALTITUDE_FT',
             'VALID_TIME', 'TIMESTAMP', 'CPOOL', 'CPOOLING', 'WSB', 'UMP_YN', 'UMP', 'PICK_UP', 'ACTION',
             'GPS_FILE', 'CIDADE', 'BAIRRO', 'NOME_RUA', 'HIERARQUIA_CWB', 'HIERARQUIA_CTB', 'LIMITE_VEL']

class Viagem():
    df_dados = pd.DataFrame()
    nome = str
    segundo_inicial = 0
    indice_viagem = int
    
    def __init__(self, df_dados, indice_viagem = 0):
        self.df_dados = df_dados
        self.indice_viagem = indice_viagem
    
    def set_nome(self, nome):
        self.nome = nome
        

class Card:
    diretorio_geral = ""
    diretorio_gps_file = ""
    diretorio_videos_front = ""
    diretorio_videos_back = ""

    videos_front = []
    videos_back = []

    condutor = str

    qnt_videos_completos = 0
    qnt_videos_incompletos = 0
    qnt_videos_inexistentes = 0

    viagens_com_video = []
    viagem_sem_video = Viagem(pd.DataFrame(), 0)

    def __init__(self, diretorio_geral, diretorio_gps_file, diretorio_videos_front, diretorio_videos_back):
        self.diretorio_geral = diretorio_geral
        self.diretorio_gps_file = diretorio_gps_file
        self.diretorio_videos_front = diretorio_videos_front
        self.diretorio_videos_back = diretorio_videos_back
        self.condutor = self.get_condutor()
    
    def popula_videos_back(self, videos_back):
        self.videos_back = videos_back
    
    def popula_videos_front(self, videos_front):
        self.videos_front = videos_front

    def get_condutor(self):
        parts = self.diretorio_geral.split('/')
        for part in parts:
            if(part.__contains__("Condutor ")):
                return (part.replace("Condutor ", ""))
            #comparar se o nome só contem caracteres entre A e Z
            elif(re.match("^[A-Z]*$", part) and part != ''):
                return (part)
            else:
                continue
        return None
        
    def get_diretorio_planilhas(self):
        if(os.path.exists(f'{self.diretorio_geral}/arquivos_gps')):
            shutil.rmtree(f'{self.diretorio_geral}/arquivos_gps')
        os.makedirs(f'{self.diretorio_geral}/arquivos_gps')
        return f'{self.diretorio_geral}/arquivos_gps'
    
    def cria_diretorio_videos(self):
        if(os.path.exists(f'{self.diretorio_geral}/videos_concatenados')):
            shutil.rmtree(f'{self.diretorio_geral}/videos_concatenados')
        os.makedirs(f'{self.diretorio_geral}/videos_concatenados')
        return f'{self.diretorio_geral}/videos_concatenados'
    
    def get_diretorio_videos(self):
        return f'{self.diretorio_geral}/videos_concatenados'

sumarizacao_erros = []

#region - Região responsável por buscar os Cards disponível no diretório passado como argumento

def valida_card(cards_encontrados: list, diretorio_card, name_card):
    conteudo_card = os.listdir(diretorio_card)
    msgErro = ""
    if "Front" not in conteudo_card:
        msgErro += (f'{name_card} ({diretorio_card}) não possui pasta Front\n')
    if "Back" not in conteudo_card:
        msgErro += (f'{name_card} ({diretorio_card}) não possui pasta Back\n')
    if "GPSData000001.txt" not in conteudo_card:
        msgErro += (f'{name_card} ({diretorio_card}) não possui arquivo de GPSData000001.txt\n')
    if msgErro == "":
        card_encontrado = Card(diretorio_card, f'{diretorio_card}/GPSData000001.txt', f'{diretorio_card}/Front', f'{diretorio_card}/Back')
        card_encontrado.popula_videos_back(os.listdir(f'{card_encontrado.diretorio_videos_back}'))
        card_encontrado.popula_videos_front(os.listdir(f'{card_encontrado.diretorio_videos_front}'))
        cards_encontrados.append(card_encontrado)
    else:
        sumarizacao_erros.append(msgErro)

#Recursão para buscar os arquivos de GPS independente do diretório passado
def destrincha_diretorio(cards_encontrados: list,caminho_atual):
    dirs = os.listdir(caminho_atual)
    for dir in dirs:
        oficial_dir = f'{caminho_atual}/{dir}'
        if os.path.isdir(oficial_dir):
            if(dir.__contains__("Card")):
                valida_card(cards_encontrados, oficial_dir, dir)
            destrincha_diretorio(cards_encontrados,oficial_dir)

def busca_cards(cards_encontrados: list, caminho_atual):
    try:
        try:
            destrincha_diretorio(cards_encontrados, caminho_atual)
        except:
            print('Não é diretório')
    except:
        print('Nenhum argumento foi passado na chamada do script')
    
#endregion
        

#region - Região responsável por separar o arquivo de GPS em viagens completas, incompletas e inexistentes

def separa_gpsfiles_dfviagenslist(diretorio_gps):
    last_index = 0
    df_viagens_list = []
    # O arquivo de txt tem um característica que utiliza o $V02 para separar as viagens
    with open(diretorio_gps, 'r') as f:
        lines = f.readlines()
        for idx, line in enumerate(lines):
            parts = line.split(',')
            if parts[0].__contains__("$V02"):
                if last_index != 0:
                    df = pd.read_csv(diretorio_gps, skiprows=last_index, nrows=idx - last_index, header=None, names=headerTXT)
                    df = df[~df["GPS_FILE"].str.contains("F.mp4", na=False)]
                    df_viagens_list.append(df)
                last_index = idx + 1 
                
        if last_index != 0:
            df = pd.read_csv(diretorio_gps, skiprows=last_index, header=None, names=headerTXT)
            df = df[~df["GPS_FILE"].str.contains("F.mp4", na=False)]
            df_viagens_list.append(df)
    return df_viagens_list


def define_viagens_card(cards_encontrados: list[Card]):
    for card in cards_encontrados:
        if isinstance(card, Card):
            videos_incompleto = []
            videos_inexistente = []
            videos_completos = []
            indice_viagem = 1
            
            df_viagens_list = separa_gpsfiles_dfviagenslist(card.diretorio_gps_file)
            
            # df_viagens_list contem varios dataframes pandas, cada um representando uma viagem
            for df_viagem in df_viagens_list:
                df_viagem= df_viagem[df_viagem["HOVER"] == "A"]
                videos_abrangidos = df_viagem["GPS_FILE"].drop_duplicates().tolist()
                
                # region - Classificação de viagens, com videos completos, incompletos e inexistentes
                if(videos_abrangidos):
                    if set(videos_abrangidos).intersection(set(card.videos_back)) == set(videos_abrangidos):
                        videos_completos.append(Viagem(df_viagem, indice_viagem))
                        indice_viagem += 1
                    else:
                        resta_algum_video = set(videos_abrangidos).intersection(set(card.videos_back))
                        if(resta_algum_video):
                            rav_df = df_viagem[df_viagem["GPS_FILE"].isin(resta_algum_video)]
                            videos_incompleto.append(rav_df)

                        sem_video = set(videos_abrangidos).difference(set(card.videos_back))
                        if(sem_video):
                            sv_df = df_viagem[df_viagem["GPS_FILE"].isin(sem_video)]
                            sv_df = sv_df.drop_duplicates(subset=['TIMESTAMP'])
                            inicio = sv_df["TIMESTAMP"].min()
                            fim = sv_df["TIMESTAMP"].iloc[-1]
                            full_range = pd.DataFrame({'TIMESTAMP': range(inicio, fim + 1)})
                            df_tratado = pd.merge(full_range, sv_df, on='TIMESTAMP', how='left')
                            df_tratado.ffill(inplace=True)
                            videos_inexistente.append(df_tratado)
                # endregion

            # region - Popula o card com as informações de viagens completas, incompletas e inexistentes
            
            card.qnt_videos_completos = len(videos_completos)
            card.qnt_videos_incompletos = len(videos_incompleto)
            card.qnt_videos_inexistentes = len(videos_inexistente)

            # Insere o vídeo com a viagem incompleta no vetor de viagens completas pois o tratamento necessário é o mesmo
            if(videos_incompleto):
                videos_completos.append(Viagem(pd.concat(videos_incompleto),0))
            
            if(videos_inexistente):
                card.viagem_sem_video = Viagem(pd.concat(videos_inexistente),0)
            if(videos_completos):   
                card.viagens_com_video = videos_completos
                
            # endregion
        
        else:
            sumarizacao_erros.append(f'Card não é uma instância de Card: {card}') 

#endregion


#region - Região responsável por definir o segundo inicial real da viagem de acordo com o vídeo

def tempo_to_secs(tempo):
    h, m, s = tempo.split(':')
    return int(h) * 3600 + int(m) * 60 + int(s)

# O valor unix apresentado no arquivo de GPSData000001.txt não é o mesmo que o valor apresentado no vídeo;
# Com isso, é necessário buscar no vídeo com o primeiro segundo valído de viagem, ou seja, o primeiro segundo que a velocidade e coordenada passam a ser apresetadas;
# Sabendo o primeiro segundo válido, é identificado o respectivo tempo apresentado no vídeo e definido o segundo inicial da viagem;
# O desvio serve para casos em que foi identificado um primeiro segundo válido, mas não foi possível identificar o tempo no vídeo, com isso é feito um desvio de 1 segundo para cada novo segundo.
def define_segundo_inicial(card: Card, viagem: Viagem, shared_list):
    primeiro_video_viagem = viagem.df_dados["GPS_FILE"].iloc[0]
    
    if primeiro_video_viagem.__contains__("B.mp4"):
        diretorio_especifico = f'{card.diretorio_videos_back}/{primeiro_video_viagem}'
        cap = cv2.VideoCapture(diretorio_especifico)
        desvio_seg = 0
        validado = False
        while cap.isOpened():
            lista_tempos = []
            velocidade = []
            coordenada = []
            for i in range (0, 30, 5):
                ret, frame = cap.read()
                if not ret:
                    break
                tempo = retorna_tempo(frame)
                padrao_tempo = r'^\d{2}:\d{2}:\d{2}$'
                if tempo and re.match(padrao_tempo, tempo):
                    lista_tempos.append(tempo)

                velocidade.append(retorna_velocidade(frame))
                coordenada.append(retorna_coordenada(frame))
            
            if not ret:
                print(f"Erro ao ler o vídeo {diretorio_especifico} utilizando valores de tempo UNIX do arquivo de GPS")
                break
            
            if velocidade:
                velocidade_mais_frequente = max(set(velocidade), key = velocidade.count)
            if coordenada:
                coordenada_mais_frequente = max(set(coordenada), key = coordenada.count)

            if lista_tempos and (validado or (velocidade_mais_frequente != "" and coordenada_mais_frequente != "")):
                # print(f"Valores encontrados: desvio:{desvio_seg}, velocidade:{velocidade_mais_frequente}, coordenada:{coordenada_mais_frequente}")
                break
            elif validado or (velocidade_mais_frequente != "" and coordenada_mais_frequente != ""):
                # print(f"Validado: desvio:{desvio_seg}, velocidade:{velocidade_mais_frequente}, coordenada:{coordenada_mais_frequente}")
                validado = True
                desvio_seg += 1
            
        if lista_tempos:
            valor_mais_frequente = max(set(lista_tempos), key = lista_tempos.count)
            valor_em_seg = tempo_to_secs(valor_mais_frequente)
            segundo_inicial_real = valor_em_seg - desvio_seg
            viagem.segundo_inicial = segundo_inicial_real
        else:
            data_inicial = convert_unix_timestamp(viagem.df_dados["TIMESTAMP"].iloc[0])
            segundo_inicial = data_inicial.hour * 3600 + data_inicial.minute * 60 + data_inicial.second
            viagem.segundo_inicial = segundo_inicial
        
        
        shared_list.append(viagem)
        print(f"Condutor:{card.get_condutor()}\tCard:{card.diretorio_geral}\tViagem {viagem.indice_viagem}")

        # print(valor_mais_frequente, velocidade_mais_frequente, coordenada_mais_frequente, desvio_seg, diretorio_especifico)

def define_segundo_incial_multiprocessing(vg_com_video, card, max_process):
    with multiprocessing.Manager() as manager:
        viagens_compartilhadas = manager.list()
        
        with multiprocessing.Pool(processes=max_process) as pool:
            pool.starmap(define_segundo_inicial, [(card, viagem, viagens_compartilhadas) for viagem in vg_com_video])
            pool.close()
            pool.join()
        for viagem in viagens_compartilhadas:
            viagem_original = [vg for vg in vg_com_video if vg.indice_viagem == viagem.indice_viagem][0]
            viagem_original.segundo_inicial = viagem.segundo_inicial
            
# endregion


# region - Região responsável por gerar as planilhas referente a cada viagem

def convert_unix_timestamp(unix_timestamp):
    dt = datetime.datetime.fromtimestamp(unix_timestamp)
    return dt

def convert_velocidade_KMH(velocidade):
    return round(float(velocidade) * 3.6 / 100, 5)

def converte_velocidade_MPH(velocidade):
    return round(float(velocidade) / 1.609, 5)

def retorna_dia_from_data(data):
    return f'{data.day:02d}/{data.month:02d}/{data.year:04d}'

def retorna_hora_from_data(data):
    return f'{data.hour:02d}:{data.minute:02d}:{data.second:02d}'

def retorna_tempo_from_segundo(segundos):
    horas = segundos // 3600
    minutos = (segundos % 3600) // 60
    segundos = segundos % 60
    return f'{horas:02d}:{minutos:02d}:{segundos:02d}'

def corrige_df(df: pd.DataFrame):
    doiszerodois = 0
    zerodoiszero = 0
    rp_dzd = 0
    rp_zdz = 0    
    idx=0  
    indices_inserir = []
    indices_remover = []    

    lista_diferencas = df['TIMESTAMP'].diff().to_list()
    while True:
        if(idx+3 >= len(lista_diferencas)):
            break

        if(idx > 1):
            valor = lista_diferencas[idx]
            valor_anterior = lista_diferencas[idx-1]
            if(valor_anterior == 1):
                if(valor == 0):
                    if(lista_diferencas[idx+1] >= 2):
                        if(lista_diferencas[idx+2] == 0):
                            if(lista_diferencas[idx+3] == 1):
                                rp_dzd += 1
                                if(rp_dzd == 1):
                                    indices_inserir.append(idx)
                                    doiszerodois += 1
                                rp_zdz = 0
                        
                        elif(lista_diferencas[idx+2] == 1):
                            rp_zdz = 0
                            rp_dzd = 0
                if(valor >= 2):
                    if(lista_diferencas[idx+1] == 0):
                        if(lista_diferencas[idx+2] >= 2):
                            if(lista_diferencas[idx+3] == 1):
                                rp_zdz += 1
                                if(rp_zdz == 1):
                                    indices_remover.append(idx)
                                    zerodoiszero += 1
                                rp_dzd = 0
                        elif(lista_diferencas[idx+2] == 1):
                            rp_zdz = 0
                            rp_dzd = 0
        idx+=1
    return indices_inserir, indices_remover


def gera_planilha(viagem: Viagem,idx,condutor,diretorio_planilhas):
    df = viagem.df_dados
    df_valido = df[df["HOVER"] == "A"]
    if(len(df_valido) > 0):

        if idx != 'sem_video':
            indices_inserir,indices_remover = corrige_df(df_valido)
        
            #remove duplicatas
            df_valido = df_valido.drop_duplicates(subset=['TIMESTAMP'])
            #-----

            # insere linhas faltantes
            inicio = df_valido["TIMESTAMP"].min()
            fim = df_valido["TIMESTAMP"].iloc[-1]
            full_range = pd.DataFrame({'TIMESTAMP': range(inicio, fim + 1)})
            df_tratado_inicial = pd.merge(full_range, df_valido, on='TIMESTAMP', how='left')
            df_tratado_inicial.ffill(inplace=True)
            
            
            linhas_inserir = []
            for indice in indices_inserir:
                nova_linha = df_tratado_inicial.iloc[indice].copy()  # Copia a linha para manter o formato
                linhas_inserir.append(pd.DataFrame([nova_linha]))

            df_tratado_inicial = pd.concat([df_tratado_inicial] + linhas_inserir).sort_index().reset_index(drop=True)

            df_tratado_inicial = df_tratado_inicial.drop(indices_remover).reset_index(drop=True)
            
            if indices_remover or indices_inserir:
                sumarizacao_erros.append(f'Viagem {idx} do condutor {condutor} teve linhas corrigidas. Linhas inseridas: {len(indices_inserir)}, Linhas removidas: {len(indices_remover)}')
        
        else:
            df_tratado_inicial = df_valido

        #------

        df_segundo_tratamento = pd.DataFrame(columns=headerCSV)


        df_segundo_tratamento["LAT"] = df_tratado_inicial["LATITUDE"]

        df_segundo_tratamento["LONG"] = df_tratado_inicial["LONGITUDE"]

        df_segundo_tratamento["VALID_TIME"] = (df_tratado_inicial["HOVER"] == "A").astype(int)

        df_segundo_tratamento["GPS_FILE"] = df_tratado_inicial["GPS_FILE"]

        df_segundo_tratamento["DATA"] = df_tratado_inicial["TIMESTAMP"].apply(convert_unix_timestamp)

        df_segundo_tratamento["DAY"] = df_segundo_tratamento["DATA"].apply(retorna_dia_from_data)

        df_segundo_tratamento["DAY_CORRIGIDO"] = df_segundo_tratamento["DAY"]

        if(idx != 'sem_video' and viagem.segundo_inicial != 0):
            segs_reposicionados = pd.DataFrame({"TIMESTAMP": range(viagem.segundo_inicial, viagem.segundo_inicial + len(df_tratado_inicial))})
            segs_reposicionados["TIMESTAMP"] = segs_reposicionados["TIMESTAMP"].apply(retorna_tempo_from_segundo)
            df_segundo_tratamento["PR"] = segs_reposicionados["TIMESTAMP"]
        else:
            df_segundo_tratamento["PR"] = df_segundo_tratamento["DATA"].apply(retorna_hora_from_data)

        df_segundo_tratamento["SPD_KMH"] = df_tratado_inicial["VELOCIDADE"].apply(convert_velocidade_KMH)

        df_segundo_tratamento["SPD_MPH"] = df_segundo_tratamento["SPD_KMH"].apply(converte_velocidade_MPH)

        df_segundo_tratamento['ACEL_MS2'] = (df_segundo_tratamento["SPD_KMH"].diff().fillna(0) / 3.6).round(5)

        df_segundo_tratamento["TIME_ACUM"] = pd.DataFrame({"TIME_ACUM": range(0, len(df_segundo_tratamento) + 1)})

        df_segundo_tratamento["S"] = df_segundo_tratamento["DATA"].diff().dt.seconds.fillna(0).astype(int)

        if(condutor):
            df_segundo_tratamento["DRIVER"] = condutor
            df_segundo_tratamento["ID"] = condutor+str(idx)
        df_segundo_tratamento["TRIP"] = str(idx)
        
        #ajuste de ponto para vírgula
        df_segundo_tratamento["LAT"] = df_segundo_tratamento["LAT"].apply(lambda x: str(x).replace(".",","))
        df_segundo_tratamento["LONG"] = df_segundo_tratamento["LONG"].apply(lambda x: str(x).replace(".",","))
        df_segundo_tratamento["SPD_KMH"] = df_segundo_tratamento["SPD_KMH"].apply(lambda x: str(x).replace(".",","))
        df_segundo_tratamento["SPD_MPH"] = df_segundo_tratamento["SPD_MPH"].apply(lambda x: str(x).replace(".",","))
        df_segundo_tratamento['ACEL_MS2'] = df_segundo_tratamento['ACEL_MS2'].apply(lambda x: str(x).replace(".",","))
        

        tempo_inicial = df_segundo_tratamento["PR"].iloc[0].replace(":","")
        data_inicial = df_segundo_tratamento["DATA"].iloc[0].strftime("%Y%m%d")
        nome_viagem = f"Viagem{condutor}{idx}-" + f"{data_inicial}-{tempo_inicial}"
        viagem.set_nome(nome_viagem)
        
        nome_arquivo = f"{diretorio_planilhas}/{nome_viagem}.csv"
        df_segundo_tratamento = df_segundo_tratamento.drop(["DATA"], axis=1)
        df_segundo_tratamento.columns = headerCSV
        df_segundo_tratamento.to_csv(nome_arquivo, index=False, header=headerCSV, sep=';')


def gera_planilhas_csv(cards_encontrados: list[Card], max_process):
    ultimo_condutor = None
    indice_inicial = 1
    for card in cards_encontrados:
        if isinstance(card, Card):
            vg_com_video = card.viagens_com_video
            vg_sem_video = card.viagem_sem_video
            condutor = card.get_condutor()
            diretorio_planilhas = card.get_diretorio_planilhas()
                
            if ultimo_condutor != condutor:
                indice_inicial = 1

            if(not vg_sem_video.df_dados.empty):
                gera_planilha(vg_sem_video,'sem_video',condutor,diretorio_planilhas)

            define_segundo_incial_multiprocessing(vg_com_video, card, max_process)
            for idx,viagem in enumerate(vg_com_video):
                gera_planilha(viagem,f"{(indice_inicial+idx):02d}",condutor,diretorio_planilhas)
            
            proximo_desvio = card.qnt_videos_completos + card.qnt_videos_incompletos
            ultimo_condutor = condutor
            indice_inicial += proximo_desvio
        
        else:
            sumarizacao_erros.append(f'Card não é uma instância de Card: {card}')

# endregion


# region - Região responsável por concatenar os vídeos de cada viagem

def concatena_video(playlist_file, name_file):
    command = ['ffmpeg', '-f', 'concat', '-safe', '0', '-i',  playlist_file, '-c', 'copy', name_file]
    subprocess.run(command)


def monta_arquivo_junta_videos(card: Card, viagem: Viagem, videos, direcaoCamera):
    diretorio_videos_concatenados = card.get_diretorio_videos()
    try:
        if direcaoCamera == 'B':
            nome_video = f'{diretorio_videos_concatenados}/{viagem.nome}-Back.mp4'
            playlist_file = f'{card.diretorio_videos_back}/{viagem.nome}playlist.txt'
        elif direcaoCamera == 'F':
            nome_video = f'{diretorio_videos_concatenados}/{viagem.nome}-Front.mp4'
            playlist_file = f'{card.diretorio_videos_front}/{viagem.nome}playlist.txt'
        else:
            raise Exception('Direção da câmera inválida')
    except:
        sumarizacao_erros.append(f'Erro ao montar arquivo de junção de videos para a viagem {viagem.nome} no card {card.diretorio_geral}')
        return
    finally:
        with open(playlist_file, 'w') as f:
            for video in videos:
                f.write(f"file {video}\n")
        concatena_video(playlist_file, nome_video)
                

def juntar_videos(idx: int, viagem: Viagem, card: Card):
    videos_back = viagem.df_dados["GPS_FILE"].drop_duplicates().tolist()
    videos_front = [video.replace("B.mp4", "F.mp4") for video in videos_back if video.replace("B.mp4", "F.mp4") in card.videos_front]
    if(len(videos_back) == len(videos_front)):
        monta_arquivo_junta_videos(card, viagem, videos_back, 'B')
        monta_arquivo_junta_videos(card, viagem, videos_front, 'F')



# Utilizar multiprocessing para concatenar os vídeos não apresentou um resultado muito agrádavel
def juntar_videos_multiprocessing(viagens_completas, max_process):
    with multiprocessing.Pool(processes=max_process) as pool:
        pool.starmap(juntar_videos, [(idx,viagem) for idx,viagem in enumerate(viagens_completas)])
        pool.close()
        pool.join()        


def concatena_videos_viagens(cards_encontrados: list[Card], max_process):
    for card in cards_encontrados:
        viagens_completas = card.viagens_com_video
        
        card.cria_diretorio_videos()
        for idx,viagem in enumerate(viagens_completas):
            print(idx)
            juntar_videos(idx, viagem, card)

        # juntar_videos_multiprocessing(viagens_completas, max_process)
        
# endregion
        

def imprime_sumario_erros(sumario_erros):
    if sumario_erros:
        for erro in sumario_erros:
            print(erro)


def main():
    caminho_atual = sys.argv[1]
    cards_encontrados = []
    
    busca_cards(cards_encontrados, caminho_atual)
    define_viagens_card(cards_encontrados)
    
    cards_encontrados.sort(key=lambda x: x.diretorio_geral, reverse=False)
    
    max_process = 8 
    gera_planilhas_csv(cards_encontrados, max_process)
    concatena_videos_viagens(cards_encontrados, max_process)
    
    
    imprime_sumario_erros(sumarizacao_erros)
    
if __name__ == '__main__':
    main()