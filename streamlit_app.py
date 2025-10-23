import streamlit as st

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="VOSCE - Simulação Clínica Virtual", layout="centered")

# --- ESTILO CHAT ---
st.markdown("""
<style>
.chat-bubble-user {
    background-color: #2c3e50;
    color: white;
    padding: 10px 14px;
    border-radius: 12px;
    margin: 6px 0;
    text-align: right;
}
.chat-bubble-patient {
    background-color: #16a085;
    color: white;
    padding: 10px 14px;
    border-radius: 12px;
    margin: 6px 0;
    text-align: left;
}
.center-logo { text-align: center; margin-bottom: 10px; }
</style>
""", unsafe_allow_html=True)

# --- ESTADOS ---
if "page" not in st.session_state:
    st.session_state.page = "inicio"
if "chat" not in st.session_state:
    st.session_state.chat = []
if "perguntas" not in st.session_state:
    st.session_state.perguntas = 0

# --- TELA INICIAL ---
if st.session_state.page == "inicio":
    st.markdown("<div class='center-logo'>", unsafe_allow_html=True)
    st.image("https://i.imgur.com/XC6fQpX.png", width=180)
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("### Bem-vindo(a) ao protótipo do **VOSCE** 👨‍⚕️💬")
    st.write("Clique abaixo para iniciar uma simulação prática.")
    if st.button("🚀 Iniciar Simulação de ITU"):
        st.session_state.page = "simulacao"
        st.rerun()

# --- TELA DE SIMULAÇÃO ---
elif st.session_state.page == "simulacao":
    st.title("🩺 Caso Clínico — Queixa principal: dor ao urinar")
    st.caption("Apenas a queixa principal foi informada — o estudante deve investigar.")

    # Exibe o histórico do chat
    for msg in st.session_state.chat:
        if msg["role"] == "user":
            st.markdown(f"<div class='chat-bubble-user'>{msg['content']}</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='chat-bubble-patient'>{msg['content']}</div>", unsafe_allow_html=True)

    pergunta = st.text_input("Digite sua pergunta para o paciente:")
    if st.button("Enviar"):
        if pergunta.strip():
            st.session_state.chat.append({"role": "user", "content": pergunta})
            st.session_state.perguntas += 1

            # Lógica simples de resposta do paciente (baseada em palavras-chave)
            p = pergunta.lower()
            if "dor" in p:
                resposta = "É uma queimação no fim da micção."
            elif "tempo" in p or "quanto" in p:
                resposta = "Começou há uns três dias."
            elif "cor" in p or "urina" in p:
                resposta = "Notei urina mais escura e com odor diferente."
            elif "febre" in p:
                resposta = "Tive febre baixa ontem à noite."
            elif "náusea" in p or "vômito" in p:
                resposta = "Não, só desconforto ao urinar."
            elif "sangue" in p or "hematúria" in p:
                resposta = "Vi um pouco de sangue na urina ontem."
            else:
                resposta = "Não tenho certeza, doutor(a)."

            st.session_state.chat.append({"role": "patient", "content": resposta})
            st.rerun()

    st.markdown("---")
    if st.button("✅ Finalizar Caso"):
        st.session_state.page = "avaliacao"
        st.rerun()

# --- TELA DE AVALIAÇÃO ---
elif st.session_state.page == "avaliacao":
    st.title("📊 Avaliação Simulada do Caso")
    total = st.session_state.perguntas
    acertos = 0

    # Análise simples do raciocínio com base nas perguntas do aluno
    for msg in st.session_state.chat:
        if msg["role"] == "user":
            p = msg["content"].lower()
            if any(k in p for k in ["dor", "quanto", "tempo", "cor", "odor", "febre", "sangre", "sangue", "hematúria", "urina"]):
                acertos += 1

    nota = min(10, (acertos / 5) * 10) if total > 0 else 0
    st.success(f"Pontuação estimada: **{nota:.1f}/10**")

    st.write("### Resumo do seu atendimento:")
    st.markdown("- Queixa principal: dor ao urinar há 3 dias.")
    st.markdown("- Dados adicionais (após investigação): queimação ao fim da micção, urina escura, odor forte, febre baixa.")
    st.markdown("- Diagnóstico provável: **Infecção do Trato Urinário (ITU)**.")
    st.markdown("- Conduta sugerida (exemplo): exame de urina tipo I, orientar hidratação e conduta antibiótica conforme protocolo local.")

    st.write("💡 Perguntas feitas pelo estudante:")
    for msg in st.session_state.chat:
        if msg["role"] == "user":
            st.write(f"- {msg['content']}")

    st.markdown("---")
    if st.button("🔁 Reiniciar Simulação"):
        st.session_state.page = "inicio"
        st.session_state.chat = []
        st.session_state.perguntas = 0
        st.rerun()
