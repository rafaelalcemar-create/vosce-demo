# streamlit_app.py
import os
import streamlit as st
from datetime import datetime
import openai

# ---- Configuração da página ----
st.set_page_config(page_title="VOSCE - Simulação Clínica com IA", page_icon="🩺", layout="centered")

# ---- Carregar chave da OpenAI (via Streamlit secrets) ----
OPENAI_KEY = None
# Try Streamlit secrets first (deployed)
try:
    OPENAI_KEY = st.secrets["OPENAI_API_KEY"]
except Exception:
    OPENAI_KEY = os.getenv("OPENAI_API_KEY")

if OPENAI_KEY:
    openai.api_key = OPENAI_KEY

# ---- Estilo (balõezinhos simples) ----
st.markdown(
    """
    <style>
    .center { text-align:center }
    .logo { width:140px; margin-bottom:10px; }
    .chat-bubble-user { background:#0f1724; color:#fff; padding:10px 14px; border-radius:12px; margin:8px 0; text-align:right; }
    .chat-bubble-patient { background:#0ea5a4; color:#fff; padding:10px 14px; border-radius:12px; margin:8px 0; text-align:left; }
    .muted { color:#9aa0a6; font-size:0.95em; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---- Estado da sessão ----
if "page" not in st.session_state:
    st.session_state.page = "inicio"
if "chat" not in st.session_state:
    st.session_state.chat = []            # lista de dicts: {"role": "user"/"patient", "content": "..."}
if "meta" not in st.session_state:
    st.session_state.meta = {"aluno": "", "caso": ""}

# ---- Funções utilitárias ----
def call_openai(messages, model="gpt-3.5-turbo"):
    """Chama a API da OpenAI chat completions. Retorna texto ou mensagem de erro."""
    if not OPENAI_KEY:
        return None, "NO_API_KEY"
    try:
        resp = openai.ChatCompletion.create(
            model=model,
            messages=messages,
            max_tokens=300,
            temperature=0.2,
        )
        text = resp.choices[0].message.content.strip()
        return text, None
    except Exception as e:
        return None, str(e)

def build_system_prompt(case_short):
    return (
        "Você é um paciente real participando de uma simulação clínica para estudantes de medicina. "
        "Responda de forma breve, natural e consistente com o caso. "
        "Não entregue informações que não forem perguntadas — somente responda ao que o estudante solicitar. "
        "Se não souber, diga 'Não sei' ou 'Não lembro'. Responda em português.\n"
        f"Queixa visível ao estudante: {case_short}"
    )

def evaluate_chat(chat):
    """Heurística simples: conta cobertura de tópicos e gera nota."""
    text_user = " ".join([m["content"].lower() for m in chat if m["role"] == "user"])
    checks = {
        "dor": ["dor", "ardência", "queima"],
        "tempo": ["quanto", "tempo", "dias"],
        "urina": ["cor", "odor", "urina", "sangue", "hematúria"],
        "febre": ["febre", "calafrio"],
        "sintomas_gastro": ["náusea", "vômito", "enjoo"]
    }
    hits = 0
    for kws in checks.values():
        if any(k in text_user for k in kws):
            hits += 1
    nota = round(min(10, (hits / len(checks)) * 10), 1)
    return nota, hits, len(checks)

# ---- PÁGINA INICIAL ----
if st.session_state.page == "inicio":
    st.markdown("<div class='center'>", unsafe_allow_html=True)
    st.image("https://i.imgur.com/XC6fQpX.png", width=140)
    st.markdown("</div>", unsafe_allow_html=True)

    st.title("VOSCE — Simulação Clínica Virtual")
    st.markdown("**Plataforma demonstrativa** para treinar anamnese clínica com um paciente virtual baseado em IA.")
    st.markdown("<p class='muted'>Instruções: preencha seu nome (opcional), escolha o caso e clique em Iniciar Simulação. "
                "Durante a simulação, faça perguntas ao paciente. Ao finalizar, você receberá um resumo e uma pontuação estimada.</p>", unsafe_allow_html=True)

    st.session_state.meta["aluno"] = st.text_input("Nome do estudante (opcional):", value=st.session_state.meta.get("aluno",""))
    caso = st.selectbox("Escolha o caso (apenas a queixa principal será exibida):", [
        "ITU: ardência ao urinar",
        "Cólica renal: dor lombar intensa em ondas",
        "Hematúria: presença de sangue na urina",
        "Disfunção miccional: jato fraco e esforço"
    ])
    st.session_state.meta["caso"] = caso

    col1, col2 = st.columns([1,1])
    with col1:
        if st.button("🚀 Iniciar Simulação"):
            # reset chat e ir para simulação
            st.session_state.chat = []
            st.session_state.page = "simulacao"
            st.experimental_rerun()
    with col2:
        st.write("")  # espaço para alinhamento

# ---- PÁGINA DE SIMULAÇÃO ----
elif st.session_state.page == "simulacao":
    st.header("Atendimento Simulado — Converse com o paciente")
    st.markdown(f"<small class='muted'>Queixa visível: {st.session_state.meta.get('caso','')}</small>", unsafe_allow_html=True)
    st.markdown("---")

    # mostrar histórico do chat
    for m in st.session_state.chat:
        if m["role"] == "user":
            st.markdown(f"<div class='chat-bubble-user'><strong>Você:</strong><br>{m['content']}</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='chat-bubble-patient'><strong>Paciente:</strong><br>{m['content']}</div>", unsafe_allow_html=True)

    # entrada do estudante
    pergunta = st.text_input("Digite sua pergunta para o paciente:", key="input_pergunta")

    cols = st.columns([1,1])
    with cols[0]:
        if st.button("Enviar pergunta"):
            if pergunta and pergunta.strip():
                # adicionar mensagem do estudante
                st.session_state.chat.append({"role":"user","content": pergunta})
                # preparar prompt para IA
                system_prompt = build_system_prompt(st.session_state.meta.get("caso",""))
                messages = [{"role":"system", "content": system_prompt}]
                # enviar histórico reduzido
                for m in st.session_state.chat[-12:]:
                    if m["role"] == "user":
                        messages.append({"role":"user","content": m["content"]})
                    else:
                        messages.append({"role":"assistant","content": m["content"]})
                # chamada OpenAI
                reply_text, err = call_openai(messages)
                if err == "NO_API_KEY":
                    # fallback simples sem API
                    p = pergunta.lower()
                    if "dor" in p: reply_text = "É uma queimação no fim da micção."
                    elif "quanto" in p or "tempo" in p: reply_text = "Começou há uns três dias."
                    elif "cor" in p or "urina" in p or "odor" in p: reply_text = "A urina está mais escura e com odor forte."
                    elif "febre" in p: reply_text = "Tive febre baixa ontem."
                    else: reply_text = "Não sei."
                elif err:
                    reply_text = f"[ERRO NA API: {err}]"
                # adicionar resposta do paciente
                st.session_state.chat.append({"role":"patient","content": reply_text})
                # limpar input (Streamlit não limpa automaticamente)
if "input_pergunta" in st.session_state:
    st.session_state.input_pergunta = ""
                st.experimental_rerun()

    with cols[1]:
        if st.button("✅ Finalizar caso / Avaliar"):
            st.session_state.page = "avaliacao"
            st.experimental_rerun()

    st.markdown("---")
    if st.button("🔙 Voltar ao início"):
        st.session_state.page = "inicio"
        st.session_state.chat = []
        st.experimental_rerun()

# ---- PÁGINA DE AVALIAÇÃO ----
elif st.session_state.page == "avaliacao":
    st.header("Relatório e Avaliação")
    nota, hits, total = evaluate_chat(st.session_state.chat)
    st.success(f"Pontuação estimada: {nota:.1f}/10  (cobertura: {hits}/{total})")
    st.markdown("### Resumo do caso com base nas respostas do paciente:")
    patient_text = " ".join([m["content"] for m in st.session_state.chat if m["role"]=="patient"])
    if patient_text:
        st.write(patient_text)
    else:
        st.write("Nenhuma resposta registrada.")

    st.markdown("### Perguntas feitas pelo estudante:")
    for m in st.session_state.chat:
        if m["role"] == "user":
            st.write(f"- {m['content']}")

    st.markdown("---")
    st.info("Observação: essa avaliação é heurística e serve apenas para demonstração do protótipo VOSCE.")
    col1, col2 = st.columns([1,1])
    with col1:
        if st.button("🔁 Reiniciar simulação"):
            st.session_state.page = "inicio"
            st.session_state.chat = []
            st.experimental_rerun()
    with col2:
        if st.button("🏠 Voltar ao início"):
            st.session_state.page = "inicio"
            st.session_state.chat = []
            st.experimental_rerun()
