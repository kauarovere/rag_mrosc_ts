"""
app_streamlit.py
================
Interface principal do RAG Jurídico MROSC.

Uso:
  streamlit run app_streamlit.py
  streamlit run app_streamlit.py -- --provider groq
"""

import sys
from pathlib import Path

# Garante que o diretório raiz está no path para imports absolutos
sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv
from src.auth import (
    exchange_code_for_session,
    get_google_oauth_url,
    is_authenticated,
    sign_out,
)

load_dotenv()

# ---------------------------------------------------------------------------
# Configuração da página (deve ser o PRIMEIRO comando Streamlit)
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="ParcerIA — Consultor Jurídico MROSC",
    page_icon=None,
    layout="centered",
    initial_sidebar_state="expanded",
    menu_items={
        "About": (
            "**ParcerIA**\n\n"
            "Consultor jurídico inteligente para a Lei Federal 13.019/2014 e o "
            "Decreto Municipal SP 57.575/2016.\n\n"
            "Esta é uma ferramenta informativa, não um canal oficial da Prefeitura de São Paulo."
        )
    },
)

# ---------------------------------------------------------------------------
# Paleta de cores — Dark Mode (estilo Claude)
# ---------------------------------------------------------------------------
FUNDO    = "#1c1c1c"   # carvão escuro — fundo principal
FUNDO_S  = "#252525"   # carvão médio — sidebar, cards
FUNDO_E  = "#2e2e2e"   # carvão claro — hover, inputs
TEXTO    = "#e8e6e1"   # off-white quente — texto principal
TEXTO_S  = "#9a9790"   # cinza quente — texto secundário
ROXO    = "#a78bfa"   # roxo claro — cor primária (mais legível no dark)
ROXO_D  = "#8b6cf0"   # roxo médio — hover states
AMARELO = "#f8ae39"   # amarelo — accent, destaques
BORDA   = "rgba(255,255,255,0.08)"  # borda sutil dark

# Mantém aliases para compatibilidade com badges legados
AZUL   = "#c8d8e8"   # azul claro — texto em badges escuros
AZUL_M = "#2a3a4a"   # para gradientes
CINZA_F = FUNDO_S

