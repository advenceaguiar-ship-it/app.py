import streamlit as st
from openai import OpenAI
import json
import pandas as pd
import os
from datetime import datetime
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from gtts import gTTS
import io

st.set_page_config(page_title="Assistente de Manutenção", layout="wide")

st.title("🛠️ Assistente de Manutenção Industrial (Zero-UI)")
st.write("Fale com a IA. O relatório, tempo de serviço e checklist são validados automaticamente.")

# --- CONTROLE DE ESTADO BLINDADO ---
if "etapa" not in st.session_state:
    st.session_state.etapa = 1
if "dados_parciais" not in st.session_state:
    st.session_state.dados_parciais = {}
if "texto_ia" not in st.session_state:
    st.session_state.texto_ia = ""
if "audio_bytes_ia" not in st.session_state:
    st.session_state.audio_bytes_ia = None
if "ja_processou" not in st.session_state:
    st.session_state.ja_processou = False

def reiniciar_os():
    st.session_state.etapa = 1
    st.session_state.dados_parciais = {}
    st.session_state.texto_ia = ""
    st.session_state.audio_bytes_ia = None
    st.session_state.ja_processou = False
    st.rerun()

# --- CAMINHO DO EXCEL (ADAPTADO PARA NUVEM E PC) ---
arquivo_excel = "relatorios_manutencao.xlsx"

def salvar_excel_seguro(df_nova, caminho):
    if not os.path.exists(caminho):
        df_nova.to_excel(caminho, index=False)
    else:
        try:
            df_existente = pd.read_excel(caminho)
            df_final = pd.concat([df_existente, df_nova], ignore_index=True)
            df_final.to_excel(caminho, index=False)
        except PermissionError:
            caminho_alt = caminho.replace(".xlsx", "_copia_segura.xlsx")
            df_nova.to_excel(caminho_alt, index=False)
            st.warning(f"⚠️ O Excel principal está aberto. Salvo temporariamente em: {caminho_alt}")
            return

    try:
        wb = openpyxl.load_workbook(caminho)
        ws = wb.active
        header_fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
        header_font = Font(name="Arial", size=11, bold=True, color="FFFFFF")
        align_center = Alignment(horizontal="center", vertical="center", wrap_text=True)
        align_left = Alignment(horizontal="left", vertical="center", wrap_text=True)
        thin_border = Border(left=Side(style='thin', color='D9D9D9'), right=Side(style='thin', color='D9D9D9'), top=Side(style='thin', color='D9D9D9'), bottom=Side(style='thin', color='D9D9D9'))

        for cell in ws[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = align_center

        for row in ws.iter_rows(min_row=2, max_row=ws.max_row, min_col=1, max_col=ws.max_column):
            for cell in row:
                cell.font = Font(name="Arial", size=10)
                cell.border = thin_border
                if cell.column in [1, 2, 3, 4]: 
                    cell.alignment = align_center
                else:
                    cell.alignment = align_left

        for col in ws.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            col_letter = get_column_letter(col[0].column)
            ws.column_dimensions[col_letter].width = max(max_len + 4, 15)
        ws.row_dimensions[1].height = 28
        wb.save(caminho)
    except Exception:
        pass

# --- BARRA LATERAL (CONFIGURAÇÕES E FILTROS DE PESQUISA) ---
st.sidebar.header("⚙️ Configurações & Filtros")

if "GROQ_API_KEY" in st.secrets:
    raw_key = st.secrets["GROQ_API_KEY"]
else:
    raw_key = st.sidebar.text_input("Cole a sua API Key da Groq:", type="password")

st.sidebar.divider()
st.sidebar.subheader("🔍 Filtrar Ordens de Serviço")
filtro_tipo = st.sidebar.selectbox("Filtrar por Tipo de Serviço:", ["Todos", "Elétrico", "Mecânico", "Resina"])
filtro_setor = st.sidebar.text_input("Filtrar por Setor (Ex: Cobre, Ferro, Usinagem):")

if raw_key:
    api_key = raw_key.strip()
    client = OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")
    
    if st.sidebar.button("🔄 Cancelar / Iniciar Nova O.S."):
        reiniciar_os()

    # ==========================================
    # ETAPA 1: RELATO INICIAL
    # ==========================================
    if st.session_state.etapa == 1:
        st.subheader("Fase 1: Descreva o problema, serviço e tempo gasto")
        
        audio_file = st.audio_input("Clique para gravar seu relato inicial:")

        if audio_file is not None and not st.session_state.ja_processou:
            st.session_state.ja_processou = True
            
            with st.spinner("Analisando relato e preenchendo dados..."):
                transcript = client.audio.transcriptions.create(model="whisper-large-v3", file=audio_file)
                
                prompt = f"""Analise o relato do técnico e extraia em formato JSON exatamente com as chaves:
                - tipo_servico (Estritamente: 'Elétrico', 'Mecânico' ou 'Resina'. Se não se enquadrar, coloque 'Não informada')
                - setor (Inicie com letra maiúscula)
                - equipamento (Inicie com letra maiúscula)
                - falha (Escreva formalmente, iniciando com letra maiúscula)
                - causa (Se o técnico mencionou a causa, preencha formatando corretamente. Senão, coloque 'Não informada')
                - acao (Escreva formalmente, iniciando com letra maiúscula)
                - tempo_gasto (Ex: '7h às 8h', '40 minutos', '2 horas'. Se não citar, coloque 'Não informado')
                - checklist_seguranca (Analise se o técnico informou no áudio se deixou o setor limpo, seguro, deu baixa, guardou ferramentas e testou. Se disse que fez tudo, preencha 'Concluído no relato'. Senão, 'Pendente')
                
                Texto do técnico: {transcript.text}"""
                
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"}
                )
                
                dados = json.loads(response.choices[0].message.content)
                st.session_state.dados_parciais = dados
                
                causa_ok = dados.get("causa") != 'Não informada'
                checklist_ok = dados.get("checklist_seguranca") == 'Concluído no relato'
                
                if causa_ok and checklist_ok:
                    agora = datetime.now().strftime("%d/%m/%Y %H:%M")
                    num_os = 1
                    if os.path.exists(arquivo_excel):
                        try:
                            df_existente = pd.read_excel(arquivo
    else:
        st.write("Nenhuma O.S. gravada ainda.")
else:
    st.warning("⚠️ Insira a sua chave de API da Groq na barra lateral para começar.")
