from transformers import AutoTokenizer, AutoModelForSequenceClassification
import os

os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

model_name = "distilbert-base-uncased-finetuned-sst-2-english"

tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name)

model.save_pretrained("./bert_model")
tokenizer.save_pretrained("./bert_model")

print("Model and tokenizer saved successfully.")
