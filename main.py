import pandas as pd
import os
import logging
import traceback
import json
import time
import configparser
import urllib3
from arcgis.features import FeatureLayer
from layout_vistoria import create_pdf_for_idtxt
from id_relatorio import atualizar_id_vstr
from funcoes_script import (
    setup_logging, carregar_config, conectar_portal, get_token, 
    baixar_csvs, baixar_imagens, criar_gdf, plot_each_point, process_object_id
)

# Desativa avisos de SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- Configurações Iniciais ---
CSV_FOLDER = 'input/CSVs'
CONFIG_FILE = os.path.join('config', 'config.ini')
MAX_RETRIES = 3 
RETRY_DELAY = 5 
MAX_GLOBALIDS_TO_TRACK = 500 

setup_logging()

def carregar_estado():
    """Carrega o progresso da última execução."""
    caminho_config = os.path.join("config", "ultimo_oid.json")
    try:
        with open(caminho_config, "r") as f:
            dados = json.load(f)
            return dados.get("ultimo_oid", 0), dados.get("ultimos_globalids", [])
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        return 0, []

def salvar_estado(oid, globalids):
    """Grava o OID atual para evitar reprocessamento."""
    caminho_config = os.path.join("config", "ultimo_oid.json")
    os.makedirs("config", exist_ok=True)
    try:
        with open(caminho_config, "w") as f:
            json.dump({"ultimo_oid": oid, "ultimos_globalids": globalids}, f, indent=4)
        logging.info(f"💾 Estado persistido. OID de controle: {oid}")
    except Exception as e:
        logging.error(f"❌ Erro ao salvar estado: {e}")

def obter_globalids_validos(camada, globalids_esperados):
    """Valida se os registros ainda existem no portal."""
    if not globalids_esperados:
        return []
    globalids_filtrados = globalids_esperados[-MAX_GLOBALIDS_TO_TRACK:]
    query = "GlobalID IN ('{}')".format("','".join(globalids_filtrados))
    try:
        features = camada.query(where=query, out_fields="globalid, objectid").features
        return [{"GlobalID": f.attributes.get("globalid"), "OID": f.attributes.get("objectid")} for f in features]
    except Exception as e:
        logging.error(f"❌ Erro ao validar GlobalIDs: {e}")
        return []

