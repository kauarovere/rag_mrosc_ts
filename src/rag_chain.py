"""
src/rag_chain.py
================
Montagem da chain de RAG jurídico via LCEL (LangChain Expression Language).

Pipeline:
  pergunta do usuário
    → retriever (busca semântica no Chroma/FAISS)
    → formata contexto com metadados (artigo, fonte)
    → prompt jurídico especializado
    → LLM
    → resposta com citações

Retorna tanto a resposta textual quanto os documentos-fonte recuperados,
para exibição destacada na interface Streamlit.

Uso:
  from src.rag_chain import build_rag_chain, ask

  chain = build_rag_chain()
  result = ask(chain, "O que é um termo de fomento?")
  print(result["answer"])
  print(result["source_documents"])
"""

import os
import time
import logging
from typing import Any, Optional

from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableParallel, RunnablePassthrough

load_dotenv()

# ---------------------------------------------------------------------------
# Prompt do sistema — instrui o LLM como se comportar em contexto jurídico
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """Você é um assistente especializado no Marco Regulatório das Organizações da Sociedade Civil (MROSC) brasileiro. Sua base de conhecimento é composta por duas fontes principais de informação:

**1. Legislação Oficial (Base Principal)**
- **Lei Federal nº 13.019/2014** (Lei MROSC), que estabelece as normas gerais de parcerias.
- **Decreto Municipal nº 57.575/2016** (Prefeitura de São Paulo), que regulamenta a aplicação da Lei no município.

**2. Documentos Complementares (Manuais e FAQs)**
- Respostas a perguntas frequentes e cartilhas práticas que explicam e facilitam a compreensão da legislação oficial.

**Regras que você DEVE seguir:**

1. **Responda SOMENTE com base nos trechos fornecidos abaixo** como contexto. Não invente dispositivos legais ou definições fora do contexto.

2. **Prioridade de Fontes:** Sempre priorize a Legislação Oficial. Se a resposta estiver tanto na lei quanto no FAQ, cite a lei. Se a resposta estiver apenas no FAQ, use o FAQ, mas deixe claro que é uma explicação de um documento complementar.

3. **Sempre cite a fonte exata:**
   - Para leis: *"conforme o art. X da Lei 13.019/2014"* ou *"nos termos do art. Y do Decreto 57.575/2016"*.
   - Para FAQs: *"conforme o documento complementar [Nome do FAQ]"*.

4. **Se a informação não estiver nos trechos fornecidos**, diga claramente: "Não encontrei base nos documentos fornecidos para responder a esta pergunta." Não complemente com conhecimento genérico do modelo.

5. **Ao final de toda resposta**, inclua obrigatoriamente o seguinte aviso:
   "⚠️ *Esta resposta é baseada nos documentos fornecidos e não substitui análise jurídica profissional.*"

**Contexto recuperado dos documentos:**

{context}

---

**Pergunta:** {question}

**Resposta:**"""

HUMAN_TEMPLATE = "{question}"


# ---------------------------------------------------------------------------
# Formatação do contexto com metadados
# ---------------------------------------------------------------------------

def format_documents_with_metadata(docs: list[Document]) -> str:
    """
    Formata os documentos recuperados incluindo metadados de fonte e artigo,
    para que o LLM possa citá-los corretamente na resposta.
    """
    formatted_parts = []
    for i, doc in enumerate(docs, 1):
        meta = doc.metadata
        fonte = meta.get("fonte", "Fonte desconhecida")
        artigo = meta.get("artigo", "?")
        status = meta.get("status", "vigente")

        tipo = meta.get("tipo", "desconhecido")

        # Formatação diferente para Leis vs Docs Complementares
        if tipo in ["faq", "manual", "glossário", "documento_complementar"]:
            header = f"[Trecho {i}] Material Complementar: {fonte} — {artigo}"
        else:
            # Aviso se o artigo estiver revogado ou alterado
            status_note = ""
            if status == "revogado":
                status_note = " [⚠️ ARTIGO REVOGADO — verifique a versão vigente]"
            elif status == "alterado":
                status_note = " [ℹ️ Artigo com redação alterada]"

            header = f"[Trecho {i}] {fonte} — Art. {artigo}{status_note}"
        formatted_parts.append(f"{header}\n{doc.page_content}")

    return "\n\n" + "\n\n---\n\n".join(formatted_parts) + "\n"


