from fastapi import APIRouter, Depends, HTTPException, status, Form, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
import time
import random
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.chat_message import ChatMessage
from app.schemas.chat import ChatMessageResponse
from app.services.pdf_ingestion import get_vectorstore, get_embeddings, delete_user_vectorstore
from langchain_community.vectorstores import Chroma
from langchain_classic.chains import RetrievalQA
import traceback
from app.core.config import settings
import os
import shutil

# google.generativeai is fully deprecated and Google has already shut down
# ALL Gemini 1.0/1.5 models on it (returns 404 for every request now).
# Migrated to the current google-genai SDK.
from google import genai
from google.genai import errors as genai_errors

# ─── Router ──────────────────────────────────────────────────────
router = APIRouter(prefix="/chat", tags=["chat"])

# ─── Gemini client (new SDK — no global .configure(), just a client object) ──
_gemini_client = None
if settings.GEMINI_API_KEY:
    _gemini_client = genai.Client(api_key=settings.GEMINI_API_KEY)
else:
    print("⚠️ GEMINI_API_KEY not configured")

# Auto-updating alias instead of a dated model name — avoids having to hunt
# down and replace a hardcoded model string every time Google retires one
# (this codebase has already been broken by gemini-1.5-flash, gemini-2.5-flash,
# and a dated gemini-3.5-flash pin in the last few weeks alone).
GEMINI_MODEL = "gemini-flash-latest"

from langchain_google_genai import ChatGoogleGenerativeAI

# ─── Cache for retrieval chains ──────────────────────────────
_retrieval_chains = {}


def get_retrieval_chain(user_id: int):
    """Load or create a RetrievalQA chain for the user."""
    if user_id in _retrieval_chains:
        return _retrieval_chains[user_id]

    persist_dir = f"chroma_db_user_{user_id}"
    if not os.path.exists(persist_dir):
        return None

    vectorstore = Chroma(
        persist_directory=persist_dir,
        embedding_function=get_embeddings(),
        collection_name=f"user_{user_id}_docs",
    )

    # Quick check
    try:
        test = vectorstore.similarity_search("test", k=1)
        if not test:
            return None
    except Exception:
        return None

    retriever = vectorstore.as_retriever(search_kwargs={"k": 4})

    if not settings.GEMINI_API_KEY:
        return None

    llm = ChatGoogleGenerativeAI(
        model=GEMINI_MODEL,
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
    return chain


def invalidate_retrieval_chain(user_id: int):
    """Drop the cached chain (no explicit client close)."""
    _retrieval_chains.pop(user_id, None)


def call_gemini(question: str, max_retries: int = 3) -> str:
    """Call Gemini directly, with retry handling for free-tier rate limits (429s)."""
    if not _gemini_client:
        raise Exception("Gemini API key not configured")

    prompt = f"You are a helpful assistant for Alzheimer's diagnosis. Answer concisely and professionally: {question}"

    last_error = None
    for attempt in range(max_retries):
        try:
            response = _gemini_client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
            )
            if not response or not response.text:
                raise Exception("Empty response from Gemini")
            return response.text

        except genai_errors.ClientError as e:
            last_error = e
            # 429 = rate limited. Google's error response includes the exact
            # wait time it wants — use that instead of guessing a backoff.
            if getattr(e, "code", None) == 429 and attempt < max_retries - 1:
                retry_delay = _extract_retry_delay(e) or (2 ** attempt + random.uniform(0, 1))
                time.sleep(retry_delay)
                continue
            raise Exception(f"Gemini error: {e}") from e

    raise Exception(f"Gemini error after {max_retries} retries: {last_error}")


def _extract_retry_delay(error) -> float | None:
    """Pull the server-suggested retry delay (in seconds) out of a 429 error, if present."""
    try:
        details = getattr(error, "details", None) or {}
        for item in details.get("error", {}).get("details", []):
            if "retryDelay" in item:
                # e.g. "8s" -> 8.0
                return float(str(item["retryDelay"]).rstrip("s"))
    except Exception:
        pass
    return None


# ─── POST /chat ────────────────────────────────────────────────
@router.post("/", response_model=ChatMessageResponse)
async def chat(
    question: str = Form(...),
    file: UploadFile = File(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if file:
        if not file.filename.endswith('.pdf'):
            raise HTTPException(400, "Only PDF files are allowed")

        temp_dir = f"temp_uploads_{user.id}"
        os.makedirs(temp_dir, exist_ok=True)
        file_path = os.path.join(temp_dir, file.filename)

        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            from app.services.pdf_ingestion import ingest_pdf
            ingest_pdf(file_path, user.id)

            os.remove(file_path)
            invalidate_retrieval_chain(user.id)

        except Exception as e:
            if os.path.exists(file_path):
                os.remove(file_path)
            raise HTTPException(500, f"File ingestion failed: {str(e)}")

    chain = get_retrieval_chain(user.id)

    if chain is None:
        try:
            answer = call_gemini(question)
        except Exception as e:
            traceback.print_exc()
            raise HTTPException(500, f"Gemini error: {str(e)}")
    else:
        try:
            result = chain.invoke({"query": question})
            answer = result["result"]

            sources = [doc.metadata.get("source", "unknown") for doc in result.get("source_documents", [])]
            if sources:
                answer += f"\n\n📚 Sources: {', '.join(set(sources))}"

        except Exception as e:
            traceback.print_exc()
            raise HTTPException(500, f"RAG error: {str(e)}")

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


# ─── GET /chat/history ────────────────────────────────────────
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
    db.query(ChatMessage).filter(ChatMessage.user_id == user.id).delete()
    db.commit()


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
    try:
        deleted = delete_user_vectorstore(user.id)
        if not deleted:
            raise HTTPException(404, "No documents found for this user.")
        invalidate_retrieval_chain(user.id)
    except Exception as e:
        raise HTTPException(500, f"Deletion failed: {str(e)}")