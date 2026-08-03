import streamlit as st
import openai
import os
import pandas as pd
from datetime import datetime

# Configuração da página
st.set_page_config(page_title="Assistente de Manutenção Industrial", page_icon="🔧", layout="wide")

st.title("🔧 Assistente de Manutenção Industrial por Voz")
st.write("Fale o relato da ocorrência. A IA estrutura a Ordem de Serviço profissionalmente e salva de forma automática no Excel.")

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
    
    # Nome fixo do arquivo Excel na pasta do projeto
    excel_file = "ordens_servico.xlsx"

    # Carrega histórico inicial do Excel ou da sessão
    if "historico_os" not in st.session_state:
        st.session_state.historico_os = []
        if os.path.exists(excel_file):
            try:
                df_load = pd.read_excel(excel_file, engine="openpyxl")
                st.session_state.historico_os = df_load.to_dict("records")
            except:
                pass

    # Gravação por áudio direta (Zero-UI)
    audio_file = st.audio_input("🎙️ Clique no microfone e relate a ocorrência:")
    
    if audio_file is not None:
        with st.spinner("Processando áudio e estruturando a Ordem de Serviço..."):
            try:
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
                
                # Geração da Ordem de Serviço estruturada e formatada profissionalmente
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "Você é um especialista sênior em manutenção industrial. "
                                "Analise o relato falado do técnico e estruture uma Ordem de Serviço limpa, formal e profissional, "
                                "dividida obrigatoriamente nestes tópicos:\n"
                                "- **Equipamento / Setor:**\n"
                                "- **Problema Constatado:**\n"
                                "- **Ação Realizada / Recomendada:**\n"
                                "- **Peças e Materiais:**\n"
                                "Se faltar alguma informação essencial, adicione um aviso curto no final."
                            )
                        },
                        {
                            "role": "user",
                            "content": f"Relato do técnico: {texto_relato}"
                        }
                    ]
                )
                
                resultado_ia = response.choices[0].message.content
                data_atual = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                
                # Adiciona ao topo do histórico da sessão
                nova_os = {
                    "Data/Hora": data_atual,
                    "Relato Falado (Áudio)": texto_relato,
                    "Ordem de Serviço Formatada": resultado_ia
                }
                st.session_state.historico_os.insert(0, nova_os)
                
                # Salvamento automático direto no Excel em segundo plano (sem corromper)
                df_final = pd.DataFrame(st.session_state.historico_os)
                df_final.to_excel(excel_file, index=False, engine='openpyxl')
                
                st.success("Ordem de Serviço gerada e salva automaticamente na pasta do Excel!")
                
            except Exception as e:
                st.error(f"Ocorreu um erro ao processar: {e}")

    # Exibição da Tabela e Pesquisa integrada no site
    st.divider()
    st.subheader("📋 Histórico e Pesquisa de Ordens de Serviço")
    
    if st.session_state.historico_os:
        termo_pesquisa = st.text_input("🔍 Pesquisar no histórico (por máquina, setor, serviço ou palavra-chave):")
        
        df_exibicao = pd.DataFrame(st.session_state.historico_os)
        
        if termo_pesquisa:
            mask = df_exibicao.astype(str).apply(lambda x: x.str.contains(termo_pesquisa, case=False, na=False)).any(axis=1)
            df_exibicao = df_exibicao[mask]
        
        # Mostra as ordens formatadas no site de forma limpa
        for index, row in df_exibicao.iterrows():
            with st.expander(f"📌 OS registrada em: {row['Data/Hora']}"):
                st.markdown(f"**Relato Original:** _{row['Relato Falado (Áudio)']}_")
                st.markdown("---")
                st.markdown(row['Ordem de Serviço Formatada'])
    else:
        st.info("Nenhuma Ordem de Serviço registrada ainda. Grave o seu primeiro relato acima!")

else:
    st.warning("⚠️ Insira a sua chave de API da Groq na barra lateral para começar.")
