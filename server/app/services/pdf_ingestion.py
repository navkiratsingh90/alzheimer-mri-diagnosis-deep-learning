import os
import shutil
from typing import List
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

_embeddings = None
_vectorstores = {}


def get_embeddings():
    global _embeddings
    if _embeddings is None:
        _embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    return _embeddings


def get_vectorstore(user_id: int):
    if user_id in _vectorstores:
        return _vectorstores[user_id]
    persist_dir = f"chroma_db_user_{user_id}"
    os.makedirs(persist_dir, exist_ok=True)
    vectorstore = Chroma(
        persist_directory=persist_dir,
        embedding_function=get_embeddings(),
        collection_name=f"user_{user_id}_docs",
    )
    _vectorstores[user_id] = vectorstore
    return vectorstore


def ingest_pdf(file_path: str, user_id: int) -> dict:
    """Load, split, and index a PDF into the user's vector store."""
    loader = PyPDFLoader(file_path)
    docs = loader.load()
    if not docs:
        raise ValueError("PDF is empty.")

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_documents(docs)
    if not chunks:
        raise ValueError("No chunks created.")

    filename = os.path.basename(file_path)
    for i, chunk in enumerate(chunks):
        chunk.metadata.update({"user_id": user_id, "source": filename, "chunk_index": i})

    vectorstore = get_vectorstore(user_id)
    vectorstore.add_documents(chunks)
    return {"chunks": len(chunks), "filename": filename}


def delete_user_vectorstore(user_id: int) -> bool:
    """Delete the user's vector store folder. Returns False if it didn't exist."""
    persist_dir = f"chroma_db_user_{user_id}"
    if not os.path.exists(persist_dir):
        return False 

    # Remove from cache
    _vectorstores.pop(user_id, None)

    # Force deletion
    try:
        shutil.rmtree(persist_dir)
        return True
    except OSError as e:
        raise RuntimeError(f"Could not delete {persist_dir}: {e}")


def get_user_documents_info(user_id: int) -> List[dict]:
    """List filenames of documents stored for the user."""
    persist_dir = f"chroma_db_user_{user_id}"
    if not os.path.exists(persist_dir):
        return []

    # Quick: read the folder, but we need to get actual filenames from the vectorstore
    vectorstore = get_vectorstore(user_id)
    # We'll do a small search to extract sources
    try:
        results = vectorstore.similarity_search("", k=100)
        sources = {doc.metadata.get("source", "unknown") for doc in results if doc.metadata.get("source") != "unknown"}
        return [{"filename": src, "chunks": 0} for src in sources]
    except Exception:
        return []