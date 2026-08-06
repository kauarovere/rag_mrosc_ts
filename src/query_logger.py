"""
src/query_logger.py
====================
Logging silencioso de consultas RAG no Supabase.

Registra na tabela `rag_queries`:
  - Pergunta do usuario
  - Resposta gerada pelo LLM
  - Fontes (artigos) usadas como contexto
  - E-mail do usuario autenticado
  - Provedor de LLM (Groq, Gemini, etc.)
  - Tempo total de resposta em ms

Design: nunca lanca excecao - em caso de falha (Supabase offline,
timeout, etc.) apenas loga um warning e continua sem interromper o chat.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


def log_query(
    user_email: Optional[str],
    question: str,
    answer: str,
    source_docs: list,
    llm_provider: str,
    response_ms: int,
) -> None:
    """
    Persiste uma consulta RAG no Supabase de forma silenciosa.

    Args:
        user_email:   E-mail do usuario autenticado (ou None).
        question:     Pergunta original do usuario.
        answer:       Resposta gerada pelo LLM.
        source_docs:  Lista de Document retornados pelo retriever.
        llm_provider: Nome do provedor LLM ("groq", "gemini", "ollama").
        response_ms:  Tempo total de resposta em milissegundos.
    """
    try:
        from src.auth import get_supabase

        # Serializa as fontes para JSONB (apenas campos relevantes)
        sources = []
        for doc in source_docs:
            meta = doc.metadata if hasattr(doc, "metadata") else {}
            sources.append(
                {
                    "fonte": meta.get("fonte", ""),
                    "artigo": meta.get("artigo", ""),
                    "tipo": meta.get("tipo", ""),
                }
            )

        payload = {
            "user_email": user_email,
            "question": question,
            "answer": answer,
            "sources": sources,
            "llm_provider": llm_provider,
            "response_ms": response_ms,
        }

        supabase = get_supabase()
        supabase.table("rag_queries").insert(payload).execute()

    except Exception as exc:
        # Logging silencioso: nunca interrompe o chat
        logger.warning("Falha ao registrar consulta no Supabase: %s", exc)
