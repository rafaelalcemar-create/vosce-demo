import streamlit as st
from openai import OpenAI

st.set_page_config(
    page_title="VOSCE - Simulação Clínica Virtual",
    page_icon="🩺",
    layout="centered"
)

# Inicializa cliente da OpenAI
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# --- Página Inicial ---
if "pagina" not in st.session_state:
    st.session_state.pagina = "inicio"

if st.session_state.pagina == "inicio":
    st.markdown("""
        <div style="text-align: center; padding: 50px 0;">
            <h1 style="font-size: 2.5em;">🩺 VOSCE — Simulação Clínica Virtual</h1>
            <h3 style="color: #999;">Plataforma de Treinamento Médico com Inteligência Artificial</h3>
            <p style="max-width: 600px; margin: auto; font-size: 1.1em;">
                Bem-vindo à simulação clínica interativa! Nesta plataforma, o estudante de Medicina poderá
                conversar com um <b>paciente virtual</b> em um cenário clínico de Urologia.
                Faça perguntas, colete informações relevantes e formule seu diagnóstico.
            </p>
        </div>
    """, unsafe_allow_html=True)

    if st.button("🚀 Iniciar Simulação", use_container_width=True):
        st.session_state.pagina = "simulacao"
        st.rerun()

# --- Página de Simulação ---
elif st.session_state.pagina == "simulacao":
    st.title("💬 Simulação Clínica — Caso: Infecção do Trato Urinário (ITU)")
    st.markdown("Paciente com **queixa de dor ao urinar há alguns dias.** Conduza a anamnese.")

    # Inicializa histórico
    if "historico" not in st.session_state:
        st.session_state.historico = []

    # Caixa de entrada
    pergunta = st.text_input("Digite sua pergunta para o paciente:")

    if st.button("Enviar"):
        if pergunta:
            st.session_state.historico.append(("Você", pergunta))

            # Chamada à IA
            chat = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Você é um paciente virtual que apresenta sintomas compatíveis com uma infecção urinária leve. Responda de forma breve e coerente com um caso clínico realista."},
                    *[
                        {"role": "user" if p[0] == "Você" else "assistant", "content": p[1]}
                        for p in st.session_state.historico
                    ]
