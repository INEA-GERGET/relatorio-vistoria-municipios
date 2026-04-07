import pandas as pd
import numpy as np
from pathlib import Path
import re

# --- 1. Configuração de Caminho ---
NOME_ARQUIVO_MAPA = "df_id_vstr.xlsx"
PASTA = Path(r"\\Bp-1hd57t3-inea\e\COGET\INPUTS_SCRIPTS")
CAMINHO_COMPLETO_MAPA = PASTA / NOME_ARQUIVO_MAPA
COLUNA_UNIQUE = 'uniquerowid'
COLUNA_ID = 'id_vstr'

# --- 2. Função Auxiliar para Encontrar o Próximo ID ---
def get_proximo_contador(df_id_vstr, coluna_id=COLUNA_ID, prefixo='VSTR'):
    """
    Determina o próximo número sequencial a ser usado.
    """
    # Verifica se o DataFrame é None, está vazio ou se a coluna de ID não existe
    if df_id_vstr is None or df_id_vstr.empty or coluna_id not in df_id_vstr.columns:
        return 1

    # Extrai a parte numérica de todos os IDs existentes
    ids_existentes_vstr = df_id_vstr[coluna_id].astype(str).str.extract(f'{prefixo}(\d+)', expand=False)
    
    # Converte para inteiro, ignora NaNs e encontra o máximo
    # O .fillna(0) garante que se a extração falhar, o máximo será 0
    numeros_existentes = ids_existentes_vstr.apply(pd.to_numeric, errors='coerce').fillna(0).astype(int)

    if numeros_existentes.empty:
        return 1
    
    return numeros_existentes.max() + 1


# --- 3. Função para CARREGAR o DataFrame do arquivo ---
def carregar_df_id_vstr():
    """
    Tenta carregar o DataFrame de mapeamento do arquivo XLSX.
    Retorna o DataFrame ou None se o arquivo não existir/for inválido.
    """
    if CAMINHO_COMPLETO_MAPA.is_file():
        try:
            # Força o tipo de dados da coluna ID como String/Objeto
            return pd.read_excel(CAMINHO_COMPLETO_MAPA, dtype={COLUNA_ID: str})
        except Exception as e:
            print(f"Erro ao ler o arquivo XLSX: {e}")
            return None
    else:
        print(f"Arquivo '{NOME_ARQUIVO_MAPA}' não encontrado.")
        return None

# --- 4. Função para SALVAR/CRIAR o DataFrame no arquivo ---
def salvar_df_id_vstr(df_para_salvar):
    """
    Cria a pasta arquivos_fixos (se não existir) e salva o DataFrame no arquivo XLSX.
    """
    try:
        # Cria o diretório (pasta) se ele não existir
        # parents=True cria as pastas pai, exist_ok=True evita erro se já existir
        PASTA.mkdir(parents=True, exist_ok=True)
        
        # Salva o DataFrame no formato XLSX (sem o índice do Pandas)
        df_para_salvar.to_excel(CAMINHO_COMPLETO_MAPA, index=False, sheet_name='Mapeamento VSTR')
        print(f"df_id_vstr salvo com sucesso em: {CAMINHO_COMPLETO_MAPA}")
    except Exception as e:
        print(f"ERRO ao salvar o arquivo XLSX: {e}")


# --- 5. Função Principal de Atualização (Integrada com Load/Save) ---
def atualizar_id_vstr(df_inicial, unique_coluna=COLUNA_UNIQUE, id_coluna=COLUNA_ID):
    
    # 1. Carrega o mapeamento existente
    df_id_vstr = carregar_df_id_vstr()
    
    # ** PASSO CHAVE: Inicializa df_id_vstr se ele não foi carregado **
    if df_id_vstr is None or df_id_vstr.empty:
        print("Inicializando novo df_id_vstr.")
        df_id_vstr = pd.DataFrame(columns=[unique_coluna, id_coluna])

    # 2. Junção (Merge) para trazer os IDs existentes para o df_inicial
    df_temp = pd.merge(
        left=df_inicial, 
        right=df_id_vstr[[unique_coluna, id_coluna]], 
        on=unique_coluna, 
        how='left'
    )

    # 3. Identificar as novas entradas (onde 'id_vstr' é NaN)
    # Garante que 'Nome' seja string para comparação segura
    df_temp[unique_coluna] = df_temp[unique_coluna].astype(str)
    novas_entradas = df_temp[df_temp[id_coluna].isna()].copy()
    
    # Se não houver novas entradas, retorna e não salva
    if novas_entradas.empty:
        #print("Nenhuma nova entrada. df_id_vstr não foi modificado.")
        return df_id_vstr

    # 4. Determinar o próximo contador (Baseado no df_id_vstr carregado/criado)
    proximo_contador = get_proximo_contador(df_id_vstr)
    
    # 5. Gerar IDs sequenciais para as novas entradas
    prefixo = 'VSTR'
    novos_ids = []
    
    for _ in range(len(novas_entradas)):
        novo_id = f"{prefixo}{proximo_contador:06d}" 
        novos_ids.append(novo_id)
        proximo_contador += 1
        
    novas_entradas[id_coluna] = novos_ids
    
    # 6. Atualizar o DataFrame mestre (df_id_vstr)
    novo_mapeamento = novas_entradas[[unique_coluna, id_coluna]].copy()
    
    df_id_vstr = pd.concat([df_id_vstr, novo_mapeamento], ignore_index=True)
    
    # 7. Salvar o arquivo XLSX
    salvar_df_id_vstr(df_id_vstr)
    
    return df_id_vstr.reset_index(drop=True)
