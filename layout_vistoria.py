import geopandas as gpd
import matplotlib.pyplot as plt
import os
import contextily as ctx
import pandas as pd
from reportlab.lib.pagesizes import A4, A3
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.styles import ParagraphStyle
from PIL import Image as PILImage
from reportlab.platypus import PageBreak
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.units import cm
import logging
import traceback
import configparser
from gerar_mapa import gerar_mapa_alerta
from reportlab.pdfgen import canvas 
import string
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Evita avisos de downcasting do pandas
pd.set_option('future.no_silent_downcasting', True) 

# --- Configuração Básica e Variáveis ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Caminhos dos arquivos de dados (Ajuste conforme necessário)
CSV_FOLDER = r"input\CSVs"
# O arquivo de configuração é mantido para usar a seção [EMAIL] DEFAULT_RECIPIENT se necessário (para nomear o PDF)
config_path = os.path.join('config', "config.ini")
config = configparser.ConfigParser()
config.read(config_path)


def create_pdf_for_idtxt(camada_linha, linha_link, repeat_rl_fotografico_linha, auto_const_linha,
                         assinaturas_linha, notificacao_linha, medida_cautelar_linha,
                         cntd, mapa, cidade, id_vistoria, idtxt):
    
    # --- Configuração Inicial ---
    logo_olho_no_verde_caminho = r"arquivos_fixos\imagens_layout\Logo_Olho_no_Verde_Branca.png"
    imagem_cbc1 = r"arquivos_fixos\imagens_layout\cbc1.jpg"
    imagem_cbc2 = r"arquivos_fixos\imagens_layout\cbc2.jpg"
    layout_folder = r"output\relatorios"
    os.makedirs(layout_folder, exist_ok=True)

    styles = getSampleStyleSheet()

    # 1. Defina os caminhos para os arquivos da fonte
    FONT_PATH_REGULAR = r'arquivos_fixos\fonte\Helvetica.ttf'
    FONT_PATH_BOLD = r'arquivos_fixos\fonte\Helvetica-Bold.ttf'

    # 2. Registre as fontes TTF no ReportLab
    pdfmetrics.registerFont(TTFont('Helvetica', FONT_PATH_REGULAR))
    pdfmetrics.registerFont(TTFont('Helvetica-Bold', FONT_PATH_BOLD))

    styles.add(ParagraphStyle(name='Titulo',
                                parent=styles['Normal'],
                                fontName='Helvetica-Bold',
                                fontSize=20,
                                alignment=TA_CENTER, 
                                spaceAfter=0.5 * cm,
                                textColor=HexColor("#000000")))
    
    styles.add(ParagraphStyle(name='Titulo2',
                                parent=styles['Normal'],
                                fontName='Helvetica-Bold',
                                fontSize=16,
                                alignment=TA_LEFT, 
                                spaceAfter=1 * cm,
                                textColor=HexColor("#000000")))
    
    styles.add(ParagraphStyle(name='Subtitulo',
                                parent=styles['Normal'],
                                fontName='Helvetica',
                                fontSize=10,
                                alignment=TA_CENTER, 
                                spaceAfter=0.5 * cm,
                                textColor=HexColor("#000000")))
    
    styles.add(ParagraphStyle(name='CorpoTexto',
                                parent=styles['Normal'],
                                fontName='Helvetica',
                                fontSize=12,
                                alignment=TA_JUSTIFY, 
                                spaceAfter=0.5 * cm,
                                textColor=HexColor("#000000")))

    styles.add(ParagraphStyle(name='Legenda',
                            parent=styles['Normal'],
                            fontName='Helvetica',
                            fontSize=12,
                            alignment=TA_CENTER, 
                            spaceAfter=0.5 * cm,
                            textColor=HexColor("#000000")))
    
      
    # Cria o nome do arquivo PDF
    pdf_file = os.path.join(layout_folder, f"Relatorio_vistoria_ONV_{idtxt}_{mapa}.pdf")
    
    # Define uma margem inferior maior para o rodapé
    doc = SimpleDocTemplate(pdf_file, pagesize=A4, leftMargin=1.5 * cm, rightMargin=1.5 * cm,
                            topMargin=1.5 * cm, bottomMargin=2.5 * cm)
    
    # As colunas são 'uniquerowid' e 'id_vstr'.
    unique_coluna = 'uniquerowid'
    id_coluna = 'id_vstr'
    
    # 1. Obter a chave de junção do DataFrame da linha atual
    current_uniquerowid = camada_linha[unique_coluna].iloc[0]

    # 2. Filtrar o DataFrame de mapeamento completo (id_vistoria) para obter o ID específico
    specific_id_vstr_df = id_vistoria[id_vistoria[unique_coluna] == current_uniquerowid][id_coluna]
    
    id_vstr_for_report = "sem código" # Valor padrão caso não encontre
    if not specific_id_vstr_df.empty:
        id_vstr_for_report = str(specific_id_vstr_df.iloc[0]) 

    # --- Funções Auxiliares Internas ---
    
    # Modifique a função addPageNumber para incluir o texto no rodapé (PASSO 2)
    def addPageNumber(canvas, doc):
        canvas.saveState()
        # Define a fonte e o tamanho
        canvas.setFont('Helvetica', 10)
        
        # --- LÓGICA EXISTENTE: PÁGINA (Canto Inferior Direito) ---
        page_num = canvas.getPageNumber()
        text_page = f"Página {page_num}"
        
        # Posição: 1 cm da margem direita (A4[0] - cm) e 1.5 cm do fundo
        x_position_right = A4[0] - cm 
        y_position = 1.5 * cm 
        
        # Desenha a string no canto inferior direito
        canvas.drawRightString(x_position_right, y_position, text_page)
        
        # --- NOVA LÓGICA: RELATÓRIO DE VISTORIA (Canto Inferior Esquerdo) ---
        report_text = f"Relatório {id_vstr_for_report}"

        # Posição: 1.5 cm da margem esquerda e 1.5 cm do fundo (mesma altura)
        # 1.5 * cm é o valor da margem esquerda definida em doc.build
        x_position_left = 1.5 * cm 
        
        # Desenha a string no canto inferior esquerdo
        canvas.drawString(x_position_left, y_position, report_text)
        
        canvas.restoreState()
    
    def clean_data(data):
        # Remove linhas e colunas totalmente vazias
        data = data.dropna(how='all')
        
        return data
    
    def add_table_with_split(data, title, qtd_colunas, col_widths_percent=None):
        data = pd.DataFrame(data)
        try:
            data = clean_data(data)
        except Exception:
            return

        if data.empty:
            return

        elements.append(Paragraph(title, styles['Titulo2']))
        columns = data.columns.tolist()
        num_tables = (len(columns) + qtd_colunas - 1) // qtd_colunas

        for i in range(num_tables):
            start_col = i * qtd_colunas
            end_col = min(start_col + qtd_colunas, len(columns))
            sub_data = data.iloc[:, start_col:end_col]
            sub_data = clean_data(sub_data)
            if sub_data.empty:
                continue
            table_data = [sub_data.columns.tolist()]
            custom_style = ParagraphStyle(name='CustomStyle', parent=styles['CorpoTexto'], fontSize=12, alignment=TA_CENTER)
            
            for row in sub_data.values.tolist():
                new_row = []
                for cell in row:
                    cell_text = str(cell)
                    new_row.append(Paragraph(cell_text, custom_style))
                table_data.append(new_row)
            
            if col_widths_percent and len(col_widths_percent) == len(sub_data.columns):
                largura_total = A4[0] - 2 * cm
                colWidths = [largura_total * (p/100) for p in col_widths_percent]
            else:
                colWidths = (A4[0] - 2 * cm) / len(sub_data.columns)
            
            sub_table = Table(table_data, colWidths=colWidths)

            style = [
                ('BACKGROUND', (0, 0), (-1, 0), HexColor("#adcb56")),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('GRID', (0, 0), (-1, -1), 0.5, HexColor("#88a529")),
                ('FONTSIZE', (0, 0), (-1, -1), 12),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('vAlign', (0, 0), (-1, -1), 'MIDDLE'),
            ]

            sub_table.setStyle(TableStyle(style))
            elements.append(sub_table)
            #elements.append(Spacer(1, 0.5 * cm))


    def add_table_without_space(data, qtd_colunas, col_widths_percent=None):
        data = pd.DataFrame(data)
        try:
            data = clean_data(data)
        except Exception:
            return

        if data.empty:
            return

        columns = data.columns.tolist()
        num_tables = (len(columns) + qtd_colunas - 1) // qtd_colunas

        for i in range(num_tables):
            start_col = i * qtd_colunas
            end_col = min(start_col + qtd_colunas, len(columns))
            sub_data = data.iloc[:, start_col:end_col]
            sub_data = clean_data(sub_data)
            if sub_data.empty:
                continue
            table_data = [sub_data.columns.tolist()]
            custom_style = ParagraphStyle(name='CustomStyle', parent=styles['CorpoTexto'], fontSize=12, alignment=TA_CENTER)
            
            for row in sub_data.values.tolist():
                new_row = []
                for cell in row:
                    cell_text = str(cell)
                    new_row.append(Paragraph(cell_text, custom_style))
                table_data.append(new_row)
            
            if col_widths_percent and len(col_widths_percent) == len(sub_data.columns):
                largura_total = A4[0] - 2 * cm
                colWidths = [largura_total * (p/100) for p in col_widths_percent]
            else:
                colWidths = (A4[0] - 2 * cm) / len(sub_data.columns)
            
            sub_table = Table(table_data, colWidths=colWidths)

            style = [
                ('BACKGROUND', (0, 0), (-1, 0), HexColor("#adcb56")),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('GRID', (0, 0), (-1, -1), 0.5, HexColor("#88a529")),
                ('FONTSIZE', (0, 0), (-1, -1), 12),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('vAlign', (0, 0), (-1, -1), 'MIDDLE'),
            ]


            sub_table.setStyle(TableStyle(style))
            elements.append(sub_table)


    def add_merged_table(df, merged_col_text, data_col_name, merged_col_name,
                        header_data_col, header_merged_col, col_widths_percent):
        # 1. PREPARAÇÃO DOS DADOS E ESTILOS
        
        # Assumindo que 'styles' e outras dependências globais (ParagraphStyle, TA_CENTER, etc.)
        # estejam definidas no escopo (Importe-as, se necessário: from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle; from reportlab.lib.enums import TA_CENTER, TA_LEFT)
        
        style_center = ParagraphStyle(name='CenterStyle', parent=styles['CorpoTexto'], fontSize=12, alignment=TA_CENTER)
        style_left = ParagraphStyle(name='LeftStyle', parent=styles['CorpoTexto'], fontSize=12, alignment=TA_LEFT)
        
        # Inicializa table_data com a linha de cabeçalho
        table_data = [[header_merged_col, header_data_col]] # Inverte a ordem das colunas para mesclar a primeira
        
        num_rows = len(df)
        
        # O conteúdo da célula que será mesclada (Paragraph)
        merged_cell = Paragraph(str(merged_col_text), style_center)

        # 2. CRIAÇÃO DAS LINHAS
        
        # Primeira Linha de Dados (Índice 1): Contém o texto mesclado e o 1º valor da coluna de dados
        first_data_value = df[data_col_name].iloc[0]
        table_data.append([
            merged_cell, 
            Paragraph(str(first_data_value), style_left)
        ])
        
        # Linhas Subsequentes: Contêm uma célula vazia (placeholder para a mesclagem) 
        # e os valores restantes.
        for i in range(1, num_rows):
            data_value = df[data_col_name].iloc[i]
            table_data.append([
                "", # Célula que será mesclada (vazia após a primeira linha)
                Paragraph(str(data_value), style_left)
            ])
                
        # 3. LARGURAS DAS COLUNAS
        # Ajuste para garantir que A4 e cm estejam acessíveis (Ex: from reportlab.lib.pagesizes import A4; from reportlab.lib.units import cm)
        largura_total = A4[0] - 2 * cm
        colWidths = [largura_total * (p/100) for p in col_widths_percent]

        # 4. CRIAÇÃO DA TABELA
        sub_table = Table(table_data, colWidths=colWidths)

        # 5. ESTILO E MESCLAGEM VERTICAL
        style = [
            # Cabeçalho
            ('BACKGROUND', (0, 0), (-1, 0), HexColor("#adcb56")),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            
            # MESCLAGEM VERTICAL: Coluna 0 (que é 'merged_col_name'), da linha 1 até a última linha de dados.
            # (coluna_inicio, linha_inicio) até (coluna_fim, linha_fim)
            ('SPAN', (0, 1), (0, num_rows)), 
            
            # Alinhamento da Célula Mesclada (Vertical e Horizontal)
            ('VALIGN', (0, 1), (0, num_rows), 'MIDDLE'),
            ('ALIGN', (0, 1), (0, num_rows), 'CENTER'),
            
            # Estilo Geral
            ('GRID', (0, 0), (-1, -1), 0.5, HexColor("#88a529")),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
        ]

        sub_table.setStyle(TableStyle(style))
        elements.append(sub_table)
        return sub_table

    def calculate_proportional_dimensions(image_path, max_width_cm):
        '''
        Calcula a largura e altura da imagem para manter a proporção original,
        limitando a largura ao valor especificado.
        
        Argumentos:
            image_path (str): Caminho completo para o arquivo de imagem.
            max_width_cm (float): Largura máxima desejada em centímetros.
            
        Retorna:
            tuple: (largura_ajustada_cm, altura_ajustada_cm) ou (None, None) se falhar.
        '''
        try:
            if not os.path.exists(image_path):
                logging.error(f"Arquivo de imagem não encontrado: {image_path}")
                return None, None
                
            # 1. Obter dimensões originais da imagem
            img_pil = PILImage.open(image_path)
            largura_original, altura_original = img_pil.size
            proporcao = altura_original / largura_original

            # 2. Definir a largura máxima no ReportLab
            largura_max_rl = max_width_cm * cm
            
            # 3. Calcular a altura proporcional em ReportLab units (cm * proporcao)
            altura_calculada_rl = largura_max_rl * proporcao

            # Retornar em unidades do ReportLab (para uso direto em img.drawWidth/drawHeight)
            return largura_max_rl, altura_calculada_rl

        except Exception as e:
            logging.error(f"Erro ao calcular dimensões proporcionais para {image_path}: {e}")
            return None, None

    # --- Preparação dos Dados (Mantendo a Renomeação Original) --
    
    notificacao_linha = notificacao_linha.rename(columns={'disp_legais_not': 'Artigos infrigidos da Lei 3.467/2000 - vazio', 'index_not':'Notificação', 'enquadramento_not': 'Enquadramento legal', 'enquadramento1_not': 'Artigos infrigidos da Lei 3.467/2000', 

                                                         'enquadramento2_not': 'Artigos da Lei 3.467/2000 relacionados à temas gerais', 'enquadramento3_not': 'Outros artigos da Lei 3.467/2000', 
                                                         'lei_not': 'O município utiliza legislação estadual 3.467/2000 ou alguma outra legislação?', 
                                                         'n_notificacao': 'Código', 'outra_lei_not': 'Outros'})
    auto_constatacao_linha = auto_const_linha.rename(columns={'index_infra':'Auto','n_auto_const': 'Código', 'disp_legais_const': 'Artigos infrigidos da Lei 3.467/2000', 'enquadramento_const': 'Enquadramento legal', 
                                                       'lei_const': 'O município utiliza legislação estadual 3.467/2000 ou alguma outra legislação?', 'enquadramento2_const': 'Artigos da Lei 3.467/2000 relacionados à temas gerais', 
                                                       'outra_lei_const': 'Outros', 'enquadramento1_const': 'Artigos infrigidos da Lei 3.467/2000', 'enquadramento3_const': 'Outros artigos da Lei 3.467/2000'})
    medida_cautelar_linha = medida_cautelar_linha.rename(columns={'num_cautelar': 'Código', 'index_mc':'Medida cautelar', 'disp_legais_mc': 'Artigos infrigidos da Lei 3.467/2000', 'enquadramento_mc': 'Enquadramento legal', 
                                                                 'lei_mc': 'O município utiliza legislação estadual 3.467/2000 ou alguma outra legislação?', 
                                                                 'enquadramento2_mc': 'Artigos da Lei 3.467/2000 relacionados à temas gerais', 'outra_lei_mc': 'Outros', 
                                                                 'enquadramento1_mc': 'Artigos infrigidos da Lei 3.467/2000', 'enquadramento3_mc': 'Outros artigos da Lei 3.467/2000', 'tipo_mc': 'Tipo da Medida'}) 
    nomes_das_colunas= {'obs': 'Observação', 'telefone': 'Telefone', 'sig_risc_saude_pop': 'Risco a saúde da população', 'descritivo': 'Descritivo da inspeção', 'id_fiscalizacao': 'ID Fiscalização',
                        'id': 'ID do Alerta', 'detalhe': 'Justificativa', 'bairro': 'Bairro', 'fonte': 'Fonte', 'municipio_imovel': 'Município do imóvel',
                        'conclusao': 'Conclusão', 'tipo_apoio': 'Tipo de apoio', 'necess_apoio': 'Necessário apoio', 'status': 'Status do alerta', 'confirmacao_uc': 'Confirma interseção com UC?', 
                        'cep': 'CEP', 'data_fisc': 'Data da fiscalização', 'num_rv': 'N° do RV', 'fonte': 'Fonte', 'status_1':'Status',
                        'objetivo': 'Objetivo e ações', 'fisico_juridico': 'Pessoa física ou jurídica', 'rel_motiv': 'Relação de motivos', 
                        'ato_admnist': 'Tipo de Ato Adm.', 'car_sim_nao': 'Há CAR', 'responsavel': 'Nome do responsável', 'placa': 'Colocada a placa?', 
                        'quant_auto': 'Quantidade de autos de constatação', 'permanencia': 'Prazo de permanência', 'distribuicao_dano': 'Distributividade do dano', 
                        'outra_infracao': 'Houve outra infração associada?', 'agenda2': 'Classificação', 'nota01': 'Agravantes','id_alerta': 'ID do alerta',
                        'id_car': 'Número de registro do CAR', 'area_ha': 'Área (ha)', 
                        'agenda': 'Classificação (categoria)', 'acesso':'Nome da propriedade',
                        'nota03': 'Atenuantes', 'nota02': 'Agente cometido infração', 'quant_notificacao': 'Quantidade de notificações', 'pras': 'Número/código da notificação de recuperação ambiental',
                        'quant_mc': 'Quantidade de medidas cautelares','teste': 'Teste', 'telefone_resp': 'Telefone do responsável', 'confirmacao_app': 'Confirma interseção com APP?',
                        'nome_rzsocial': 'Nome ou razão social', 'data': 'Data da fiscalização1', 'muni': 'Município responsável pelo atendimento',
                        'num_asv': 'Número da autorização', 'multi_propri': 'Proprietário',
                        'email_resp': 'E-mail do responsável', 'cpf': 'CPF', 'cnpj': 'CNPJ', 'muni_corresp': 'Município de correspondência',
                        'autorizacao': 'Apresentou autorização?', 'sup_irreg': 'Atestada supressão irregular?','chave_acesso': 'Chave de acesso fornecida',
                        'categ_denu2': 'Categoria da infração', 'endereco_imovel': 'Endereço do imóvel e descrição de acesso', 'cpf_respon': 'CPF do responsável',
                        'atividade': 'Atividade', 'motiv_mc': 'Categorização ambiental do dano', 'nome_operacao': 'Nome da operação', 'telefone_cad_car': 'Telefone', 
                        'sub_cat2': 'Sub. Categoria', 'processo_origem': 'Processo SEI', 'infracao': 'Infrações observadas', 'relevancia': 'Relevância', 'cpf_cnpj': 'CPF/CNPJ', 
                        'modo_atend': 'Forma de atendimento', 'reversibilidade': 'Reversibilidade', 'area_m2': 'Área (m²)', 'data_refer': 'Data de referência', 'email_cad_car': 'Email',
                        'prasn': 'O proprietário foi notificado à aderir à recuperação ambiental do dano?', 'emissao_ato': 'Emissão de Ato Adm.', 'municip_imvl': 'Município de localização do imóvel',
                        'categoria_denuncia': 'Categoria da infração', 'endereco': 'Endereço', 'orgao_apoio': 'Instituição de apoio', 'todos_enquadramentos': 'Todos os enquadramentos', 
                        'endereco_corresp': 'Endereço para correspondência', 'data_atual': 'Data atual', 'ente': 'Ente', 'data_rv': 'Data', 'equipe': 'Equipe', 'sub_cat_denuncia': 'Sub. categoria', 'objectid': 'Id do objeto',
                        'uc_federal': 'Interseção com UC federal', 'uc_municip': 'Interseção com UC municipal', 'apps': 'Interseção com APPs', 'uc_estadua': 'Interseção com UC estadual',
                        'distribuicao_dano': 'Distribuição do dano', 'permanencia': 'Permanência', 'reversibilidade': 'Reversibilidade', 'relevancia': 'Relevância', 'centro_x':'Latitude (centro)', 'centro_y':'Longitude (centro)'}
    

    
    camada_linha = camada_linha.rename(columns=nomes_das_colunas)
    linha_link = linha_link.rename(columns=nomes_das_colunas)
    assinaturas_linha = assinaturas_linha.rename(columns={'email_fisc01': 'Email do responsável', 'cargo_fisc01': 'Cargo', 'lotacao_fisc01': 'Lotação', 'nomes': 'Atendimento', 'id_fisc01': 'ID funcional'})
    
    linha_link['ID do Alerta'] = linha_link['ID do Alerta'].astype(str)
    mapa_info = pd.merge(
        camada_linha[['Município responsável pelo atendimento', 'ID do alerta']],
                        linha_link[['ID do Alerta','Latitude (centro)', 'Longitude (centro)']],
                         left_on='ID do alerta',      
                        right_on='ID do Alerta',
                        how='left')            
    
    # --- Construção do PDF (Elementos) ---
    elements = []

    # Seção de Cabeçalho (CBC1 e Olho No Verde)
    if os.path.exists(imagem_cbc1):
        img_cbc1 = RLImage(imagem_cbc1)
        img_cbc1.drawHeight = 4 * cm
        img_cbc1.drawWidth = 7.72 * cm
        elements.append(img_cbc1)

    if os.path.exists(logo_olho_no_verde_caminho):
        img_olho_no_verde = RLImage(logo_olho_no_verde_caminho)
        img_olho_no_verde.drawHeight = 2 * cm
        img_olho_no_verde.drawWidth = 4.88 * cm
        elements.append(img_olho_no_verde)
        elements.append(Spacer(1, 0.2 * cm))

    # Títulos
    elements.append(Paragraph(f"Relatório de Vistoria", styles['Titulo']))
    elements.append(Spacer(0, 0 * cm))

    subtitulo = "Documento automatizado gerado a partir do sistema de detecção de alertas"
    centered_style = styles['Subtitulo'].clone('CenteredStyle')
    centered_style.alignment = TA_CENTER
    elements.append(Paragraph(subtitulo, centered_style))
    elements.append(Spacer(0, 0 * cm))

    # Introdução
    introducao = """O Programa Olho no Verde realiza o monitoramento por intermédio de disponibilização sistemática e contínua de 
    produtos espectrais, fruto de uma constelação de satélites, que geram imagens de alta resolução espacial. 
    O método de aquisição das informações se dá por meio do processamento automático e semiautomático utilizando técnicas de 
    sensoriamento remoto e aprendizagem de máquina. Detectada a mudança na vegetação, a partir da comparação de imagens de diferentes datas, 
    é materializado o polígono resultante do processamento. """
    elements.append(Paragraph(introducao, styles['CorpoTexto']))
    elements.append(Spacer(1, 0.5 * cm))

    # Tabela Informações Inicias da Fiscalização     

    for index, linha_camada in camada_linha.iterrows():
        
        # 2.1. Extrair chaves de filtragem
        car_id = linha_camada['Número de registro do CAR']
        alerta_id = linha_camada['ID do alerta']
        unique_id = linha_camada['uniquerowid']
        
        # 2.2. FILTRAGEM: Criar o DataFrame de Notificações
        # Usamos o 'uniquerowid' da linha_camada para filtrar a 'notificacao_linha'
        assinatura_por_car_alerta = assinaturas_linha[
            assinaturas_linha['parentrowid'] == unique_id
        ].copy()

        dados_informacao = assinatura_por_car_alerta[['Atendimento', 'Lotação', 'Cargo', 'ID funcional']]

        objetivo = camada_linha['Objetivo e ações']
        informacoes_iniciais = camada_linha[['Município responsável pelo atendimento', 'Data da fiscalização']].copy()
        # As duas linhas abaixo são para passar a data do formato Unix Epoch para d/m/a
        informacoes_iniciais['Data da fiscalização'] = pd.to_datetime(informacoes_iniciais['Data da fiscalização'], unit = 'ms')
        informacoes_iniciais['Data da fiscalização'] = informacoes_iniciais['Data da fiscalização'].dt.strftime('%d/%m/%Y')
        # Deixa a primeira letra da cidade maiúscula (importante para a entrada do mapa)
        informacoes_iniciais['Município responsável pelo atendimento'] = informacoes_iniciais['Município responsável pelo atendimento'].str.title()

        lista_cidades_renomear = {'Aperibe':'Aperibé', 
                        'Armação Dos Buzios':'Armação Dos Búzios',
                        'Barra Do Pirai':'Barra Do Piraí',
                        'Conceicao De Macabu':'Conceição De Macabu',
                        'Itaborai':'Itaboraí',
                        'Itaguai':'Itaguaí',
                        'Laje Do Muriae':'Laje Do Muriaé',
                        'Macae':'Macaé',
                        'Mage':'Magé',
                        'Marica':'Maricá',
                        'Nilopolis':'Nilópolis',
                        'Niteroi':'Niterói',
                        'Paraiba Do Sul':'Paraíba Do Sul',
                        'Petropolis':'Petrópolis',
                        'Pirai':'Piraí',
                        'Porcincula':'Porciúncula',
                        'Quissama':'Quissamã',
                        'Santo Antonio De Padua':'Santo Antônio De Pádua',
                        'Sao Francisco De Itabapoana':'São Francisco De Itabapoana',
                        'Sao Fidelis':'São Fidélis',
                        'Sao Goncalo':'São Gonçalo',
                        'Sao Joao Da Barra':'São João Da Barra',
                        'Sao Joao De Meriti':'São João De Meriti',
                        'Sao Jose De Uba':'São José De Ubá',
                        'Sao Jose Do Vale Do Rio Preto':'São José Do Vale Do Rio Preto',
                        'Sao Pedro Da Aldeia':'São Pedro Da Aldeia',
                        'Sao Sebastiao Do Alto':'São Sebastião Do Alto',
                        'Seropedica':'Seropédica',
                        'Tangua':'Tanguá',
                        'Teresopolis':'Teresópolis',
                        'Tres Rios':'Três Rios',
                        'Valenca':'Valença',
                        'Varre Sai':'Varre-Sai'}
    
        informacoes_iniciais['Município responsável pelo atendimento'] = informacoes_iniciais['Município responsável pelo atendimento'].replace(lista_cidades_renomear)
        add_table_with_split(informacoes_iniciais, "Informações iniciais da fiscalização", 2, [50, 50])
        add_table_without_space(dados_informacao, 4, [35, 35, 15, 15])
        add_table_without_space(objetivo, 1, [100])
        elements.append(Spacer(1, 0.5 * cm))
    

    # Tabelas de Informações do Alerta 
    # Verificar o motivo de não estar aparecendo em alguns pdfs, parece que o links não aparece em alguns casos, enquanto que com a camada funciona, mas não tem o dado de fonte

    informacoes_alerta = linha_link[['ID do Alerta', 'Data de referência', 'Data atual',
                                         'Fonte', 'Área (m²)', 'Área (ha)', 'Latitude (centro)', 'Longitude (centro)']].copy()
    
    if 'Área (m²)' in informacoes_alerta.columns:
        informacoes_alerta['Área (m²)'] = informacoes_alerta['Área (m²)'].fillna('0').astype(str).str.replace(',', '.').apply(lambda x: f"{float(x):.2f}")  
    if 'Área (ha)' in informacoes_alerta.columns:
        informacoes_alerta['Área (ha)'] = informacoes_alerta['Área (ha)'].fillna('0').astype(str).str.replace(',', '.').apply(lambda x: f"{float(x):.2f}")      
    
    #id_df = pd.DataFrame({'ID do Alerta': idtxt}, index=[0])
    #add_table_with_split(id_df, "Informações do alerta", 1, [100])
    add_table_with_split(informacoes_alerta, "Informações do alerta", 3, [33, 33, 34])


    # Tabela de Interseção com UC e APP (junto com a tabela anterior, sem espaçamento)

    intersecao_uc = camada_linha[['Interseção com UC federal', 'Interseção com UC estadual', 'Interseção com UC municipal']].T.reset_index()
    intersecao_uc.columns = ['Tipo de UC', 'Faz interseção?']
    intersecao_uc['Faz interseção?'] = intersecao_uc['Faz interseção?'].replace('NAO FAZ INTERSECAO', 'Não faz interseção')
    add_table_without_space(intersecao_uc, 3, [33.3, 33.3, 33.4])
    intersecao_app = camada_linha[['Interseção com APPs', 'Confirma interseção com APP?']].copy()
    intersecao_app['Interseção com APPs'] = intersecao_app['Interseção com APPs'].replace('NAO FAZ INTERSECAO', 'Não faz interseção')
    intersecao_app['Confirma interseção com APP?'] = intersecao_app['Confirma interseção com APP?'].fillna('Não respondido')
    add_table_without_space(intersecao_app, 2, [50, 50])
    elements.append(Spacer(1, 0.5 * cm))


    # Tabela de Informações do CAR
 
    # Verificação mais rigorosa (ignora strings vazias ou NaN)
    numero_car = camada_linha['Número de registro do CAR'].iloc[0]
    if pd.notna(numero_car) and str(numero_car).strip() != "":
        print(f"✅ CAR encontrado para o alerta {idtxt}: {numero_car}")
        informacoes_CAR = camada_linha[['Número de registro do CAR']].copy()
        add_table_with_split(informacoes_CAR, "Dados do CAR", 1, [100])
        info_propri = camada_linha['Proprietário']
        add_table_without_space(info_propri, 1, [100])
        informacoes_CAR2 = camada_linha[['Nome da propriedade']].copy()
        add_table_without_space(informacoes_CAR2, 1, [100])
        informacoes_CAR3 = camada_linha[['Município de localização do imóvel']].copy()
        informacoes_CAR3['Município de localização do imóvel'] = informacoes_CAR3['Município de localização do imóvel'].replace(lista_cidades_renomear)
        add_table_without_space(informacoes_CAR3, 1, [100])
        elements.append(Spacer(1, 0.5 * cm))
    else:
        print(f"⚠️    Alerta {idtxt} sem número de CAR válido. Pulando tabela CAR.")


    # Informações da Fiscalização
    elements.append(Paragraph("Informações do local da fiscalização", styles['Titulo']))
    elements.append(Spacer(1, 1 * cm))

    # Cria o mapa Estado - cidade - alerta
    mapa_info['Longitude (centro)'] = mapa_info['Longitude (centro)'].astype(str).str.replace(',', '.', regex=True).astype(float)
    mapa_info['Latitude (centro)'] = mapa_info['Latitude (centro)'].astype(str).str.replace(',', '.', regex=True).astype(float)

    for index, row in mapa_info.iterrows():
        
        # 1. Obter valores da linha atual
        cidade = str(row['Município responsável pelo atendimento'])
        longitude = row['Longitude (centro)'] 
        latitude = row['Latitude (centro)'] 
        id_alerta = str(row['ID do Alerta'])
        
        # --- LÓGICA DE NORMALIZAÇÃO SIMPLIFICADA (CORREÇÃO) ---
        # Capitaliza a string
        cidade_normalizada = string.capwords(cidade)
        
        # Obtém o nome final. Se 'cidade_normalizada' estiver no dicionário, usa o valor
        # Se não estiver, usa 'cidade_normalizada' como fallback.
        cidade_final_str = lista_cidades_renomear.get(cidade_normalizada, cidade_normalizada)
        
        # --- FIM DA LÓGICA DE NORMALIZAÇÃO ---
        
        # Usa cidade_final_str para criar o caminho e para a lógica
        mapa_localizacao = f"output\\mapa\\mapa_{cidade_final_str.replace(' ', '_')}_{id_alerta}.png"
        
        if os.path.exists(mapa_localizacao):
                print(f"😎 🗺️  Mapa {cidade_final_str} (ID {id_alerta}).png já existe")
        else: 
            # Agora o .lower() é chamado em uma string
            if cidade_final_str.lower() in ['nan', 'none']:
                print(f"⚠️ 🗺️  AVISO: Pulando registro {index} devido a nome de município ausente (ID {id_alerta}).")
                continue        
            try:
                # Passa a string correta para a função
                gerar_mapa_alerta(cidade_final_str, idtxt, longitude, latitude)
            except Exception as e:
                print(f"❌ 🗺️  ERRO ao gerar mapa para {cidade_final_str} (ID {id_alerta}): {e}")
        

    # Imagem do Mapa Estado - cidade
    png_ilustrativo1 = f"output\\mapa\\mapa_{cidade_final_str.replace(' ', '_')}_{id_alerta}.png"
    if os.path.exists(png_ilustrativo1):
        img = RLImage(png_ilustrativo1)
        img.drawHeight = 12 * cm
        img.drawWidth = 22 * cm
        elements.append(img)
        elements.append(Spacer(1.5, 0.5 * cm))

    # Imagem do Mapa
    png_ilustrativo = f"input\\pontos\\ponto_{mapa}.png"
    if os.path.exists(png_ilustrativo):
        img = RLImage(png_ilustrativo)
        img.drawHeight = 9 * cm
        img.drawWidth = 9 * cm
        elements.append(img)
        elements.append(Spacer(1.5, 0.5 * cm))
    
    # Links
    link_imagemAD = linha_link['ant_dep'].astype(str).tolist()
    link_poligono = linha_link['link_kml'].astype(str).tolist()
    if link_imagemAD:
        elements.append(Paragraph(f"Link para imagens de antes e depois: {link_imagemAD}", styles['CorpoTexto']))
        elements.append(Spacer(0.5, 0.5 * cm))
    if link_poligono:
        elements.append(Paragraph(f"Link para o polígono georeferenciado: {link_poligono}", styles['CorpoTexto']))
        elements.append(Spacer(1.5, 0.5 * cm))

    # Tabela Informações da Fiscalização
    elements.append(Paragraph('Informações sobre a fiscalização', styles['Titulo']))
    elements.append(Spacer(1, 0.5 * cm))
    informacoes_processo = camada_linha[['Processo SEI']]
    add_table_without_space(informacoes_processo, 1, [100])
    informacoes_processo0 = camada_linha[['N° do RV']]
    add_table_without_space(informacoes_processo0, 1, [100])
    status = camada_linha['Status do alerta']
    status_series = pd.Series(status, dtype="category")
    lista_status = {'NFPV': 'Não foi possível vistoriar', 'atendido': 'Vistoriado'}
    status_renomeado = status_series.cat.rename_categories(lista_status)
    status = pd.DataFrame(status_renomeado, columns=['Status do alerta'])
    add_table_without_space(status, 1, [100])
    justificativa = camada_linha['Justificativa']
    add_table_without_space(justificativa, 1, [100])
    informacoes_processo1 = camada_linha[['Nome da operação', 'Colocada a placa?', 'Forma de atendimento',
                                          'Necessário apoio', 'Tipo de apoio', 'Instituição de apoio']].copy()
    informacoes_processo1 = informacoes_processo1.fillna('Não se aplica')
    add_table_without_space(informacoes_processo1, 3, [40, 30, 30])
    informacoes_processo2 = camada_linha[['Atestada supressão irregular?']].copy()
    add_table_without_space(informacoes_processo2, 1, [100])
    informacao_autorizacao = camada_linha[['Apresentou autorização?', 'Número da autorização']].copy()
    informacao_autorizacao['Número da autorização'] = informacao_autorizacao['Número da autorização'].str.title()
    if 'Apresentou autorização?' in informacao_autorizacao.columns:
        informacao_autorizacao['Apresentou autorização?'] = informacao_autorizacao['Apresentou autorização?'].fillna('Não').astype(str)     
    if 'Número da autorização' in informacao_autorizacao.columns:
        informacao_autorizacao['Número da autorização'] = informacao_autorizacao['Número da autorização'].fillna('Não se aplica').astype(str)     
    add_table_without_space(informacao_autorizacao, 2, [40, 60])
    informacoes_processo3 = camada_linha[['Infrações observadas']].copy()
    add_table_without_space(informacoes_processo3, 1, [100])

    # Adiciona Categoria e Subcategorias da Infração (usando a nova função)

    if 'Sub. categoria' in camada_linha.columns and pd.notna(camada_linha['Sub. categoria'].iloc[0]):
        subcategorias_str = camada_linha['Sub. categoria'].iloc[0]
        categoria = camada_linha['Categoria da infração'].iloc[0] # <--- Valor a ser mesclado
        
        lista_subcat = subcategorias_str.split(',')
        
        # Cria o DataFrame apenas com as Subcategorias e renomeias as sub. categorias
        sub_cat_DF = pd.DataFrame(lista_subcat, columns=['Sub. categoria'])
        sub_cat = sub_cat_DF['Sub. categoria']
        cat_series = pd.Series(sub_cat, dtype="category")
        lista_sub_cat = {'Unidade_de_conservacao': 'Unidade de conservação',
                         'Corte_raso':'Corte raso',
                         'outros': 'Outros',
                         'Associado_a_Coleta_de_madeira_e_ou_outros_produtos_florestais': 'Associado a Coleta de madeira e/outros produtos florestais',
                         'Corte_de_Talude': 'Corte de talude',
                         'Atividade_Agropecuária': 'Atividade agropecuária',
                         'Associado_a_Coleta_de_madeira_ou_outros_produtos_florestais': 'Associado a Coleta de madeira e/outros produtos florestais',
                         'Unidade_de_conservação': 'Unidade de conservação',
                         'Área_de_reserva_legal': 'Área de reserva legal',
                         'Área_de_preservação_permanente': 'Área de preservação permanente'}
        
        sub_cat_renomeado = cat_series.cat.rename_categories(lista_sub_cat)
        sub_cat_renomeado_DF = pd.DataFrame(sub_cat_renomeado, columns=['Sub. categoria'])
        
        # 2. Gera a Tabela Adaptada (Mesclagem Vertical) usando a nova função
        add_merged_table(
            df=sub_cat_renomeado_DF,
            merged_col_text=categoria,
            data_col_name='Sub. categoria',           # Nome da coluna no DF com os valores a serem listados
            merged_col_name='Categoria da infração',  # Nome da coluna no DF que teria o valor mesclado (apenas para referência)
            header_data_col='Sub. categoria',         # Título no cabeçalho
            header_merged_col='Categoria da Infração',# Título no cabeçalho
            col_widths_percent=[50, 50]
        )

    # Adiciona Observação
    informacao_observacao = camada_linha[['Observação']]
    add_table_without_space(informacao_observacao, 1, [100])
    elements.append(Spacer(1, 0.5 * cm))

    # Adiciona Tipo e Subtipos de Ato Administrativo 

    if 'Tipo de Ato Adm.' in camada_linha.columns and pd.notna(camada_linha['Tipo de Ato Adm.'].iloc[0]):
        tipo_ato_str = camada_linha['Tipo de Ato Adm.'].iloc[0]
        categoria = camada_linha['Emissão de Ato Adm.'].iloc[0] # <--- Valor a ser mesclado
        
        lista_tipo_ato = tipo_ato_str.split(',')
        lista_ato_renomear = {'notificacao': 'Notificação',
                              'Medida_Cautelar': 'Medida cautelar',
                              'Auto_Constatação_ou_Infração': 'Auto de constação ou infração'}
        lista_tipo_ato_series = pd.Series(lista_tipo_ato, dtype="category")
        tipo_renomeado = lista_tipo_ato_series.cat.rename_categories(lista_ato_renomear)
        sub_cat_DF = pd.DataFrame(tipo_renomeado, columns=['Tipo de Ato Adm.'])

        # 2. Gera a Tabela Adaptada (Mesclagem Vertical) usando a nova função
        elements.append(Paragraph('Ato administrativo', styles['Titulo2']))
        add_merged_table(
            df=sub_cat_DF,
            merged_col_text=categoria,
            data_col_name='Tipo de Ato Adm.',           # Nome da coluna no DF com os valores a serem listados
            merged_col_name='Emissão de Ato Adm.',  # Nome da coluna no DF que teria o valor mesclado (apenas para referência)
            header_data_col='Tipo de Ato Adm.',         # Título no cabeçalho
            header_merged_col='Emissão de Ato Adm.',# Título no cabeçalho
            col_widths_percent=[50, 50])
        elements.append(Spacer(1, 0.5 * cm))


    # Gera a tabela de notificação
    informacao_notificacao = camada_linha[['Quantidade de notificações']].copy()
    qtd_notificacoes = informacao_notificacao['Quantidade de notificações'].iloc[0]
    try:
        qtd_notificacoes = int(qtd_notificacoes)
    except ValueError:
        qtd_notificacoes = 0

    if qtd_notificacoes != 0: 
        add_table_with_split(informacao_notificacao, 'Notificação', 1, [100])
        for index, linha_camada in camada_linha.iterrows():
            
            # 2.1. Extrair chaves de filtragem
            car_id = linha_camada['Número de registro do CAR']
            alerta_id = linha_camada['ID do alerta']
            unique_id = linha_camada['uniquerowid']
            
            # 2.2. FILTRAGEM: Criar o DataFrame de Notificações
            # Usamos o 'uniquerowid' da linha_camada para filtrar a 'notificacao_linha'
            notificacao_por_car_alerta = notificacao_linha[
                notificacao_linha['parentrowid'] == unique_id].copy()
            dados_notificacao = notificacao_por_car_alerta[['Notificação', 'Código', 'Enquadramento legal']].copy()
            if 'Enquadramento legal' in dados_notificacao.columns:
                dados_notificacao['Enquadramento legal'] = dados_notificacao['Enquadramento legal'].fillna('Não se aplica').astype(str)
                
            # 2.3. Verificação de Dados
            if notificacao_por_car_alerta.empty:
                print(f"😨  Nenhuma notificação encontrada para CAR={car_id}, Alerta={alerta_id} (Parent ID: {unique_id}). Pulando...")
                continue # Pula para o próximo item do loop
            add_table_without_space(dados_notificacao, 4, [20, 20, 30, 30])
            elements.append(Spacer(1, 1 * cm))

    # Gera a tabela de auto de contastação
   
    informacao_auto_constastacao = camada_linha[['Quantidade de autos de constatação']].copy()
    qtd_auto_const = informacao_auto_constastacao['Quantidade de autos de constatação'].iloc[0]
    try:
        qtd_auto_const = int(qtd_auto_const)
    except ValueError:
        qtd_auto_const = 0

    if qtd_auto_const != 0:
        add_table_with_split(informacao_auto_constastacao, 'Auto Constatação ou Infração', 1, [100])
        for index, linha_camada in camada_linha.iterrows():
            
            # 2.1. Extrair chaves de filtragem
            car_id = linha_camada['Número de registro do CAR']
            alerta_id = linha_camada['ID do alerta']
            unique_id = linha_camada['uniquerowid']
            auto_constatacao_por_car_alerta = auto_constatacao_linha[
                auto_constatacao_linha['parentrowid'] == unique_id].copy()
            dados_auto_constatacao = auto_constatacao_por_car_alerta[['Auto','Código', 'Enquadramento legal']].copy()
            if 'Enquadramento legal' in dados_auto_constatacao.columns:
                dados_auto_constatacao['Enquadramento legal'] = dados_auto_constatacao['Enquadramento legal'].fillna('Não se aplica').astype(str)

            # 2.3. Verificação de Dados
            if auto_constatacao_por_car_alerta.empty:
                print(f"😨  Nenhum auto de constatação encontrado para CAR={car_id}, Alerta={alerta_id} (Parent ID: {unique_id}). Pulando...")
                continue # Pula para o próximo item do loop
            add_table_without_space(dados_auto_constatacao, 4, [20, 20, 30, 30])
            elements.append(Spacer(1, 1 * cm))

    # Gera a tabela de medida cautelar
    informacao_medida_cautelar = camada_linha[['Quantidade de medidas cautelares']].copy()
    qtd_medida_cautelar = informacao_medida_cautelar['Quantidade de medidas cautelares'].iloc[0]
    try:
        qtd_medida_cautelar = int(qtd_medida_cautelar)
    except ValueError:
        qtd_medida_cautelar = 0
    if qtd_medida_cautelar != 0:
        add_table_with_split(informacao_medida_cautelar, 'Medida Cautelar', 1, [100])
        for index, linha_camada in camada_linha.iterrows():

            car_id = linha_camada['Número de registro do CAR']
            alerta_id = linha_camada['ID do alerta']
            unique_id = linha_camada['uniquerowid']
            medida_cautelar_por_car_alerta = medida_cautelar_linha[
                medida_cautelar_linha['parentrowid'] == unique_id].copy()
            dados_medida_cautelar = medida_cautelar_por_car_alerta[['Medida cautelar', 'Código', 'Enquadramento legal']].copy()
            if 'Enquadramento legal' in dados_medida_cautelar.columns:
                dados_medida_cautelar['Enquadramento legal'] = dados_medida_cautelar['Enquadramento legal'].fillna('Não se aplica').astype(str)
  
            # 2.3. Verificação de Dados
            if medida_cautelar_por_car_alerta.empty:
                print(f"😨  Nenhuma medida cautelar encontrada para CAR={car_id}, Alerta={alerta_id} (Parent ID: {unique_id}). Pulando...")
                continue # Pula para o próximo item do loop
            add_table_without_space(dados_medida_cautelar, 4, [20, 20, 30, 30])
            elements.append(Spacer(1, 1 * cm))


    # Adiciona as informações do autuado, se houve emissão de Ato Adm.

    houve_ato_adm = str(camada_linha['Emissão de Ato Adm.'].iloc[0]).strip()
    if houve_ato_adm == 'Sim':

        # Escolhe o nome do proprietário a partir do nome_rz ou multi_propri
        if pd.notna(numero_car) and str(numero_car).strip() != "":
            nome_com_car = camada_linha['Proprietário'].copy()
            add_table_with_split(nome_com_car, "Dados do autuado", 1, [100])
        else:
            nome_sem_car = camada_linha['Nome ou razão social'].copy()
            add_table_with_split(nome_sem_car, "Dados do autuado", 1, [100])
        #Adiciona o restante das informações do autuado
        info_autuado = camada_linha[['CPF','CNPJ','Email', 'Telefone']].copy()
        info_autuado = camada_linha[['CPF','CNPJ','Email', 'Telefone']].copy()
        info_autuado['CPF'] = info_autuado['CPF'].fillna('Não se aplica')
        info_autuado['CNPJ'] = info_autuado['CNPJ'].fillna('Não se aplica')
        add_table_without_space(info_autuado, 2, [50, 50])
        info_end = camada_linha[['Endereço para correspondência', 'CEP', 'Município de correspondência']].copy()
        add_table_without_space(info_end, 2, [60, 40])
        info_end_imvl = camada_linha[['Endereço do imóvel e descrição de acesso','Município de localização do imóvel']]
        add_table_without_space(info_end_imvl, 1, [100])
        elements.append(Spacer(1, 0.5 * cm))



        # Adiciona Informações pelo Respnsável pelo recebimento da autuação
        msm_resp = str(camada_linha['resp_s_n'].iloc[0]).strip()
        if msm_resp == 'Não':
            informacao_recebimento = camada_linha[['Nome do responsável', 'CPF do responsável', 'E-mail do responsável', 'Telefone do responsável']].copy()
            add_table_with_split(informacao_recebimento, "Dados do responsável pelo recebimento da autuação", 2, [50, 50])
            elements.append(Spacer(1, 0.5 * cm))
        elif msm_resp == 'Sim':
            elements.append(Paragraph("Observação: A pessoa responsável pelo recebimento da autuação é a mesma autuada.", styles['Legenda']))
            elements.append(Spacer(1, 0.5 * cm))
        

    # Adiciona Informações sobre a Recuperação do dano Ambiental
    informacao_dano_amb = camada_linha[['O proprietário foi notificado à aderir à recuperação ambiental do dano?',
                                        'Número/código da notificação de recuperação ambiental']].copy()
    add_table_with_split(informacao_dano_amb, "Recuperação do dano ambiental", 1, [100])
    elements.append(Spacer(1, 0.5 * cm))


    arquivos_RL = []
    
    if not repeat_rl_fotografico_linha.empty:
        imagem_RL = repeat_rl_fotografico_linha['parentrowid'].iloc[0] 
        for arquivo in os.listdir(r"input/RL"): 
            caminho_completo = os.path.join("input", "RL", arquivo)
            if os.path.isfile(caminho_completo) and arquivo.startswith(f"Img_{imagem_RL}_"):
                arquivos_RL.append(caminho_completo)
        
        if arquivos_RL:
            elements.append(Paragraph("Relatório fotográfico", styles['Titulo']))
            elements.append(Spacer(0.5, 0.5 * cm))
            vez = 0
            for caminho_assinatura in arquivos_RL:
                img = RLImage(caminho_assinatura)
                largura_max = 8.9 # cm
                largura_ajustada, altura_ajustada = calculate_proportional_dimensions(caminho_assinatura, largura_max)
                if largura_ajustada is not None and altura_ajustada is not None:
                    img.drawWidth = largura_ajustada
                    img.drawHeight = altura_ajustada
                else:
                    img.drawHeight = 6.35 * cm
                    img.drawWidth = 8.9 * cm
                elements.append(img)
                elements.append(Spacer(1.5, 1 * cm))
                try:
                    descricao = repeat_rl_fotografico_linha['descr_foto'].iloc[vez]
                    elements.append(Paragraph(descricao, styles['Legenda']))
                except Exception:
                    elements.append(Paragraph("Descrição não disponível", styles['Legenda']))
                    elements.append(Spacer(2, 0.5 * cm))
                vez += 1
        elements.append(Spacer(2, 1 * cm))

    # Conclusão
    conclusao = camada_linha['Conclusão'].astype(str).iloc[0]
    if conclusao != 'nan':
        elements.append(Paragraph(f"Conclusão", styles['Titulo']))
        elements.append(Spacer(0.5, 0.5 * cm))
        elements.append(Paragraph(conclusao, styles['CorpoTexto']))
        elements.append(Spacer(2, 1 * cm))

    # --- Seção de Assinaturas (Com verificação de contingência) ---
    arquivos_assinatura = []
    if not assinaturas_linha.empty:
        imagem_assinatura = camada_linha['ID Fiscalização'].iloc[0]
        # ... (O código de busca de arquivos_assinatura está correto) ...
        for arquivo in os.listdir(r"input/assinaturas"):
            caminho_completo = os.path.join("input", "assinaturas", arquivo)
            if os.path.isfile(caminho_completo) and arquivo.startswith(f"Img_{imagem_assinatura}"):
                arquivos_assinatura.append(caminho_completo)
        
        if arquivos_assinatura:
            elements.append(Paragraph("Assinaturas dos Fiscais", styles['Titulo']))
            vz = 0 
            
            for caminho_assinatura in arquivos_assinatura:
                img = RLImage(caminho_assinatura)
                img.drawHeight = 3.81 * cm
                img.drawWidth = 6.35 * cm 
                legenda_fiscal = Paragraph("Nome do fiscal não disponível", centered_style) # Valor padrão
                try:
                    if vz < len(assinatura_por_car_alerta): 
                        # Usa 'vz' para buscar a linha correta a cada iteração
                        nome_fiscal = assinatura_por_car_alerta['Atendimento'].iloc[vz]
                        id_func = assinatura_por_car_alerta['ID funcional'].iloc[vz]
                        # Cria o Parágrafo com os dados corretos
                        legenda_fiscal = Paragraph(f"{nome_fiscal}, ID funcional: {id_func}", centered_style)
                    else:
                        legenda_fiscal = Paragraph("Fiscal não encontrado no DataFrame", centered_style)
                except Exception as e:
                    # O valor padrão é usado se der erro no try
                    print(f"⚠️  Erro ao obter dados do fiscal {vz}: {e}")
                
                dados_tabela = [[img], [legenda_fiscal]]
                tabela_assinatura = Table(dados_tabela, colWidths=[10 * cm]) 

                tabela_assinatura.setStyle(TableStyle([
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('LEFTPADDING', (0,0), (-1,-1), 0),
                ('RIGHTPADDING', (0,0), (-1,-1), 0),
                ('BOTTOMPADDING', (0,0), (-1,-1), 0),
                ('TOPPADDING', (0,0), (-1,-1), 0),]))

                elements.append(tabela_assinatura)
                vz += 1 
                elements.append(Spacer(1, 1 * cm))
    
    # Rodapé
    if os.path.exists(imagem_cbc2):
        img_cbc2 = RLImage(imagem_cbc2)
        img_cbc2.drawHeight = 3.81 * cm
        img_cbc2.drawWidth = 15.7 * cm
        elements.append(img_cbc2)

    # --- Anexo de autorização ---

    valor_autorizacao = camada_linha['Apresentou autorização?'].iloc[0]
    legenda_autorizacao = informacao_autorizacao['Número da autorização'].iloc[0]
    if valor_autorizacao == 'Sim':
        try:
            imagem_nome = linha_camada['Id do objeto']
            autorizacao = f"input\\autorizacao\\{imagem_nome}.jpeg"
            
            # Inserir cabeçalho do anexo
            elements.append(PageBreak())
            elements.append(Paragraph("Anexo - autorização", styles['Titulo']))
            elements.append(Spacer(0.5, 0.5 * cm))

            # 2. VERIFICA se o arquivo existe
            if os.path.exists(autorizacao):
                print(f"😎 📃  Anexo da autorização {imagem_nome}.jpg inserido no relatório.")
                
                # Adiciona a imagem
                img = RLImage(autorizacao)
                img.drawHeight = 22 * cm
                img.drawWidth = 15 * cm
                elements.append(img)
                elements.append(Paragraph(f"Autorização Nº {legenda_autorizacao}", styles['Legenda']))
                elements.append(Spacer(1.5, 0.5 * cm))
            else:
                # 3. Bloco ELSE executado se os.path.exists for False
                print('⚠️ 📃  Anexo da autorização não encontrada')
                elements.append(Paragraph("Arquivo da autorização não encontrado", styles['CorpoTexto']))
                elements.append(Spacer(1.5, 0.5 * cm))
                
        except KeyError:
            print('⚠️ 📃  Erro de chave ao tentar nomear o arquivo de autorização.')
        except Exception as e:
            print(f'❌ 📃  Erro inesperado: {e}')


    try:
        doc.build(elements, onFirstPage=addPageNumber, onLaterPages=addPageNumber)
        print(f"✅  PDF gerado com sucesso: {idtxt}_{mapa}")
    except Exception as e:
        print(f"❌  Erro ao gerar PDF para {idtxt}_{mapa}: {e}")


    logging.info(f"✅ {cntd} PDFs gerados: {pdf_file}")


