import geobr
import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
import os
import string
import math
from shapely.geometry import Point
# Importação de ScaleBar corrigida e usada de forma funcional
from matplotlib_map_utils.core.scale_bar import ScaleBar, scale_bar 
from matplotlib.offsetbox import AnnotationBbox, OffsetImage
import matplotlib.image as mpimg
from pyproj import CRS, Transformer 
from matplotlib.ticker import MaxNLocator, FuncFormatter

pd.set_option('display.max_rows', None)

# --- Configurações de Caminho ---
mapa_folder = r"output\mapa"
if not os.path.exists(mapa_folder):
    os.makedirs(mapa_folder, exist_ok=True)
caminho_seta_norte_png = r"arquivos_fixos\imagens_layout\norte.png" 
COR_DESTAQUE = '#adcb56'
CODIGO_ESTADO_RJ = 33
CRS_PROJETADO_RJ = 32723 

def formatar_km(x, pos):
    """Converte o valor de metros (m) para uma string em quilômetros (km)."""
    return f'{x / 1000:.0f} km' 


def gerar_mapa_alerta(cidade_alvo, id_alerta, x_center=None, y_center=None):
    """
    Gera um mapa em dois subplots (Estado do RJ e Detalhe da Cidade),
    destacando uma cidade específica e plotando um ponto de alerta,
    com barra de escala e seta do norte.
    """

    print(f"🗺️  Gerando mapa para: {cidade_alvo} (Alerta ID: {id_alerta})")
    try:
        municipios_rj = geobr.read_municipality(code_muni=CODIGO_ESTADO_RJ, year=2020)
    except Exception as e:
        print(f"❌ 🗺️  ERRO: Não foi possível baixar dados do geobr: {e}")
        return
    
    municipios_rj['cor'] = COR_DESTAQUE # Corrigindo cor de fundo do estado para o plot geral
    municipios_rj['borda'] = 'grey'
    
    municipios_rj.loc[municipios_rj['name_muni'] == cidade_alvo, 'cor'] = COR_DESTAQUE
    municipios_rj.loc[municipios_rj['name_muni'] == cidade_alvo, 'borda'] = 'black'

    municipio_selecionado_geo = municipios_rj[municipios_rj['name_muni'] == cidade_alvo]

    if municipio_selecionado_geo.empty:
        print(f"⚠️ 🗺️  AVISO: O município '{cidade_alvo}' não foi encontrado no geobr. Pulando.")
        return
        
    # --- Reprojeção para o Detalhe da Cidade (Subplot 2) ---
    municipio_selecionado_proj = municipio_selecionado_geo.to_crs(epsg=CRS_PROJETADO_RJ)

    # Reprojeção do Ponto de Alerta (Coordenadas)
    ponto_valido = False
    x_center_proj, y_center_proj = None, None
    if x_center is not None and y_center is not None:
        try:
            if not pd.isna(x_center) and not pd.isna(y_center):
                transformer = Transformer.from_crs(CRS("EPSG:4674"), CRS(f"EPSG:{CRS_PROJETADO_RJ}"), always_xy=True)
                x_center_proj, y_center_proj = transformer.transform(x_center, y_center)
                ponto_valido = True
        except TypeError:
            pass 
    
    # 4. Criar o Plot com Subplots e Tamanho Fixo
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 8), gridspec_kw={'width_ratios': [1, 1], 'wspace': 0.1})
    
    # --- Subplot 1: Mapa do Estado com Destaque (CRS Geográfico) ---
    municipios_rj.plot(ax=ax1, color=municipios_rj['cor'], edgecolor=municipios_rj['borda'], linewidth=0.5)
    municipio_selecionado_geo.plot(ax=ax1, color=COR_DESTAQUE, edgecolor='black', linewidth=1.5, zorder=2)
    ax1.set_title('Estado do Rio de Janeiro', fontsize=22)
    ax1.set_axis_off() 

    # --- Subplot 2: Detalhe da Cidade Selecionada (CRS Projetado em Metros) ---
    municipio_selecionado_proj.plot(ax=ax2, color=COR_DESTAQUE, edgecolor='black', linewidth=1.5)

    if ponto_valido:
        # Plotar o PONTO REPROJETADO
        ax2.plot(x_center_proj, y_center_proj, 
                  marker='o', 
                  color='red', 
                  markersize=8, 
                  zorder=11, 
                  label='Ponto de Alerta')
        
        # --- AJUSTE DE LIMITES DE VISUALIZAÇÃO (ZOOM) ---
        minx, miny, maxx, maxy = municipio_selecionado_proj.total_bounds
        margin_x = (maxx - minx) * 0.10 
        margin_y = (maxy - miny) * 0.10
        
        ax2.set_xlim(minx - margin_x, maxx + margin_x)
        ax2.set_ylim(miny - margin_y, maxy + margin_y)
    else:
        print(f"⚠️ 🗺️  AVISO: Coordenadas ausentes para {cidade_alvo} (ID {id_alerta}). Plotando mapa sem ponto.")
    
    # --- Barra de Escala (Usando Matplotlib-Map-Utils) ---
    scale_bar(ax2, location="lower left", style="ticks", 
              bar={"projection": municipio_selecionado_proj.crs},
              units={"loc": "bar", "fontsize": 12})

    # Aplica o formatador de KM para os eixos X e Y
    ax2.xaxis.set_major_formatter(FuncFormatter(formatar_km))
    ax2.yaxis.set_major_formatter(FuncFormatter(formatar_km))
    
    # Reduz o número de ticks (pontos/rótulos)
    ax2.xaxis.set_major_locator(MaxNLocator(nbins=4)) 
    ax2.yaxis.set_major_locator(MaxNLocator(nbins=3))
    

    plt.setp(ax2.get_yticklabels(), rotation=90, va="center_baseline", ha='left', rotation_mode="anchor")
    ax2.set_xlabel('Leste', fontsize=14)
    ax2.set_ylabel('Norte', fontsize=14)
    
    # Aumenta o tamanho da fonte dos rótulos dos ticks (os números)
    ax2.tick_params(axis='both', which='major', labelsize=12)
    
    # Adiciona a grade
    ax2.grid(True, linestyle='--', alpha=0.6)
    
    # --- ADIÇÃO: Seta do Norte (Usando 'norte.png') ---
    if os.path.exists(caminho_seta_norte_png):
        try:
            img_seta = mpimg.imread(caminho_seta_norte_png)
            imagebox = OffsetImage(img_seta, zoom=0.15) 
            
            # Posição: Canto Superior Direito
            ab = AnnotationBbox(imagebox, xy=(0.9, 0.9), xycoords='axes fraction', frameon=False)
            ax2.add_artist(ab)
        except Exception as e:
            print(f"ERRO: Não foi possível carregar a imagem da seta do norte: {e}. Usando 'N' de texto.")
            # Fallback para texto
            ax2.text(0.9, 0.9, 'N', transform=ax2.transAxes, fontsize=24, va='center', ha='center', color='black',
                     bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="black", lw=1))
            
    # 6. Configurações e Título de Saída
    ax2.set_title(f'Município de {cidade_alvo}\nAlerta: {id_alerta}', fontsize=16)
    ax2.set_aspect('equal', adjustable='box')

    # 7. Salvar a figura
    nome_arquivo = f"mapa_{cidade_alvo.replace(' ', '_')}_{id_alerta}.png"

    plt.tight_layout()
    plt.savefig(os.path.join(mapa_folder, nome_arquivo), dpi=200)
    #plt.show()

    print(f"✨ 🗺️  Sucesso! Arquivo salvo como: {nome_arquivo}")
