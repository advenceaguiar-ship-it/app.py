import streamlit as st
import openai
import pandas as pd
import os

# Configuração da página
st.set_page_config(page_title="Assistente de Manutenção Industrial", page_icon="🔧", layout="wide")

# Título do aplicativo
st.title("🔧 Assistente de Manutenção Industrial com IA")
st.write("Grave o áudio da ocorrência ou digite o relato. A IA identificará os detalhes automaticamente.")

# Gerenciamento da chave da OpenAI API
if "OPENAI_API_KEY" in st.secrets:
    openai.api_key = st.secrets["OPENAI_API_KEY"]
else:
    api_key_input = st.sidebar.text_input("Insira sua OpenAI API Key", type="password")
    if api_key_input:
        openai.api_key = api_key_input
    else:
        st.sidebar.warning("Insira a API Key para habilitar a Inteligência Artificial.")

# Formulário simplificado (tudo automático)
with st.form("form_os"):
    st.subheader("Registro de Ocorrência")
    
    metodo_registro = st.radio("Como deseja registrar a ocorrência?", ["Gravar Áudio", "Digitar Texto"], horizontal=True)
    
    audio_bytes = None
    texto_relato = ""
    
    if metodo_registro == "Gravar Áudio":
        st.write("🎙️ **Grave a sua mensagem de áudio:**")
        audio_file = st.audio_input("Clique no microfone para gravar o relato:")
        if audio_file is not None:
            audio_bytes = audio_file.read()
            st.success("Áudio gravado com sucesso!")
    else:
        texto_relato = st.text_area("Descreva o problema, o nome da máquina e o técnico envolvido:")
        
    submitted = st.form_submit_button("🚀 Gerar Ordem de Serviço Automática", use_container_width=True)

# Processamento automático
if submitted:
    if not openai.api_key:
        st.error("A chave da API da OpenAI não foi configurada.")
    elif metodo_registro == "Gravar Áudio" and audio_bytes is None:
        st.warning("Por favor, grave um áudio antes de enviar.")
    elif metodo_registro == "Digitar Texto" and not texto_relato.strip():
        st.warning("Por favor, digite o texto antes de enviar.")
    else:
        with st.spinner("Processando e organizando a Ordem de Serviço com Inteligência Artificial..."):
            try:
                relato_final = texto_relato
                
                # Transcrição se for áudio
                if metodo_registro == "Gravar Áudio" and audio_bytes:
                    temp_audio_path = "temp_audio.wav"
                    with open(temp_audio_path, "wb") as f:
                        f.write(audio_bytes)
                    
                    with open(temp_audio_path, "rb") as file_to_transcribe:
                        transcription = openai.audio.transcriptions.create(
                            model="whisper-1", 
                            file=file_to_transcribe
                        )
                    relato_final = transcription.text
                    
                    if os.path.exists(temp_audio_path):
                        os.remove(temp_audio_path)
                    
                    st.info(f"🗣️ **O que foi captado no áudio:** {relato_final}")

                # Geração inteligente extraindo dados automaticamente do texto/áudio
                response = openai.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {
                            "role": "system", 
                            "content": (
                                "Você é um assistente especialista em manutenção industrial. "
                                "Analise o relato livre do usuário, extraia ou deduza o nome da máquina/equipamento, "
                                "o nome do técnico (se mencionado) e estruture uma Ordem de Serviço limpa com: "
                                "1. Equipamento Identificado, 2. Técnico Responsável, 3. Diagnóstico do Problema, "
                                "e 4. Ações Corretivas Recomendadas."
                            )
                        },
                        {
                            "role": "user", 
                            "content": f"Relato livre: {relato_final}"
                        }
                    ]
                )
                
                resultado_ia = response.choices[0].message.content
                
                st.success("Ordem de Serviço gerada com sucesso!")
                st.markdown("---")
                st.markdown(resultado_ia)
                
            except Exception as e:
                st.error(f"Ocorreu um erro ao processar: {e}")
