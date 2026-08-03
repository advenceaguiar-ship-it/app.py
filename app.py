import streamlit as st
import openai
import pandas as pd
import os
from gTTS import gTTS
import base64

# Configuração da página
st.set_page_config(page_title="Assistente de Manutenção Industrial", page_icon="🔧", layout="wide")

# Título do aplicativo
st.title("🔧 Assistente de Manutenção Industrial com IA")
st.write("Grave ou digite a ocorrência para gerar a Ordem de Serviço automaticamente.")

# Simulação de campo de chave da API ou uso do secrets do Streamlit
if "OPENAI_API_KEY" in st.secrets:
    openai.api_key = st.secrets["OPENAI_API_KEY"]
else:
    api_key_input = st.sidebar.text_input("Insira sua OpenAI API Key", type="password")
    if api_key_input:
        openai.api_key = api_key_input
    else:
        st.warning("Por favor, insira a chave da API da OpenAI para continuar.")

# Área de entrada de dados
with st.form("form_os"):
    st.subheader("Registro de Ocorrência")
    descricao = st.text_area("Descreva o problema ou manutenção realizada:")
    
    col1, col2 = st.columns(2)
    with col1:
        maquina = st.text_input("Equipamento / Máquina:")
    with col2:
        tecnico = st.text_input("Nome do Técnico:")
        
    submitted = st.form_submit_button("Gerar Ordem de Serviço")

if submitted:
    if not openai.api_key:
        st.error("A chave da API da OpenAI é necessária para processar a solicitação.")
    elif not descricao or not maquina or not tecnico:
        st.warning("Preencha todos os campos obrigatórios.")
    else:
        with st.spinner("Processando Ordem de Serviço com Inteligência Artificial..."):
            try:
                # Chamada simples para a OpenAI gerar um resumo técnico estruturado
                response = openai.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "Você é um assistente especialista em manutenção industrial. Formate a O.S. de forma limpa e técnica."},
                        {"role": "user", "content": f"Máquina: {maquina}\nTécnico: {tecnico}\nRelato: {descricao}"}
                    ]
                )
                resultado_ia = response.choices[0].message.content
                
                st.success("Ordem de Serviço gerada com sucesso!")
                st.write(resultado_ia)
                
                # Exemplo de uso do gTTS (geração de áudio sem erro de subprocesso)
                tts = gTTS(text="Ordem de serviço gerada com sucesso.", lang="pt")
                tts.save("resposta.mp3")
                
                audio_file = open("resposta.mp3", "rb")
                audio_bytes = audio_file.read()
                st.audio(audio_bytes, format="audio/mp3")
                
            except Exception as e:
                st.error(f"Ocorreu um erro ao processar: {e}")