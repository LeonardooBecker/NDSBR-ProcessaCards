# NDSBR-ProcessaCards

Link de explicação sobre como utilizar o script no youtube:

https://www.youtube.com/watch?v=4o3pmF3Huyc

# Processamento de Dados de GPS e Vídeo para Viagens

Este repositório contém um script Python para processar dados de GPS e vídeos de viagens, gerando planilhas estruturadas e vídeos concatenados por viagem.

## Funcionalidades Principais

- **Validação de Diretórios**: Busca por pastas `Card` contendo dados de GPS (`GPSData000001.txt`) e vídeos (pastas `Front` e `Back`).
- **Separação de Viagens**: Divide os dados de GPS em viagens individuais com base no marcador `$V02`.
- **Sincronização de Tempo**: Identifica o primeiro segundo válido nos vídeos para sincronizar com os dados de GPS.
- **Geração de Planilhas**: Cria arquivos CSV com métricas como latitude, longitude, velocidade, aceleração e tempo acumulado.
- **Concatenação de Vídeos**: Junta vídeos de cada viagem (frontal e traseira) usando FFmpeg.

## Estrutura do Diretório

Os dados devem estar organizados conforme abaixo:

```
Diretório_Raiz/
├── Condutor_X/                # Pasta do condutor
│   ├── Card_YYY/              # Pasta do cartão de dados
│   │   ├── Front/             # Vídeos da câmera frontal
│   │   ├── Back/              # Vídeos da câmera traseira
│   │   └── GPSData000001.txt  # Arquivo de dados do GPS
```

## Dependências

- Python 3.x

### Bibliotecas Python

```bash
pip install pandas opencv-python datetime multiprocess subprocess.run ffmpeg
```

Ou se preferir:

```bash
pip install -r requirements.txt
```


### Outras Dependências

- FFmpeg (para concatenação de vídeos).
- Módulo `retorna_primeiro_segundo` (não incluído no repositório).

## Uso

Execute o script passando o diretório raiz como argumento:

```bash
python script.py /caminho/do/diretorio_raiz
```

### Saídas Geradas

- **Pasta `arquivos_gps`**: CSVs com dados processados de cada viagem.
- **Pasta `videos_concatenados`**: Vídeos unificados por viagem (`Front` e `Back`).

## Notas

- O módulo `retorna_primeiro_segundo` é necessário para extrair tempo, velocidade e coordenadas dos frames.
- Vídeos incompletos ou inexistentes são registrados em `sumarizacao_erros`.
- A concatenação de vídeos requer FFmpeg instalado e acessível via `PATH`.

Contribuições são bem-vindas!  
