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

import json
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

    /* ── Header Nativo e Seta da Sidebar ── */
    [data-testid="stToolbar"] {{ display: none !important; }}
    .stAppDeployButton {{ display: none !important; }}
    [data-testid="stHeader"] {{
        visibility: hidden !important;
        pointer-events: none !important;
    }}
    [data-testid="collapsedControl"] {{
        visibility: visible !important;
        pointer-events: auto !important;
        z-index: 99999999 !important;
        color: {TEXTO} !important;
    }}
    [data-testid="stSidebarHeader"] {{
        visibility: visible !important;
        display: block !important;
    }}
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
    /* ── VLibras Widget — override dark mode ── */
    /* Garante que o botão flutuante do VLibras fique acima de tudo */
    [vw] {{ z-index: 9999990 !important; }}
    [vw-access-button] {{
        z-index: 9999990 !important;
    }}
    [vw-plugin-wrapper] {{
        z-index: 9999989 !important;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# VLibras — Função reutilizável para injetar o widget em qualquer tela
# ---------------------------------------------------------------------------
def _inject_vlibras():
    """VLibras como plugin flutuante no canto direito da tela.

    O iframe do Streamlit é reposicionado via window.frameElement:
    - Fechado: 80px de largura (apenas o botão de acesso visível)
    - Aberto: 400px de largura (painel completo do avatar)

    FIXES aplicados:
    - Suprime window.alert e window.onerror ANTES de carregar vlibras-plugin.js,
      evitando o dialog "Script error." causado pelo Unity WebGL cross-origin.
    - Inicialização do Widget com retry (vlibras-plugin.js carrega assincronamente).
    """
    components.html(
        """
        <!DOCTYPE html>
        <html>
        <head>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            html, body {
                background: transparent !important;
                overflow: hidden;
                width: 100%; height: 100%;
            }
        </style>
        </head>
        <body>

        <!-- Estrutura requerida pelo VLibras -->
        <div vw class="enabled">
            <div vw-access-button class="active"></div>
            <div vw-plugin-wrapper>
                <div class="vw-plugin-top-wrapper"></div>
            </div>
        </div>

        <!-- ① Suprime SOMENTE window.alert do Unity — não toca em onerror para não
             quebrar a inicialização do vlibras-plugin.js nem o layout do Streamlit -->
        <script>
        (function suppressUnityAlert() {
            // O Unity WebGL chama window.alert("An error occurred...") ao falhar.
            // Substituímos alert() para bloquear apenas esses alertas da Unity.
            // NÃO sobrescrevemos window.onerror: o vlibras-plugin.js usa-o internamente
            // para registrar window.VLibras — sobrescrevê-lo impede a inicialização.
            var _origAlert = window.alert;
            window.alert = function(msg) {
                var s = String(msg || '').toLowerCase();
                if (s.indexOf('unity') !== -1 ||
                    s.indexOf('script error') !== -1 ||
                    s.indexOf('an error occurred') !== -1) {
                    console.warn('[VLibras] Alert Unity suprimido:', String(msg).substring(0, 80));
                    return;
                }
                _origAlert.apply(window, [msg]);
            };
            // Tenta suprimir também no parent (mesma origem no Streamlit Cloud).
            // IMPORTANTE: NÃO alteramos window.parent.onerror — o Streamlit
            // depende desse handler para controle interno de layout/componentes.
            try {
                var _pAlert = window.parent.alert;
                window.parent.alert = function(msg) {
                    var s = String(msg || '').toLowerCase();
                    if (s.indexOf('unity') !== -1 ||
                        s.indexOf('script error') !== -1 ||
                        s.indexOf('an error occurred') !== -1) {
                        console.warn('[VLibras/parent] Alert Unity suprimido.');
                        return;
                    }
                    _pAlert.apply(window.parent, [msg]);
                };
            } catch(e) { /* cross-origin — sem problema */ }
        })();
        </script>

        <script src="https://vlibras.gov.br/app/vlibras-plugin.js"></script>
        <script>
        (function () {
            var frame = window.frameElement;
            var panelOpen = false;

            /* ── Redimensiona o iframe conforme estado do VLibras ── */
            function resize(open) {
                if (!frame) return;
                panelOpen = open;
                frame.style.cssText = [
                    'position:fixed',
                    'top:0',
                    'right:0',
                    'bottom:0',
                    'height:100vh',
                    open ? 'width:400px' : 'width:80px',
                    'border:none',
                    'background:transparent',
                    'z-index:2147483646'
                ].join(';');
                // Cursor pointer só quando painel aberto
                try {
                    var pb = window.parent.document.body;
                    if (open) pb.classList.add('vlibras-active');
                    else       pb.classList.remove('vlibras-active');
                } catch(e) {}
            }

            /* Começa fechado (só o botão de 80px) */
            resize(false);

            /* ── Inicializa o VLibras — síncrono primeiro, retry como fallback ── */
            var vlibrasInstance = null;

            function tryInitVLibras(attempt) {
                attempt = attempt || 1;
                if (window.VLibras) {
                    try {
                        vlibrasInstance = new window.VLibras.Widget({
                            rootPath: 'https://vlibras.gov.br/app',
                            avatar:   'icaro',
                            position: 'R',
                            opacity:  1
                        });
                        console.log('[VLibras] Widget inicializado (tentativa ' + attempt + ')');
                    } catch(e) {
                        console.warn('[VLibras] Falha ao instanciar Widget:', e);
                    }
                } else if (attempt < 8) {
                    // vlibras-plugin.js pode carregar outros scripts de forma async
                    setTimeout(function() { tryInitVLibras(attempt + 1); }, 600);
                } else {
                    console.warn('[VLibras] window.VLibras indisponível após 8 tentativas.');
                }
            }
            // Tenta imediatamente (caso vlibras-plugin.js já carregou window.VLibras)
            // e agenda retries para caso de carregamento assíncrono
            tryInitVLibras(1);

            /* ── Controle de abertura/fechamento do painel ── */
            setTimeout(function () {
                var btn = document.querySelector('[vw-access-button]');

                if (btn) {
                    btn.addEventListener('click', function() {
                        panelOpen = !panelOpen;
                        resize(panelOpen);
                    });
                }

                /* ─────────────────────────────────────────────────────────────
                 *  Bridge de tradução: intercepta cliques no documento pai
                 *  e repassa o texto para o VLibras traduzir via Libras.
                 * ───────────────────────────────────────────────────────────── */
                function doTranslate(text) {
                    if (!text || text.length < 3) return;
                    console.log('[VLibras] 🔄 Traduzindo:', text.substring(0, 60));

                    // Método 0: API da instância do Widget (mais confiável)
                    try {
                        if (vlibrasInstance && typeof vlibrasInstance.translate === 'function') {
                            vlibrasInstance.translate(text);
                            console.log('[VLibras] 🤟 via widget.translate()');
                            return;
                        }
                    } catch(e0) { console.warn('[VLibras] widget.translate erro:', e0); }

                    // Método 1: API pública window.vlibras
                    try {
                        if (window.vlibras && typeof window.vlibras.translate === 'function') {
                            window.vlibras.translate(text);
                            console.log('[VLibras] 🤟 via vlibras.translate');
                            return;
                        }
                    } catch(e1) {}

                    // Método 2: API pelo Player
                    try {
                        if (window.VLibras && window.VLibras.Player &&
                            typeof window.VLibras.Player.translate === 'function') {
                            window.VLibras.Player.translate(text);
                            console.log('[VLibras] 🤟 via VLibras.Player.translate');
                            return;
                        }
                    } catch(e2) {}

                    // Método 3: Simula seleção de texto no iframe + eventos de clique
                    var tmp = document.createElement('p');
                    tmp.id  = 'vw-translate-tmp';
                    tmp.textContent = text;
                    tmp.style.cssText = 'position:fixed;top:0;left:0;width:1px;height:1px;' +
                                        'z-index:-999;color:rgba(0,0,0,0.01);font-size:1px;overflow:hidden;';
                    document.body.appendChild(tmp);

                    var range = document.createRange();
                    range.selectNodeContents(tmp);
                    var sel = window.getSelection();
                    sel.removeAllRanges();
                    sel.addRange(range);

                    ['mousedown', 'mouseup', 'click'].forEach(function(evtType) {
                        var opts = {bubbles: true, cancelable: true, view: window};
                        tmp.dispatchEvent(new MouseEvent(evtType, opts));
                        document.body.dispatchEvent(new MouseEvent(evtType, opts));
                        document.dispatchEvent(new MouseEvent(evtType, opts));
                    });
                    console.log('[VLibras] 🤟 via simulação DOM');

                    setTimeout(function() {
                        var el = document.getElementById('vw-translate-tmp');
                        if (el && el.parentNode) el.parentNode.removeChild(el);
                    }, 5000);
                }

                function translateWithOpen(text) {
                    if (!panelOpen) return;
                    doTranslate(text);
                }

                try {
                    var pDoc = window.parent.document;
                    var pWin = window.parent;

                    if (!pDoc.querySelector('#vw-bridge-style')) {
                        var sty = pDoc.createElement('style');
                        sty.id  = 'vw-bridge-style';
                        sty.textContent =
                            'body.vlibras-active p:hover,' +
                            'body.vlibras-active li:hover,' +
                            'body.vlibras-active h1:hover,' +
                            'body.vlibras-active h2:hover,' +
                            'body.vlibras-active h3:hover,' +
                            'body.vlibras-active h4:hover,' +
                            'body.vlibras-active h5:hover,' +
                            'body.vlibras-active h6:hover {' +
                            'cursor: pointer !important; outline: 2px dashed #7B2FBE55 !important; }';
                        pDoc.head.appendChild(sty);
                    }

                    pDoc.body.addEventListener('click', function(e) {
                        if (!panelOpen) return;

                        var tag = (e.target.tagName || '').toUpperCase();
                        if (/^(INPUT|TEXTAREA|BUTTON|A|SELECT|OPTION|SVG|PATH)$/.test(tag)) return;

                        var sel  = pWin.getSelection();
                        var text = sel && sel.toString().trim();
                        if (!text || text.length < 3) {
                            var el = e.target.closest('p, li, h1, h2, h3, h4, h5, h6, td, th') || e.target;
                            text   = (el.textContent || '').trim();
                        }
                        if (text && text.length >= 3) doTranslate(text);
                    });

                    console.log('[VLibras] ✅ Bridge de tradução ativo.');
                } catch(be) {
                    console.error('[VLibras] ❌ Erro ao configurar bridge:', be);
                }

                console.log('[VLibras] ✅ Pronto — botão visível na borda direita.');
            }, 1200);

        })();
        </script>
        </body>
        </html>
        """,
        height=1,
    )


# ---------------------------------------------------------------------------
# Funções auxiliares para cookies via JavaScript
# ---------------------------------------------------------------------------
def _set_cookie_js(name: str, value: str, max_age: int = 60*60*24*30):
    """Injeta JS para salvar um cookie no navegador."""
    escaped = value.replace('\\', '\\\\').replace("'", "\\'")
    components.html(
        f"<script>document.cookie='{name}={escaped}; path=/; max-age={max_age}; SameSite=Lax';</script>",
        height=0,
    )

def _delete_cookie_js(name: str):
    """Injeta JS para remover um cookie do navegador."""
    components.html(
        f"<script>document.cookie='{name}=; path=/; max-age=0'; window.parent.location.href='/';</script>",
        height=0,
    )

def _read_cookie_from_headers(name: str):
    """Lê um cookie diretamente dos headers HTTP da requisição."""
    try:
        from streamlit.web.server.websocket_headers import _get_websocket_headers
        headers = _get_websocket_headers()
        if headers:
            cookie_str = headers.get("Cookie", "")
            for part in cookie_str.split(";"):
                part = part.strip()
                if part.startswith(f"{name}="):
                    return part[len(name) + 1:]
    except Exception:
        pass
    return None

# ---------------------------------------------------------------------------
# Autenticação — restaura sessão do cookie se existir
# ---------------------------------------------------------------------------
if not is_authenticated(st.session_state):
    saved_cookie = _read_cookie_from_headers("parceria_session")
    if saved_cookie:
        try:
            import urllib.parse as _up
            decoded = _up.unquote(saved_cookie)
            data = json.loads(decoded)
            st.session_state["auth_user"] = data
            st.rerun()
        except Exception:
            pass

# Autenticação — troca code OAuth por sessão
params = st.query_params
if "code" in params and not is_authenticated(st.session_state):
    code_verifier = params.get("cv", None)
    auth_data = exchange_code_for_session(params["code"], code_verifier)
    if auth_data and "error" not in auth_data:
        st.session_state["auth_user"] = auth_data
        # Salva dados serializáveis no cookie (30 dias)
        cookie_data = json.dumps({
            "email": auth_data.get("email", ""),
            "name": auth_data.get("name", ""),
            "avatar": auth_data.get("avatar", ""),
        })
        _set_cookie_js("parceria_session", cookie_data)
        st.query_params.clear()
        # Removido st.rerun() propositalmente para evitar falha no JS
    else:
        error_msg = auth_data.get("error", "Erro desconhecido") if auth_data else "Erro desconhecido"
        st.error(f"Falha na autenticação: {error_msg}")
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
            background: #202124;
            border: 1px solid #5f6368;
            color: #ffffff !important;
            font-size: 1rem;
            font-weight: 500;
            padding: 10px 24px;
            border-radius: 9999px;
            text-decoration: none !important;
            transition: background 0.2s, border-color 0.2s;
        }}
        .login-btn:hover {{ background: #303134; border-color: #8ab4f8; color: #ffffff !important; text-decoration: none !important; }}
        .login-footer {{
            position: fixed;
            bottom: 32px;
            left: 0;
            width: 100%;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 16px;
        }}
        .login-footer img {{
            width: 32px;
            height: 32px;
            opacity: 0.9;
        }}
        .footer-links {{
            display: flex;
            gap: 12px;
            font-size: 0.85rem;
            color: #9aa0a6;
        }}
        .footer-links a {{
            color: #9aa0a6;
            text-decoration: none;
            transition: color 0.2s;
        }}
        .footer-links a:hover {{
            color: #e8eaed;
            text-decoration: underline;
        }}
        </style>
        <div class="login-wrap">
            <div class="login-title">Parcer<span class="ia">IA</span></div>
            <div class="login-sub">Consultor jurídico inteligente para parcerias.<br>Faça login para continuar.</div>
            <a class="login-btn" href="{oauth_url}" target="_blank">
                <svg width="20" height="20" viewBox="0 0 48 48">
                    <path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"/>
                    <path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"/>
                    <path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"/>
                    <path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"/>
                    <path fill="none" d="M0 0h48v48H0z"/>
                </svg>
                Continuar com o Google
            </a>
        </div>
        <div class="login-footer">
            <img src="data:image/png;base64,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" alt="Logo ParcerIA">
            <div class="footer-links">
                <a href="#">Termos de uso</a>
                <span>|</span>
                <a href="#">Política de privacidade</a>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    _inject_vlibras()  # Disponível também na tela de login
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
_inject_vlibras()  # Disponível na tela principal (pós-login)

# ---------------------------------------------------------------------------
# Logo Base64
# ---------------------------------------------------------------------------
LOGO_B64 = "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"

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown(
        f"""
        <div style="display:flex; justify-content:flex-start; margin-bottom: 48px; margin-top: -30px;">
            <img src="data:image/png;base64,{LOGO_B64}" width="40" height="40" style="opacity: 0.9;">
        </div>
        """,
        unsafe_allow_html=True
    )
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
        _delete_cookie_js("parceria_session")
        st.stop()  # Aborta execução, o JS recarrega a tela sozinho
    st.divider()
    st.markdown("### Configurações")

    provider_options = {
        "Groq": "groq",
        "Google Gemini": "gemini",
    }
    selected_label = st.selectbox(
        "Provedor de LLM",
        options=list(provider_options.keys()),
        index=1,  # Gemini padrão — mais rápido e melhor qualidade em português
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
                from src.query_logger import log_query
                import time as _time

                _t0 = _time.monotonic()
                result = ask(chain, question)
                _response_ms = int((_time.monotonic() - _t0) * 1000)

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

                # Salva a consulta no Supabase (silencioso em caso de falha)
                _user_email = st.session_state.get("auth_user", {}).get("email")
                log_query(
                    user_email=_user_email,
                    question=question,
                    answer=answer,
                    source_docs=source_docs,
                    llm_provider=selected_provider,
                    response_ms=_response_ms,
                )

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
