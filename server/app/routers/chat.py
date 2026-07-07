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
from app.services.pdf_ingestion import get_vectorstore, get_embeddings, delete_user_vectorstore
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

    # Check if the vector store has any documents
    embeddings = get_embeddings()
    vectorstore = Chroma(
        persist_directory=persist_dir,
        embedding_function=embeddings,
        collection_name=f"user_{user_id}_docs",
    )
    
    # Quick check: try a similarity search with a dummy query
    try:
        test_results = vectorstore.similarity_search("test", k=1)
        if not test_results:
            return None
    except Exception:
        return None

    retriever = vectorstore.as_retriever(search_kwargs={"k": 4})

    if not settings.GEMINI_API_KEY:
        return None

    # ✅ Updated model name
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",          # ← stable model
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


def call_gemini(question: str) -> str:
    """Call Gemini directly (without RAG)."""
    if not settings.GEMINI_API_KEY:
        raise Exception("Gemini API key not configured")
    
    # ✅ Updated model name
    model = genai.GenerativeModel("gemini-2.5-flash")   # ← stable model
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
    # ─── Handle file upload if provided ──────────────────────
    if file:
        # Validate file type
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")
        
        # Save file temporarily
        temp_dir = f"temp_uploads_{user.id}"
        os.makedirs(temp_dir, exist_ok=True)
        file_path = os.path.join(temp_dir, file.filename)
        
        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # Ingest the file
            from app.services.pdf_ingestion import ingest_pdf
            result = ingest_pdf(file_path, user.id)
            
            # Clean up temp file
            os.remove(file_path)
            
            # Clear cached chain since vector store changed
            if user.id in _retrieval_chains:
                del _retrieval_chains[user.id]
                
        except Exception as e:
            # Clean up on error
            if os.path.exists(file_path):
                os.remove(file_path)
            raise HTTPException(status_code=500, detail=f"File ingestion failed: {str(e)}")

    # ─── Get the retrieval chain ──────────────────────────────
    chain = get_retrieval_chain(user.id)

    # ─── Generate answer ──────────────────────────────────────
    if chain is None:
        # No PDF uploaded – use simple Gemini (no RAG)
        try:
            answer = call_gemini(question)
        except Exception as e:
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"Gemini error: {str(e)}")
    else:
        # Use RAG with the vector store
        try:
            result = chain.invoke({"query": question})
            answer = result["result"]
            
            # Append sources if available
            sources = [doc.metadata.get("source", "unknown") for doc in result.get("source_documents", [])]
            if sources:
                unique_sources = list(set(sources))
                answer += f"\n\n📚 Sources: {', '.join(unique_sources)}"
                
        except Exception as e:
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"RAG error: {str(e)}")

    # ─── Save conversation to DB ──────────────────────────────
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
    """
    Retrieve all chat messages for the current user, newest first.
    """
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
    """
    Get a list of all uploaded PDF documents for the current user.
    """
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
    from app.services.pdf_ingestion import delete_user_vectorstore

    print(f"🗑️  Deleting documents for user_id: {user.id}")
    expected_folder = f"chroma_db_user_{user.id}"
    print(f"📂 Expected folder: {expected_folder}")
    print(f"📁 Exists? {os.path.exists(expected_folder)}")

    try:
        if os.path.exists(expected_folder):
            deleted = delete_user_vectorstore(user.id)
            if deleted:
                print("✅ Deletion successful.")
                return
            else:
                # Should not happen, but just in case
                raise HTTPException(status_code=500, detail="Deletion function returned False.")
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