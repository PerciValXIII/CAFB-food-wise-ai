# FoodWise AI 🍽️🤖

> AI-Powered Content Automation for the Capital Area Food Bank (CAFB)

FoodWise AI is an end-to-end intelligent content generation platform built to assist the Capital Area Food Bank (CAFB) by automating the reuse and transformation of existing content (images, reports, blogs, PPTs, PDFs) into new formats. It uses Retrieval-Augmented Generation (RAG) and modern LLM APIs to reduce manual workload and maximize impact on food insecurity initiatives.

🌐 **Live Demo**: [https://cafb-food-wise-ai.streamlit.app/](https://cafb-food-wise-ai.streamlit.app/)

---

## Key Features

- **Multimodal RAG Pipeline**: Integrates structured documents, annotated images, and blogs into a unified semantic search system.
- **Smart Search**: Retrieves the most relevant content chunks using vector similarity.
- **Auto Content Generation**: Generates polished Blogs, PDFs, Presentations, and Q&A content.
- **Human-in-the-loop**: Ensures accuracy and quality via manual review interface.
- **Scalable Architecture**: Uses Amazon S3, Supabase, Qdrant, and EC2.

---

## Tech Stack

- **Frontend**: `Streamlit` (for chatbot interface and file uploads)
- **Backend**: Python-based API for inference, generation, and search logic
- **Vector Search**: Qdrant (vector DB)
- **Storage**: Supabase (PostgreSQL) + S3 for content
- **Embedding**: `text-embedding-3-small` (OpenAI API)
- **Deployment**: Docker-ready, EC2-based processing
- **LLMs**: OpenAI GPT API or compatible local models

---


## Project Structure

```bash
CAFB-FOOD-WISE-AI/
├── backend/
│   └── src/
│       ├── auth.py              # API auth logic
│       ├── main.py              # Main FastAPI app
│       ├── Dockerfile           # Docker backend setup
│       ├── requirements.txt     # Backend dependencies
├── frontend/
│   ├── app.py                   # Streamlit app UI
│   ├── config.py                # UI config
│   ├── renderer.py              # Display logic (blog, ppt, image)
│   └── services/
│       └── api_client.py        # Calls backend API
├── notebooks/
│   ├── RAG.ipynb                # Exploratory notebook for RAG
│   └── Inference_API_Call.ipynb # API call testing
├── scripts/                     # One-off scripts or data processors
├── data/                        # Preloaded/processed datasets
├── cdk/                         # Infra-as-code (CDK for AWS)
├── README.md                    # You're here!
```

## Team FoodWise AI
1. [Adwaith Santosh](https://github.com/CoderAd1))
2. [Swattik Maiti](https://github.com/swattikmaiti)
3. [Neomi Sule](https://github.com/neomisule))
4. [Dhwani Muni](https://github.com/DhwaniMuni))
5. Emil George

University of Maryland – AI and Food Insecurity Case Competition

