from fastapi import FastAPI
from pydantic import BaseModel
import os
import requests
from fastapi.middleware.cors import CORSMiddleware

# Load environment variable
HF_API_KEY = os.getenv("HF_API_KEY")

app = FastAPI()

# Allow CORS for Flutter
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
    """
    Send extracted text to Hugging Face model and return structured menu
    """
    HF_MODEL = "flax-community/text2json"  # e.g., a text2json model
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    payload = {"inputs": req.text}

    try:
        response = requests.post(
            f"https://api-inference.huggingface.co/models/{HF_MODEL}",
            headers=headers,
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        # Hugging Face model might return string JSON, so parse it
        import json
        try:
            menu_data = json.loads(data.get("generated_text", "{}"))
        except:
            menu_data = {"categories": []}
        return menu_data
    except Exception as e:
        return {"categories": [], "error": str(e)}