# ---------------------------------------------------------------------------
# Construção da chain via LCEL
# ---------------------------------------------------------------------------

def build_rag_chain(provider: Optional[str] = None, k: int = 6):
    """
    Monta a chain de RAG usando LCEL (LangChain Expression Language).

    A chain retorna um dict com:
      - "answer": str — a resposta gerada pelo LLM
      - "source_documents": list[Document] — chunks usados como contexto

    Args:
        provider: Provedor de LLM ("ollama" | "groq" | "gemini").
                  None = lê do .env (padrão: "ollama").
        k: Número de chunks a recuperar por consulta.

    Returns:
        Chain LCEL que aceita {"question": str} e retorna {"answer": str, "source_documents": list}.
    """
    from src.llm_provider import get_llm
    from src.vectorstore import get_retriever

    print("\n🔧 Inicializando RAG chain...")

    # 1. Retriever
    retriever = get_retriever(k=k)

    # 2. LLM
    llm = get_llm(provider)

    # 3. Prompt
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            ("human", "{question}"),
        ]
    )

    # 4. Chain LCEL
    # Passo 1: recupera documentos e passa a questão adiante em paralelo
    retrieve_and_passthrough = RunnableParallel(
        {
            "source_documents": retriever,
            "question": RunnablePassthrough(),
        }
    )

    # Passo 2: formata contexto + monta prompt + chama LLM + parseia
    def build_prompt_input(inputs: dict) -> dict:
        return {
            "context": format_documents_with_metadata(inputs["source_documents"]),
            "question": inputs["question"],
        }

    answer_chain = (
        {
            "context": lambda x: format_documents_with_metadata(x["source_documents"]),
            "question": lambda x: x["question"],
        }
        | prompt
        | llm
        | StrOutputParser()
    )

    # Chain completa: retorna answer + source_documents
    full_chain = retrieve_and_passthrough | RunnableParallel(
        {
            "answer": answer_chain,
            "source_documents": lambda x: x["source_documents"],
        }
    )

    print("   ✅ Chain inicializada com sucesso!")
    return full_chain


def ask(
    chain,
    question: str,
    max_retries: int = 3,
    initial_wait: float = 5.0,
) -> dict[str, Any]:
    """
    Faz uma pergunta à chain e retorna a resposta com metadados de fonte.
    Implementa retry com backoff exponencial para erros de rate limit (429).

    Args:
        chain: Chain LCEL construída por build_rag_chain().
        question: Pergunta do usuário em linguagem natural.
        max_retries: Número máximo de tentativas após erro 429 (padrão: 3).
        initial_wait: Tempo de espera inicial em segundos (dobra a cada tentativa).

    Returns:
        Dict com:
          - "answer": str — resposta gerada
          - "source_documents": list[Document] — documentos-fonte
          - "question": str — pergunta original
    """
    last_error = None
    wait = initial_wait

    for attempt in range(1, max_retries + 1):
        try:
            result = chain.invoke(question)
            result["question"] = question
            return result

        except Exception as e:
            error_str = str(e)
            is_rate_limit = "429" in error_str or "RESOURCE_EXHAUSTED" in error_str or "rate_limit" in error_str.lower()

            if is_rate_limit and attempt < max_retries:
                logging.warning(
                    f"Rate limit atingido (tentativa {attempt}/{max_retries}). "
                    f"Aguardando {wait:.0f}s antes de tentar novamente..."
                )
                time.sleep(wait)
                wait *= 2  # backoff exponencial: 5s → 10s → 20s
                last_error = e
                continue

            # Erro não é rate limit, ou esgotou as tentativas → propaga
            raise

    # Nunca deve chegar aqui, mas garante que o erro seja propagado
    raise last_error


def has_base_in_documents(answer: str) -> bool:
    """
    Verifica se a resposta indica que não há base nos documentos.
    Usado pela interface Streamlit para exibir alerta visual.
    """
    no_base_indicators = [
        "não encontrei base nos documentos",
        "não há base nos textos",
        "não encontrado nos documentos",
        "fora do escopo dos documentos",
        "não está presente nos documentos",
        "não consta nos documentos",
    ]
    answer_lower = answer.lower()
    return not any(indicator in answer_lower for indicator in no_base_indicators)