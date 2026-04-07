from arcgis.gis import GIS
from arcgis.features import FeatureLayer
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import contextily as ctx
from pathlib import Path
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import requests
import os
import logging
from logging.handlers import RotatingFileHandler
import configparser
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from jinja2 import Template
import re
import json
import time

config_path = os.path.join('config', "config.ini") # Caminho do arquivo de configuração
config = configparser.ConfigParser() # Ler o arquivo de configuração
config.read(config_path)

EMAIL_USER = config["EMAIL"]["EMAIL_USER"]
ARQUIVO_PASSWORD = r"\\Bp-1hd57t3-inea\e\COGET\INPUTS_SCRIPTS\acessos.xlsx"
df_envio = pd.read_excel(ARQUIVO_PASSWORD)
df_envio = df_envio[df_envio['filtro'] == EMAIL_USER]
password = str(df_envio['senha'].iloc[0])



SMTP_SERVER = config["EMAIL"]["SMTP_SERVER"]
SMTP_PORT = int(config["EMAIL"]["SMTP_PORT"])
DEFAULT_RECIPIENT = config["EMAIL"]["DEFAULT_RECIPIENT"]
MAX_RETRIES = 3 
RETRY_DELAY = 5 # Atraso em segundos entre as tentativas

def setup_logging():
    """
    Configura o sistema de logging para o script.

    Define o formato das mensagens de log e configura dois handlers:
    - RotatingFileHandler: Para salvar os logs em um arquivo com rotação (logs/execucao.log).
    - StreamHandler: Para exibir os logs no console.
    """
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
    log_file = os.path.join("logs", "execucao.log") # Diretório dedicado para logs
    # Configurar handlers
    handlers = [RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=3, encoding="utf-8"), logging.StreamHandler()]
    logging.basicConfig(level=logging.INFO, format=log_format, handlers=handlers)

def conectar_portal():
    """
    Estabelece conexão com o portal ArcGIS Online.

    Lê as credenciais (URL, usuário e senha) do arquivo de configuração
    e tenta autenticar no portal.

    Returns:
        arcgis.gis.GIS: Objeto GIS representando a conexão com o portal em caso de sucesso.
    """
    portal_url = config["PORTAL"]["URL_PORTAL"]
    username = config["PORTAL"]["GIS_USER"]
    ARQUIVO_PASSWORD = r"\\Bp-1hd57t3-inea\e\COGET\INPUTS_SCRIPTS\acessos.xlsx"
    df_envio = pd.read_excel(ARQUIVO_PASSWORD)
    df_envio = df_envio[df_envio['filtro'] == username]
    password = str(df_envio['senha'].iloc[0])
    try:
        gis = GIS(portal_url, username=username, password=password, verify_cert=True)
        logging.info("✅ Conexão com ArcGIS Online estabelecida.")
        return gis
    except Exception as e:
        logging.error(f"❌ Erro ao conectar ao ArcGIS Online: {e}")

