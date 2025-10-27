# 📌 Minor Project – Startup News Sentiment Analysis

## 🚀 Overview
This project is developed as part of the **Minor Project** for the B.Tech program.  
It demonstrates the integration of **Data Science, NLP, and CI/CD pipelines** to build an end-to-end solution.  

The aim of the project is to **analyze startup-related news articles and determine the sentiment (positive, negative, neutral)** using machine learning and natural language processing.

---

## 🛠️ Tech Stack
| Layer | Technology |
|-------|-------------|
| **Language** | Python 3.11 |
| **Database** | PostgreSQL |
| **API Source** | NewsAPI |
| **ML Model** | FinBERT (custom fine-tuned) |
| **Libraries** | `torch`, `transformers`, `requests`, `psycopg2`, `concurrent.futures` |
| **Deployment** | GitHub Actions (CI/CD) |
| **Logging** | Custom structured logging system |

---

## ⚙️ Features
- ✅ Fetching startup-related news using APIs  
- ✅ Preprocessing and cleaning textual data  
- ✅ Sentiment analysis (positive, neutral, negative)  
- ✅ Database integration for storing analyzed results  
- ✅ CI/CD pipeline with automated testing & deployment  
- ✅ Logging and error handling  

---

## 📂 Project Structure
```bash
│
├── main.py
└── src/
├── utils/
│ ├── db_utils.py ← DB operations
│ ├── cache_utils.py ← Duplicate URL cache
│ ├── newsapi_utils.py ← NewsAPI fetch & key rotation
│ ├── sentiment_utils.py ← FinBERT sentiment scoring
│ ├── text_utils.py ← Text merge & truncation
│ └── pipeline_utils.py ← Full pipeline orchestration
│
├── database/
│ └── init.py ← DB connection handler
├── logger/
│ └── init.py ← Structured logger
├── sentiments/
│ └── finbert_model/ ← Model folder
└── constants.py
```

---

## 🧩 Database Design

### **Startups Table**
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Unique startup ID |
| name | TEXT | Startup name |
| findingKeywords | JSON | Keyword list for targeted queries |
| createdAt | TIMESTAMP | Record creation time |

### **Articles Table**
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Unique article ID |
| startupId | UUID | Foreign key reference |
| title | TEXT | Article title |
| content | TEXT | Truncated content (≤ 300 chars) |
| url | TEXT | Article URL |
| publishedAt | TIMESTAMP | Publication time |
| sentiment | TEXT | Sentiment label (pos/neu/neg) |
| sentimentScore | FLOAT | Weighted sentiment score |
| sourceName | TEXT | Publisher |
| createdAt | TIMESTAMP | DB insertion time |

---

## 🔍 Key Features

✅ **Automatic news fetching** — startup-specific queries via NewsAPI  
✅ **Sentiment analysis** — using `Soumil24/finbert-custom` (fine-tuned FinBERT)  
✅ **Duplicate prevention** — in-memory URL cache + DB check  
✅ **Threaded execution** — uses `ThreadPoolExecutor` for parallel fetching  
✅ **Multi-key API rotation** — round-robin handling of multiple NewsAPI keys  
✅ **Resilient pipeline** — retries, error handling, exponential backoff  
✅ **Structured logging** — clean, timestamped JSON logs  
✅ **CI/CD integration** — GitHub Actions auto-runs pipeline daily  

---

## 🧠 Sentiment Analysis Logic

| Label | Meaning | Weight |
|--------|----------|--------|
| **Positive** | Favorable coverage | `+1` |
| **Neutral** | Objective tone | `0` |
| **Negative** | Criticism or risk | `-1` |

Weighted sentiment score =  
`Σ(probability × weight)` across all three classes.

---

## 🚀 Getting Started

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/<your-username>/<repo-name>.git
cd Startup-News-Sentiment-Analysis
```
### 2️⃣ Create Virtual Environment
```
python -m venv .venv
source .venv/bin/activate   # for Linux/Mac
.venv\Scripts\activate      # for Windows
```

### 3️⃣ Install Dependencies
```
pip install -r requirements.txt
```

### 4️⃣ Run the Project
```
python src/main.py
```

## 🧪 Running Tests
```
pytest tests/
```

##⚡ CI/CD Pipeline

This project uses GitHub Actions for continuous integration and deployment:

- Runs tests on every push
- Builds project automatically
- Deploys updates (if configured)

## 📊 Results

**Validation Accuracy:** ~96%  
**Validation F1 Score:** ~0.96  
**Model Used:** DistilBERT (fine-tuned on FinancialPhraseBank dataset with class weights to handle imbalance)  

**Key Insights:**
- Positive coverage is strongly associated with successful funding rounds, growth announcements, and partnerships.  
- Negative coverage is often linked to company losses, shutdowns, or layoffs.  
- Neutral coverage corresponds to market stability updates, general company information, or announcements without sentiment.  

## 👨‍💻 Contributors

Soumil Malik – Developer

## 📜 License

This project is licensed under the MIT License – feel free to use and modify with credits.
