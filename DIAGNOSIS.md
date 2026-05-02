# magicpin AI Challenge: Diagnosis & Recovery Plan

## 1. Why we hit 23/50 (The "Generic Fallback" Trap)
The score of 23/50 is the result of the bot failing to generate a specific message and the judge failing to analyze the result.

### Root Causes:
*   **LLM Fallback Triggered**: The bot's `compose_async` function is returning the hardcoded fallback: `"Hi {merchant['identity']['name']}, I have some interesting data about your {category['slug']} profile. Can we chat?"`. This happens when the `_call_llm` function returns `None`.
*   **Rate Limit Exhaustion (429)**: Even with a new API key, the high volume of requests (5 batch triggers + Judge scoring calls) is exceeding the Groq `8b-instant` rate limits. 
*   **Judge Failure**: The output shows `[WARN] LLM error: HTTP Error 429`. This means the judge couldn't even "read" the message properly, leading to a default baseline score.

---

## 2. Score Breakdown (Estimated)
*   **Specificity (3/10)**: The fallback message has zero facts, numbers, or citations.
*   **Category Fit (5/10)**: Neutral; it mentions the category name but doesn't use the correct voice.
*   **Engagement (5/10)**: Uses a weak curiosity hook ("interesting data") but no real compulsion levers.

---

## 3. Possible Solutions

### A. Throttle the Judge
The `judge_simulator.py` fires requests as fast as possible. We can add a small `time.sleep()` in the simulator's batch loop to give the API keys room to breathe.

### B. Use Multi-Model Redundancy
Modify `bot.py` to use a "Backup" provider. If Groq hits a 429, the bot should immediately try the same prompt with **Gemini 1.5 Flash** (which has a very generous free tier).

### C. Improve the Fallback
The fallback should be less generic. We can create a "Template-based Fallback" that at least uses some hard stats from the `MerchantContext` (e.g., "I saw your CTR is 2.1%") so it doesn't look like a total failure.

### D. Increase Retry Jitter
Instead of a flat 2-second sleep on 429s, use exponential backoff with jitter to ensure we don't sync up with the judge's own retry logic.

---

## 4. Next Step Recommendation
1.  Verify the `GROQ_API_KEY` status in the Groq console.
2.  Implement a **Gemini backup** in `bot.py`.
3.  Add a 1-second delay between triggers in `bot.py`'s `tick` function.
