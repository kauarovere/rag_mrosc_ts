"""
src/auth.py
===========
Módulo de autenticação via Supabase OAuth (Google).

Fluxo:
  1. Usuário clica em "Entrar com Google"
  2. Redirecionado ao Google via Supabase OAuth
  3. Google autentica e redireciona de volta com ?code=...
  4. Trocamos o code por uma sessão Supabase
  5. Sessão armazenada no st.session_state
"""

import os
from typing import Optional

from dotenv import load_dotenv
from supabase import Client, create_client

load_dotenv()

SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY: str = os.getenv("SUPABASE_ANON_KEY", "")
APP_URL: str = os.getenv("APP_URL", "http://localhost:8501")


def get_supabase() -> Client:
    """Retorna o cliente Supabase inicializado."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError(
            "SUPABASE_URL e SUPABASE_ANON_KEY precisam estar definidos no .env"
        )
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def get_google_oauth_url() -> str:
    """Gera a URL de autenticação OAuth do Google via Supabase."""
    supabase = get_supabase()
    response = supabase.auth.sign_in_with_oauth(
        {
            "provider": "google",
            "options": {
                "redirect_to": APP_URL,
                "scopes": "openid email profile",
            },
        }
    )
    return response.url


def exchange_code_for_session(code: str) -> Optional[dict]:
    """Troca o código OAuth por uma sessão Supabase."""
    supabase = get_supabase()
    try:
        response = supabase.auth.exchange_code_for_session({"auth_code": code})
        return {
            "user": response.user,
            "session": response.session,
            "email": response.user.email if response.user else None,
            "name": (
                response.user.user_metadata.get("full_name", "")
                if response.user
                else ""
            ),
            "avatar": (
                response.user.user_metadata.get("avatar_url", "")
                if response.user
                else ""
            ),
        }
    except Exception as e:
        return None


def sign_out() -> None:
    """Encerra a sessão do usuário no Supabase."""
    try:
        supabase = get_supabase()
        supabase.auth.sign_out()
    except Exception:
        pass


def is_authenticated(session_state) -> bool:
    """Verifica se há uma sessão ativa no session_state."""
    return session_state.get("auth_user") is not None
