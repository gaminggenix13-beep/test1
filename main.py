import os
import asyncio
import httpx
from fastapi import FastAPI, Request, BackgroundTasks
import google.generativeai as genai

app = FastAPI()

# 1. Configure Gemini API
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

model = genai.GenerativeModel('gemini-3.6-flash')

# 2. Make.com Webhook URL (Add this to your Render Environment Variables)
MAKE_WEBHOOK_URL = os.getenv("MAKE_WEBHOOK_URL")

async def process_pr_and_notify(pr_data: dict):
    """Background task to avoid GitHub timeouts and rate limits."""
    # Safety delay: Prevents rate-limit spikes if multiple PRs merge simultaneously
    await asyncio.sleep(2)

    pr_title = pr_data.get("title", "No title")
    pr_body = pr_data.get("body", "No description provided")
    pr_author = pr_data.get("user", {}).get("login", "Unknown author")
    repo_name = pr_data.get("head", {}).get("repo", {}).get("name", "Repository")

    prompt = f"""
    You are an expert DevRel and Product Marketer. A pull request was just merged into the repo '{repo_name}'.
    
    PR Title: {pr_title}
    Author: {pr_author}
    Description/Diff Context: {pr_body}

    Generate the following 3 artifacts in clean Markdown:
    1. A benefit-driven Changelog entry for users.
    2. An internal Slack announcement summary for the team.
    3. A concise social post (X/LinkedIn) highlighting the release.
    """

    try:
        response = model.generate_content(prompt)
        generated_text = response.text
    except Exception as e:
        generated_text = f"Error generating artifact: {str(e)}"

    # If Make.com webhook URL is configured, forward the generated text
    if MAKE_WEBHOOK_URL:
        payload_to_make = {
            "repository": repo_name,
            "pr_title": pr_title,
            "author": pr_author,
            "gtm_artifact": generated_text
        }
        try:
            async with httpx.AsyncClient() as client:
                await client.post(MAKE_WEBHOOK_URL, json=payload_to_make, timeout=10.0)
        except Exception as e:
            print(f"Failed to push to Make.com: {e}")

@app.post("/webhook")
async def receive_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Catches GitHub webhooks, filters out noise to save operations,
    and responds instantly with 200 OK.
    """
    event_type = request.headers.get("X-GitHub-Event")
    payload = await request.json()

    # If it's a direct manual test or custom prompt (backward compatibility)
    if "prompt" in payload:
        try:
            res = model.generate_content(payload["prompt"])
            return {"status": "success", "artifact": res.text}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    # Filter: Only process 'pull_request' events that are officially closed and merged
    if event_type == "pull_request":
        action = payload.get("action")
        is_merged = payload.get("pull_request", {}).get("merged", False)

        if action == "closed" and is_merged:
            pr_data = payload.get("pull_request", {})
            # Schedule heavy AI processing in the background and return 200 OK immediately
            background_tasks.add_task(process_pr_and_notify, pr_data)
            return {"status": "accepted", "message": "PR is merged. Processing GTM artifact in background."}
        else:
            # Drop silently: Saves free operations
            return {"status": "ignored", "message": f"PR action '{action}' (merged={is_merged}) ignored."}

    # Ignore all other GitHub events (pushes, stars, forks)
    return {"status": "ignored", "message": f"Event '{event_type}' ignored to save resources."}

@app.get("/")
async def root():
    return {"status": "online", "service": "GTM-Artifact Automator"}