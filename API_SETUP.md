# API & Secret Configuration Guide

The agent is designed to function completely in safe deterministic mode without requiring external API keys. If you wish to enable LLM-powered narrative synthesis and live Telegram alerts, follow the steps below to configure your credentials.

---

## 1. Google Gemini API (Primary AI Synthesis)

1. Navigate to [Google AI Studio](https://aistudio.google.com/).
2. Click **Get API Key** and create a new project API key.
3. Add the key to your `.env` file:
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   GEMINI_MODEL=gemini-2.5-flash
   ```

---

## 2. OpenRouter API (Secondary AI Fallback)

1. Sign up at [OpenRouter](https://openrouter.ai/).
2. Create an API key under your Account settings.
3. Add the key to your `.env` file:
   ```env
   OPENROUTER_API_KEY=your_openrouter_api_key_here
   ```

---

## 3. Telegram Bot Configuration (Live Alerts)

1. **Create Bot**: Open Telegram, search for `@BotFather`, start a chat, and send `/newbot`. Follow the instructions to get your **Bot Token** (e.g. `123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ`).
2. **Get Chat ID**:
   - Start a chat with your new bot or add it to your channel/group.
   - Forward a message from that chat to `@userinfobot` or `@RawDataBot` to find your numerical **Chat ID** (e.g. `987654321` or `-1001234567890` for channels).
3. Add credentials to `.env`:
   ```env
   TELEGRAM_BOT_TOKEN=123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ
   TELEGRAM_CHAT_ID=987654321
   TELEGRAM_ALERTS_ENABLED=true
   ```

---

## 4. Verification

Run the verification test cycle to confirm key connectivity:
```bash
python scripts/run_cycle.py
```
Check that the output reflects your chosen AI provider and that a Telegram alert appears in your configured chat.
