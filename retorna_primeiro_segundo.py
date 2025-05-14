import cv2
import numpy as np
from ultralytics import YOLO

selected_base = "pequena"

def retorna_maior_correspondencia(image_of_interest):
    max_val = 0
    indice=-1
    imagens_referencia = []
    if selected_base == "pequena":
        imagens_referencia = images_base
    # else:
        # imagens_referencia = big_images_base
    for idx, image in enumerate(imagens_referencia):
        val = comparar_imagens(image, image_of_interest)
        if val > max_val and val > 0.6:
            max_val = val
            indice = idx
    return indice


def comparar_imagens(base_image, target_image, threshold=0.8):
    """
    Compara a imagem base com a imagem alvo usando Template Matching.
    
    base_image: Caminho da imagem base (ex: 'numeros_base/0.png')
    target_image: Caminho da imagem a ser comparada (ex: 'novas_imagens/numero.png')
    threshold: Limite de confiança para considerar a imagem semelhante (padrão: 0.8)
    
    Retorna True se forem semelhantes, False caso contrário.
    """
    # Carregar as imagens em escala de cinza
    base = base_image
    target = target_image

    # Aplicar Template Matching (cv2.TM_CCOEFF_NORMED é um método de correlação)
    resultado = cv2.matchTemplate(target, base, cv2.TM_CCOEFF_NORMED)
    
    # Achar o valor máximo da correlação
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(resultado)
    
    return max_val


def separa_imagens(frame):
    threshold = 20
    _, black_mask = cv2.threshold(frame, threshold, 255, cv2.THRESH_BINARY_INV)
    sum_columns = np.sum(black_mask == 255, axis=0)

    percentage_black = 0.97
    min_black_pixels = int(black_mask.shape[0] * percentage_black)

    # # Encontre colunas onde pelo menos 97% dos pixels são pretos
    partial_black_columns = np.where(sum_columns >= min_black_pixels)[0]
    
    objeto_images = {}
    last=0
    identificador_local=0
    for vals in partial_black_columns:
        now = vals
        if now - last > 1 and abs(now - last) > 10:
            objeto_images[f'pos{identificador_local}'] = frame[0:, last:now]
            identificador_local+=1
        last = now

    return objeto_images

numeros_base = ['base_numbers/0.jpg', 'base_numbers/1.jpg', 'base_numbers/2.jpg', 'base_numbers/3.jpg', 'base_numbers/4.jpg',
            'base_numbers/5.jpg', 'base_numbers/6.jpg', 'base_numbers/7.jpg', 'base_numbers/8.jpg', 'base_numbers/9.jpg']
images_base = [cv2.imread(img, 0) for img in numeros_base]
# big_numbers_base = ['big_base_numbers/0.jpg', 'big_base_numbers/1.jpg', 'big_base_numbers/2.jpg', 'big_base_numbers/3.jpg', 'big_base_numbers/4.jpg', 'big_base_numbers/5.jpg', 'big_base_numbers/6.jpg', 'big_base_numbers/7.jpg', 'big_base_numbers/8.jpg', 'big_base_numbers/9.jpg']
# big_images_base = [cv2.imread(img, 0) for img in big_numbers_base]

def buscar_valor(objeto_images: dict):
    valor_completo = []
    for key, value in enumerate(objeto_images.values()):
        indice_imagem = retorna_maior_correspondencia(value)
        if indice_imagem != -1:
            valor_completo.append(indice_imagem)
        
    if(len(valor_completo) == 6):
        resultado = f'{valor_completo[0]}{valor_completo[1]}:{valor_completo[2]}{valor_completo[3]}:{valor_completo[4]}{valor_completo[5]}'
    else:
        resultado = str(''.join(map(str, valor_completo[0:2])))
    return resultado, len(valor_completo)


def retorna_tempo(frame):
    img_width = frame.shape[1]
    img_height = frame.shape[0]
    
    if img_height == 1080 and img_width == 1920:
        selected_base = "pequena"
        width_of_interest = [300, 500]
        height_of_interest = [1030, 1060]
        
        time_img = frame[height_of_interest[0]:height_of_interest[1], width_of_interest[0]:width_of_interest[1]]
        threshold = 235  
        gray = cv2.cvtColor(time_img, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, threshold, 255, cv2.THRESH_BINARY)
        objeto_images = separa_imagens(thresh)
        tempo, _ = buscar_valor(objeto_images) 
        return tempo
    
def retorna_velocidade(frame):
    img_width = frame.shape[1]
    img_height = frame.shape[0]
    
    if img_height == 1080 and img_width == 1920:
        selected_base = "pequena"
        width_of_interest = [1280,1460]
        height_of_interest = [1030, 1060]
        
        time_img = frame[height_of_interest[0]:height_of_interest[1], width_of_interest[0]:width_of_interest[1]]
        threshold = 235  
        gray = cv2.cvtColor(time_img, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, threshold, 255, cv2.THRESH_BINARY)
        objeto_images = separa_imagens(thresh)
        velocidade, _ = buscar_valor(objeto_images) 
        return velocidade
    
def retorna_coordenada(frame):
    img_width = frame.shape[1]
    img_height = frame.shape[0]
    
    if img_height == 1080 and img_width == 1920:
        selected_base = "pequena"
        width_of_interest = [1460, img_width]
        height_of_interest = [1030, 1060]
        
        time_img = frame[height_of_interest[0]:height_of_interest[1], width_of_interest[0]:width_of_interest[1]]
        threshold = 235  
        gray = cv2.cvtColor(time_img, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, threshold, 255, cv2.THRESH_BINARY)
        objeto_images = separa_imagens(thresh)
        coordenada, _ = buscar_valor(objeto_images) 
        return coordenada