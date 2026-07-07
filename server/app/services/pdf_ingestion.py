import os
import shutil
import time
import gc
import subprocess
import traceback
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
    embeddings = get_embeddings()
    vectorstore = Chroma(
        persist_directory=persist_dir,
        embedding_function=embeddings,
        collection_name=f"user_{user_id}_docs",
    )
    _vectorstores[user_id] = vectorstore
    return vectorstore

def ingest_pdf(file_path: str, user_id: int) -> dict:
    loader = PyPDFLoader(file_path)
    documents = loader.load()
    if not documents:
        raise ValueError(f"No content found in PDF: {file_path}")

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", " ", ""],
        length_function=len,
    )
    chunks = text_splitter.split_documents(documents)
    if not chunks:
        raise ValueError(f"Failed to split PDF into chunks: {file_path}")

    filename = os.path.basename(file_path)
    for i, chunk in enumerate(chunks):
        chunk.metadata.update({
            "user_id": user_id,
            "source": filename,
            "chunk_index": i,
            "total_chunks": len(chunks),
        })

    vectorstore = get_vectorstore(user_id)
    vectorstore.add_documents(chunks)
    return {
        "chunks": len(chunks),
        "filename": filename,
        "file_path": file_path,
    }

def delete_user_vectorstore(user_id: int) -> bool:
    """
    Force delete the vector store folder – raises an exception on failure.
    """
    persist_dir = f"chroma_db_user_{user_id}"
    if not os.path.exists(persist_dir):
        return False

    # 1. Clear cache and close client
    if user_id in _vectorstores:
        try:
            if hasattr(_vectorstores[user_id], "_client"):
                _vectorstores[user_id]._client._close()
        except Exception:
            pass
        del _vectorstores[user_id]
    gc.collect()
    time.sleep(0.5)

    # 2. Try the rename trick first
    temp_dir = persist_dir + "_to_delete"
    try:
        os.rename(persist_dir, temp_dir)
        shutil.rmtree(temp_dir, ignore_errors=True)
        print(f"✅ Deleted via rename: {persist_dir}")
        return True
    except (OSError, PermissionError) as e:
        print(f"⚠️ Rename failed: {e}")

    # 3. Retry direct deletion
    target = temp_dir if os.path.exists(temp_dir) else persist_dir
    for attempt in range(5):
        try:
            shutil.rmtree(target, ignore_errors=True)
            print(f"✅ Deleted on attempt {attempt+1}: {target}")
            return True
        except PermissionError:
            time.sleep(2 * (attempt + 1))
            gc.collect()
            continue

    # 4. Fallback: use system command (Windows: rmdir, Unix: rm -rf)
    try:
        if os.name == 'nt':  # Windows
            subprocess.run(
                ["cmd", "/c", "rmdir", "/s", "/q", target],
                check=True,
                capture_output=True,
                timeout=10
            )
        else:  # Linux/Mac
            subprocess.run(
                ["rm", "-rf", target],
                check=True,
                capture_output=True,
                timeout=10
            )
        print(f"✅ Deleted via subprocess: {target}")
        return True
    except Exception as e:
        print(f"❌ Subprocess deletion failed: {e}")

    # 5. If all attempts fail, raise an exception
    raise RuntimeError(f"Could not delete folder after all attempts: {persist_dir}")

def get_user_documents_info(user_id: int) -> List[dict]:
    vectorstore = get_vectorstore(user_id)
    results = vectorstore.similarity_search("", k=100)
    sources = set()
    for doc in results:
        source = doc.metadata.get("source", "unknown")
        if source != "unknown":
            sources.add(source)
    return [{"filename": s, "chunks": 0} for s in sources]