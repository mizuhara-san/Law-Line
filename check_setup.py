import os

files = {
    "static/login.html": "Login Page",
    "static/app.html": "Main App Page",
    "data/legal_data.json": "Legal Data",
    "main.py": "Server Code",
    ".env": "API Key"
}

print("\n--- DIAGNOSTIC REPORT ---")
all_good = True
for path, name in files.items():
    if os.path.exists(path):
        print(f"✅ FOUND: {name}")
    else:
        print(f"❌ MISSING: {name} (Expected at: {path})")
        all_good = False

if all_good:
    print("\nAll files are correct! Try restarting the server.")
else:
    print("\n⚠️ Fix the MISSING files above by moving them to the right folder.")