def baixar_csvs():
    """
    Baixa dados de várias tabelas de um Feature Service e os salva como arquivos Excel.

    As URLs das tabelas são lidas do arquivo de configuração. Cada tabela é
    consultada, convertida para um DataFrame do pandas e salva em um arquivo .xlsx
    na pasta 'CSVs'.
    """
    saida_csvs = r"input/CSVs"
    os.makedirs(saida_csvs, exist_ok=True)
    # URLs das tabelas
    url_atual = config["PORTAL"]["CSV_URL"]
    url_link = config["PORTAL"]["URL_LINK"]
    urls = {
        'camada': f'{url_atual}/0',
        'notificacao': f'{url_atual}/1',
        'auto_const': f'{url_atual}/2',
        'medida_cautelar': f'{url_atual}/3',
        'repeat_rl_fotografico': f'{url_atual}/4',
        'assinaturas': f'{url_atual}/5',
        'links': f"{url_link}"
    }
    dfs = {} # Dicionário para armazenar os DataFrames
    for nome, url in urls.items(): # Loop para criar cada DataFrame
        try:
            layer = FeatureLayer(url) # Carrega a tabela
            query_result = layer.query(where="1=1", out_fields="*") # Consulta os dados
            if len(query_result.features) > 0:
                df = pd.DataFrame([f.attributes for f in query_result.features])
                dfs[nome] = df
            else:
                logging.warning(f"⚠️  Aviso: Nenhum registro encontrado para {nome}DF")
        except Exception as e:
            logging.error(f"❌ Erro ao processar {nome}: {str(e)}")
    # Removendo a coluna e atualizando o dicionário
    dfs['links'] = dfs['links'].drop('observacao', axis=1, errors='ignore')
    for nome_df, df in dfs.items():
        try:
            df.to_excel(f"{saida_csvs}\\{nome_df}.xlsx", index=False)
        except Exception as e:
            logging.error(f"❌ Erro ao salvar o DataFrame '{nome_df}': {str(e)}")
    logging.info(f"✅ CSVs salvos!")