def clean_df_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Limpa cabeçalhos de DataFrames."""
    if df.empty:
        return df
    df.columns = df.columns.astype(str).str.replace('ï»¿', '', regex=False).str.strip().str.lower()
    return df

def join_camada_notificacoes(camada, notificacoes, globalid):
    """Join entre tabelas via parentrowid."""
    camada_linha = camada[camada["globalid"] == globalid]
    if camada_linha.empty:
        return pd.DataFrame()
    parentrowid = camada_linha["uniquerowid"].iloc[0]
    return notificacoes[notificacoes["parentrowid"] == parentrowid]

def main():
    """Retorna lista de IDs dos PDFs gerados com sucesso."""
    ids_gerados_nesta_sessao = []
    config = None
    auth_token = None
    
    # --- 1. Sincronização com Portal ---
    try:
        print("\n" + "="*55)
        print("Iniciando o download dos dados do portal")
        print("="*55)
        config = carregar_config(CONFIG_FILE)
        auth_token = get_token(config)
        
        conectar_portal() 
        camada = FeatureLayer(config["PORTAL"]["URL_CAMADA"])

        # Carrega onde o script parou
        oid_referencia_inicial, ultimos_globalids = carregar_estado()
        globalids_validos = obter_globalids_validos(camada, ultimos_globalids)
        
        # Filtra novas entradas
        query = f"OBJECTID > {oid_referencia_inicial}"
        novas_features = camada.query(where=query, out_fields="globalid, objectid").features

        if not novas_features:
            logging.info("✅ Tudo atualizado. Nenhuma nova feature detectada.")
        else:
            logging.info(f"ℹ️ {len(novas_features)} novas features para processar.")
            
            # Downloads Necessários
            baixar_csvs() 
            baixar_imagens(4, r"input\assinaturas", 'id_fiscalizacao_assinaturas')
            baixar_imagens(3, r"input\RL", 'parentrowid')
            
            logging.info("🗺️ Gerando GeoDataFrames e mapas...")
            gdf = criar_gdf()
            plot_each_point(gdf, r"input\Pontos", buffer_distance=100, id_column='GlobalID')

            # Processamento de Anexos e Atualização de Estado
            object_ids_novas = [f.attributes["objectid"] for f in novas_features]
            maior_oid_encontrado = max(object_ids_novas)

            for object_id in object_ids_novas:
                if auth_token is None: auth_token = get_token(config)
                process_object_id(config, auth_token, str(object_id))

            globalids_novos = [f.attributes["globalid"] for f in novas_features]
            nova_lista_globalids = ([g["GlobalID"] for g in globalids_validos] + globalids_novos)[-MAX_GLOBALIDS_TO_TRACK:]
            salvar_estado(maior_oid_encontrado, nova_lista_globalids)

    except Exception as e:
        logging.error(f"🔥 Erro no download: {e}")
        traceback.print_exc()

    # --- 2. Geração de PDFs ---
    try:
        print("\n" + "="*70)
        print("⏳ Gerando PDFs para registros recentes")
        print("="*70)

        camada_DF = clean_df_columns(pd.read_excel(os.path.join(CSV_FOLDER, "camada.xlsx"), dtype=object))
        links_DF = clean_df_columns(pd.read_excel(os.path.join(CSV_FOLDER, "links.xlsx")))
        notificacao_DF = clean_df_columns(pd.read_excel(os.path.join(CSV_FOLDER, "notificacao.xlsx")))
        auto_const_DF = clean_df_columns(pd.read_excel(os.path.join(CSV_FOLDER, "auto_const.xlsx")))
        medida_cautelar_DF = clean_df_columns(pd.read_excel(os.path.join(CSV_FOLDER, "medida_cautelar.xlsx")))
        repeat_rl_fotografico_DF = clean_df_columns(pd.read_excel(os.path.join(CSV_FOLDER, "repeat_rl_fotografico.xlsx")))
        assinaturas_DF = clean_df_columns(pd.read_excel(os.path.join(CSV_FOLDER, "assinaturas.xlsx")))

        # FILTRO: Apenas o que for maior que o OID do início desta execução
        if 'objectid' in camada_DF.columns:
            camada_DF['objectid'] = pd.to_numeric(camada_DF['objectid'], errors='coerce')
            camada_DF = camada_DF[camada_DF['objectid'] > oid_referencia_inicial].copy()
            
        if camada_DF.empty:
            logging.info("☕ Sem novos laudos para gerar.")
            return []

        logging.info(f"🚀 Processando {len(camada_DF)} registros...")
        
        cnt = 0
        for _, row in camada_DF.iterrows():
            try:
                globalid = row['globalid']
                id_alerta = str(row['id_alerta'])
                
                # ... (Lógica de filtragem interna igual à anterior)
                camada_linha = camada_DF[camada_DF['globalid'] == globalid]
                linha_link = links_DF[links_DF['id'].astype(str) == id_alerta]
                not_lin = join_camada_notificacoes(camada_DF, notificacao_DF, globalid)
                med_lin = join_camada_notificacoes(camada_DF, medida_cautelar_DF, globalid)
                aut_lin = join_camada_notificacoes(camada_DF, auto_const_DF, globalid)
                ass_lin = pd.merge(camada_linha[['id_alerta','id_fiscalizacao']], assinaturas_DF, 
                                   left_on='id_fiscalizacao', right_on='id_fiscalizacao_assinaturas', how='left')
                id_vist = atualizar_id_vstr(camada_DF)
                rl_lin = repeat_rl_fotografico_DF[repeat_rl_fotografico_DF['parentrowid'] == row['uniquerowid']]
                
                # Chama a geração do PDF
                create_pdf_for_idtxt(camada_linha, linha_link, rl_lin, aut_lin, ass_lin, not_lin, 
                                     med_lin, cnt+1, globalid, row['municip_imvl'], id_vist, id_alerta)
                
                # REGISTRA SUCESSO
                ids_gerados_nesta_sessao.append(id_alerta)
                cnt += 1
                logging.info(f"✅ PDF Concluído: {id_alerta}")

            except Exception as e:
                logging.error(f"❌ Erro no ID {row.get('id_alerta')}: {e}")

        print(f"\n✨ Ciclo finalizado! {cnt} novos PDFs disponíveis.")
        return ids_gerados_nesta_sessao

    except Exception as e:
        logging.critical(f"⚠️ Erro na geração: {e}")
        traceback.print_exc()
        return []

if __name__ == "__main__":
    print("\n" + "="*110)
    print("="*20 + " "*22 + " 📃 GERAÇÃO DE VISTORIAS 📃 " + " "*21 + "="*20)
    print("="*110)
    
    lista_para_envio = []
    
    # 1. Parte de Geração
    if input("\nDeseja baixar dados e gerar relatórios agora? (s/n): ").strip().lower() == 's':
        # Certifique-se que sua função main() retorna uma lista de IDs (ex: return lista_final)
        lista_para_envio = main()

    # 2. Parte de E-mail
    print("\n" + "="*110)
    print("="*20 + " "*24 + " 📧 ENVIO DE EMAILS 📧 " + " "*23 + "="*20)
    print("="*110)
    
    if input("\nDeseja iniciar o envio dos e-mails agora? (s/n): ").strip().lower() == 's':
        from enviar_email import envio_em_massa
        
        if not lista_para_envio:
            print("⚠️ Nenhuma nova vistoria foi gerada nesta sessão para enviar.")
            if input("Deseja enviar TODOS os PDFs da pasta mesmo sem novos registros? (s/n): ").strip().lower() == 's':
                envio_em_massa()  # Modo: Varre a pasta e cruza com Excel
        else:
            # Caso a lista_para_envio tenha IDs, envia apenas eles
            print(f"✅ Enviando apenas os {len(lista_para_envio)} relatórios gerados nesta sessão.")
            envio_em_massa(lista_para_envio)
    
    print("\n🏁 Processo totalmente finalizado. Pode fechar o terminal.")
