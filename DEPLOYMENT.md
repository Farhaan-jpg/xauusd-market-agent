# Deployment & Hosting Guide

This guide details deployment options for Docker, Render, and automated GitHub Actions.

---

## 1. Local / Dedicated Server (Docker Compose)

The easiest way to run the continuous agent and dashboard locally or on a VPS (AWS, DigitalOcean, Hetzner):

```bash
# Build and start the container in background
docker compose up -d --build

# View real-time logs
docker compose logs -f

# Stop container
docker compose down
```

The Web Dashboard will be available at `http://localhost:8000`.

---

## 2. Render Deployment (Web Service)

The repository includes a ready-to-deploy `render.yaml` blueprint:

1. Push your repository to GitHub.
2. Sign in to [Render](https://render.com/).
3. Click **New +** $\rightarrow$ **Blueprint**.
4. Select your repository. Render will automatically detect `render.yaml`.
5. Under Environment Variables in the Render dashboard, provide:
   - `GEMINI_API_KEY` (Optional)
   - `OPENROUTER_API_KEY` (Optional)
   - `TELEGRAM_BOT_TOKEN` (Optional)
   - `TELEGRAM_CHAT_ID` (Optional)
6. Click **Apply**.

> [!NOTE]
> Render Free instances sleep after 15 minutes of inactivity. Use the included `.github/workflows/health.yml` workflow to ping `/health` every 15 minutes to keep the service warm, or deploy on a persistent server / GitHub Actions schedule.

---

## 3. GitHub Actions Scheduled Automation

You can run the agent 100% serverless via GitHub Actions:

1. Go to your repository **Settings** $\rightarrow$ **Secrets and variables** $\rightarrow$ **Actions**.
2. Add your repository secrets:
   - `GEMINI_API_KEY`
   - `OPENROUTER_API_KEY`
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
3. The workflow in `.github/workflows/analysis.yml` will automatically run every 30 minutes on weekdays (`cron: '*/30 * * * 1-5'`), perform market analysis, persist data, and deliver Telegram updates.
