import json
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import google.generativeai as genai

# 1. Setup
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("No API Key found! Check your .env file.")

genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-2.5-flash')

app = FastAPI()

# 2. Allow Frontend to talk to Backend (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Load Legal Data
with open("data/legal_data.json", "r") as f:
    LEGAL_DATA = json.load(f)

# 4. Define Input Format
# ... (Keep your imports and setup at the top)

class UserQuery(BaseModel):
    text: str
    language: str = "English"  # <--- Added Language Support

@app.post("/analyze")
async def analyze_legal_issue(query: UserQuery):
    print(f"Received query: {query.text} in {query.language}")
    
    # 1. Identify Category (Same as before)
    available_keys = list(LEGAL_DATA.keys())
    prompt = f"""
    You are a legal dispatcher. Query: "{query.text}"
    Map to exactly one key from: {available_keys}.
    If unrelated, return 'irrelevant'. If related but not in list, return 'unknown'.
    Output ONLY the key string.
    """
    try:
        response = model.generate_content(prompt)
        category_key = response.text.strip().replace('"', '').replace("'", "")
    except Exception as e:
        return {"error": str(e)}

    # 2. Generate Logic + DRAFTING
    if category_key in LEGAL_DATA:
        result = LEGAL_DATA[category_key]
        
        # New: Ask Gemini to write a formal letter
        draft_prompt = f"""
        Act as a professional lawyer.
        User Situation: "{query.text}"
        Legal Ground: "{result['act']}"
        
        Task: Write a formal "Complaint Letter" or "Legal Notice" that the user can send to the authority/offender.
        - Keep it strict and formal.
        - Use placeholders like [Date], [My Name] for details the user needs to fill.
        - Language: {query.language}
        """
        draft_letter = model.generate_content(draft_prompt).text

        # New: Translate the explanation if needed
        explainer_prompt = f"Explain {result['procedure']} in simple {query.language}. Keep it as a numbered list."
        translated_steps = model.generate_content(explainer_prompt).text
        
        return {
            "status": "success",
            "category": result["title"],
            "act": result["act"],
            "simple_explanation": translated_steps, # Now AI generated & translated
            "draft_letter": draft_letter,           # <--- THE KEY DIFFERENTIATOR
            "source": result["source"]
        }
    
    # ... (Keep your error handling 'elif' blocks same as before)
    elif category_key == "irrelevant":
         return {"status": "error", "message": "Please describe a legal problem."}
    else:
         return {"status": "partial", "message": "This is a valid legal issue, but our database is still growing. Please consult a lawyer."}

@app.get("/")
def home():
    return {"message": "Law Line API is Running!"}