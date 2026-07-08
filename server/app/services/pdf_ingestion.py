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


def try_close_client(vs) -> bool:
    """
    Best-effort attempt to close the underlying chromadb client so file
    handles on chroma.sqlite3 are released. Tries several attribute paths
    since these vary across chromadb/langchain versions.

    Public (no leading underscore) so other modules — e.g. chat.py, which
    creates its own separate Chroma client for the retrieval chain cache —
    can reuse this same closing logic instead of duplicating it.
    """
    print(f"🔍 vectorstore type: {type(vs)}")

    candidates = [
        vs,
        getattr(vs, "_client", None),
        getattr(vs, "_collection", None),
        getattr(getattr(vs, "_client", None), "_client", None),
        getattr(getattr(vs, "_client", None), "_producer", None),
        getattr(getattr(vs, "_client", None), "_system", None),
    ]

    for obj in candidates:
        if obj is None:
            continue
        for method_name in ("_close", "close", "stop", "reset"):
            method = getattr(obj, method_name, None)
            if callable(method):
                try:
                    method()
                    print(f"✅ Closed via {type(obj).__name__}.{method_name}()")
                    return True
                except Exception as e:
                    print(f"⚠️ {type(obj).__name__}.{method_name}() failed: {e}")

    print("⚠️ Could not find a working close method on the vectorstore/client.")
    return False


def delete_user_vectorstore(user_id: int) -> bool:
    """
    Force delete the vector store folder. Raises RuntimeError if it truly
    can't be deleted. Returns False only if the folder didn't exist in the
    first place.

    NOTE: callers should close any OTHER vectorstore instances pointing at
    this same persist_dir (e.g. chat.py's retrieval-chain cache) BEFORE
    calling this, or the folder will stay locked on Windows.
    """
    persist_dir = f"chroma_db_user_{user_id}"
    if not os.path.exists(persist_dir):
        return False

    # 1. Pop and close the Chroma client so file handles are released
    if user_id in _vectorstores:
        vs = _vectorstores.pop(user_id)
        try:
            try_close_client(vs)
        except Exception as e:
            print(f"⚠️ Error while closing client: {e}")
        del vs
    else:
        print(f"ℹ️ No cached vectorstore found for user_id {user_id}")

    gc.collect()
    time.sleep(1.0)  # give Windows a moment to release the file handle

    # 2. Try the rename trick first — VERIFY it actually worked
    temp_dir = persist_dir + "_to_delete"
    try:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)
        os.rename(persist_dir, temp_dir)
        shutil.rmtree(temp_dir, ignore_errors=True)
        if not os.path.exists(temp_dir):
            print(f"✅ Deleted via rename: {persist_dir}")
            return True
        print(f"⚠️ rmtree left files behind in {temp_dir}, will retry")
    except (OSError, PermissionError) as e:
        print(f"⚠️ Rename failed: {e}")

    # 3. Retry direct deletion — VERIFY it actually worked
    target = temp_dir if os.path.exists(temp_dir) else persist_dir
    for attempt in range(5):
        shutil.rmtree(target, ignore_errors=True)
        if not os.path.exists(target):
            print(f"✅ Deleted on attempt {attempt + 1}: {target}")
            return True
        print(f"⚠️ Attempt {attempt + 1} left {target} behind, retrying...")
        time.sleep(2 * (attempt + 1))
        gc.collect()

    # 4. Diagnostics: list what's still present (Windows, best-effort)
    if os.path.exists(target):
        try:
            remaining = os.listdir(target)
            print(f"🔍 Files still present in {target}: {remaining}")
        except Exception:
            pass

    # 5. Fallback: system command — VERIFY it actually worked
    try:
        if os.name == 'nt':
            result = subprocess.run(
                ["cmd", "/c", "rmdir", "/s", "/q", target],
                capture_output=True, timeout=10, text=True
            )
        else:
            result = subprocess.run(
                ["rm", "-rf", target],
                capture_output=True, timeout=10, text=True
            )
        if result.returncode != 0:
            print(f"⚠️ Subprocess stderr: {result.stderr}")
        if not os.path.exists(target):
            print(f"✅ Deleted via subprocess: {target}")
            return True
    except Exception as e:
        print(f"❌ Subprocess deletion failed: {e}")

    # 6. If we get here, it genuinely could not be deleted
    raise RuntimeError(
        f"Could not delete folder after all attempts: {target} "
        f"(a file handle is very likely still open on chroma.sqlite3 by "
        f"some OTHER cached client — check every module that creates a "
        f"Chroma(persist_directory=...) instance for this user, and make "
        f"sure no other process/terminal/Explorer window has this folder open)"
    )


def get_user_documents_info(user_id: int) -> List[dict]:
    vectorstore = get_vectorstore(user_id)
    results = vectorstore.similarity_search("", k=100)
    sources = set()
    for doc in results:
        source = doc.metadata.get("source", "unknown")
        if source != "unknown":
            sources.add(source)
    return [{"filename": s, "chunks": 0} for s in sources]