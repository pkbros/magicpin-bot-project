import asyncio
import os
import json
from unittest.mock import patch, AsyncMock
from bot import _call_llm_tiered

async def test_fallback():
    print("\n--- Testing Tiered Fallback (Mocking Failures) ---")
    
    # 1. Test Groq Success
    with patch("bot._call_llm_groq", new_callable=AsyncMock) as mock_groq:
        mock_groq.return_value = '{"msg": "Groq Success"}'
        print("Scenario 1: Groq available")
        res = await _call_llm_tiered("sys", "user")
        print(f"Result: {res}")
        assert "Groq Success" in res

    # 2. Test Fallback to Gemini
    with patch("bot._call_llm_groq", new_callable=AsyncMock) as mock_groq:
        mock_groq.return_value = None
        with patch("bot._call_llm_gemini", new_callable=AsyncMock) as mock_gemini:
            mock_gemini.return_value = '{"msg": "Gemini Success"}'
            print("\nScenario 2: Groq fails, Gemini available")
            res = await _call_llm_tiered("sys", "user")
            print(f"Result: {res}")
            assert "Gemini Success" in res

    # 3. Test Fallback to NVIDIA
    with patch("bot._call_llm_groq", new_callable=AsyncMock) as mock_groq:
        mock_groq.return_value = None
        with patch("bot._call_llm_gemini", new_callable=AsyncMock) as mock_gemini:
            mock_gemini.return_value = None
            with patch("bot._call_llm_nvidia", new_callable=AsyncMock) as mock_nvidia:
                mock_nvidia.return_value = '{"msg": "NVIDIA Success"}'
                print("\nScenario 3: Groq & Gemini fail, NVIDIA available")
                res = await _call_llm_tiered("sys", "user")
                print(f"Result: {res}")
                assert "NVIDIA Success" in res

    # 4. Test Total Failure
    with patch("bot._call_llm_groq", new_callable=AsyncMock) as mock_groq:
        mock_groq.return_value = None
        with patch("bot._call_llm_gemini", new_callable=AsyncMock) as mock_gemini:
            mock_gemini.return_value = None
            with patch("bot._call_llm_nvidia", new_callable=AsyncMock) as mock_nvidia:
                mock_nvidia.return_value = None
                print("\nScenario 4: All providers fail")
                res = await _call_llm_tiered("sys", "user")
                print(f"Result: {res}")
                assert res is None

    print("\n--- Fallback Logic Verified (No API tokens were used) ---")

if __name__ == "__main__":
    asyncio.run(test_fallback())
