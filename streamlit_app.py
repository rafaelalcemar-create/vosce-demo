# streamlit_app.py
import os
import streamlit as st
import google.generativeai as genai  # Importa a biblioteca do Google
from datetime import datetime

# ---- Configurações da página ----
st.set_page_config(page_title="VOSCE - Simulação Clínica Virtual", page_icon="🩺", layout="centered")

# ---- Configuração da API ----
# Configura a API do Google (Gemini)
GOOGLE_API_KEY = None
try:
    # Carrega a chave do Streamlit Secrets
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=GOOGLE_API_KEY)
except Exception:
    # Tenta carregar do ambiente local (se rodando no seu PC)
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    if GOOGLE_API_KEY:
        genai.configure(api_key=GOOGLE_API_KEY)

# ---- Estilo visual ----
st.markdown("""
<style>
body {background-color: #0d1117; color: #e6edf3;}
h1,h2,h3,h4 {color: #00bcd4;}
button, .stButton>button {background-color:#00bcd4; color:white; border-radius:8px; padding:0.6em 1.2em; font-weight:600;}
.chat-bubble-user {background:#1e2a38; color:#fff; padding:10px 14px; border-radius:12px; margin:8px 0; text-align:right;}
.chat-bubble-patient {background:#009688; color:#fff; padding:10px 14px; border-radius:12px; margin:8px 0; text-align:left;}
.muted {color:#9aa0a6; font-size:0.95em;}
footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ---- Sessão ----
if "page" not in st.session_state:
    st.session_state.page = "inicio"
if "chat" not in st.session_state:
    st.session_state.chat = []
if "meta" not in st.session_state:
    st.session_state.meta = {"aluno": "", "caso": ""}

# ---- Funções ----

# Função de API reescrita para o Gemini
def get_ai_response(messages_history):
    """Chama o modelo do Gemini ou retorna resposta simulada se sem chave."""
    if not GOOGLE_API_KEY:
        st.warning("Chave de API do Google não configurada. Usando respostas de fallback.", icon="⚠️")
        pergunta = messages_history[-1]["content"].lower()
        if "dor" in pergunta:
            return "Sinto uma queimação leve quando urino."
        elif "tempo" in pergunta:
            return "Isso começou há uns três dias."
        elif "urina" in pergunta:
            return "Notei que a urina está mais escura e com cheiro forte."
        elif "febre" in pergunta:
            return "Sim, tive febre leve ontem à noite."
        else:
            return "Não sei dizer, doutor."
    
    try:
        # Extrai o prompt do sistema (a primeira mensagem)
        system_prompt_text = messages_history[0]["content"]
        
        # Converte o histórico de chat para o formato do Gemini
        # Pula a primeira mensagem (sistema) e converte o resto
        gemini_history = []
        for msg in messages_history[1:]:
            # Converte 'assistant' (OpenAI) para 'model' (Gemini)
            role = "model" if msg["role"] == "assistant" else msg["role"]
            gemini_history.append({"role": role, "parts": [msg["content"]]})

        # Inicializa o modelo com o prompt do sistema
        model = genai.GenerativeModel(
            # === CORREÇÃO ESTÁ AQUI ===
            model_name="gemini-pro", # <<< MUDANÇA: Usando um modelo mais estável
            # ==========================
            system_instruction=system_prompt_text
        )

        # A API do Gemini lida com o histórico diretamente na chamada
        # A `gemini_history` já contém a última pergunta do usuário
        response = model.generate_content(gemini_history)
        
        return response.text.strip()
        
    except Exception as e:
        st.error(f"Erro ao contatar a API Google Gemini: {e}", icon="🚨")
        return "[ERRO NA API]"

def system_prompt(case_short):
    return (
        "Você é um paciente em uma simulação clínica com um estudante de medicina. "
        "Responda de forma curta e natural, sem entregar diagnósticos. "
        "Seja coerente com o caso e só revele detalhes quando perguntado. "
        f"Queixa principal: {case_short}"
    )

def evaluate_conversation(chat):
    """Gera nota simples com base em tópicos abordados."""
    user_text = " ".join([m["content"].lower() for m in chat if m["role"] == "user"])
    keywords = {
        "dor": ["dor", "ardência", "queima"],
        "tempo": ["quanto", "tempo", "dias"],
        "urina": ["urina", "odor", "cor", "sangue"],
        "febre": ["febre", "calafrio"],
        "associado": ["náusea", "enjoo", "vômito"]
    }
    hits = sum(1 for k in keywords.values() if any(w in user_text for w in k))
    nota = round((hits / len(keywords)) * 10, 1)
    return nota, hits, len(keywords)

# ---- Página inicial ----
if st.session_state.page == "inicio":
    st.markdown("<h1 style='text-align:center;'>🩺 VOSCE — Simulação Clínica Virtual</h1>", unsafe_allow_html=True)
    st.markdown("<p class='muted' style='text-align:center;'>Treine anamnese com um paciente virtual baseado em IA.</p>", unsafe_allow_html=True)
    
    st.session_state.meta["aluno"] = st.text_input("Nome do estudante (opcional):", st.session_state.meta.get("aluno", ""))
    caso = st.selectbox("Escolha o caso clínico:", [
        "Infecção do Trato Urinário (ardência ao urinar)",
        "Cólica renal (dor lombar intensa em ondas)",
        "Hematúria (presença de sangue na urina)",
        "Disfunção miccional (jato fraco e esforço)"
    ])
    st.session_state.meta["caso"] = caso

    if st.button("🚀 Iniciar Simulação"):
        st.session_state.chat = []
        st.session_state.page = "simulacao"
        st.rerun() 

# ---- Simulação ----
elif st.session_state.page == "simulacao":
    st.header("Atendimento Simulado — Converse com o paciente")
    st.markdown(f"<p class='muted'>Queixa principal: {st.session_state.meta['caso']}</p>", unsafe_allow_html=True)
    st.markdown("---")

    # Histórico
    for msg in st.session_state.chat:
        if msg["role"] == "user":
            st.markdown(f"<div class='chat-bubble-user'><b>Você:</b><br>{msg['content']}</div>", unsafe_allow_html=True)
        elif msg["role"] == "assistant":
            if not msg['content'].startswith("[ERRO NA API]"):
                st.markdown(f"<div class='chat-bubble-patient'><b>Paciente:</b><br>{msg['content']}</div>", unsafe_allow_html=True)

    pergunta = st.text_input("Digite sua pergunta para o paciente:", key="input_pergunta")

    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("Enviar pergunta"):
            if pergunta.strip():
                st.session_state.chat.append({"role": "user", "content": pergunta})
                
                # Lógica de chamada de API simplificada
                # Prepara a lista de mensagens para o Gemini
                prompt = system_prompt(st.session_state.meta["caso"])
                msgs_para_api = [{"role": "system", "content": prompt}]
                
                # Adiciona o histórico do chat
                for m in st.session_state.chat[-10:]: # Pega as últimas 10 mensagens
                    msgs_para_api.append({"role": m["role"], "content": m["content"]})
                
                # Chama a nova função get_ai_response
                resposta = get_ai_response(msgs_para_api)
                
                st.session_state.chat.append({"role": "assistant", "content": resposta})
                
                if "input_pergunta" in st.session_state:
                    st.session_state.input_pergunta = ""
                st.rerun()

    with col2:
        if st.button("✅ Finalizar Caso"):
            st.session_state.page = "avaliacao"
            st.rerun()

    if st.button("🔙 Voltar"):
        st.session_state.page = "inicio"
        st.rerun()

# ---- Avaliação ----
elif st.session_state.page == "avaliacao":
    st.header("Relatório da Simulação")
    nota, hits, total = evaluate_conversation(st.session_state.chat)
    st.success(f"Pontuação estimada: {nota}/10 (cobertura: {hits}/{total} tópicos)")
    
    st.subheader("Resumo das respostas do paciente:")
    respostas = " ".join([m["content"] for m in st.session_state.chat if m["role"] == "assistant" and not m['content'].startswith("[ERRO NA API]")])
    st.write(respostas if respostas else "Nenhuma resposta registrada.")

    st.subheader("Perguntas feitas pelo estudante:")
    perguntas_feitas = [m['content'] for m in st.session_state.chat if m["role"] == "user"]
    if perguntas_feitas:
        for p in perguntas_feitas:
            st.write(f"- {p}")
    else:
        st.write("Nenhuma pergunta registrada.")

    st.info("Observação: pontuação gerada automaticamente apenas para fins de demonstração.")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔁 Repetir caso"):
            st.session_state.page = "simulacao"
            st.session_state.chat = []
            st.rerun()
    with col2:
        if st.button("🏠 Voltar ao início"):
            st.session_state.page = "inicio"
            st.session_state.chat = []
            st.rerun()
