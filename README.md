# 📌 Minor Project – Startup News Sentiment Analysis

## 🚀 Overview
This project is developed as part of the **Minor Project** for the B.Tech program.  
It demonstrates the integration of **Data Science, NLP, and CI/CD pipelines** to build an end-to-end solution.  

The aim of the project is to **analyze startup-related news articles and determine the sentiment (positive, negative, neutral)** using machine learning and natural language processing.

---

## 🛠️ Tech Stack
- **Programming Language:** Python 3.11  
- **Frameworks/Libraries:**
  - Hugging Face Transformers
  - PyTorch
  - Pandas, NumPy
  - Scikit-learn (for preprocessing + metrics) 
- **Database:** PostgreSQL  
- **Version Control:** Git + GitHub  
- **CI/CD:** GitHub Actions  

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
Startup-News-Sentiment-Analysis/
│── src/
│   ├── database/         # Database connection & queries
│   ├── pipeline/         # Data processing & ML pipeline
│   ├── logger.py         # Logging setup
│   └── utils.py          # Helper functions
│── tests/                # Unit tests
│── requirements.txt      # Project dependencies
│── README.md             # Project documentation
│── .github/workflows/    # CI/CD pipeline configs
```

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
