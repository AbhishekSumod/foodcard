from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
HF_API_KEY = os.getenv("HF_API_KEY")

# Initialize FastAPI
app = FastAPI()

# Allow Flutter app to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------- Root route -----------------
@app.get("/")
async def root():
    return {"message": "Menu Parser API is running!"}

# ----------------- MenuText Schema -----------------
class MenuText(BaseModel):
    text: str

# ----------------- Menu Parser using Hugging Face -----------------
@app.post("/parse_menu")
async def parse_menu_hf(data: MenuText):
    prompt = f"""
You are an AI menu parser. Analyze the following restaurant menu text.
Return a JSON array of categories. Each category must have a 'name' and an 'items' array.
Each item must have 'name' and 'price' fields.

Format example:
[
  {{
    "name": "Drinks",
    "items": [
      {{"name": "Lemon Soda", "price": "$2"}},
      {{"name": "Mango Shake", "price": "$3"}}
    ]
  }},
  {{
    "name": "Fast Food",
    "items": [
      {{"name": "Cheese Burger", "price": "$5"}}
    ]
  }}
]

Menu Text:
{data.text}
"""

    try:
        headers = {
            "Authorization": f"Bearer {HF_API_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "inputs": prompt,
            "parameters": {"max_new_tokens": 500},
        }

        response = requests.post(
            "https://api-inference.huggingface.co/models/google/flan-t5-small",
            headers=headers,
            json=payload,
            timeout=30
        )

        result = response.json()

        # Hugging Face returns text in 'generated_text'
        text_output = result[0]["generated_text"] if isinstance(result, list) else str(result)

        # Try to parse as JSON
        try:
            categories = json.loads(text_output)
        except Exception as e:
            categories = []
            return {"categories": [], "error": f"Failed to parse JSON: {str(e)}", "raw_response": text_output}

        return {"categories": categories}

    except Exception as e:
        return {"categories": [], "error": str(e)}
