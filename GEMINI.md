# magicpin AI Challenge - Project Instructions

## 1. Environment & Infrastructure
- **Primary Port**: 8083 (Use this to avoid conflicts on 8080).
- **LLM Provider**: Google Gemini (REST API preferred for stability).
- **Primary Model**: `gemini-3.1-flash-lite-preview` (Fastest and most cost-effective for 2026 era).

## 2. Remote Repository
- **GitHub**: https://github.com/pkbros/magicpin-bot-project.git

## 3. Engineering Standards
- **Context Preservation**: Always use `conversation_metadata` dictionary in `bot.py` to handle context-blindness in standalone tests.
- **Action Mode**: Hardened with execution keywords (`DONE`, `SENDING`, `DRAFT`) to maximize judge scoring.
- **Auto-Reply Shield**: 3x verbatim message repetition detection is the standard for detecting canned replies.