# ---------------------------------------------------------------------------
# CSS — Design System Profissional
# ---------------------------------------------------------------------------
st.markdown(
    f"""
    <style>
    /* ── Tipografia ── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Open+Sans:wght@400;600;700&display=swap');
    html, body, [class*="css"] {{ font-family: 'Inter', sans-serif; }}

    /* ── Reset de margens do bloco principal ── */
    .block-container {{ padding-top: 3.5rem !important; padding-bottom: 2rem; overflow: visible !important; }}

    /* ── Background global dark ── */
    .stApp, html, body {{ background-color: {FUNDO} !important; }}

    /* ── Oculta o header nativo do Streamlit ── */
    [data-testid="stHeader"] {{ display: none !important; }}

    /* ── Nossa topbar (substitui o header do Streamlit) ── */
    .parceria-topbar {{
        position: fixed;
        top: 0;
        left: 21rem;
        right: 0;
        height: 52px;
        background: {FUNDO};
        border-bottom: 1px solid {BORDA};
        display: flex;
        align-items: center;
        padding: 0 1.5rem;
        z-index: 999999;
    }}
    .parceria-topbar__name {{
        font-size: 1.1rem;
        font-weight: 700;
        letter-spacing: -0.4px;
        line-height: 1;
        user-select: none;
    }}
    .parceria-topbar__name .parc {{ color: {TEXTO}; }}
    .parceria-topbar__name .ia   {{ color: {ROXO}; font-style: italic; }}

    /* ── Tela de boas-vindas ── */
    .welcome-screen {{
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: flex-end;
        min-height: calc(100vh - 180px);
        padding: 0 1rem 4rem;
        text-align: center;
    }}
    .welcome-greeting {{
        font-family: 'Open Sans', sans-serif !important;
        font-size: 3.8rem !important;
        font-weight: 700 !important;
        color: {AZUL} !important;
        letter-spacing: -1px !important;
        margin: 0 0 0.8rem 0 !important;
        line-height: 1.1 !important;
    }}
    .welcome-greeting span.ia-color {{ color: {ROXO} !important; font-style: italic; }}
    .welcome-sub {{
        font-family: 'Open Sans', sans-serif !important;
        font-size: 1.2rem !important;
        color: #8a95a3 !important;
        margin: 0 !important;
        font-weight: 400 !important;
        max-width: 560px;
        line-height: 1.55;
    }}

    /* ── Badges ── */
    .badge {{
        display: inline-block;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.68rem;
        font-weight: 700;
        letter-spacing: 0.3px;
        margin-right: 4px;
        vertical-align: middle;
    }}
    .badge--lei      {{ background: {ROXO}; color: #0d0d0d; }}
    .badge--decreto  {{ background: {AMARELO}; color: #1c1c1c; }}
    .badge--artigo   {{ background: {FUNDO_E}; color: {TEXTO}; border: 1px solid {BORDA}; }}
    .badge--revogado {{ background: #7f1d1d; color: #fecaca; }}
    .badge--alterado {{ background: #78350f; color: #fde68a; }}

    /* ── Cards de fonte ── */
    .source-card {{
        border: 1px solid {BORDA};
        border-left: 3px solid {AMARELO};
        border-radius: 6px;
        padding: 0.7rem 1rem;
        margin: 0.35rem 0;
        background: {FUNDO_S};
        font-size: 0.81rem;
        color: {TEXTO};
        line-height: 1.5;
    }}
    .source-card--lei      {{ border-left-color: {ROXO}; }}
    .source-card--revogado {{ border-left-color: #f87171; background: #2d1515; }}
    .source-card__trecho   {{ color: {TEXTO_S}; font-size: 0.78rem; margin-top: 0.4rem; display: block; }}

    /* ── Alertas ── */
    .alert-no-base {{
        background: #2a2200;
        border: 1px solid rgba(248,174,57,0.35);
        border-left: 3px solid {AMARELO};
        border-radius: 6px;
        padding: 0.85rem 1.1rem;
        margin: 0.6rem 0;
        color: #fde68a;
        font-size: 0.88rem;
    }}
    .alert-no-base strong {{ color: {ROXO}; }}
    .alert-error {{
        background: #2d1515;
        border: 1px solid rgba(248,113,113,0.3);
        border-left: 3px solid #f87171;
        border-radius: 6px;
        padding: 0.85rem 1.1rem;
        margin: 0.6rem 0;
        color: #fecaca;
        font-size: 0.88rem;
    }}

    /* ── Modal de Aviso Legal ── */
    .modal-overlay {{
        display: none;
        position: fixed;
        inset: 0;
        background: rgba(0, 0, 0, 0.55);
        z-index: 9999998;
        align-items: center;
        justify-content: center;
        backdrop-filter: blur(3px);
    }}
    .modal-overlay.active {{ display: flex; }}
    .modal-box {{
        background: {FUNDO_S};
        border: 1px solid {BORDA};
        border-radius: 14px;
        padding: 2rem 2.2rem 1.8rem;
        max-width: 520px;
        width: 90%;
        box-shadow: 0 20px 60px rgba(0,0,0,0.6);
        position: relative;
        animation: modalIn 0.25s ease;
    }}
    @keyframes modalIn {{
        from {{ opacity: 0; transform: translateY(12px) scale(0.97); }}
        to   {{ opacity: 1; transform: translateY(0)  scale(1);    }}
    }}
    .modal-box__title {{
        font-size: 1rem;
        font-weight: 700;
        color: {TEXTO};
        margin: 0 0 0.8rem 0;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }}
    .modal-box__title::before {{
        content: '';
        display: inline-block;
        width: 4px;
        height: 1.1rem;
        background: {AMARELO};
        border-radius: 2px;
        flex-shrink: 0;
    }}
    .modal-box__body {{
        font-size: 0.86rem;
        color: {TEXTO_S};
        line-height: 1.7;
        margin: 0 0 1.4rem 0;
    }}
    .modal-box__body strong {{ color: {TEXTO}; }}
    .modal-btn {{
        display: inline-block;
        background: {ROXO};
        color: #fff;
        border: none;
        border-radius: 7px;
        padding: 0.6rem 1.6rem;
        font-size: 0.88rem;
        font-weight: 600;
        cursor: pointer;
        transition: background 0.18s ease, transform 0.1s ease;
        font-family: 'Inter', sans-serif;
    }}
    .modal-btn:hover {{ background: {ROXO_D}; transform: translateY(-1px); }}
    .modal-btn:active {{ transform: translateY(0); }}

    /* ── Botões ── */
    .stButton > button {{
        background: {ROXO} !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 6px !important;
        font-size: 0.83rem !important;
        font-weight: 500 !important;
        transition: background 0.18s ease, transform 0.12s ease, box-shadow 0.18s ease !important;
    }}
    .stButton > button:hover {{
        background: {ROXO_D} !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 3px 10px rgba(139, 85, 216, 0.28) !important;
    }}
    .stButton > button:active {{ transform: translateY(0) !important; }}

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {{
        background: {FUNDO_S} !important;
        border-right: 1px solid {BORDA};
    }}
    [data-testid="stSidebar"] h3 {{
        color: {TEXTO};
        font-size: 0.82rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }}

    /* ── Sidebar labels ── */
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] .stSlider label,
    [data-testid="stSidebar"] .stSelectbox label {{
        font-size: 0.82rem !important;
        font-weight: 600 !important;
        color: {TEXTO} !important;
    }}

    /* ── Chat input ── */
    [data-testid="stChatInput"],
    [data-testid="stChatInput"] textarea,
    [data-testid="stChatInputTextArea"],
    .stChatInput > div,
    .stChatInput textarea {{
        background: {FUNDO_E} !important;
        border-color: {BORDA} !important;
        color: {TEXTO} !important;
        outline: none !important;
        box-shadow: none !important;
    }}
    [data-testid="stChatInput"]:focus-within,
    [data-testid="stChatInput"] textarea:focus,
    .stChatInput textarea:focus {{
        border-color: {ROXO} !important;
        box-shadow: 0 0 0 2px rgba(167,139,250,0.2) !important;
        outline: none !important;
    }}
    /* Remove qualquer vermelho residual do Streamlit */
    textarea:focus {{ outline-color: {ROXO} !important; }}

    /* ── Oculta avatares do chat de forma agressiva ── */
    div[data-testid="stChatMessage"] > div:first-child,
    div[data-testid="stChatMessageAvatar"],
    .stChatMessageAvatar,
    .stAvatar,
    div[class*="stAvatar"] {{
        display: none !important;
    }}

    /* ── Estilo Chat Bubble (ChatGPT/Claude) ── */
    div[data-testid="stChatMessage"] {{
        background-color: transparent !important;
        gap: 0 !important;
    }}

    .user-msg-marker, .assistant-msg-marker {{
        display: none !important;
    }}

    div[data-testid="stChatMessage"]:has(.user-msg-marker) {{
        display: flex !important;
        flex-direction: row !important;
        justify-content: flex-end !important;
        align-items: center !important;
        width: 100% !important;
    }}
    
    div[data-testid="stChatMessage"]:has(.user-msg-marker) > div[data-testid="stChatMessageContent"] {{
        background-color: #383838 !important;
        color: #ffffff !important;
        border-radius: 1.2rem !important;
        padding: 0.7rem 1.2rem !important;
        max-width: 75% !important;
        flex-grow: 0 !important;
        width: fit-content !important;
        margin-left: auto !important;
        margin-right: 0 !important;
        display: block !important;
    }}

    /* Remove qualquer margem parasita de todos os níveis internos do Streamlit */
    div[data-testid="stChatMessage"]:has(.user-msg-marker) > div[data-testid="stChatMessageContent"] .element-container,
    div[data-testid="stChatMessage"]:has(.user-msg-marker) > div[data-testid="stChatMessageContent"] .stMarkdown,
    div[data-testid="stChatMessage"]:has(.user-msg-marker) div[data-testid="stMarkdownContainer"],
    div[data-testid="stChatMessage"]:has(.user-msg-marker) p {{
        margin: 0 !important;
        padding: 0 !important;
        line-height: 1.5 !important;
        text-align: left !important;
    }}
    
    /* Esconde spans e quebras de linha acidentais */
    div[data-testid="stChatMessage"]:has(.user-msg-marker) br {{
        display: none !important;
    }}

    div[data-testid="stChatMessage"]:has(.assistant-msg-marker) {{
        display: flex !important;
        flex-direction: row !important;
        justify-content: flex-start !important;
        width: 100% !important;
    }}

    div[data-testid="stChatMessage"]:has(.assistant-msg-marker) > div[data-testid="stChatMessageContent"] {{
        padding: 0.5rem 0 !important;
        max-width: 90% !important;
        flex-grow: 1 !important;
        margin-left: 0 !important;
    }}

    /* ── Slider — accent-color é a forma mais confiável no Streamlit ── */
    [data-testid="stSlider"] input[type="range"] {{
        accent-color: {ROXO} !important;
    }}
    /* Números min/max sempre visíveis (padrão do Streamlit só mostra no hover) */
    [data-testid="stTickBarMin"],
    [data-testid="stTickBarMax"] {{
        opacity: 1 !important;
        color: {AZUL} !important;
        font-size: 0.75rem !important;
        font-weight: 500 !important;
    }}
    /* Valor atual acima do thumb — sempre visível */
    [data-testid="stSlider"] [data-baseweb="tooltip"] {{
        opacity: 1 !important;
        visibility: visible !important;
    }}

    /* ── Divider ── */
    hr {{ border-color: rgba(13, 49, 69, 0.1) !important; }}

    /* ── Expander ── */
    .streamlit-expanderHeader {{
        font-size: 0.82rem !important;
        font-weight: 600 !important;
        color: {AZUL} !important;
        background: {CINZA_F} !important;
        border-radius: 6px !important;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Autenticação — troca code OAuth por sessão
# ---------------------------------------------------------------------------
params = st.query_params
if "code" in params and not is_authenticated(st.session_state):
    auth_data = exchange_code_for_session(params["code"])
    if auth_data:
        st.session_state["auth_user"] = auth_data
        st.query_params.clear()
        st.rerun()
    else:
        st.error("Falha na autenticação. Tente novamente.")
        st.stop()

if not is_authenticated(st.session_state):
    # ── Tela de Login ─────────────────────────────────────────────────────
    try:
        oauth_url = get_google_oauth_url()
    except Exception:
        oauth_url = ""

    st.markdown(
        f"""
        <style>
        .login-wrap {{
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 70vh;
            gap: 24px;
            text-align: center;
        }}
        .login-title {{
            font-size: 2.4rem;
            font-weight: 800;
            color: {TEXTO};
            line-height: 1.2;
        }}
        .login-title .ia {{ color: {ROXO}; font-style: italic; }}
        .login-sub {{
            font-size: 1rem;
            color: {TEXTO_S};
            max-width: 400px;
        }}
        .login-btn {{
            display: inline-flex;
            align-items: center;
            gap: 12px;
            background: {ROXO};
            color: #fff;
            font-size: 1rem;
            font-weight: 600;
            padding: 14px 32px;
            border-radius: 12px;
            text-decoration: none;
            transition: background 0.2s;
        }}
        .login-btn:hover {{ background: {ROXO_D}; }}
        </style>
        <div class="login-wrap">
            <div class="login-title">Parcer<span class="ia">IA</span></div>
            <div class="login-sub">Consultor jurídico inteligente para o MROSC.<br>Faça login para continuar.</div>
            <a class="login-btn" href="{oauth_url}" target="_blank">
                <svg width="20" height="20" viewBox="0 0 48 48">
                    <path fill="#FFF" d="M44.5 20H24v8.5h11.8C34.7 33.9 30.1 37 24 37c-7.2 0-13-5.8-13-13s5.8-13 13-13c3.1 0 5.9 1.1 8.1 2.9l6.4-6.4C34.6 4.1 29.6 2 24 2 11.8 2 2 11.8 2 24s9.8 22 22 22c11 0 21-8 21-22 0-1.3-.2-2.7-.5-4z"/>
                </svg>
                Entrar com Google
            </a>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.stop()

# ---------------------------------------------------------------------------
# Cabeçalho (só exibido após login)
# ---------------------------------------------------------------------------
st.markdown(
    """
    <div class="parceria-topbar">
        <span class="parceria-topbar__name">
            <span class="parc">Parcer</span><span class="ia">IA</span>
        </span>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    # ── Usuário logado ────────────────────────────────────────────────
    user = st.session_state.get("auth_user", {})
    user_name = user.get("name", "") or user.get("email", "Usuário")
    user_email = user.get("email", "")
    st.markdown(
        f"""
        <div style="display:flex; align-items:center; gap:10px; padding:4px 0 12px;">
            <div style="flex:1; min-width:0;">
                <div style="font-weight:600; font-size:0.88rem; color:{TEXTO}; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">{user_name}</div>
                <div style="font-size:0.75rem; color:{TEXTO_S}; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">{user_email}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("Sair", use_container_width=True):
        sign_out()
        st.session_state.clear()
        st.rerun()
    st.divider()
    st.markdown("### Configurações")

    provider_options = {
        "Groq": "groq",
        "Google Gemini": "gemini",
    }
    selected_label = st.selectbox(
        "Provedor de LLM",
        options=list(provider_options.keys()),
        index=0,
        help="Escolha o modelo de linguagem: Groq ou Google Gemini.",
    )
    selected_provider = provider_options[selected_label]

    k_chunks = st.slider(
        "Fontes desejáveis por consulta",
        min_value=2,
        max_value=12,
        value=6,
        step=1,
        help="Quantidade de trechos legais usados como contexto. Valores maiores geram respostas mais completas, porém mais lentas.",
    )



    st.markdown("### Perguntas sugeridas")
    example_questions = [
        "O que é um termo de fomento?",
        "Quando é obrigatório o chamamento público e quais são as exceções?",
        "Qual o prazo de vigência de uma parceria de natureza continuada?",
        "Quais são as hipóteses de dispensa de chamamento público?",
        "O que é uma organização da sociedade civil para fins do MROSC?",
    ]
    for q in example_questions:
        if st.button(q, use_container_width=True, key=f"example_{q[:20]}"):
            st.session_state["input_question"] = q
            st.rerun()

    st.divider()
    st.markdown("### Adicionar Documentos")
    uploaded_files = st.file_uploader(
        "Faça upload de PDFs ou DOCXs",
        type=["pdf", "docx"],
        accept_multiple_files=True,
    )
    
    if uploaded_files:
        if st.button("Salvar e Processar Arquivos", use_container_width=True):
            with st.spinner("Processando e gerando embeddings (isso pode demorar um pouco)..."):
                import subprocess
                data_dir = Path("data")
                data_dir.mkdir(exist_ok=True)
                
                for uploaded_file in uploaded_files:
                    file_path = data_dir / uploaded_file.name
                    with open(file_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                
                try:
                    subprocess.run([sys.executable, "src/ingest.py"], check=True)
                    st.session_state["chain"] = None # força recarregar a chain
                    st.success("✅ Banco atualizado! O RAG já está ciente dos novos documentos.")
                except subprocess.CalledProcessError as e:
                    st.error(f"Erro durante a ingestão: {e}")

    st.divider()
    st.caption(
        "Esta ferramenta é de uso informativo e não constitui canal oficial da Prefeitura de São Paulo."
    )

# ---------------------------------------------------------------------------
# Inicialização da sessão
# ---------------------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state["messages"] = []


@st.cache_resource(show_spinner=False)
def _build_chain_cached(provider: str, k: int):
    """
    Constrói e armazena a RAG chain em cache no nível do servidor.

    @st.cache_resource garante que o modelo de embeddings e o índice FAISS
    são carregados UMA ÚNICA VEZ por processo do servidor — mesmo que múltiplos
    usuários acessem a aplicação ao mesmo tempo. Isso é fundamental para caber
    nos 512 MB de RAM do plano gratuito do Render.

    O cache é invalidado automaticamente se `provider` ou `k` mudarem.
    """
    from src.rag_chain import build_rag_chain
    return build_rag_chain(provider=provider, k=k)


def get_or_init_chain(provider: str, k: int):
    """Carrega ou reutiliza a chain (evita reinicializar a cada mensagem)."""
    with st.spinner(
        "Pensando"
    ):
        try:
            return _build_chain_cached(provider, k)
        except RuntimeError as e:
            st.error(
                f"**Vector store não encontrado.**\n\n"
                f"Execute primeiro no terminal:\n```\npython src/ingest.py\n```\n\n"
                f"Detalhes: {e}"
            )
            return None
        except Exception as e:
            st.error(f"Erro ao inicializar a chain: {e}")
            return None


# ---------------------------------------------------------------------------
# Helpers de renderização
# ---------------------------------------------------------------------------

def render_source_badges(meta: dict) -> str:
    """Gera HTML de badges para exibição das fontes."""
    fonte = meta.get("fonte", "?")
    artigo = meta.get("artigo", "?")
    status = meta.get("status", "vigente")

    badge_class = "badge--decreto" if "Decreto" in fonte else "badge--lei"
    html = f'<span class="badge {badge_class}">{fonte}</span>'
    
    tipo = meta.get("tipo", "desconhecido")
    if tipo in ["lei_federal", "decreto_municipal"]:
        html += f'<span class="badge badge--artigo">Art. {artigo}</span>'
    else:
        html += f'<span class="badge badge--artigo">{artigo}</span>'

    if status == "revogado":
        html += '<span class="badge badge--revogado">Revogado</span>'
    elif status == "alterado":
        html += '<span class="badge badge--alterado">Alterado</span>'

    return html


def render_source_cards(source_docs: list) -> None:
    """Renderiza os cards de fontes citadas abaixo da resposta."""
    if not source_docs:
        return

    # Remove duplicatas de artigos
    seen = set()
    unique_docs = []
    for doc in source_docs:
        key = (doc.metadata.get("fonte", ""), doc.metadata.get("artigo", ""))
        if key not in seen:
            seen.add(key)
            unique_docs.append(doc)

    with st.expander(f"Fontes consultadas — {len(unique_docs)} artigo(s)", expanded=False):
        for doc in unique_docs:
            meta = doc.metadata
            fonte = meta.get("fonte", "?")
            status = meta.get("status", "vigente")

            card_class = "source-card"
            if "Lei" in fonte:
                card_class += " source-card--lei"
            if status == "revogado":
                card_class += " source-card--revogado"

            badges = render_source_badges(meta)
            trecho = doc.page_content[:300].replace("\n", " ") + (
                "..." if len(doc.page_content) > 300 else ""
            )

            st.markdown(
                f"""
                <div class="{card_class}">
                    {badges}
                    <span class="source-card__trecho">{trecho}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )


# ---------------------------------------------------------------------------
# Histórico do chat
# ---------------------------------------------------------------------------
def render_chat_history():
    """Renderiza o histórico completo da conversa."""
    for message in st.session_state["messages"]:
        role = message["role"]
        content = message["content"]
        source_docs = message.get("source_documents", [])

        if role == "user":
            with st.chat_message("user"):
                st.markdown(f'<span class="user-msg-marker"></span>{content}', unsafe_allow_html=True)
        else:
            with st.chat_message("assistant"):
                st.markdown('<div class="assistant-msg-marker"></div>', unsafe_allow_html=True)
                from src.rag_chain import has_base_in_documents

                if not has_base_in_documents(content):
                    st.markdown(
                        """
                        <div class="alert-no-base">
                            <strong>Informação não localizada nos documentos</strong><br/>
                            O sistema não encontrou base legal nos documentos indexados para esta pergunta.
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                st.markdown(content)

                if source_docs:
                    render_source_cards(source_docs)


# ---------------------------------------------------------------------------
# Área principal do chat
# ---------------------------------------------------------------------------

# Tela de boas-vindas (exibida só quando não há histórico)
if not st.session_state["messages"]:
    components.html(
        f"""
        <!DOCTYPE html>
        <html>
        <head>
        <meta charset="utf-8">
        <link href="https://fonts.googleapis.com/css2?family=Open+Sans:wght@400;700&display=swap" rel="stylesheet">
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            html, body {{ background: {FUNDO}; overflow: hidden; }}
            .welcome-wrap {{
                display: flex;
                flex-direction: column;
                align-items: center;
                text-align: center;
                padding: 2.5rem 1rem 1rem;
            }}
            .greeting {{
                font-family: 'Open Sans', sans-serif;
                font-size: 3.6rem;
                font-weight: 700;
                color: {TEXTO};
                letter-spacing: -1px;
                line-height: 1.1;
                margin-bottom: 0.8rem;
            }}
            .mrosc {{ color: {ROXO}; font-style: italic; }}
            .cursor {{
                display: inline-block;
                color: {ROXO};
                animation: blink 0.75s step-end infinite;
            }}
            @keyframes blink {{
                0%, 100% {{ opacity: 1; }}
                50%       {{ opacity: 0; }}
            }}
            .sub {{
                font-family: 'Open Sans', sans-serif;
                font-size: 1.2rem;
                color: {TEXTO_S};
                font-weight: 400;
                max-width: 560px;
                line-height: 1.55;
                opacity: 0;
                transition: opacity 0.7s ease;
            }}
        </style>
        </head>
        <body>
        <div class="welcome-wrap">
            <p class="greeting">
                <span id="p1"></span><span id="p2" class="mrosc"></span><span id="p3"></span><span class="cursor">|</span>
            </p>
        </div>
        <script>
            var part1 = "No que posso ajudar hoje?";
            var part2 = "";
            var part3 = "";
            var p1 = document.getElementById('p1');
            var p2 = document.getElementById('p2');
            var p3 = document.getElementById('p3');
            var cursor = document.querySelector('.cursor');
            var sub = document.getElementById('sub');
            var i = 0;
            var total = part1.length + part2.length + part3.length;
            function typeChar() {{
                if (i < part1.length) {{
                    p1.textContent += part1[i];
                }} else if (i < part1.length + part2.length) {{
                    p2.style.display = 'inline';
                    p2.textContent += part2[i - part1.length];
                }} else {{
                    p3.textContent += part3[i - part1.length - part2.length];
                }}
                i++;
                if (i < total) {{
                    setTimeout(typeChar, 44);
                }} else {{
                    setTimeout(function() {{
                        cursor.style.display = 'none';
                        sub.style.opacity = '1';
                    }}, 700);
                }}
            }}
            setTimeout(typeChar, 400);
        </script>
        </body>
        </html>
        """,
        height=260,
        scrolling=False,
    )

render_chat_history()

input_value = st.session_state.pop("input_question", "")
chat_val = st.chat_input(
    "Digite sua pergunta sobre a Lei MROSC ou o Decreto Municipal...",
)
question = chat_val or input_value

if question:
    chain = get_or_init_chain(selected_provider, k_chunks)

    if chain is None:
        st.stop()

    st.session_state["messages"].append({"role": "user", "content": question})

    with st.chat_message("user"):
        st.markdown(f'<span class="user-msg-marker"></span>{question}', unsafe_allow_html=True)

    with st.chat_message("assistant"):
        st.markdown('<div class="assistant-msg-marker"></div>', unsafe_allow_html=True)
        with st.spinner("Pensando"):
            try:
                from src.rag_chain import ask, has_base_in_documents

                result = ask(chain, question)
                answer = result["answer"]
                # Remove aviso jurídico gerado pelo LLM (mesmo sem instrução no prompt)
                import re as _re
                answer = _re.sub(
                    r"\u26a0\ufe0f?\s*\*?Esta resposta[^\n]*análise jurídica profissional\.?\*?",
                    "",
                    answer,
                    flags=_re.IGNORECASE,
                ).strip()
                source_docs = result.get("source_documents", [])

            except Exception as e:
                answer = f"Erro ao processar a pergunta: {e}"
                source_docs = []

        if "Erro ao processar" in answer:
            st.markdown(
                f"""
                <div class="alert-error">
                    <strong>Erro ao processar a pergunta</strong><br/>
                    {answer.replace("Erro ao processar a pergunta: ", "")}
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            if not has_base_in_documents(answer):
                st.markdown(
                    """
                    <div class="alert-no-base">
                        <strong>Informação não localizada nos documentos</strong><br/>
                        O sistema não encontrou base legal nos documentos indexados para esta pergunta.
                        A resposta abaixo indica o que foi possível recuperar.
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            st.markdown(answer)

            if source_docs:
                render_source_cards(source_docs)

    st.session_state["messages"].append(
        {
            "role": "assistant",
            "content": answer,
            "source_documents": source_docs,
        }
    )

# ---------------------------------------------------------------------------
# Botão limpar conversa
# ---------------------------------------------------------------------------
col1, col2, col3 = st.columns([4, 2, 4])
with col2:
    if st.button("Limpar conversa", use_container_width=True):
        st.session_state["messages"] = []
        st.rerun()

# ---------------------------------------------------------------------------
# Rodapé
# ---------------------------------------------------------------------------
st.markdown(
    f"""
    <div class="modal-overlay" id="legalModal">
        <div class="modal-box">
            <p class="modal-box__title">Aviso Legal</p>
            <p class="modal-box__body">
                Este sistema é uma ferramenta informativa de consulta a textos jurídicos e
                <strong>não substitui análise jurídica profissional</strong>.
                As respostas são geradas automaticamente com base nos documentos indexados
                (Lei 13.019/2014 e Decreto 57.575/2016) e podem conter imprecisões.<br><br>
                Para casos concretos, consulte um advogado especializado.
                Esta ferramenta <strong>não é um canal oficial da Prefeitura de São Paulo</strong>.
            </p>
            <button class="modal-btn" onclick="closeModal()">Entendi</button>
        </div>
    </div>
    <script>
        function closeModal() {{
            document.getElementById('legalModal').classList.remove('active');
            sessionStorage.setItem('legalAccepted', '1');
        }}
        (function() {{
            if (!sessionStorage.getItem('legalAccepted')) {{
                document.getElementById('legalModal').classList.add('active');
            }}
        }})();
    </script>
    """,
    unsafe_allow_html=True,
)
