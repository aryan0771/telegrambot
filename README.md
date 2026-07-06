# Telegram Channel Mirror Bot

A production-ready Telegram message mirroring system written in Python using Telethon.
It listens to a source channel and instantly copies new messages, edits, and deletions to a destination channel using your own Telegram account.

## Features
- **Real-Time Mirroring:** Copies messages in < 2 seconds.
- **Full Support:** Handles text, photos, videos, documents, and media groups.
- **Edit & Delete Sync:** If a message is edited or deleted in the source channel, the destination channel updates automatically.
- **Duplicate Prevention:** Uses SQLite to store message mappings and process history, ensuring no duplicates on restart.
- **FloodWait Handling:** Automatically sleeps and retries if rate-limited by Telegram.
- **Production-Ready:** Includes Dockerfile, auto-reconnect, structured logging, and clean architecture.

---

## 🛠 Prerequisites

1. **Telegram API ID and Hash:**
   - Go to [my.telegram.org](https://my.telegram.org) and log in.
   - Go to **API development tools**.
   - Create a new application to get your `API_ID` and `API_HASH`.

2. **Source and Destination Channels:**
   - You must be a member of the source channel.
   - You must have post permissions in the destination channel.
   - Get their IDs (typically starting with `-100`). You can use a bot like `@userinfobot` or a client like Kotatogram to find these IDs.

---

## 🚀 Local Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone <repo-url>
   cd telegram-automation
   ```

2. **Install requirements:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables:**
   Rename `.env.example` to `.env` and fill in your details:
   ```ini
   API_ID=your_api_id
   API_HASH=your_api_hash
   SESSION=mirror_session
   SOURCE_CHANNEL=-100123456789
   DESTINATION_CHANNEL=-100987654321
   LOG_LEVEL=INFO
   ```

4. **First Run (Login):**
   ```bash
   python src/main.py
   ```
   On the first run, Telethon will ask for your phone number and OTP in the terminal. Once logged in, it will create a `data/mirror_session.session` file. **Keep this file safe!** It prevents you from needing to log in again.

---

## 🐳 Running with Docker

Once you have generated the `.session` file locally inside the `data` folder, you can run the bot using Docker so it runs continuously in the background.

```bash
docker-compose up -d
```

---

## ☁️ Deployment

### 1. Railway.app
This repository contains a `railway.json` for easy deployment.
- Create a new project on Railway.
- Connect your GitHub repository.
- **IMPORTANT:** Add a volume named `data` and mount it to `/app/data` to persist your SQLite database and session file.
- Add your environment variables in the Railway dashboard.

### 2. Render.com
- Create a new **Background Worker**.
- Connect your GitHub repo.
- Build Command: `pip install -r requirements.txt`
- Start Command: `python src/main.py`
- Add a **Disk** mounted to `/app/data` so your session and database are not lost on restarts.
- Add your Environment Variables.

### 3. Fly.io
```bash
fly launch
```
- Edit `fly.toml` to add a volume mount for `/app/data`.
- Set secrets: `fly secrets set API_ID="..." API_HASH="..."`
- Deploy: `fly deploy`

---

## 🔧 Troubleshooting

- **Database Errors (No such table):** If the SQLite DB fails, it will automatically recreate the tables on the next startup. Ensure your `data` folder is mounted to a persistent volume.
- **FloodWait:** Telegram strictly limits how fast you can send messages. If you get FloodWait errors, the bot will automatically pause and resume.
- **Session Expired:** If the session file is corrupted or revoked, delete the `data/mirror_session.session` file and run `python src/main.py` locally to log in again.
