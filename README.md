# 🧠 NeuroSight – AI‑Powered Alzheimer’s MRI Diagnostic Platform

NeuroSight is a full‑stack web application that uses deep learning to classify Alzheimer’s disease from MRI scans.  
It generates professional PDF reports, provides an AI‑powered clinical chat (with optional PDF ingestion), and stores all patient data for future review.

---

## 🎯 Why We Built This

Alzheimer’s disease affects millions worldwide, and early detection is critical for better patient outcomes. However, access to expert radiologists and neurologists is limited in many regions. **NeuroSight** was created to:

- **Democratise early screening** – Provide an accessible, AI‑assisted first‑line tool for clinicians and patients.
- **Bridge the gap between AI and clinical practice** – By generating human‑readable reports with clear recommendations, we make AI outputs actionable.
- **Empower continuous learning** – The built‑in clinical chat (with RAG) allows doctors and researchers to query uploaded PDFs (papers, patient notes) and get instant, evidence‑based answers.
- **Streamline patient monitoring** – All predictions and reports are stored per user, enabling easy tracking of disease progression over time.

Ultimately, NeuroSight aims to support – not replace – medical professionals, speeding up triage and helping patients receive timely care.

---

## 🚀 Features

- **🔬 MRI Classification** – Upload an MRI scan and get an instant prediction (Non‑Demented, Very Mild, Mild, or Moderate Dementia) with confidence score.
- **📄 PDF Report Generation** – Produce a beautifully formatted, color‑coded clinical report that includes:
  - Diagnostic result & confidence bar
  - AI‑generated summary (7‑8 lines)
  - Precautions & lifestyle recommendations
  - Prognosis overview
  - List of recommended neurology centers
  - Embedded scan image
- **💬 AI Clinical Chat** – Ask questions about Alzheimer’s, upload PDFs (research papers, clinical notes) and get answers grounded in your documents (RAG).
- **📊 Dashboard & History** – View all past scans, track progression, and generate reports from any scan.
- **🔐 Authentication** – Secure login/register with JWT stored in HTTP‑only cookies.
- **📁 Report Management** – List and download all previously generated PDF reports.

---

## 🛠️ Tech Stack

### Frontend
- [Next.js 14](https://nextjs.org/) (App Router)
- React + TypeScript
- Tailwind CSS
- Axios (with automatic cookie‑based auth)

### Backend
- [FastAPI](https://fastapi.tiangolo.com/)
- SQLAlchemy + SQLite (production‑ready with PostgreSQL support)
- [TensorFlow / Keras](https://www.tensorflow.org/) – DenseNet121 model for classification
- [ReportLab](https://www.reportlab.com/) – PDF generation
- [LangChain](https://www.langchain.com/) + Chroma – RAG pipeline
- [Google Gemini 2.5 / 1.5](https://ai.google.dev/) – AI summaries & chat

---

## 📁 File Structure

neuroSight/
├── server/ # FastAPI backend
│ ├── app/
│ │ ├── core/ # Config, DB, dependencies
│ │ ├── models/ # SQLAlchemy models
│ │ ├── routers/ # API endpoints
│ │ ├── schemas/ # Pydantic schemas
│ │ ├── services/ # Business logic
│ │ │ ├── ai_summary.py # Gemini summary generation
│ │ │ ├── pdf_generator.py # PDF report builder
│ │ │ └── pdf_ingestion.py # PDF chunking + vector store
│ │ ├── ml/ # Model loader & predictor
│ │ └── main.py
│ ├── static/ # Uploaded images, reports, and PDFs
│ ├── instance/ # SQLite database
│ └── .env
│
├── client/ # Next.js frontend
│ ├── src/
│ │ ├── app/ # Pages (dashboard, reports, chat, etc.)
│ │ ├── lib/ # API client, auth context, types
│ │ └── styles/
│ ├── public/
│ └── .env.local
│
├── ml_model/ # Trained TensorFlow models (.h5)
│ ├── custom_cnn_model.h5
│ └── densenet_model.h5
│
└── README.md


---

## ⚙️ Setup & Installation

### Backend (FastAPI)

```bash
cd server
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt

SECRET_KEY=your-secret-key
GEMINI_API_KEY=your-gemini-api-key
DATABASE_URL=sqlite:///./instance/alzheimer.db
MODEL_PATH=ml_model/densenet_model.h5
UPLOAD_DIR=static/uploads

uvicorn app.main:app --reload

cd client
npm install

NEXT_PUBLIC_API_URL=http://localhost:8000

npm run dev
