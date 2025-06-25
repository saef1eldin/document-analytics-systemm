# document-analytics-systemm
# 📄 Document Analytics System

A cloud-based document analytics system that allows users to upload, search, sort, and classify large collections of PDF and Word documents using AI-powered techniques.

## 🚀 Features

- **Upload Documents:** Upload `.pdf` and `.docx` files through a simple and intuitive interface.
- **Search Documents:** Search across all uploaded documents using keyword or phrase-based queries.
- **Sort Documents:** Sort documents by title or upload date (metadata and extracted titles).
- **Classify Documents:** Automatically classify documents using a predefined classification tree and ML algorithms.
- **Statistics Dashboard:** View total number of documents, total size, and analytics on search/sort/classification performance.

## 🧠 Technologies Used

- **Frontend:** React.js + Vite
- **Backend:** Python + Flask + SQLAlchemy
- **Database:** SQLite
- **Parsing & NLP:** `pdfminer`, `python-docx`, `nltk`, `scikit-learn`
- **Deployment Ready:** Fully prepared for deployment on any cloud service (e.g., DigitalOcean, AWS, Heroku)

## 📂 Project Structure

```
document-analytics-system/
│
├── document-analytics-frontend/     # React frontend
│   └── ...
│
├── document-analytics-service/      # Python backend (Flask)
│   └── src/
│       ├── main.py
│       ├── document.py
│       ├── classification.py
│       └── ...
│
├── README.md                        # This file
```

## ⚙️ How to Run Locally

### Backend (Flask)
```bash
cd document-analytics-service
python -m venv venv
venv\Scripts\activate         # On Windows
pip install -r requirements.txt
python src/main.py
```

### Frontend (React)
```bash
cd document-analytics-frontend
npm install --legacy-peer-deps
npm run dev
```

Then go to: `http://localhost:5173`

## ☁️ Cloud Deployment

You can deploy the backend and frontend separately using any cloud platform. Suggested services:

- **Backend:** DigitalOcean / Heroku / Render
- **Frontend:** Vercel / Netlify / Render

> Replace `localhost` URLs in frontend with your deployed backend API URL.

## 📊 Statistics Features

The system provides:

- Total number of uploaded documents
- Total storage used
- Time taken to process searches, sorts, and classifications
- Class-wise distribution of documents

## 📚 How It Works

1. **Document Parsing**: Text is extracted from PDF/DOCX.
2. **Search**: Keywords are matched across the document contents.
3. **Highlighting**: Search results are highlighted.
4. **Classification**: ML model assigns category based on content and predefined rules.
   
## 🌐 Live Demo

> https://document-analytics-systemm-2.onrender.com/

## 📎 GitHub Repository

> https://github.com/saef1eldin/document-analytics-systemm
