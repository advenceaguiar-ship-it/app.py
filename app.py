import streamlit as st
import openai
import pandas as pd
import os

# Configuração da página
st.set_page_config(page_title="Assistente de Manutenção Industrial", page_icon="🔧", layout="wide")

# Título do aplicativo
st.title("🔧 Assistente de Manutenção Industrial com IA")
st.write("Grave o áudio da ocorrência ou digite para gerar a Ordem de Serviço automaticamente.")

# Gerenciamento da chave da OpenAI API
if "OPENAI_API_KEY" in st.secrets:
    openai.api_key = st.secrets["OPENAI_API_KEY"]
else:
    api_key_input = st.sidebar.text_input("Insira sua OpenAI API Key", type="password")
    if api_key_input:
        openai.api_key = api_key_input
    else:
        st.sidebar.warning("Insira a API Key para habilitar a Inteligência Artificial.")

# Formulário de registro da O.S.
with st.form("form_os"):
    st.subheader("Registro de Ocorrência")
    
    # Alternância entre Áudio e Texto
    metodo_registro = st.radio("Como deseja registrar a ocorrência?", ["Gravar Áudio", "Digitar Texto"], horizontal=True)
    
    audio_bytes = None
    texto_relato = ""
    
    if metodo_registro == "Gravar Áudio":
        st.write("🎙️ **Grave a sua mensagem de áudio:**")
        audio_file = st.audio_input("Clique no microfone para gravar o relato do técnico:")
        if audio_file is not None:
            audio_bytes = audio_file.read()
            st.success("Áudio gravado com sucesso! Clique em 'Gerar Ordem de Serviço' para processar.")
    else:
        texto_relato = st.text_area("Descreva o problema ou a manutenção realizada em detalhe:")
        
    st.divider()
    
    col1, col2 = st.columns(2)
    with col1:
        maquina = st.text_input("Equipamento / Máquina:")
    with col2:
        tecnico = st.text_input("Nome do Técnico:")
        
    submitted = st.form_submit_button("🚀 Gerar Ordem de Serviço", use_container_width=True)

# Processamento ao enviar o formulário
if submitted:
    if not openai.api_key:
        st.error("A chave da API da OpenAI não foi configurada. Insira a chave na barra lateral.")
    elif not maquina or not tecnico:
        st.warning("Preencha o nome do equipamento e do técnico.")
    elif metodo_registro == "Gravar Áudio" and audio_bytes is None:
        st.warning("Por favor, grave um áudio antes de enviar.")
    elif metodo_registro == "Digitar Texto" and not texto_relato.strip():
        st.warning("Por favor, digite o texto da ocorrência antes de enviar.")
    else:
        with st.spinner("Processando com Inteligência Artificial..."):
            try:
                relato_final = texto_relato
                
                # Transcrição do áudio usando OpenAI Whisper (se áudio for selecionado)
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
                    
                    st.info(f"🗣️ **Transcrição do Áudio:** {relato_final}")

                # Geração da Ordem de Serviço estruturada pela IA
                response = openai.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {
                            "role": "system", 
                            "content": (
                                "Você é um especialista em manutenção industrial. "
                                "Receba o relato de uma ocorrência e gere uma Ordem de Serviço técnica, "
                                "organizada em tópicos claros: Diagnóstico do Problema, Ações Recomendadas, "
                                "e Peças/Ferramentas Necessárias."
                            )
                        },
                        {
                            "role": "user", 
                            "content": f"Máquina: {maquina}\nTécnico: {tecnico}\nRelato do Técnico: {relato_final}"
                        }
                    ]
                )
                
                resultado_ia = response.choices[0].message.content
                
                # Exibição do Resultado
                st.success("Ordem de Serviço gerada com sucesso!")
                st.markdown("---")
                st.markdown(resultado_ia)
                
            except Exception as e:
                st.error(f"Ocorreu um erro ao processar a solicitação: {e}")
