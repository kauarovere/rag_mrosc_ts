"""
src/vectorstore.py
==================
Criação e carregamento do vector store FAISS persistente.

- Embeddings: intfloat/multilingual-e5-large (padrão) ou configurável via .env
- Vector store: FAISS (local, CPU, persistente entre sessões)

Uso:
  from src.vectorstore import build_vectorstore, load_vectorstore
"""

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

load_dotenv()

# ---------------------------------------------------------------------------
# Configurações (lidas do .env ou valores padrão)
# ---------------------------------------------------------------------------
FAISS_PERSIST_DIR = os.getenv("FAISS_PERSIST_DIR", "./faiss_index")
EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL",
    "intfloat/multilingual-e5-large",
)

# Normaliza o caminho relativo ao diretório raiz do projeto
_PROJECT_ROOT = Path(__file__).parent.parent
_FAISS_PATH = str(_PROJECT_ROOT / FAISS_PERSIST_DIR.lstrip("./\\"))


def get_embeddings() -> HuggingFaceEmbeddings:
    """
    Cria o objeto de embeddings com o modelo multilíngue selecionado.
    O modelo é baixado e cacheado localmente na 1ª execução.
    """
    print(f"   Modelo de embeddings: {EMBEDDING_MODEL}")
    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )


def build_vectorstore(
    documents: list[Document],
    persist_dir: Optional[str] = None,
) -> FAISS:
    """
    Cria o vector store FAISS a partir dos documentos fornecidos e salva no disco.
    """
    persist_dir = persist_dir or _FAISS_PATH

    embeddings = get_embeddings()

    # Cria o FAISS com os documentos
    vectorstore = FAISS.from_documents(
        documents=documents,
        embedding=embeddings,
    )
    
    # Garante que o diretório de persistência existe
    Path(persist_dir).mkdir(parents=True, exist_ok=True)

    # Salva o índice e metadados no disco
    vectorstore.save_local(persist_dir)

    return vectorstore


def load_vectorstore(
    persist_dir: Optional[str] = None,
) -> FAISS:
    """
    Carrega um vector store FAISS já existente do disco.
    Levanta RuntimeError se o diretório não existir.
    """
    persist_dir = persist_dir or _FAISS_PATH

    if not Path(persist_dir).exists():
        raise RuntimeError(
            f"Vector store não encontrado em: {persist_dir}\n"
            "Execute primeiro: python src/ingest.py"
        )

    embeddings = get_embeddings()

    # allow_dangerous_deserialization=True é estritamente necessário no LangChain
    # para carregar arquivos Pickle (.pkl) gerados localmente pelo próprio FAISS.
    vectorstore = FAISS.load_local(
        persist_dir, 
        embeddings, 
        allow_dangerous_deserialization=True
    )

    return vectorstore


def get_retriever(
    persist_dir: Optional[str] = None,
    k: int = 6,
):
    """
    Retorna um retriever configurado para buscar os k chunks mais relevantes.
    """
    vectorstore = load_vectorstore(persist_dir)
    return vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": k},
    )