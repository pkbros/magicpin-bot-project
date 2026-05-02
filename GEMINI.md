# magicpin AI Challenge - Project Instructions

## 1. Environment & Infrastructure
- **Primary Port**: 8083 (Use this to avoid conflicts on 8080).
- **LLM Provider**: Google Gemini (REST API preferred for stability).
- **Primary Model**: `gemini-3.1-flash-lite-preview` (Fastest and most cost-effective for 2026 era).

## 2. Remote Repository & Deployment
- **GitHub**: https://github.com/pkbros/magicpin-bot-project.git
- **Production URL**: https://magicpin-vera-bot-700751489270.asia-southeast1.run.app

## 4. Model Context Protocol (MCP)
- **GCP Server**: Added `@googlecloudplatform/mcp-server-google-cloud` to user settings.
- **Tools**: This enables direct management of Cloud Run, IAM, and other GCP services via the AI agent.
- **Verification**: Run `gemini mcp list` to ensure `google-cloud` is active.
