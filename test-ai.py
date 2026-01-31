import os
from dotenv import load_dotenv
import google.generativeai as genai

# 1. Load Key
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

print(f"Checking Key: {api_key[:5]}... (Hidden)") 

if not api_key:
    print("❌ ERROR: No API Key found in .env file!")
    exit()

# 2. Configure Gemini
try:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    print("🤖 Sending test message to Gemini...")
    response = model.generate_content("Hello, are you working?")
    
    print("✅ SUCCESS! Gemini replied:")
    print(response.text)

except Exception as e:
    print("\n❌ GEMINI FAILED:")
    print(e)