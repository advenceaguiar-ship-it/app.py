import streamlit as st
import openai
import os
import pandas as pd
from datetime import datetime

# Configuração da página
st.set_page_config(page_title="Assistente de Manutenção Industrial", page_icon="🔧", layout="wide")

st.title("🔧 Assistente de Manutenção Industrial por Voz")
st.write("Fale a sua ocorrência. O sistema transcreve, gera a Ordem de Serviço e salva automaticamente no Excel.")

# Configuração da API da Groq
if "GROQ_API_KEY" in st.secrets:
    api_key = st.secrets["GROQ_API_KEY"]
else:
    api_key = st.sidebar.text_input("Insira sua Groq API Key (gsk_...)", type="password")

if api_key:
    client = openai.OpenAI(
        api_key=api_key,
        base_url="https://api.groq.com/openai/v1"
    )
    
    # Gravador de áudio direto (Zero-UI)
    audio_file = st.audio_input("🎙️ Clique no microfone e relate o problema:")
    
    if audio_file is not None:
        with st.spinner("Processando áudio e gerando Ordem de Serviço..."):
            try:
                # Salva o áudio temporariamente
                temp_audio = "audio_temp.wav"
                with open(temp_audio, "wb") as f:
                    f.write(audio_file.read())
                
                # Transcrição via Whisper (Groq)
                with open(temp_audio, "rb") as f_audio:
                    transcription = client.audio.transcriptions.create(
                        model="whisper-large-v3",
                        file=f_audio
                    )
                texto_relato = transcription.text
                
                if os.path.exists(temp_audio):
                    os.remove(temp_audio)
                
                st.info(f"🗣️ **Relato Captado:** {texto_relato}")

                # Geração da Ordem de Serviço estruturada pela IA
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "Você é um especialista em manutenção industrial. "
                                "Analise o relato falado do técnico e estruture uma Ordem de Serviço contendo: "
                                "Equipamento, Problema Constatado, Ação Realizada e Peças/Materiais (se houver)."
                            )
                        },
                        {
                            "role": "user",
                            "content": f"Relato: {texto_relato}"
                        }
                    ]
                )
                
                resultado_ia = response.choices[0].message.content
                
                st.success("Ordem de Serviço gerada com sucesso!")
                st.markdown("---")
                st.markdown(resultado_ia)
                
                # Salvamento automático no Excel com suporte total a acentos (engine openpyxl)
                excel_file = "ordens_servico.xlsx"
                data_atual = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                
                nova_linha = pd.DataFrame([{
                    "Data/Hora": data_atual,
                    "Relato Original": texto_relato,
                    "Ordem de Serviço Gerada": resultado_ia
                }])
                
                if os.path.exists(excel_file):
                    df_existente = pd.read_excel(excel_file)
                    df_final = pd.concat([df_existente, nova_linha], ignore_index=True)
                else:
                    df_final = nova_linha
                
                # Salvando explicitamente com o motor openpyxl para evitar conflitos de codificação
                df_final.to_excel(excel_file, index=False, engine='openpyxl')
                st.success("📁 Dados salvos automaticamente no Excel com sucesso!")
                
                # Botão para descarregar o Excel atualizado
                with open(excel_file, "rb") as f:
                    st.download_button(
                        label="📥 Descarregar Planilha Excel Atualizada",
                        data=f,
                        file_name="ordens_servico.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                
            except Exception as e:
                st.error(f"Ocorreu um erro ao processar: {e}")
else:
    st.warning("⚠️ Insira a sua chave de API da Groq na barra lateral para começar.")
