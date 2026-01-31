import json
import os
import secrets
from fastapi import FastAPI, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv
import google.generativeai as genai

# 1. Setup
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("❌ ERROR: No API Key found in .env file!")

genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-2.5-flash')

app = FastAPI()

# 2. Serve HTML Files (The "Pages")
# Ensure the 'static' folder exists before mounting
if os.path.isdir("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")
else:
    print("⚠️ WARNING: 'static' folder not found. Please create it and move html files there.")

@app.get("/")
def read_root():
    return FileResponse('static/login.html')

@app.get("/app")
def read_app():
    return FileResponse('static/app.html')

@app.get("/about")
def read_about():
    if os.path.exists('static/about.html'):
        return FileResponse('static/about.html')
    return {"message": "About page coming soon"}

# 3. Load Data
try:
    with open("data/legal_data.json", "r") as f:
        LEGAL_DATA = json.load(f)
except FileNotFoundError:
    print("❌ ERROR: data/legal_data.json not found!")
    LEGAL_DATA = {}

# 4. Security Logic
class LoginRequest(BaseModel):
    username: str
    password: str

@app.post("/api/login")
def login(creds: LoginRequest):
    # Hardcoded user for demo
    if creds.username == "admin" and creds.password == "lawline2026":
        token = secrets.token_hex(16)
        return {"status": "success", "token": token, "user": "Administrator"}
    else:
        return JSONResponse(status_code=401, content={"status": "error", "message": "Invalid Credentials"})

# 5. The AI Brain (Restored!)
class UserQuery(BaseModel):
    text: str
    language: str = "English"

@app.post("/analyze")
async def analyze_legal_issue(query: UserQuery):
    print(f"🔍 ANALYZING: {query.text}")
    
    # A. Identify Category
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
        print(f"🤖 AI DECISION: {category_key}")
        
        # B. Handle Logic
        if category_key in LEGAL_DATA:
            result = LEGAL_DATA[category_key]
            
            # Draft Formal Letter
            draft_prompt = f"""
            Act as a professional lawyer.
            User Situation: "{query.text}"
            Legal Ground: "{result['act']}"
            Task: Write a formal 'Legal Notice' or 'Complaint Letter'.
            - Use placeholders like [Date], [Name].
            - Language: {query.language}.
            """
            draft_letter = model.generate_content(draft_prompt).text
            
            # Simple Steps
            steps_prompt = f"Explain these steps in simple {query.language} as a bulleted list: {result['procedure']}"
            simple_steps = model.generate_content(steps_prompt).text

            return {
                "status": "success",
                "category": result["title"],
                "act": result["act"],
                "simple_explanation": simple_steps,
                "draft_letter": draft_letter,
                "source": result["source"]
            }

        elif category_key == "irrelevant":
            return {"status": "error", "message": "I can only help with legal problems. Please describe the incident."}
        
        else:
            return {"status": "error", "message": "This is a valid legal issue, but my database is still learning it. Please consult a lawyer."}

    except Exception as e:
        print(f"💥 CRASH: {str(e)}")
        return {"status": "error", "message": f"Server Error: {str(e)}"}