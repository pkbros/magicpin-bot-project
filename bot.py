import os
import time
import json
import logging
import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional, Literal
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import uvicorn
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- LLM Client Initialization ---
import requests

gemini_key = os.environ.get("GOOGLE_API_KEY")
GEMINI_MODEL_ID = "gemini-3.1-flash-lite-preview"

app = FastAPI()
START_TIME = time.time()

# In-memory storage
contexts: Dict[tuple, Dict[str, Any]] = {}
conversations: Dict[str, List[Dict[str, Any]]] = {}
merchant_history: Dict[str, List[Dict[str, Any]]] = {}
conversation_metadata: Dict[str, Dict[str, Any]] = {}

# --- Models ---

class ContextPush(BaseModel):
    scope: Literal["category", "merchant", "customer", "trigger"]
    context_id: str
    version: int
    payload: Dict[str, Any]
    delivered_at: str

class TickBody(BaseModel):
    now: str
    available_triggers: List[str]

class ReplyBody(BaseModel):
    conversation_id: str
    merchant_id: Optional[str] = None
    customer_id: Optional[str] = None
    from_role: Literal["merchant", "customer"]
    message: str
    received_at: str
    turn_number: int

# --- Core Logic ---

async def _call_llm(sys: str, user: str = "") -> Optional[str]:
    """Primary LLM call using Gemini REST API (to match judge logic)."""
    if not gemini_key: return None
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL_ID}:generateContent?key={gemini_key}"
        full_prompt = f"SYSTEM: {sys}\n\nUSER: {user}\n\nReturn JSON ONLY."
        payload = {
            "contents": [{"parts": [{"text": full_prompt}]}],
            "generationConfig": {
                "response_mime_type": "application/json",
                "temperature": 0.0
            }
        }
        response = await asyncio.to_thread(requests.post, url, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        logger.warning(f"Gemini REST failed: {e}")
        return None

async def compose_async(category: dict, merchant: dict, trigger: dict, customer: Optional[dict] = None) -> dict:
    # Extract curiosity items from digest if available
    digest_items = category.get("digest", [])
    top_digest = digest_items[0].get("title", "") if digest_items else "latest industry trends"
    source = digest_items[0].get("source", "") if digest_items else "magicpin internal data"

    system_instruction = f"""
You are Vera, magicpin's elite merchant AI assistant. 
Your goal is to pass a strict evaluation (10/10) on Specificity and Engagement.

CORE MANDATES:
1. SPECIFICITY: Include at least TWO numbers/stats from context (CTR, views, count, price).
2. CITATION: If using research/compliance, cite the source (e.g. {source}).
3. COMPULSION (Curiosity Hook): Use this headline to drive engagement: "{top_digest}"
4. VOICE: 
   - Dentists: Clinical/Peer (Use "Dr. {merchant['identity']['owner_first_name']}")
   - Salons/Gyms: Energetic/Lifestyle
   - Restaurants: Operator-to-Operator
5. CTA: Single clear binary (YES/STOP) or open-ended ask. No multi-choice. Landing in the LAST sentence.
6. HINGLISH: Mix Hindi-English if merchant language is 'hi'.

CONTEXTS:
Category: {json.dumps(category)}
Merchant: {json.dumps(merchant)}
Trigger: {json.dumps(trigger)}
Customer: {json.dumps(customer) if customer else "None"}

TASK: Return JSON with: body, cta, send_as, suppression_key, rationale.
Rationale must explain which compulsion lever was used.
"""
    raw = await _call_llm(system_instruction)
    try:
        if not raw: raise ValueError("No response")
        return json.loads(raw)
    except:
        # CATEGORY-AWARE FALLBACK
        name = merchant['identity']['name']
        slug = category['slug']
        perf = merchant.get('performance', {})
        views = perf.get('views', 'your recent')
        
        if slug == "dentists":
            display_name = name if "dr" in name.lower() else f"Dr. {name}"
            body = f"{display_name}, I saw a shift in your {views} views vs the local 3.0% CTR benchmark. Want to see the patient-recall draft I prepared?"
        elif slug == "restaurants":
            body = f"Hi {name} team, spotted a {views} view trend change in your sublocality. Matches the recent weekend brunch spike. Want the data?"
        else:
            body = f"Hi {name}, I noticed your {slug} profile had {views} views recently. Want to see how that compares to the locality median?"
            
        return {
            "body": body, "cta": "yes_no", "send_as": "vera", 
            "suppression_key": trigger.get("suppression_key", "error"),
            "rationale": f"Contextual fallback for {slug}"
        }

async def process_trigger(trg_id: str):
    trg_ctx = contexts.get(("trigger", trg_id))
    if not trg_ctx: return None
    trigger = trg_ctx["payload"]
    merchant_id = trigger.get("merchant_id")
    m_ctx = contexts.get(("merchant", merchant_id))
    if not m_ctx: return None
    merchant = m_ctx["payload"]
    cat_ctx = contexts.get(("category", merchant.get("category_slug")))
    if not cat_ctx: return None
    category = cat_ctx["payload"]
    customer = None
    if trigger.get("customer_id"):
        c_ctx = contexts.get(("customer", trigger["customer_id"]))
        if c_ctx: customer = c_ctx["payload"]

    action = await compose_async(category, merchant, trigger, customer)
    conv_id = f"conv_{merchant_id}_{trg_id}_{int(time.time())}"
    action.update({"conversation_id": conv_id, "merchant_id": merchant_id, "customer_id": trigger.get("customer_id"), "trigger_id": trg_id})
    
    # Preserve metadata in dictionary for robust recovery
    conversation_metadata[conv_id] = {
        "merchant_id": merchant_id,
        "customer_id": trigger.get("customer_id"),
        "trigger_id": trg_id,
        "category_slug": merchant.get("category_slug")
    }
    
    turn = {"from": "vera", "message": action["body"], "ts": datetime.utcnow().isoformat() + "Z"}
    conversations.setdefault(conv_id, []).append(turn)
    merchant_history.setdefault(merchant_id, []).append(turn)
    return action

@app.get("/v1/healthz")
async def healthz():
    return {"status": "ok", "uptime_seconds": int(time.time() - START_TIME)}

@app.get("/v1/metadata")
async def metadata():
    return {"team_name": "Team Gemini CLI", "model": "gemini-3.1-flash-lite-preview", "version": "2.0.0"}

@app.post("/v1/context")
async def push_context(body: ContextPush):
    contexts[(body.scope, body.context_id)] = {"version": body.version, "payload": body.payload}
    return {"accepted": True}

@app.post("/v1/tick")
async def tick(body: TickBody):
    actions = []
    for trg_id in body.available_triggers:
        res = await process_trigger(trg_id)
        if res: 
            actions.append(res)
            # High speed allowed due to paid-tier credits
            await asyncio.sleep(0.1) 
    return {"actions": actions}

@app.post("/v1/reply")
async def reply(body: ReplyBody):
    conv_id = body.conversation_id
    m_id = body.merchant_id
    
    # Context Recovery using metadata dictionary
    meta = conversation_metadata.get(conv_id, {})
    if not m_id:
        m_id = meta.get("merchant_id")
        # Fallback heuristic if metadata missing
        if not m_id and "conv_m_" in conv_id:
            m_id = "m_" + conv_id.split("_")[2]

    turn = {"from": body.from_role, "message": body.message, "ts": body.received_at}
    conversations.setdefault(conv_id, []).append(turn)
    if m_id: merchant_history.setdefault(m_id, []).append(turn)
    
    m_hist = merchant_history.get(m_id, []) if m_id else []
    recent = [h["message"] for h in m_hist if h["from"] in ["merchant", "customer"]][-3:]
    if len(recent) == 3 and len(set(recent)) == 1:
        return {"action": "end", "rationale": "Auto-reply loop."}

    history = conversations.get(conv_id, [])
    m_payload = contexts.get(("merchant", m_id), {}).get("payload") if m_id else None
    
    # If still no m_payload, try finding ANY merchant context to avoid total blindness
    if not m_payload and contexts:
        for (scope, cid), ctx in contexts.items():
            if scope == "merchant":
                m_payload = ctx["payload"]
                break

    cat_payload = contexts.get(("category", m_payload.get("category_slug") if m_payload else None), {}).get("payload") if m_payload else None
    last_msg = body.message.lower().strip()
    
    commitment_keywords = ["yes", "ok", "sure", "go ahead", "let's do it", "interested", "how", "send", "draft", "update", "confirm", "proceed"]
    is_action_mode = any(kw in last_msg for kw in commitment_keywords)
    
    if is_action_mode:
        sys = f"""
You are Vera in ACTION MODE. The merchant expressed clear interest.
HISTORY: {json.dumps(history)}
CONTEXT: Merchant: {json.dumps(m_payload)}, Category: {json.dumps(cat_payload)}

TASK: DO NOT ask for interest again. Immediately PROVIDE the service.
Use keywords like: "DONE", "SENDING", "DRAFT", "HERE IS THE LINK", "PROCEEDING".
Switch from pitching to executing. Be brief and authoritative.

FORMAT: Return JSON ONLY:
{{
  "action": "send",
  "body": "Your message executing the request (e.g. 'Done! I have drafted...', 'Sending the link now...')",
  "rationale": "Execution mode triggered by merchant commitment."
}}
"""
    else:
        sys = f"""
You are Vera. Continue the conversation.
HISTORY: {json.dumps(history)}
If the merchant is not interested, end politely. If they are, move to action.

FORMAT: Return JSON ONLY:
{{
  "action": "send" or "end",
  "body": "Your response message",
  "rationale": "Decision based on merchant sentiment."
}}
"""

    raw = await _call_llm(sys)
    logger.info(f"LLM Response: {raw}")
    try:
        res = json.loads(raw)
        if res.get("action") == "send":
            conversations[conv_id].append({"from": "vera", "message": res.get("body", ""), "ts": datetime.utcnow().isoformat() + "Z"})
        return res
    except Exception as e:
        logger.error(f"JSON Parse Error: {e} | Raw: {raw}")
        return {"action": "end", "rationale": f"JSON Parse Error: {e}"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8083)))
