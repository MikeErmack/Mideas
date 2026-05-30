# GrokBet Pre-Match Analyzer

This tool automatically analyzes upcoming football matches (next 3 days) from the major leagues + World Cup and sends you a detailed report via Telegram every morning.

It is designed to be **API-efficient** (stays well under 95 calls per day) while providing useful stats and suggestions for pre-match analysis.

## Features
- Analyzes matches from 11 leagues (including World Cup)
- Runs automatically every morning via GitHub Actions
- Sends 2 Telegram messages:
  1. Summary of the top 15 most interesting matches
  2. Deep dive analysis on the best 6 matches + suggestions
- Focuses on the most relevant stats for decision making
- Fully automated (no need to run locally)

## Requirements
- Free API-Football key (100 calls/day)
- Telegram Bot + Chat ID
- GitHub account (free)

---

## Setup Instructions

### 1. Create a new GitHub Repository
1. Go to GitHub and create a new repository (can be public or private).
2. Name it something like `grokbet-prematch-analyzer`.

### 2. Add your files
Upload the following files to your repository:
- `main.py` (the analyzer script)
- `.github/workflows/daily-analysis.yml` (the automation file)

### 3. Add Secrets (Very Important)
Go to your repository → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

Add these 3 secrets:

| Secret Name            | Description                          |
|------------------------|--------------------------------------|
| `API_KEY`              | Your API-Football key                |
| `TELEGRAM_BOT_TOKEN`   | Your Telegram Bot token              |
| `TELEGRAM_CHAT_ID`     | Your Telegram Chat ID                |

### 4. Enable GitHub Actions
- Go to the **Actions** tab in your repository.
- If prompted, click **"I understand my workflows, go ahead and enable them"**.

The workflow is already configured to run every day at **07:30 French Guiana time** (10:30 UTC).

---

## How to Change the Run Time

Open the file `.github/workflows/daily-analysis.yml` and edit this line:

```yaml
cron: '30 10 * * *'   # Runs at 10:30 UTC = 07:30 French Guiana time
```

To change the time, calculate UTC based on French Guiana (UTC-3):

- 07:00 French Guiana time → `00 10 * * *`
- 08:00 French Guiana time → `00 11 * * *`
- 09:00 French Guiana time → `00 12 * * *`

---

## How to Update the Script

1. Make changes to `main.py`
2. Commit and push to GitHub
3. The next scheduled run will use the new version

---

## Notes & Limitations

- The free API-Football plan has 100 calls/day. This script is optimized to use ~70-85 calls per run.
- The quality of analysis depends on the data available in the API.
- This tool is for **analysis and information only**. It does not guarantee winning bets.
- World Cup data will only appear when matches are scheduled.

---

## Support

If you want to:
- Add more leagues
- Change the number of matches analyzed
- Modify the message format
- Add more stats

Just tell me and I can update the script for you.

Good luck with your analysis!