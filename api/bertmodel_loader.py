import os
from transformers import AutoTokenizer, AutoModel
from pathlib import Path

# Define model directory path
model_dir = Path(__file__).parent.parent / "bert_model"
model_name = "distilbert-base-uncased-finetuned-sst-2-english"

# Create directory if it doesn't exist
os.makedirs(model_dir, exist_ok=True)

# Check if model is already saved locally
if not (model_dir / "config.json").exists():
    print(f"Downloading and saving model {model_name} to {model_dir}...")
    # Download from Hugging Face and save
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModel.from_pretrained(model_name)
    tokenizer.save_pretrained(model_dir)
    model.save_pretrained(model_dir)
    print("Model saved successfully.")
else:
    print(f"Loading model from {model_dir}...")
    # Load from local directory
    tokenizer = AutoTokenizer.from_pretrained(model_dir)
    model = AutoModel.from_pretrained(model_dir)
    print("Model loaded successfully.")

# Export the model and tokenizer for use in other modules
