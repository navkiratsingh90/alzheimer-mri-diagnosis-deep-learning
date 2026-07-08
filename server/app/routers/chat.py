from fastapi import APIRouter, Depends, HTTPException, status, Form, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.dependencies import get_current_user
import glob
import re
from app.models.user import User
from app.models.chat_message import ChatMessage
from app.schemas.chat import ChatRequest, ChatMessageResponse
from app.services.pdf_ingestion import get_vectorstore, get_embeddings, delete_user_vectorstore, try_close_client
from langchain_community.vectorstores import Chroma
from langchain_classic.chains import RetrievalQA
import traceback
from app.core.config import settings
import os
import gc
import shutil
import google.generativeai as genai

# ─── Router ──────────────────────────────────────────────────────
router = APIRouter(prefix="/chat", tags=["chat"])

# ─── Configure Gemini ──────────────────────────────────────────
if settings.GEMINI_API_KEY:
    genai.configure(api_key=settings.GEMINI_API_KEY)
else:
    print("⚠️ GEMINI_API_KEY not configured")

from langchain_google_genai import ChatGoogleGenerativeAI

# ─── Cache for retrieval chains ──────────────────────────────
_retrieval_chains = {}
# Tracks the underlying Chroma vectorstore behind each cached chain, so we
# can explicitly close its client on delete/invalidate (this is a SEPARATE
# Chroma client from the one in pdf_ingestion._vectorstores — if we don't
# close it too, Windows keeps a lock on chroma.sqlite3 and deletion fails).
_retrieval_vectorstores = {}


def get_retrieval_chain(user_id: int):
    """
    Load or create a RetrievalQA chain for the user using Gemini.
    Returns None if the user has no vector store.
    """
    if user_id in _retrieval_chains:
        return _retrieval_chains[user_id]

    persist_dir = f"chroma_db_user_{user_id}"
    if not os.path.exists(persist_dir):
        return None

    embeddings = get_embeddings()
    vectorstore = Chroma(
        persist_directory=persist_dir,
        embedding_function=embeddings,
        collection_name=f"user_{user_id}_docs",
    )

    # Quick check: try a similarity search with a dummy query.
    # IMPORTANT: if we bail out early on any of these paths, we must close
    # this client — otherwise it's an orphaned open handle on chroma.sqlite3.
    try:
        test_results = vectorstore.similarity_search("test", k=1)
        if not test_results:
            try_close_client(vectorstore)
            return None
    except Exception:
        try_close_client(vectorstore)
        return None

    retriever = vectorstore.as_retriever(search_kwargs={"k": 4})

    if not settings.GEMINI_API_KEY:
        try_close_client(vectorstore)
        return None

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0.2,
        google_api_key=settings.GEMINI_API_KEY,
    )

    chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=True,
        verbose=True,
    )
    _retrieval_chains[user_id] = chain
    _retrieval_vectorstores[user_id] = vectorstore  # keep a reference so we can close it later
    return chain


def invalidate_retrieval_chain(user_id: int):
    """
    Drop the cached chain AND explicitly close its underlying Chroma client.
    Call this before deleting a user's vector store, or whenever the store
    changes (new upload), so no stale file handle survives.
    """
    _retrieval_chains.pop(user_id, None)
    vs = _retrieval_vectorstores.pop(user_id, None)
    if vs is not None:
        try:
            try_close_client(vs)
        except Exception as e:
            print(f"⚠️ Error while closing retrieval-chain vectorstore: {e}")
        del vs
    gc.collect()


def call_gemini(question: str) -> str:
    """Call Gemini directly (without RAG)."""
    if not settings.GEMINI_API_KEY:
        raise Exception("Gemini API key not configured")

    model = genai.GenerativeModel("gemini-2.5-flash")
    prompt = f"You are a helpful assistant for Alzheimer's diagnosis. Answer this question concisely and professionally: {question}"
    response = model.generate_content(prompt)

    if not response or not response.text:
        raise Exception("Empty response from Gemini")

    return response.text


