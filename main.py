from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import requests
import json

# Load environment variables
load_dotenv()
HF_API_KEY = os.getenv("HF_API_KEY")

app = FastAPI()

# Request body
class MenuRequest(BaseModel):
    text: str

# Test GET route
@app.get("/")
def home():
    return {"message": "Backend is live!"}

# Parse menu POST route
@app.post("/parse_menu")
async def parse_menu(req: MenuRequest):
    try:
        prompt = f"""
        You are an assistant that converts raw restaurant menu text into structured JSON.
        Input text:
        {req.text}

        Return a JSON object with this structure:

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
        """
        
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
            data=json.dumps(payload)
        )

        if response.status_code != 200:
            return {"error": f"Hugging Face API error: {response.text}"}

        output_text = response.json().get("generated_text", "")

        # Ensure valid JSON
        try:
            menu_json = json.loads(output_text)
        except:
            # If parsing fails, return a fallback empty menu
            menu_json = {"categories": []}

        return menu_json

    except Exception as e:
        return {"error": str(e)}
