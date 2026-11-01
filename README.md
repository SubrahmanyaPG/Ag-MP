# Automated Audience Sentiment and Feedback Analysis Using Natural Language Processing (v2.0)

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.1-green.svg)](https://www.djangoproject.com/)
[![React](https://img.shields.io/badge/React-18.3-61dafb.svg)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-5.4-646CFF.svg)](https://vitejs.dev/)
[![TailwindCSS](https://img.shields.io/badge/TailwindCSS-3.4-38B2AC.svg)](https://tailwindcss.com/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED.svg)](https://www.docker.com/)
[![Celery](https://img.shields.io/badge/Celery-5.4-37814A.svg)](https://docs.celeryq.dev/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17-336791.svg)](https://www.postgresql.org/)
[![Groq](https://img.shields.io/badge/Groq%20LLM-openai%2Fgpt--oss--120b-f55036.svg)](https://groq.com/)
[![Tests](https://img.shields.io/badge/Tests-47%20Passed-brightgreen.svg)]()
[![License](https://img.shields.io/badge/License-MIT-lightgrey.svg)](LICENSE)

An enterprise-grade, end-to-end full-stack intelligence platform designed to ingest YouTube audience discussions, isolate malicious spam/bots with explainable reasons, perform multilingual Hinglish sentiment classification, track sentiment trajectory over time, compute like-weighted engagement polarity, automatically select optimal topic clusters via silhouette score analysis, detect viewer questions with 1-click AI reply drafting, and synthesize strategic content recommendations using Generative AI (Groq API).

---

## 📑 Table of Contents
1. [Project Overview & Motivation](#-project-overview--motivation)
2. [System Architecture](#-system-architecture)
3. [Key Features (v2.0 Advanced Enhancements)](#-key-features-v20-advanced-enhancements)
4. [Ablation Study & Evaluation Benchmark](#-ablation-study--evaluation-benchmark)
5. [Technology Stack](#-technology-stack)
6. [Directory Structure](#-directory-structure)
7. [Prerequisites & Environment Variables](#-prerequisites--environment-variables)
8. [Docker Compose Quickstart (One Command)](#-docker-compose-quickstart-one-command)
9. [Local Manual Installation Guide](#-local-manual-installation-guide)
10. [REST API Documentation](#-rest-api-documentation)
11. [Testing & Verification (47 Test Cases)](#-testing--verification-47-test-cases)
12. [College Presentation & Evaluator Demo Guide](#-college-presentation--evaluator-demo-guide)

---

## 🎯 Project Overview & Motivation

Digital creators, educators, and enterprise marketing teams receive thousands of viewer comments across their video publications. Manually reviewing this feedback introduces severe bottlenecks:
- **Noise & Malicious Spam**: Promotional bots, WhatsApp recovery scams, and telegram link drops pollute comment sections.
- **Mixed Languages & Sarcasm**: Modern Indian and global YouTube audiences communicate using Hinglish, internet slang (*op, mast, zabardast, bakwas, bekar, banger, clutch*), and informal expressions that off-the-shelf sentiment models misclassify.
- **Unweighted Feedback**: A viral comment with 1,000 likes historically carried the exact same weight as a comment with 0 likes.
- **Actionability Gap**: Creators need immediate answers to questions like *"What specific aspect did viewers dislike (Audio, Visuals, Pacing, Content)?"* and *"Which viewer questions need my response right now?"*.

This project solves these challenges through a hybrid architecture combining **specialized NLP (Hinglish-extended VADER, dynamic Silhouette topic clustering, aspect & emotion classifiers)**, **explainable heuristics**, **Generative AI (Groq LLM)**, and a **high-performance React dashboard**.

---

## 🏗️ System Architecture

```mermaid
flowchart TD
    subgraph Client ["Client Layer (React 18 + Vite + Tailwind CSS)"]
        UI["React SPA Dashboard\n(Recharts, Lucide, Tailwind)"]
        TIMELINE["Sentiment Trajectory Timeline"]
        RADAR["Aspect & Emotion Profile"]
        CMP_MODAL["Side-by-Side Video Comparison Modal"]
        MY_MODAL["My Saved Analyses (JWT Gated)"]
        AUTH_UI["JWT Auth Modal\n(Login / Register / Me)"]
    end

    subgraph Backend ["Backend API Layer (Django 5.1 + DRF)"]
        DRF["DRF API Endpoints\n(/api/videos/analyze/, /api/analyses/compare/, /api/reports/)"]
        CACHE["24h Video Analysis Caching & Quota Guard"]
        ASYNC["Asynchronous Task Manager\n(Celery Worker + Background Daemon Fallback)"]
    end

    subgraph Storage ["Persistence Layer"]
        PG[("PostgreSQL 17 Database\n(Videos, Comments, Jobs, Reports)")]
        REDIS[("Redis 7 In-Memory Queue & Broker")]
    end

    subgraph NLP_Engine ["Machine Learning & NLP Engine v2.0"]
        PRE["Text Sanitizer & Normalizer"]
        LANG["Language Detector (en / hi / hinglish)"]
        SPAM["Hybrid Spam Detector + Explainability Engine"]
        SENT["Hinglish-Enhanced VADER + Like-Weighting"]
        ASPECT["Aspect-Based Classifier (Content, Audio, Visuals, Pacing)"]
        EMOTION["Emotion Polarity Profiler (Joy, Inquiry, Frustration, Surprise)"]
        TOPIC["Silhouette-Optimized K-Means Clustering (k=2..5)"]
        REPLY["Question Detector & Creator Reply Drafter"]
    end

    subgraph External ["External Services"]
        YT["YouTube Data API v3"]
        GROQ["Groq Cloud API\n(openai/gpt-oss-120b)"]
        PDF["ReportLab PDF Engine\n(Executive Multi-page Report)"]
    end

    UI -->|HTTP / REST| DRF
    AUTH_UI -->|JWT Bearer Token| DRF
    DRF --> CACHE
    CACHE -->|Cache Hit| UI
    CACHE -->|Cache Miss| ASYNC
    DRF -->|Read / Write| PG
    ASYNC -->|Queue Task| REDIS
    ASYNC -->|Fetch Comments| YT
    ASYNC --> NLP_Engine
    NLP_Engine --> PRE --> LANG --> SPAM --> SENT --> ASPECT --> EMOTION --> TOPIC --> REPLY
    ASYNC -->|Synthesize Insights| GROQ
    ASYNC -->|Persist Findings| PG
    DRF -->|Stream PDF / CSV| UI
```

---

## ✨ Key Features (v2.0 Advanced Enhancements)

1. **Sentiment Trajectory Over Time**
   - Area/Line chart plotting daily/weekly sentiment trajectory derived from comment publication dates (`published_at`).
   - Identifies whether viewer reception was initially hostile and improved, or vice-versa.

2. **Like-Weighted Sentiment Polarity**
   - High-engagement comments contribute proportionally to the overall video polarity using logarithmic weighting:
     $$w_i = \ln(1 + \text{likes}_i) + 1$$
     $$\text{Weighted Polarity} = \frac{\sum_{i=1}^{N} (w_i \cdot c_i)}{\sum_{i=1}^{N} w_i}$$

3. **Multilingual Hinglish & Slang Lexicon**
   - Extended VADER lexicon with Hinglish vocabulary and YouTube internet slang (*zabardast, badhiya, shandar, mast, op, banger, bakwas, bekar, ghatiya, scam, fake, clutch, w, l*).
   - Integrated language detection identifying English (`en`), Devanagari Hindi (`hi`), and Romanized Hindi (`hinglish`).

4. **Side-by-Side Video Comparison (`/api/analyses/compare/`)**
   - Allows users to benchmark any two videos across sentiment ratio, like-weighted score, spam isolation count, topic clusters, and comparative advantage.

5. **Creator Response Center & 1-Click AI Reply Drafting**
   - Automatically detects viewer questions, confusion, and requests (`needs_response=True`).
   - In-app 1-click action triggers AI-generated creator response drafts that can be copied directly to the clipboard.

6. **Aspect-Based Sentiment & Emotion Profiling**
   - Breaks down audience opinions across 4 core production pillars: **Content & Explanation**, **Audio & Sound Quality**, **Visuals & Editing**, and **Pacing & Length**.
   - Quantifies emotional polarity profile across **Joy & Praise**, **Questions & Curiosity**, **Critique & Frustration**, and **Awe & Surprise**.

7. **Explainable Spam Quarantine**
   - Comments flagged as spam feature transparent badges detailing *why* they were quarantined (e.g. *WhatsApp/Telegram Solicitation*, *High ML Spam Probability*, *Excessive Emoji/Cap Flooding*).

8. **Dynamic Topic Modeling via Silhouette Optimization**
   - Replaced fixed cluster count $K$ with automatic Silhouette Score optimization across $k \in [2, 5]$ to guarantee meaningful cluster separation.

9. **Quota Protection & 24h Caching**
   - Automatically reuses completed analysis reports within 24 hours to prevent burning Google Cloud's 10,000 units/day quota.

10. **Per-User History & JWT Protection**
    - Analysis jobs link to authenticated user accounts with a dedicated "My Analyses" modal.

---

## 📊 Ablation Study & Evaluation Benchmark

To rigorously justify the hybrid architecture, an empirical ablation study was conducted across **165+ ground-truth labeled YouTube comments** comparing:
1. **Regex-Only Heuristic Rule Engine**
2. **Machine Learning-Only Classifier (TF-IDF + Logistic Regression)**
3. **Proposed Hybrid Architecture (Regex + ML ensemble)**

### Empirical Results

| Model Architecture | Precision | Recall | F1-Score | Accuracy | Key Observations |
|---|---|---|---|---|---|
| **Regex-Only Engine** | 100.0% | 77.5% | 87.3% | 94.5% | Zero false positives on known patterns; missed novel obfuscated spam variations. |
| **ML-Only (TF-IDF + LR)** | 100.0% | 100.0% | 100.0% | 100.0% | High generalized performance on vocabulary, but requires heuristic safety net for phone numbers/URLs. |
| **Proposed Hybrid Ensemble** | **100.0%** | **100.0%** | **100.0%** | **100.0%** | Combines deterministic pattern catching with statistical text generalization. |

*Run the benchmark on your local machine with:*
```powershell
python backend/manage.py test_nlp_pipeline
```

---

## 🛠️ Technology Stack

| Component | Technology | Version | Purpose |
|---|---|---|---|
| **Backend Web Framework** | Python / Django | 5.1 | High-throughput REST API and ORM |
| **API Architecture** | Django REST Framework | 3.15 | Serialization, viewsets, and pagination |
| **Authentication** | SimpleJWT | 5.3 | Secure stateless JWT bearer token authentication |
| **Database** | PostgreSQL | 17 | Relational persistence for videos, comments, jobs, and reports |
| **Task Queue & Broker** | Celery / Redis | 5.4 / 7.0 | Distributed async processing with thread fallback |
| **NLP & Sentiment** | NLTK (VADER) | 3.8.1 | Rule-based sentiment scoring with custom Hinglish lexicon |
| **Machine Learning** | scikit-learn | 1.4.0 | TF-IDF vectorization, Logistic Regression, K-Means, Silhouette scoring |
| **Generative AI** | Groq Cloud SDK | 0.9.0 | High-speed LLM inference (`openai/gpt-oss-120b`) |
| **Document Generation** | ReportLab | 4.2.0 | Multi-page executive PDF reporting with vector graphics |
| **Frontend Framework** | React / Vite | 18.3 / 5.4 | Single Page Application dashboard |
| **Styling & Icons** | Tailwind CSS / Lucide | 3.4 / 0.450 | Dark modern theme and responsive components |
| **Data Visualization** | Recharts | 2.13 | Interactive area charts, pie charts, and radar breakdowns |
| **Containerization** | Docker & Docker Compose | 24+ | Multi-container orchestration |

---

## 📁 Directory Structure

```text
Ag MP/
├── .github/
│   └── workflows/
│       └── ci.yml                   # Automated GitHub Actions CI test & build workflow
├── backend/
│   ├── analyzer/
│   │   ├── llm/
│   │   │   ├── client.py            # Resilient Groq client with JSON schema validation
│   │   │   ├── prompts.py           # Separated, user-editable LLM prompt templates
│   │   │   └── service.py           # High-level entry point for LLM synthesis
│   │   ├── management/commands/
│   │   │   ├── fetch_comments.py    # Fetch YouTube comments via CLI
│   │   │   ├── test_llm.py          # Direct test of Groq LLM integration
│   │   │   └── test_nlp_pipeline.py # Ablation benchmark suite (Regex vs ML vs Hybrid)
│   │   ├── nlp/
│   │   │   ├── aspect_emotion.py    # Aspect-based sentiment, emotion classifier & reply drafter
│   │   │   ├── benchmark_data.py    # Ground-truth labeled benchmark comments
│   │   │   ├── evaluation.py        # Precision, recall, F1, confusion matrix, & ablation
│   │   │   ├── pipeline.py          # Unified NLP pipeline coordinator
│   │   │   ├── preprocessor.py      # HTML unescaping, URL/timestamp scrubber
│   │   │   ├── request_extractor.py # Regex feature & viewer request extractor
│   │   │   ├── sentiment.py         # Hinglish VADER, language detection, timeline generator
│   │   │   ├── spam_classifier.py   # Hybrid spam detector with explainability reasons
│   │   │   └── topic_modeler.py     # Silhouette score dynamic K-Means topic modeler
│   │   ├── services/
│   │   │   ├── pdf_generator.py     # ReportLab multi-page executive PDF generator
│   │   │   └── youtube.py           # YouTube Data API v3 integration & policy handling
│   │   ├── models.py                # Video, Comment, AnalysisJob, Report data models
│   │   ├── serializers.py           # DRF serializers (Comments, Jobs, Reports, Auth)
│   │   ├── tasks.py                 # Celery async worker task with thread fallback
│   │   ├── tests.py                 # 47 comprehensive unit & integration tests
│   │   ├── urls.py                  # API endpoints routing
│   │   └── views.py                 # DRF API views & comparison endpoints
│   ├── core/
│   │   ├── celery.py                # Celery application configuration
│   │   ├── settings.py              # Django configuration (PostgreSQL, CORS, JWT)
│   │   └── urls.py                  # Root URL configuration
│   ├── Dockerfile                   # Python 3.12-slim backend container
│   ├── manage.py                    # Django management CLI
│   └── requirements.txt             # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── AiRecommendations.jsx  # AI strategic takeaways & title suggestions
│   │   │   ├── AspectRadarCard.jsx    # Aspect breakdown & emotion distribution
│   │   │   ├── AuthModal.jsx          # Sign In & Registration JWT modal
│   │   │   ├── CommentsTable.jsx      # Paginated table with spam explainability & AI reply
│   │   │   ├── CompareVideosModal.jsx # Side-by-side comparative analysis modal
│   │   │   ├── JobProgress.jsx        # 5-stage visual progress stepper
│   │   │   ├── MyAnalysesModal.jsx    # User saved analyses history modal
│   │   │   ├── Navbar.jsx             # Brand navigation with compare & history buttons
│   │   │   ├── SentimentCard.jsx      # Sentiment pie chart & metrics
│   │   │   ├── SentimentTimeline.jsx  # Daily/weekly chronological sentiment trajectory
│   │   │   ├── Toast.jsx              # Toast notification system
│   │   │   ├── TopicsChart.jsx        # Keywords & viewer requests display
│   │   │   └── VideoInputForm.jsx     # YouTube URL input & presets
│   │   ├── services/
│   │   │   └── api.js                 # Axios API service with JWT interceptors
│   │   ├── App.jsx                    # Root dashboard coordinator
│   │   └── index.css                  # Tailwind styles
│   ├── Dockerfile                     # Multi-stage Node builder + Nginx production image
│   ├── nginx.conf                     # Nginx SPA configuration
│   └── package.json
├── docker-compose.yml                 # Orchestration for Postgres, Redis, Backend, Celery, Frontend
├── .env                               # Environment configuration & API credentials
└── README.md
```

---

## ⚙️ Prerequisites & Environment Variables

Create or verify the `.env` file in the project root:

```ini
# Django Settings
SECRET_KEY=your-django-super-secret-key-change-in-production
DEBUG=True
ALLOWED_HOSTS=*

# Database Connection (PostgreSQL 17)
DATABASE_URL=postgres://postgres:root@localhost:5432/youtube_analyzer

# Celery & Redis
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
CELERY_ALWAYS_EAGER=False

# YouTube Data API v3
YOUTUBE_API_KEY=AIzaSy...your_youtube_api_key_here

# Groq Cloud LLM API
GROQ_API_KEY=gsk_...your_groq_api_key_here
GROQ_MODEL=openai/gpt-oss-120b
```

---

## 🐳 Docker Compose Quickstart (One Command)

If you have Docker Desktop installed, run the entire stack with a single command:

```powershell
# Build and launch all 5 services: db, redis, backend, celery_worker, frontend
docker-compose up --build
```

- **Frontend Dashboard**: Open `http://localhost:3000`
- **Backend API**: Open `http://localhost:8000/api/health/`
- To stop the services:
```powershell
docker-compose down
```

---

## 🚀 Local Manual Installation Guide

### Step 1: Initialize Virtual Environment & Install Dependencies
```powershell
# Create virtual environment
python -m venv .venv

# Activate environment (Windows PowerShell)
.\.venv\Scripts\Activate.ps1

# Upgrade pip & install requirements
pip install -r backend/requirements.txt
```

### Step 2: Initialize PostgreSQL Database
Ensure PostgreSQL is active on port `5432`:
```sql
CREATE DATABASE youtube_analyzer;
```
Apply migrations:
```powershell
python backend/manage.py migrate
```

### Step 3: Install Frontend Dependencies
```powershell
cd frontend
npm install
cd ..
```

### Step 4: Run the Application
In Terminal 1 (Backend):
```powershell
python backend/manage.py runserver 127.0.0.1:8000
```

In Terminal 2 (Frontend):
```powershell
cd frontend
npm run dev
```
Open `http://localhost:5173` in your browser.

---

## 📡 REST API Documentation

| Method | Endpoint | Description | Request Body / Query Params |
|---|---|---|---|
| `POST` | `/api/videos/analyze/` | Initiates YouTube video analysis (24h cache enabled) | `{"url": "...", "max_comments": 100, "refresh": false}` |
| `GET` | `/api/jobs/{id}/status/` | Polls current status of analysis job | Returns `pending`, `running`, `done`, `failed` |
| `GET` | `/api/reports/{job_id}/` | Fetches complete analysis report | Returns sentiment, timeline, aspects, emotions, topics, AI insights |
| `GET` | `/api/reports/{job_id}/export/` | Downloads report file | `?format=pdf` (PDF report) or `?format=csv` (CSV log) |
| `GET` | `/api/analyses/my/` | Returns analysis history for logged-in user | Header: `Authorization: Bearer <access_token>` |
| `GET` | `/api/analyses/compare/` | Compares two completed video reports side by side | `?job1=<id1>&job2=<id2>` |
| `POST` | `/api/comments/{id}/draft-reply/` | Generates personalized AI creator response draft | Path parameter `id` |
| `GET` | `/api/videos/{id}/comments/` | Paginated comments with filters | `?sentiment=positive&aspect=content&needs_response=true` |
| `POST` | `/api/auth/register/` | Registers new user & returns JWT tokens | `{"username": "...", "email": "...", "password": "..."}` |
| `POST` | `/api/auth/token/` | Obtains JWT access & refresh tokens | `{"username": "...", "password": "..."}` |
| `GET` | `/api/auth/me/` | Retrieves authenticated user profile | Header: `Authorization: Bearer <access_token>` |

---

## 🧪 Testing & Verification (47 Test Cases)

The project includes an automated test suite with **47 test cases** testing backend APIs, NLP models, Hinglish lexicon, spam explainability, PDF generation, and JWT authentication:

```powershell
# Run the complete test suite
python backend/manage.py test analyzer
```

Expected output:
```text
Ran 47 tests in 14.050s
OK
```

### Run Ablation Benchmark & Accuracy Report
```powershell
python backend/manage.py test_nlp_pipeline
```

### Test Groq LLM Direct Synthesis
```powershell
python backend/manage.py test_llm
```

---

## 🎓 College Presentation & Evaluator Demo Guide

Follow these steps for a live demonstration during project review:

1. **System Launch**:
   - Start Django backend (`python backend/manage.py runserver 127.0.0.1:8000`).
   - Start React frontend (`npm run dev --prefix frontend`).
   - Open `http://localhost:5173`. Point out the dark glassmorphic UI, live API status badge, and version indicator (`NLP v2.0`).

2. **Trigger Analysis & Real-Time Progress**:
   - Paste a YouTube URL or click a preset (e.g. *Never Gonna Give You Up* or a coding tutorial).
   - Set sample size to 100 comments and click **"Run Sentiment & Feedback Analysis"**.
   - Show the 5-stage progress indicator: Fetching $\rightarrow$ Preprocessing $\rightarrow$ Sentiment & Spam $\rightarrow$ Topic Clustering $\rightarrow$ Groq AI Synthesis.

3. **Demonstrate Sentiment Trajectory & Like-Weighting**:
   - Point out the **Sentiment Trajectory Timeline** showing how audience reaction changed by date.
   - Point out the **Like-Weighted Polarity Score** chip, explaining to evaluators how high-engagement comments contribute proportionally.

4. **Aspect & Emotion Breakdown**:
   - Review the **Aspect-Based Audience Sentiment** card showing scores for Content, Audio, Visuals, and Pacing.
   - Show the **Emotion Polarity Profile** showing percentages for Joy, Questions, Critique, and Surprise.

5. **Creator Response Center & 1-Click AI Reply**:
   - Scroll down to the Comments Table.
   - Click the **"Questions Only"** filter chip to isolate viewer questions (`needs_response`).
   - Click **"Draft Reply"** on any comment to show the real-time AI reply generator and click the copy button.

6. **Spam Explainability**:
   - Switch filter to **"Spam Only"** and show the explainability badges (*WhatsApp/Telegram Solicitation*, *High ML Spam Probability*).

7. **Side-by-Side Video Comparison**:
   - Click **"Compare Videos"** in the top navigation bar.
   - Select two analyzed videos and click **"Compare"** to display the comparative matrix table.

8. **User History ("My Analyses")**:
   - Click **"Sign In"** in the navbar, log in, then click **"My Analyses"** to show personal saved jobs.

9. **Export Deliverables**:
   - Click **"Download PDF"** to display the multi-page vector PDF report generated by ReportLab.
   - Click **"Export CSV"** to demonstrate raw data export.

10. **Ablation Study Verification**:
    - Open terminal and run `python backend/manage.py test_nlp_pipeline` to show evaluators the empirical ablation metrics (Regex vs ML vs Hybrid).

---
