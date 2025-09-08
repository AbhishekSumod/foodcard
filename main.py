from fastapi import FastAPI
from pydantic import BaseModel
import requests
import os
from fastapi.middleware.cors import CORSMiddleware
import json

# Hugging Face API key from environment variables
HF_API_KEY = os.getenv("HF_API_KEY")

app = FastAPI()

# Enable CORS so Flutter can talk to backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class MenuRequest(BaseModel):
    text: str

@app.post("/parse_menu")
async def parse_menu(req: MenuRequest):
    menu_text = req.text
    if not menu_text.strip():
        return {"categories": []}

    try:
        # Hugging Face prompt
        prompt = f"""
        Extract all menu items and prices from the text below.
        Categorize them (drinks, starters, fast food, desserts, etc.).
        Return ONLY valid JSON like this:
        {{
          "categories": [
            {{
              "name": "Category Name",
              "items": [
                {{"name": "Item Name", "price": "Item Price"}}
              ]
            }}
          ]
        }}

        Menu text:
        {menu_text}
        """

        headers = {"Authorization": f"Bearer {HF_API_KEY}"}
        payload = {"inputs": prompt}

        response = requests.post(
            "https://api-inference.huggingface.co/models/google/flan-t5-small",
            headers=headers,
            json=payload,
        )

        result = response.json()
        text_output = result[0]["generated_text"]

        try:
            data = json.loads(text_output)
        except:
            data = {"categories": []}

        return data

    except Exception as e:
        print("❌ HuggingFace error:", e)
        return {"categories": []}
