from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from groq import Groq
import json
import os

# -----------------------------------------------------------
# App Setup
# -----------------------------------------------------------
app = FastAPI(title="FoodCard API", version="1.0")

# CORS (for Flutter/web frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------------------------------------
# Groq Client
# -----------------------------------------------------------
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# -----------------------------------------------------------
# Models
# -----------------------------------------------------------
class MenuRequest(BaseModel):
    text: str

# -----------------------------------------------------------
# Routes
# -----------------------------------------------------------
@app.get("/")
def root():
    """Default route (for browser visits)."""
    return {
        "message": "✅ FoodCard backend is running.",
        "endpoints": {
            "health": "/healthz",
            "parse menu": "POST /parse_menu",
            "debug": "POST /debug",
        },
    }


@app.get("/healthz")
def health_check():
    """Render health check endpoint."""
    return {"status": "ok"}


@app.post("/parse_menu")
async def parse_menu(req: MenuRequest):
    """Parses raw menu text into structured JSON using Groq."""
    try:
        prompt = f"""
        You are a helpful assistant. Analyze the following restaurant menu text
        and extract structured JSON with categories and items.

        STRICTLY return valid JSON only in this format:
        [
          {{
            "name": "CategoryName",
            "items": [
              {{"name": "Item Name", "price": "Price"}}
            ]
          }}
        ]

        Menu text:
        {req.text}
        """

        # Groq API call
        completion = groq_client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=500,
        )

        # Raw response
        ai_response = completion.choices[0].message.content.strip()

        # Try parsing JSON
        try:
            categories = json.loads(ai_response)
        except json.JSONDecodeError:
            # If Groq gives text instead of JSON → fallback
            categories = [
                {"name": "Menu", "items": [{"name": req.text, "price": ""}]}
            ]

        return {"categories": categories}

    except Exception as e:
        return {"categories": [], "error": str(e)}


@app.post("/debug")
async def debug_groq(req: MenuRequest):
    """Returns raw Groq output (for debugging)."""
    try:
        prompt = f"Extract menu items as JSON: {req.text}"

        completion = groq_client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=500,
        )

        return {"raw": completion.choices[0].message.content}

    except Exception as e:
        return {"raw": "", "error": str(e)}
