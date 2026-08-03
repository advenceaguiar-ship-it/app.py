import streamlit as st
import openai
import os

# Configuração da página
st.set_page_config(page_title="Assistente de Manutenção Industrial", page_icon="🔧", layout="wide")

st.title("🔧 Assistente de Manutenção Industrial com IA")
st.write("Fale ou digite a sua ocorrência. O sistema gera a Ordem de Serviço de forma totalmente automática.")

# Configuração da API da Groq (substituindo a OpenAI para aceitar chaves gsk_)
if "GROQ_API_KEY" in st.secrets:
    api_key = st.secrets["GROQ_API_KEY"]
else:
    api_key = st.sidebar.text_input("Insira sua Groq API Key (gsk_...)", type="password")

if api_key:
    # A Groq usa a mesma estrutura da OpenAI, mas com a base URL própria
    client = openai.OpenAI(
        api_key=api_key,
        base_url="https://api.groq.com/openai/v1"
    )
    
    # Entrada de áudio ou texto de forma direta e automática
    opcao = st.radio("Escolha o formato:", ["Gravar Áudio", "Digitar Texto"], horizontal=True)
    
    texto_relato = ""
    
    if opcao == "Gravar Áudio":
        audio_file = st.audio_input("Grave o relato da ocorrência:")
        if audio_file is not None:
            with st.spinner("Processando áudio automaticamente..."):
                temp_audio = "audio_temp.wav"
                with open(temp_audio, "wb") as f:
                    f.write(audio_file.read())
                
                with open(temp_audio, "rb") as f_audio:
                    transcription = client.audio.transcriptions.create(
                        model="whisper-large-v3",
                        file=f_audio
                    )
                texto_relato = transcription.text
                if os.path.exists(temp_audio):
                    os.remove(temp_audio)
                st.success(f"Áudio transcrito: {texto_relato}")
    else:
        texto_relato = st.text_area("Descreva a ocorrência:")

    # Assim que houver texto (seja por digitação ou áudio), gera automaticamente
    if texto_relato:
        with st.spinner("Gerando Ordem de Serviço automática com Inteligência Artificial..."):
            try:
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {
                            "role": "system",
                            "content": "Você é um assistente de manutenção industrial. Crie uma Ordem de Serviço limpa e organizada com base no relato do técnico."
                        },
                        {
                            "role": "user",
                            "content": f"Relato: {texto_relato}"
                        }
                    ]
                )
                st.markdown("### 📋 Ordem de Serviço Gerada:")
                st.markdown(response.choices[0].message.content)
            except Exception as e:
                st.error(f"Erro ao gerar a IA: {e}")
else:
    st.warning("⚠️ Insira a sua chave de API da Groq na barra lateral para começar.")
