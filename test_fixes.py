import asyncio
import json
import os
from bot import _call_llm, ReplyBody

# Mocking the context for the dentist case in the email
m_payload = {
    "identity": {"name": "Dr. Meera", "owner_first_name": "Meera"},
    "category_slug": "dentists",
    "performance": {"ctr": "2.1%"}
}

async def test_hallucination_fix():
    print("--- Testing Appointment Hallucination Fix ---")
    history = [
        {"from": "vera", "message": "Dr. Meera, your current clinic CTR of 2.1% is trailing the metro solo practice median of 3.0%..."},
        {"from": "merchant", "message": "Got it doc — need help auditing my X-ray setup. We have an old D-speed film unit."},
        {"from": "vera", "message": "Understood. Transitioning from D-speed film to digital is a significant upgrade..."},
        {"from": "customer", "message": "Yes please book me for Wed 5 Nov, 6pm."}
    ]
    
    # Simulate the 'customer' reply logic
    sys = f"""
You are Vera, assisting 'Dr. Meera'.
CUSTOMER MESSAGE: "Yes please book me for Wed 5 Nov, 6pm."
HISTORY: {json.dumps(history)}

TASK: Help the customer fulfill their request (booking, info, etc.).
STRICT RULE: Ground your response ONLY in the current conversation history. 
Do NOT hallucinate tasks (like drafting Google posts) that were not explicitly discussed in this thread.
Be helpful, professional, and very brief.

FORMAT: Return JSON ONLY:
{{
  "action": "send",
  "body": "Your response confirming or assisting the customer",
  "rationale": "Customer service fulfillment based strictly on history."
}}
"""
    response = await _call_llm(sys)
    print(f"Bot Response: {response}")

async def test_specificity_and_engagement():
    print("\n--- Testing Specificity and Engagement ---")
    history = [
        {"from": "vera", "message": "Hi Lakshmi, your 4.8% CTR is currently outperforming the local salon median..."},
        {"from": "merchant", "message": "That's good to hear, what should I do next?"}
    ]
    
    # Simulate the 'merchant engagement' reply logic
    sys = f"""
You are Vera, elite merchant assistant.
MERCHANT MESSAGE: "That's good to hear, what should I do next?"
HISTORY: {json.dumps(history)}
CONTEXT: {json.dumps(m_payload)}

TASK:
1. Continue the conversation toward a high-value action.
2. SPECIFICITY: Use at least one number from the CONTEXT in your reply.
3. ENGAGEMENT: End with a clear, low-friction binary question or next step.
4. If not interested, end politely.

FORMAT: Return JSON ONLY:
{{
  "action": "send" or "end",
  "body": "Your response message",
  "rationale": "Driving engagement with specific data points."
}}
"""
    response = await _call_llm(sys)
    print(f"Bot Response: {response}")

if __name__ == "__main__":
    asyncio.run(test_hallucination_fix())
    asyncio.run(test_specificity_and_engagement())
