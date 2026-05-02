import json
import requests
import time
from pathlib import Path

BOT_URL = "http://localhost:8083"
DATASET_DIR = Path("dataset")
OUTPUT_FILE = "submission.jsonl"

def push_context(scope, cid, payload):
    url = f"{BOT_URL}/v1/context"
    body = {
        "scope": scope,
        "context_id": cid,
        "version": 1,
        "payload": payload,
        "delivered_at": "2026-05-02T10:00:00Z"
    }
    resp = requests.post(url, json=body)
    return resp.status_code == 200

def get_submission():
    with open(DATASET_DIR / "test_pairs.json") as f:
        test_pairs = json.load(f)["pairs"]

    # Load categories
    categories = {}
    for f in (DATASET_DIR / "categories").glob("*.json"):
        with open(f) as fp:
            data = json.load(fp)
            categories[data["slug"]] = data

    results = []
    
    print(f"Generating submission for {len(test_pairs)} test pairs...")
    
    for pair in test_pairs:
        test_id = pair["test_id"]
        trg_id = pair["trigger_id"]
        m_id = pair["merchant_id"]
        c_id = pair["customer_id"]
        
        # Load payloads
        with open(DATASET_DIR / "merchants" / f"{m_id}.json") as f:
            merchant = json.load(f)
        with open(DATASET_DIR / "triggers" / f"{trg_id}.json") as f:
            trigger = json.load(f)
        
        category = categories[merchant["category_slug"]]
        
        # Push context
        push_context("category", merchant["category_slug"], category)
        push_context("merchant", m_id, merchant)
        if c_id:
            with open(DATASET_DIR / "customers" / f"{c_id}.json") as f:
                customer = json.load(f)
            push_context("customer", c_id, customer)
        push_context("trigger", trg_id, trigger)
        
        # Tick
        url = f"{BOT_URL}/v1/tick"
        body = {"now": "2026-05-02T10:30:00Z", "available_triggers": [trg_id]}
        resp = requests.post(url, json=body)
        
        if resp.status_code == 200:
            actions = resp.json().get("actions", [])
            if actions:
                action = actions[0]
                submission_entry = {
                    "test_id": test_id,
                    "body": action["body"],
                    "cta": action["cta"],
                    "send_as": action["send_as"],
                    "suppression_key": action["suppression_key"],
                    "rationale": action["rationale"]
                }
                results.append(submission_entry)
                print(f"  [{test_id}] Success")
            else:
                print(f"  [{test_id}] No action returned")
        else:
            print(f"  [{test_id}] Failed with status {resp.status_code}")
        
        time.sleep(0.5) # Slight delay to be safe

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for entry in results:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    
    print(f"Done! Submission saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    get_submission()
