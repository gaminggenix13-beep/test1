import google.generativeai as genai
from fastapi import FastAPI, Request
import requests

app = FastAPI()

# Configure Gemini AI
api_key = os.getenv("GEMINI_API_KEY")
model = genai.GenerativeModel('gemini-3.6-flash')

# Discord Delivery Settings
DISCORD_WEBHOOK_URL = "https://discordapp.com/api/webhooks/1533007553250852964/DRHwmA68B1A6PSaCnGv6p5ePkovT2OLgmXSyVjNpMBE6LQ6ExywSSZsK9iH2mcIR7tz_" 

@app.post("/webhook")
async def receive_webhook(request: Request):
    payload = await request.json()

    # 1. Parse GitHub Action and PR Data
    pr_action = payload.get("action")
    pull_request = payload.get("pull_request", {})
    is_merged = pull_request.get("merged", False)
    
    # 2. THE LOGIC GATE: Only proceed if closed AND merged
    if not (pr_action == "closed" and is_merged):
        print(f"⚠️ Event ignored. Action: {pr_action}, Merged: {is_merged}")
        return {"status": "ignored", "reason": "PR not closed and merged"}

    # 3. Extract Clean PR Data
    pr_title = pull_request.get("title", "No Title")
    pr_body = pull_request.get("body", "No Body")
    pr_url = pull_request.get("html_url", "No URL")

    print("\n========================================")
    print("🎯 MERGED PR DATA CAUGHT")
    print("========================================")
    print(f"📌 Title: {pr_title}\n")
    
    # 4. Advanced Prompt Engineering
    print("🧠 Sending data to Gemini AI...\n")
    
    ai_prompt = f"""
    You are a top-tier technical copywriter. Convert the following GitHub Pull Request data into a minimalist, punchy product update. 
    
    Rules:
    - Use a high-contrast, editorial rhythm. Short sentences. Zero fluff.
    - Do not use emojis in the main text.
    - Focus strictly on the value delivered.
    
    PR Title: {pr_title}
    PR Body: {pr_body}
    """
    
    response = model.generate_content(ai_prompt)
    generated_artifact = response.text.strip()

    print("========================================")
    print("🚀 GTM ARTIFACT GENERATED")
    print("========================================")
    print(generated_artifact)
    print("========================================\n")

    # 5. Discord Embed Delivery
    print("📡 Broadcasting Premium Embed to Discord...")
    
    discord_data = {
        "embeds": [
            {
                "title": "SYSTEM UPDATE DEPLOYED",
                "description": generated_artifact,
                "url": pr_url,
                "color": 16777215,
                "footer": {
                    "text": "Developer-to-GTM Automator"
                }
            }
        ]
    }
    
    response = requests.post(DISCORD_WEBHOOK_URL, json=discord_data)
    
    if response.status_code == 204:
        print("✅ Successfully delivered to Discord!")
    else:
        print(f"❌ Failed to deliver. Status code: {response.status_code}")

    return {"status": "success"}