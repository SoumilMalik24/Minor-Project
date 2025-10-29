# src/utils/sentiment_utils.py
import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from src.constants import hf_token
from src.logger import logging

MODEL_ID = "Soumil24/finbert-custom"

logging.info(f"Loading FinBERT model from Hugging Face: {MODEL_ID}")
tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, use_auth_token=hf_token)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_ID, use_auth_token=hf_token)
model.eval()
device = "cuda" if torch.cuda.is_available() else "cpu"
model.to(device)
logging.info(f"FinBERT model loaded successfully on {device.upper()}")


def sentiment_score_batch(texts):
    if not texts:
        return []
    inputs = tokenizer(texts, return_tensors="pt", truncation=True, padding=True, max_length=256).to(device)
    with torch.no_grad():
        outputs = model(**inputs)
        probs = F.softmax(outputs.logits, dim=-1).cpu().numpy()
    labels = ["negative", "neutral", "positive"]
    weights = {"negative": -1, "neutral": 0, "positive": 1}
    results = []
    for prob in probs:
        sentiment = labels[int(prob.argmax())]
        score = float(sum(prob[i] * weights[labels[i]] for i in range(len(prob))))
        results.append((sentiment, score))
    return results
