from fastapi import APIRouter, Depends, HTTPException, status, Form, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
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
        model="gemini-1.5-flash",
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


def call_gemini(question: str) -> str:
    """Call Gemini directly."""
    if not settings.GEMINI_API_KEY:
        raise Exception("Gemini API key not configured")

    model = genai.GenerativeModel("gemini-flash-latest")
    prompt = f"You are a helpful assistant for Alzheimer's diagnosis. Answer concisely and professionally: {question}"
    response = model.generate_content(prompt)

    if not response or not response.text:
        raise Exception("Empty response from Gemini")
    return response.text


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