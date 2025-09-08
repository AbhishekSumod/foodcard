from fastapi import FastAPI
from pydantic import BaseModel
import requests
import os
from dotenv import load_dotenv

load_dotenv()
HF_API_KEY = os.getenv("HF_API_KEY")
MODEL_URL = "https://api-inference.huggingface.co/models/gpt2"  # You can choose a text generation model

app = FastAPI()

class MenuRequest(BaseModel):
    text: str

@app.post("/parse_menu")
async def parse_menu(req: MenuRequest):
    text = req.text
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    data = {
        "inputs": f"Extract menu categories, item names, and prices from this text: {text}",
    }

    try:
        response = requests.post(MODEL_URL, headers=headers, json=data, timeout=30)
        result = response.json()
        
        # You may need to parse result[0]['generated_text'] depending on the model
        generated_text = result[0].get("generated_text", "") if isinstance(result, list) else ""
        
        # Simple mock parser (replace with proper logic or regex)
        categories = []
        for line in generated_text.split("\n"):
            if "$" in line or "₹" in line:  # crude price detection
                parts = line.split("-")
                if len(parts) == 2:
                    name = parts[0].strip()
                    price = parts[1].strip()
                    categories.append({"name": "Menu", "items": [{"name": name, "price": price}]})
        
        return {"categories": categories}
    except Exception as e:
        return {"categories": [], "error": str(e)}