# ─── POST /chat (with optional file upload) ────────────────────
@router.post("/", response_model=ChatMessageResponse)
async def chat(
    question: str = Form(..., description="Your question to the AI assistant"),
    file: UploadFile = File(None, description="Optional PDF file to upload"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Send a question to the AI assistant.
    Optionally upload a PDF file to be used as context for the answer.
    """
    if file:
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")

        temp_dir = f"temp_uploads_{user.id}"
        os.makedirs(temp_dir, exist_ok=True)
        file_path = os.path.join(temp_dir, file.filename)

        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            from app.services.pdf_ingestion import ingest_pdf
            result = ingest_pdf(file_path, user.id)

            os.remove(file_path)

            # Vector store changed — invalidate + properly close the cached chain
            invalidate_retrieval_chain(user.id)

        except Exception as e:
            if os.path.exists(file_path):
                os.remove(file_path)
            raise HTTPException(status_code=500, detail=f"File ingestion failed: {str(e)}")

    chain = get_retrieval_chain(user.id)

    if chain is None:
        try:
            answer = call_gemini(question)
        except Exception as e:
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"Gemini error: {str(e)}")
    else:
        try:
            result = chain.invoke({"query": question})
            answer = result["result"]

            sources = [doc.metadata.get("source", "unknown") for doc in result.get("source_documents", [])]
            if sources:
                unique_sources = list(set(sources))
                answer += f"\n\n📚 Sources: {', '.join(unique_sources)}"

        except Exception as e:
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"RAG error: {str(e)}")

    chat_msg = ChatMessage(
        user_id=user.id,
        question=question,
        answer=answer,
    )
    db.add(chat_msg)
    db.commit()
    db.refresh(chat_msg)

    return ChatMessageResponse(
        id=chat_msg.id,
        question=chat_msg.question,
        answer=chat_msg.answer,
        timestamp=chat_msg.timestamp,
    )


# ─── GET /chat/history ──────────────────────────────────────────
@router.get("/history", response_model=List[ChatMessageResponse])
async def get_chat_history(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.user_id == user.id)
        .order_by(ChatMessage.timestamp.desc())
        .all()
    )
    return messages


# ─── DELETE /chat/history ──────────────────────────────────────
@router.delete("/history", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat_history(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Delete all chat messages for the current user.
    This does NOT delete uploaded PDFs – use DELETE /chat/documents for that.
    """
    db.query(ChatMessage).filter(ChatMessage.user_id == user.id).delete()
    db.commit()
    return


# ─── GET /chat/documents ────────────────────────────────────────
@router.get("/documents", response_model=List[dict])
async def get_uploaded_documents(
    user: User = Depends(get_current_user),
):
    from app.services.pdf_ingestion import get_user_documents_info
    return get_user_documents_info(user.id)


# ─── DELETE /chat/documents ─────────────────────────────────────
@router.delete("/documents", status_code=status.HTTP_204_NO_CONTENT)
async def delete_documents(
    user: User = Depends(get_current_user),
):
    """
    Delete all uploaded PDF documents (vector store) for the current user.
    """
    print(f"🗑️  Deleting documents for user_id: {user.id}")
    expected_folder = f"chroma_db_user_{user.id}"
    print(f"📂 Expected folder: {expected_folder}")
    print(f"📁 Exists? {os.path.exists(expected_folder)}")

    # 🔑 Close AND clear the retrieval-chain's own Chroma client first —
    # this is the second, independent client that was leaving a lock on
    # chroma.sqlite3 even after pdf_ingestion's client was closed.
    invalidate_retrieval_chain(user.id)
    print(f"🧹 Cleared + closed cached retrieval chain for user_id: {user.id}")

    try:
        if os.path.exists(expected_folder):
            deleted = delete_user_vectorstore(user.id)
            if deleted:
                print("✅ Deletion successful.")
                return
            else:
                raise HTTPException(status_code=404, detail="No documents found for this user.")
        else:
            raise HTTPException(status_code=404, detail="No documents found for this user.")
    except RuntimeError as e:
        print(f"❌ RuntimeError: {e}")
        raise HTTPException(status_code=500, detail=f"Deletion failed: {str(e)}")
    except PermissionError as e:
        print(f"❌ PermissionError: {e}")
        raise HTTPException(status_code=500, detail=f"Permission denied: {str(e)}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")