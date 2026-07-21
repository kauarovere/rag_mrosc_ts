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
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Configuração da página (deve ser o PRIMEIRO comando Streamlit)
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="RAG Jurídico MROSC — Prefeitura de São Paulo",
    page_icon="⚖",
    layout="centered",
    initial_sidebar_state="expanded",
    menu_items={
        "About": (
            "**RAG Jurídico MROSC**\n\n"
            "Sistema de consulta à Lei Federal 13.019/2014 e ao "
            "Decreto Municipal SP 57.575/2016.\n\n"
            "Esta é uma ferramenta informativa, não um canal oficial da Prefeitura de São Paulo."
        )
    },
)

# ---------------------------------------------------------------------------
# Paleta de cores
# ---------------------------------------------------------------------------
AZUL    = "#0d3145"   # azul escuro — fundo header, sidebar, footer
ROXO    = "#8b55d8"   # roxo — cor primária, interações, badge Lei
AMARELO = "#f8ae39"   # amarelo — accent, destaques, badge Decreto
ROXO_D  = "#6b3db8"   # roxo escuro — hover states
AZUL_M  = "#1a4a6b"   # azul médio — gradiente, elementos secundários
CINZA_F = "#f4f6f9"   # fundo geral da sidebar e cards

# ---------------------------------------------------------------------------
# CSS — Design System Profissional
# ---------------------------------------------------------------------------
st.markdown(
    f"""
    <style>
    /* ── Tipografia ── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    html, body, [class*="css"] {{ font-family: 'Inter', sans-serif; }}

    /* ── Reset de margens do bloco principal ── */
    .block-container {{ padding-top: 1rem !important; padding-bottom: 2rem; overflow: visible !important; }}

    /* ── Cabeçalho ── */
    .app-header {{
        background: linear-gradient(135deg, {AZUL} 0%, {AZUL_M} 100%);
        border-left: 4px solid {AMARELO};
        border-radius: 12px;
        padding: 1.6rem 2rem;
        margin-top: 2rem;
        margin-bottom: 1.75rem;
        box-shadow: 0 4px 18px rgba(13, 49, 69, 0.22);
    }}
    .app-header__title {{
        margin: 0 0 0.3rem 0;
        font-size: 1.45rem;
        font-weight: 700;
        color: #ffffff;
        letter-spacing: -0.3px;
        line-height: 1.3;
    }}
    .app-header__subtitle {{
        margin: 0;
        font-size: 0.82rem;
        color: rgba(255,255,255,0.72);
        font-weight: 400;
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
    .badge--lei      {{ background: {ROXO}; color: #fff; }}
    .badge--decreto  {{ background: {AMARELO}; color: {AZUL}; }}
    .badge--artigo   {{ background: {AZUL}; color: #fff; }}
    .badge--revogado {{ background: #c0392b; color: #fff; }}
    .badge--alterado {{ background: #d4801a; color: #fff; }}

    /* ── Cards de fonte ── */
    .source-card {{
        border: 1px solid #e2e8f0;
        border-left: 3px solid {AMARELO};
        border-radius: 6px;
        padding: 0.7rem 1rem;
        margin: 0.35rem 0;
        background: #ffffff;
        font-size: 0.81rem;
        color: #3d4a5c;
        line-height: 1.5;
    }}
    .source-card--lei      {{ border-left-color: {ROXO}; }}
    .source-card--revogado {{ border-left-color: #c0392b; background: #fdf5f5; }}
    .source-card__trecho   {{ color: #6b7a8d; font-size: 0.78rem; margin-top: 0.4rem; display: block; }}

    /* ── Alertas ── */
    .alert-no-base {{
        background: #fffbf0;
        border: 1px solid {AMARELO};
        border-left: 3px solid {AMARELO};
        border-radius: 6px;
        padding: 0.85rem 1.1rem;
        margin: 0.6rem 0;
        color: {AZUL};
        font-size: 0.88rem;
    }}
    .alert-no-base strong {{ color: {ROXO}; }}
    .alert-error {{
        background: #fdf5f5;
        border: 1px solid #e0a0a0;
        border-left: 3px solid #c0392b;
        border-radius: 6px;
        padding: 0.85rem 1.1rem;
        margin: 0.6rem 0;
        color: {AZUL};
        font-size: 0.88rem;
    }}

    /* ── Rodapé ── */
    .legal-footer {{
        background: {AZUL};
        border-top: 3px solid {AMARELO};
        border-radius: 8px;
        padding: 0.9rem 1.4rem;
        font-size: 0.76rem;
        color: rgba(255,255,255,0.65);
        margin-top: 2.5rem;
        text-align: center;
        line-height: 1.6;
    }}
    .legal-footer strong {{ color: {AMARELO}; }}

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
        background: {CINZA_F};
        border-right: 2px solid rgba(248, 174, 57, 0.3);
    }}
    [data-testid="stSidebar"] h3 {{
        color: {AZUL};
        font-size: 0.82rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }}

    /* ── Sidebar labels — SEM uppercase para evitar corte de texto ── */
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] .stSlider label,
    [data-testid="stSidebar"] .stSelectbox label {{
        font-size: 0.82rem !important;
        font-weight: 600 !important;
        color: {AZUL} !important;
    }}

    /* ── Chat input — corrige borda vermelha do Streamlit ── */
    [data-testid="stChatInput"],
    [data-testid="stChatInput"] textarea,
    [data-testid="stChatInputTextArea"],
    .stChatInput > div,
    .stChatInput textarea {{
        border-color: #d0d8e4 !important;
        outline: none !important;
        box-shadow: none !important;
    }}
    [data-testid="stChatInput"]:focus-within,
    [data-testid="stChatInput"] textarea:focus,
    .stChatInput textarea:focus {{
        border-color: {ROXO} !important;
        box-shadow: 0 0 0 2px rgba(139, 85, 216, 0.18) !important;
        outline: none !important;
    }}
    /* Remove qualquer vermelho residual do Streamlit */
    textarea:focus {{ outline-color: {ROXO} !important; }}

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
# Cabeçalho
# ---------------------------------------------------------------------------
st.markdown(
    """
    <div class="app-header">
        <p class="app-header__title">RAG Jurídico MROSC</p>
        <p class="app-header__subtitle">
            Consulta à Lei Federal 13.019/2014 e ao Decreto Municipal SP 57.575/2016
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### Configurações")

    provider_options = {
        "Ollama — local, sem chave": "ollama",
        "Groq — API gratuita": "groq",
        "Google Gemini — API gratuita": "gemini",
    }
    selected_label = st.selectbox(
        "Provedor de LLM",
        options=list(provider_options.keys()),
        index=1,
        help="Ollama roda localmente e não precisa de chave de API. Groq e Gemini requerem chave configurada no .env.",
    )
    selected_provider = provider_options[selected_label]

    k_chunks = st.slider(
        "Trechos recuperados por consulta",
        min_value=2,
        max_value=12,
        value=6,
        step=1,
        help="Quantidade de trechos legais usados como contexto. Valores maiores geram respostas mais completas, mas mais lentas.",
    )

    st.divider()
    st.markdown("### Base de conhecimento")
    st.markdown(
        f"""
        <div style="font-size:0.82rem; color:#3d4a5c; line-height:2;">
            <div style="display:flex; align-items:center; gap:8px; flex-wrap:nowrap; white-space:nowrap; overflow:hidden;">
                <span style="width:10px; height:10px; border-radius:50%; background:{ROXO}; flex-shrink:0; display:inline-block;"></span>
                <span>Lei Federal 13.019/2014 (MROSC)</span>
            </div>
            <div style="display:flex; align-items:center; gap:8px; flex-wrap:nowrap; white-space:nowrap; overflow:hidden; margin-top:4px;">
                <span style="width:10px; height:10px; border-radius:50%; background:{AMARELO}; flex-shrink:0; display:inline-block;"></span>
                <span>Decreto Municipal 57.575/2016 (SP)</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()
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
    st.caption(
        "Esta ferramenta é de uso informativo e não constitui canal oficial da Prefeitura de São Paulo."
    )

# ---------------------------------------------------------------------------
# Inicialização da sessão
# ---------------------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state["messages"] = []

if "chain" not in st.session_state:
    st.session_state["chain"] = None

if "chain_provider" not in st.session_state:
    st.session_state["chain_provider"] = None

if "chain_k" not in st.session_state:
    st.session_state["chain_k"] = None


def get_or_init_chain(provider: str, k: int):
    """Carrega ou reutiliza a chain (evita reinicializar a cada mensagem)."""
    if (
        st.session_state["chain"] is None
        or st.session_state["chain_provider"] != provider
        or st.session_state["chain_k"] != k
    ):
        with st.spinner(
            "Inicializando modelo de embeddings e chain — aguarde alguns instantes..."
        ):
            try:
                from src.rag_chain import build_rag_chain
                st.session_state["chain"] = build_rag_chain(provider=provider, k=k)
                st.session_state["chain_provider"] = provider
                st.session_state["chain_k"] = k
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

    return st.session_state["chain"]


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
    html += f'<span class="badge badge--artigo">Art. {artigo}</span>'

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

    with st.expander(f"Fontes consultadas — {len(unique_docs)} artigo(s)", expanded=True):
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
                st.markdown(content)
        else:
            with st.chat_message("assistant"):
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
render_chat_history()

input_value = st.session_state.pop("input_question", "")

if question := st.chat_input(
    "Digite sua pergunta sobre a Lei MROSC ou o Decreto Municipal...",
):
    chain = get_or_init_chain(selected_provider, k_chunks)

    if chain is None:
        st.stop()

    st.session_state["messages"].append({"role": "user", "content": question})

    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Consultando os documentos jurídicos..."):
            try:
                from src.rag_chain import ask, has_base_in_documents

                result = ask(chain, question)
                answer = result["answer"]
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

# Suporte a pergunta via botão da sidebar
if input_value and input_value not in [
    m["content"] for m in st.session_state["messages"] if m["role"] == "user"
]:
    st.session_state["messages"].append({"role": "user", "content": input_value})
    st.rerun()

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
    """
    <div class="legal-footer">
        <strong>Aviso Legal</strong> — Este sistema é uma ferramenta informativa de consulta a textos jurídicos e
        <strong>não substitui análise jurídica profissional</strong>. As respostas são geradas automaticamente
        com base nos documentos indexados (Lei 13.019/2014 e Decreto 57.575/2016) e podem conter imprecisões.
        Para casos concretos, consulte um advogado especializado.
        Esta ferramenta <strong>não é um canal oficial da Prefeitura de São Paulo</strong>.
    </div>
    """,
    unsafe_allow_html=True,
)
