from fastapi import FastAPI
from pydantic import BaseModel
import openai
import os
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
import re

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Initialize FastAPI
app = FastAPI()

# Allow Flutter (mobile/web) to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------- Chat Endpoint -----------------
class ChatRequest(BaseModel):
    message: str

@app.post("/chat")
async def chat(req: ChatRequest):
    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": req.message}],
        )
        return {"reply": response.choices[0].message["content"]}
    except Exception as e:
        return {"error": str(e)}

# ----------------- Menu Parser Endpoint -----------------
class MenuText(BaseModel):
    text: str

CATEGORY_KEYWORDS = {
    "veg": ["veg", "paneer"],
    "non veg": ["chicken", "mutton", "fish", "egg"],
    "drinks": ["lassi", "juice", "shake", "soda", "drink", "mocktail", "cocktail"],
    "biryani": ["biryani"],
    "starters": ["starter", "tandoor", "appetizer"],
    "main course": ["curry", "dal", "rice", "naan", "roti"]
}

@app.post("/parse_menu")
async def parse_menu(data: MenuText):
    lines = data.text.split("\n")
    categories = []

    for cat_name, keywords in CATEGORY_KEYWORDS.items():
        items = []
        for line in lines:
            if any(kw.lower() in line.lower() for kw in keywords):
                match = re.search(r"(.*?)(₹?\$?\d+)", line)
                if match:
                    item_name = match.group(1).strip()
                    price = match.group(2).strip()
                else:
                    item_name, price = line.strip(), ""
                items.append({"name": item_name, "price": price})
        if items:
            categories.append({"name": cat_name, "items": items})

    return {"categories": categories}
