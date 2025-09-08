# main.py
import os
import json
import re
import logging
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

# Try import groq; if not installed, error will show in logs
from groq import Groq

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("foodcard")

# Read API key from environment (Render -> Environment Variables)
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    logger.warning("GROQ_API_KEY not set in environment. Set it in Render or .env for local dev.")

# Initialize Groq client
groq_client = Groq(api_key=GROQ_API_KEY)

app = FastAPI(title="FoodCard API", version="1.0")

# CORS for mobile/web clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class MenuRequest(BaseModel):
    text: str

def extract_first_json_substring(s: str):
    """
    Find the first balanced JSON object or array in `s` and return the substring.
    Returns None if not found.
    """
    if not s:
        return None
    # Find first opening brace/bracket
    for i, ch in enumerate(s):
        if ch in ['{', '[']:
            start = i
            stack = []
            pair = {'{': '}', '[': ']'}
            opener = ch
            stack.append(opener)
            j = i + 1
            while j < len(s) and stack:
                c = s[j]
                if c == opener:
                    stack.append(c)
                elif c == pair[opener]:
                    stack.pop()
                    # If popped last and stack empty and opener might appear nested — handle general nesting
                    if not stack:
                        return s[start:j+1]
                else:
                    # handle nested of different type
                    if c in ['{','[']:
                        stack.append(c)
                        # change opener/pair? keep stack content — simplest approach: track each on stack with its own expected closer
                j += 1
    return None

@app.get("/")
def root():
    return {
        "message": "FoodCard backend is running.",
        "usage": "POST /parse_menu with {\"text\": \"...\"}. Use /debug for raw AI output."
    }

@app.get("/healthz")
def healthz():
    return {"status": "ok"}

@app.post("/debug")
async def debug(req: MenuRequest):
    """
    Return the raw Groq response (no JSON parsing). Useful to inspect exactly what Groq returned.
    """
    try:
        prompt = f"Return the parsed menu from the following text. ONLY return JSON array of categories (no explanation):\n\n{req.text}"
        completion = groq_client.chat.completions.create(
           model="llama-3.3-70b-versatile",

            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=800,
        )
        # Attempt to read content
        try:
            raw = completion.choices[0].message.content
        except Exception:
            raw = str(completion)
        return {"raw": raw}
    except Exception as e:
        logger.exception("Error during /debug call")
        return {"raw": "", "error": str(e)}

@app.post("/parse_menu")
async def parse_menu(req: MenuRequest):
    """
    Receive OCR text (req.text), send to Groq, parse JSON (robust), and return:
      { "categories": [...] , "raw": "<raw ai text>", "error": "<optional>" }
    """
    if not req.text or not req.text.strip():
        return {"categories": [], "error": "empty input text", "raw": ""}

    prompt = f"""
You are a reliable assistant. Given a restaurant menu text below, EXTRACT structured JSON and RETURN ONLY the JSON array (no explanation, no markdown). The JSON must be in this exact shape:

[
  {{
    "name": "Category Name",
    "items": [
      {{"name": "Item Name", "price": "Price"}},
      ...
    ]
  }},
  ...
]

Menu text:
{req.text}
"""

    try:
        completion = groq_client.chat.completions.create(
           model="llama-3.3-70b-versatile",

            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=800,
        )
        # Read raw AI output safely:
        try:
            ai_raw = completion.choices[0].message.content
        except Exception:
            ai_raw = str(completion)

        ai_raw = ai_raw.strip()
        logger.info("Raw AI response: %s", ai_raw[:1000])  # limited log slice

        # 1) Try direct parse
        try:
            categories = json.loads(ai_raw)
            # If parse succeeded but not in expected shape, validate minimally:
            if not isinstance(categories, list):
                raise ValueError("Parsed JSON is not a list")
            return {"categories": categories, "raw": ai_raw}
        except Exception as e_direct:
            # 2) Try extracting JSON substring (robust)
            json_sub = extract_first_json_substring(ai_raw)
            if json_sub:
                try:
                    categories = json.loads(json_sub)
                    if not isinstance(categories, list):
                        raise ValueError("Extracted JSON is not a list")
                    return {"categories": categories, "raw": ai_raw}
                except Exception as e_sub:
                    logger.warning("Failed parsing extracted JSON: %s", e_sub)

            # 3) Fallback: try simple heuristics (lines with price symbols)
            fallback_items = []
            lines = req.text.splitlines()
            for line in lines:
                text = line.strip()
                if not text:
                    continue
                # simple price extraction: numbers with currency symbols or plain numbers at end
                m = re.search(r"(.+?)\s*[-–—]?\s*(₹|\$|Rs\.|Rs|INR)?\s*([0-9]+(?:\.[0-9]{1,2})?)\s*$", text)
                if m:
                    name = m.group(1).strip()
                    price = (m.group(2) or "") + m.group(3)
                    fallback_items.append({"name": name, "price": price})
            if fallback_items:
                return {"categories": [{"name": "Menu", "items": fallback_items}], "raw": ai_raw, "notice": "fallback used"}

            # ultimate fallback: return raw text as single item (no price)
            return {"categories": [{"name": "Menu", "items": [{"name": req.text.strip(), "price": ""}]}], "raw": ai_raw, "error": "could not parse structured JSON from AI output"}
    except Exception as ex:
        logger.exception("Error calling Groq")
        return {"categories": [], "error": str(ex), "raw": ""}


