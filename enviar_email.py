import pandas as pd
import smtplib
import os
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from mimetypes import guess_type



# --- CONFIGURAÇÕES ---
# Senha está na pasta do COGET, tendo acesso, deverá compilar normalmente na sua máquina local :)

ARQUIVO_ENVIO = r"\\Bp-1hd57t3-inea\e\COGET\INPUTS_SCRIPTS\enviar_email.xlsx"
SENDER_EMAIL = "geget.inea@gmail.com" 
df_envio = pd.read_excel(ARQUIVO_ENVIO)
df_envio = df_envio[df_envio['email'] == SENDER_EMAIL]
SENDER_PASSWORD = str(df_envio['senha'].iloc[0])
print(SENDER_PASSWORD)
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
CC_EMAIL = "olhonoverde@gmail.com" 

ARQUIVO_ASSINATURA = r'input\CSVs\assinaturas.xlsx'
ARQUIVO_CAMADA = r'input\CSVs\camada.xlsx'
DIRETORIO_PDFS = r'output\relatorios' 

def send_email_with_pdf(to_email, name, pdf_filename):
    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = to_email
    msg['Subject'] = f"Relatório de vistoria - Olho no Verde"
    if CC_EMAIL: msg['Cc'] = CC_EMAIL
    msg.attach(MIMEText(f"Prezados,\n\nSegue o relatório de vistoria em anexo.\n\nAtenciosamente,\nEquipe Técnica GERGET,\n", 'plain'))

    try:
        with open(pdf_filename, "rb") as f:
            attachment = MIMEApplication(f.read(), _subtype="pdf")
            attachment.add_header('Content-Disposition', 'attachment', filename=os.path.basename(pdf_filename))
            msg.attach(attachment)
            
        recipients = [to_email]
        if CC_EMAIL: recipients.append(CC_EMAIL)

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, recipients, msg.as_string())
        print(f"📧 SUCESSO: {to_email} | {os.path.basename(pdf_filename)}")
        return True
    except Exception as e:
        print(f"❌ ERRO no envio para {to_email}: {e}")
        return False

def envio_em_massa(lista_ids_novos=None):
    try:
        # 1. Leitura Limpa das Planilhas
        df_sig_raw = pd.read_excel(ARQUIVO_ASSINATURA)
        df_cam_raw = pd.read_excel(ARQUIVO_CAMADA, dtype={'id_alerta': str})

        # --- CORREÇÃO DAS COLUNAS DUPLICADAS ---
        # Se houver qualquer coluna chamada 'email', nós a removemos para priorizar a 'email_fisc01'
        if 'email' in df_sig_raw.columns:
            df_sig_raw = df_sig_raw.drop(columns=['email'])

        # Selecionamos apenas as colunas necessárias para garantir que não haja lixo
        df_sig = df_sig_raw[['id_fiscalizacao_assinaturas', 'email_fisc01', 'nomes']].copy()
        df_sig = df_sig.rename(columns={
            'id_fiscalizacao_assinaturas': 'id_fisc', 
            'email_fisc01': 'email', 
            'nomes': 'nome'
        })

        df_cam = df_cam_raw[['id_alerta', 'id_fiscalizacao', 'globalid']].copy()
        df_cam = df_cam.rename(columns={'id_fiscalizacao': 'id_fisc'})
        
        # 2. Cruzamento (Merge)
        df = pd.merge(df_cam, df_sig, on='id_fisc', how='left')
        df = df.drop_duplicates(subset=['id_alerta', 'globalid'])

        # 3. Filtro (Novos ou Todos)
        if lista_ids_novos:
            lista_ids_limpos = [str(i).strip() for i in lista_ids_novos]
            df = df[df['id_alerta'].isin(lista_ids_limpos)]
        else:
            print("📂 Modo: Enviando PDFs existentes na pasta...")
            arquivos = os.listdir(DIRETORIO_PDFS)
            df['nome_f'] = df.apply(lambda r: f"Relatorio_vistoria_ONV_{r['id_alerta']}_{r['globalid']}.pdf", axis=1)
            df = df[df['nome_f'].isin(arquivos)]

        if df.empty:
            print("ℹ️ Nenhum dado para envio.")
            return

        # 4. Loop de Envio Seguro
        registros = df.to_dict('records')
        print(f"⏳ Processando {len(registros)} e-mails...")

        for reg in registros:
            email_dest = str(reg.get('email', 'nan')).strip()
            id_alerta = str(reg.get('id_alerta', ''))
            globalid = str(reg.get('globalid', ''))
            nome_dest = str(reg.get('nome', 'Técnico'))

            if not email_dest or email_dest.lower() == 'nan' or '@' not in email_dest:
                print(f"⚠️ Alerta {id_alerta}: E-mail inválido ou não encontrado para Fiscal {reg.get('id_fisc')}")
                continue

            pdf_path = os.path.join(DIRETORIO_PDFS, f"Relatorio_vistoria_ONV_{id_alerta}_{globalid}.pdf")
            
            if os.path.exists(pdf_path):
                send_email_with_pdf(email_dest, nome_dest, pdf_path)
                time.sleep(1.5) # Evita spam
            else:
                print(f"⚠️ Arquivo não encontrado: {os.path.basename(pdf_path)}")

        print("\n✅ Processo finalizado.")

    except Exception as e:
        print(f"❌ Erro: {e}")