def baixar_imagens(table, input, identificacao):
    """
    Baixa imagens anexadas de uma tabela de um Feature Service.

    Conecta-se ao portal, acessa um item específico e sua tabela correspondente.
    Em seguida, itera sobre as feições, obtém a lista de anexos e baixa
    as imagens (arquivos .jpg), salvando-as no diretório de saída especificado.

    Args:
        table (int): O índice da tabela no Feature Service de onde baixar as imagens.
        output (str): O caminho da pasta onde as imagens serão salvas.
        identificacao (str): O nome do campo de atributo usado para nomear os arquivos de imagem.
    """
    gis = conectar_portal()
    id_imagens = config["PORTAL"]["ID_IMAGENS"]
    item = gis.content.get(id_imagens)
    sublayer = item.tables[table] # 4
    oid_field = sublayer.properties.objectIdField # Verificar o campo OID
    features = sublayer.query(where="1=1", return_attachments=True).features # Consulta features (com return_attachments=True)
    token = gis._con.token.replace('\n', '') # Obtem token sem quebras de linha
    lista_imagens = [] # Listar anexos corretamente
    features = sublayer.query(where="1=1").features
    oid_field = sublayer.properties.objectIdField
    pasta_saida = input # r"Output\assinaturas"
    os.makedirs(pasta_saida, exist_ok=True) # Cria diretório se não existir
    for feature in features:
        try:
            feature_id = feature.attributes.get(identificacao, "N/A") # id_fiscalizacao_assinaturas  id_fiscalizacao_rl_foto
            oid = feature.attributes[oid_field]
            attachments = sublayer.attachments.get_list(oid)
            for attachment in attachments:
                if attachment['name'].lower().endswith('.jpg'):
                    # URL corrigida (com OID e token sem quebras)
                    url_imagem = f"{sublayer.url}/{oid}/attachments/{attachment['id']}?token={token}"
                    lista_imagens.append({"feature_id": feature_id, "nome_imagem": attachment['name'], "url": url_imagem})
        except Exception as e:
            logging.error(f"Erro na feature {oid}: {str(e)}")
    for item in lista_imagens:
        try:
            url = item['url']
            nome_imagem =  f"Img_{item['feature_id']}_{item['nome_imagem']}"
            caminho_imagem = f"{pasta_saida}\\{nome_imagem}"
            headers = {"Referer": config["PORTAL"]["URL_PORTAL"], 
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
            response = requests.get(url, headers=headers, timeout=10, stream=True)
            if response.status_code == 200:
                content_type = response.headers.get('Content-Type', '')
                if 'image' not in content_type:
                    logging.error(f"⚠️ A URL não é uma imagem válida: {url} (Content-Type: {content_type})")
                    continue
                with open(caminho_imagem, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                if os.path.getsize(caminho_imagem) > 0:
                    None
                else:
                    logging.error(f"❌ Arquivo vazio: {caminho_imagem}")
                    os.remove(caminho_imagem)
            else:
                logging.error(f"❌ Falha ao baixar {nome_imagem} (Status: {response.status_code})")
        except Exception as e:
            logging.error(f"🔥 Erro ao baixar {nome_imagem}: {str(e)}")
    logging.info(f"✅ {len(lista_imagens)} imagens salvas na pasta {pasta_saida}!")

def get_token(config):
    """Obtém o token de autenticação da API ArcGIS."""
    print("🔑 Tentando obter o token de autenticação...")
    
    username = config['PORTAL']['GIS_USER']
    ARQUIVO_PASSWORD = r"\\Bp-1hd57t3-inea\e\COGET\INPUTS_SCRIPTS\acessos.xlsx"
    df_envio = pd.read_excel(ARQUIVO_PASSWORD)
    df_envio = df_envio[df_envio['filtro'] == username]
    password = str(df_envio['senha'].iloc[0])
    portal_url = config['PORTAL']['URL_PORTAL']
    
    token_url = f"{portal_url}/sharing/rest/generateToken"
    
    payload = {
        'username': username,
        'password': password,
        'referer': portal_url,
        'f': 'json'
    }

    try:
        response = requests.post(token_url, data=payload)
        response.raise_for_status()
        
        token_data = response.json()
        
        if 'token' in token_data:
            print("✅ Token obtido com sucesso.")
            return token_data['token']
        elif 'error' in token_data:
            print(f"❌ Erro ao obter token: {token_data['error']['message']}")
            return None
        else:
            print("❌ Resposta inesperada ao tentar obter o token.")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro de requisição ao tentar obter o token: {e}")
        return None
    
def carregar_config(config_file):
    """Carrega as configurações do arquivo .ini."""
    config = configparser.ConfigParser()
    if not os.path.exists(config_file):
        raise FileNotFoundError(f"O arquivo de configuração '{config_file}' não foi encontrado.")
    config.read(config_file)
    return config


def process_object_id(config, auth_token, objectid):
    """
    Tenta baixar o anexo para um único OBJECT_ID usando o token.
    Inclui lógica de retry para erros temporários de servidor (502, 503, 504).
    Retorna 1 se o download for bem-sucedido, 0 se falhar ou não houver anexo,
    e "STOP" em caso de erro fatal de token (código 499).
    """
    try:
        # 1. Configurar URLs com Token
        base_download_url = config['PORTAL']['URL_CAMADA'] 
        json_info_url = f"{base_download_url}/{objectid}/attachments?f=json&token={auth_token}"
        
        # 2. Obter o JSON de informações do anexo 
        json_response = requests.get(json_info_url)
        json_response.raise_for_status()
        
        try:
            data = json_response.json()
        except json.JSONDecodeError:
            print(f"❌ Erro ao decodificar o JSON. Conteúdo: {json_response.text[:200]}...")
            return 0 # Falha

        # 3. Verificar o JSON (pode ter "error" ou estar vazio)
        if 'error' in data:
            error_msg = data['error']['message']
            print(f"❌ Erro na API para ID {objectid}: {error_msg}")
            if data['error']['code'] == 499: 
                print("🚫 O token provavelmente expirou ou é inválido. Interrompendo a execução.")
                return "STOP" # Instrução para interromper o loop principal
            return 0 # Falha

        if not data.get("attachmentInfos") or not data["attachmentInfos"]:
            #print(f"⚠️ Aviso: 'attachmentInfos' vazio. A Feature {objectid} NÃO POSSUI anexos.")
            return 0 # Falha

        # 4. Extrair informações do primeiro anexo
        attachment_info = data["attachmentInfos"][0]
        
        attachment_id = attachment_info.get("attachmentid")
        content_type = attachment_info.get("contentType", "")
        
        if attachment_id is None:
            print(f"❌ Erro: 'attachmentid' não encontrado no JSON para ID {objectid}.")
            return 0 # Falha

        # Mapeamento do Content-Type para a extensão do arquivo
        extensao_map = {"image/jpeg": ".jpeg", "image/png": ".png", "application/pdf": ".pdf"}
        extensao = extensao_map.get(content_type.lower(), "") 
        
        # 5. Construir a URL final de Download e o nome do arquivo 
        output_dir = os.path.join("input", "autorizacao")
        filename = os.path.join(output_dir, f"{objectid}{extensao}")
        download_url = f"{base_download_url}/{objectid}/attachments/{attachment_id}?token={auth_token}"

        #print(f"🔗 URL de Download: {download_url}")
        #print(f"💾 Nome do arquivo de saída: {filename}")
        
        # 6. Fazer a requisição HTTP para baixar o anexo com Retry
        for attempt in range(MAX_RETRIES):
            try:
                #print(f"📥 Iniciando o download... (Tentativa {attempt + 1}/{MAX_RETRIES})")
                response = requests.get(download_url, stream=True, timeout=30) # Aumentei o timeout opcionalmente
                response.raise_for_status()
                
                # 7. Salvar o conteúdo em um arquivo (só executa se o download for bem-sucedido)
                os.makedirs(output_dir, exist_ok=True) # Cria o diretório se não existir
                
                with open(filename, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=1024):
                        if chunk:
                            f.write(chunk)
                
                #print(f"✅ Download concluído para a autorização {objectid}!")
                return 1 
            
            except requests.exceptions.RequestException as e:
                # Se for erro 502, 503 ou 504 e não for a última tentativa, tenta novamente
                if (response.status_code in [502, 503, 504] if 'response' in locals() else False) and attempt < MAX_RETRIES - 1:
                    print(f"⚠️ Erro de servidor temporário ({response.status_code}). Tentando novamente em {RETRY_DELAY}s...")
                    time.sleep(RETRY_DELAY)
                    continue # Volta para o próximo loop (próxima tentativa)
                
                # Se for outro erro ou a última tentativa
                print(f"❌ Erro de requisição HTTP fatal para ID {objectid}: {e}")
                return 0 
                
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro de requisição HTTP (informações do anexo) para ID {objectid}: {e}")
        return 0 
    except Exception as e:
        print(f"❌ Ocorreu um erro inesperado ao processar ID {objectid}: {e}")
        return 0 


def criar_gdf():
    """
    Cria um GeoDataFrame a partir dos pontos de uma camada de feição do ArcGIS.

    Consulta uma camada de feição (definida no arquivo de configuração),
    extrai a geometria (x, y) e os atributos de cada ponto, e os converte
    em um GeoDataFrame do GeoPandas com o sistema de coordenadas WGS84 (EPSG:4326).

    Returns:
        geopandas.GeoDataFrame: Um GeoDataFrame contendo os pontos da camada.
    """
    service_url = config["PORTAL"]["URL_CAMADA"]
    layer = FeatureLayer(service_url)
    features = layer.query(where="1=1").features
    pontos = [] # Lista para armazenar dados dos pontos (coordenadas + atributos)
    for feature in features:
        if feature.geometry and "x" in feature.geometry and "y" in feature.geometry:
            # Extrair geometria
            x = feature.geometry["x"]
            y = feature.geometry["y"]
            # Extrair atributos (ex: GlobalID, OBJECTID, etc.)
            atributos = feature.attributes  # Dicionário com todos os campos
            pontos.append({
                "Longitude": x,
                "Latitude": y,
                "GlobalID": atributos.get("globalid"),  # Substitua pelo nome correto do campo
                "OBJECTID": atributos.get("objectid"),  # Campo padrão do ArcGIS
                # Adicione outros campos necessários aqui
            })
    df = pd.DataFrame(pontos) # Criar DataFrame com todos os atributos
    df = df[(df["Longitude"].abs() > 1e-10) & (df["Latitude"].abs() > 1e-10)] # Filtrar pontos inválidos (ajuste conforme necessário)
    # Criar GeoDataFrame
    gdf = gpd.GeoDataFrame(
        df,  # Usar o DataFrame completo (com atributos)
        geometry=gpd.points_from_xy(df["Longitude"], df["Latitude"]),
        crs="EPSG:4326"
    )
    return gdf

def plot_each_point(gdf, png_folder, buffer_distance=50, color='red', opacity=0.9, marker_size=200, basemap_source=ctx.providers.Esri.WorldImagery, id_column='GlobalID'):
    """
    Gera e salva uma imagem de mapa para cada ponto em um GeoDataFrame.

    Itera sobre cada ponto, cria um mapa centrado no ponto com um buffer
    específico, adiciona um basemap, um ícone de pino e uma legenda com as
    coordenadas. A imagem resultante é salva em formato PNG.

    Args:
        gdf (geopandas.GeoDataFrame): GeoDataFrame com os pontos a serem plotados.
        png_folder (str): Caminho da pasta para salvar as imagens dos mapas.
        buffer_distance (int, optional): Distância do buffer para definir o zoom do mapa. Defaults to 50.
        color (str, optional): Cor do marcador (atualmente não utilizado). Defaults to 'red'.
        opacity (float, optional): Opacidade do marcador (atualmente não utilizado). Defaults to 0.9.
        marker_size (int, optional): Tamanho do marcador (atualmente não utilizado). Defaults to 200.
        basemap_source (object, optional): Fonte do basemap do contextily. Defaults to ctx.providers.Esri.WorldImagery.
        id_column (str, optional): Nome da coluna a ser usada para nomear os arquivos de saída. Defaults to 'GlobalID'.
    """
    Path(png_folder).mkdir(parents=True, exist_ok=True)
    gdf_web = gdf.to_crs(epsg=3857)  # Converter para Web Mercator
    for idx, row in gdf_web.iterrows():
        if row.geometry.geom_type != 'Point':
            logging.warning(f"⚠️ Entrada {idx} não é um ponto. Pulando...")
            continue
        try:
            fig, ax = plt.subplots(figsize=(10, 10))
            # Coordenadas para zoom
            x, y = row.geometry.x, row.geometry.y
            ax.set_xlim(x - buffer_distance, x + buffer_distance)
            ax.set_ylim(y - buffer_distance, y + buffer_distance)
            pin_icon = plt.imread(r'arquivos_fixos\imagens_layout\pin.png')
            imagebox = OffsetImage(pin_icon, zoom=0.1)
            ab = AnnotationBbox(imagebox, (x, y), frameon=False)
            ax.add_artist(ab),
            ctx.add_basemap(ax, source=basemap_source, zoom=18) # Adicionar basemap
            # Obter coordenadas WGS84 (lat/lon)
            point_wgs84 = gpd.GeoSeries([row.geometry], crs='EPSG:3857').to_crs('EPSG:4326').geometry[0]
            lon, lat = point_wgs84.x, point_wgs84.y
            # Legenda com coordenadas
            texto_legenda = f'Lat: {lat:.6f}°\nLon: {lon:.6f}°'
            ax.text(0.05, 0.95, texto_legenda, transform=ax.transAxes,
                bbox=dict(facecolor='white', alpha=0.8, edgecolor='black', boxstyle='round'),
                fontsize=12, verticalalignment='top')
            # Nome do arquivo usando o ID (ex: GlobalID)
            file_id = row[id_column] if id_column in gdf.columns else idx
            output_path = os.path.join(png_folder, f"ponto_{file_id}.png")
            plt.savefig(output_path, dpi=300, bbox_inches='tight', pad_inches=0)
            plt.close()
        except Exception as e:
            logging.error(f"🔥 Erro ao plotar ponto: {str(e)}")
    logging.info(f"✅ {len(gdf_web)} mapas salvos em '{png_folder}'")
