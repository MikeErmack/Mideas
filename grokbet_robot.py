import json
import requests
import os
from datetime import datetime, timedelta

# ===================== CONFIG (from GitHub Secrets) =====================
API_KEY = os.getenv("API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

headers = {'x-apisports-key': API_KEY}

LEAGUES = {
    39: "Premier League", 140: "La Liga", 78: "Bundesliga",
    135: "Serie A", 61: "Ligue 1", 88: "Eredivisie",
    203: "Primeira Liga", 307: "Saudi Pro League",
    40: "Austrian Bundesliga", 38: "Belgian Pro League"
}

def send_telegram_message(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
        requests.post(url, json=payload, timeout=15)
        print("✅ Telegram sent")
    except Exception as e:
        print("❌ Telegram error:", e)

class GrokBetRobot:
    def __init__(self):
        print("🚀 GrokBet Robot (GitHub Actions) Started")
    
    def fetch_fixtures(self):
        today = datetime.now()
        from_date = (today + timedelta(days=1)).strftime("%Y-%m-%d")
        to_date = (today + timedelta(days=10)).strftime("%Y-%m-%d")
        
        all_matches = []
        for league_id, name in LEAGUES.items():
            try:
                url = f"https://api-football-v1.p.rapidapi.com/v3/fixtures?league={league_id}&season=2026&from={from_date}&to={to_date}"
                resp = requests.get(url, headers=headers, timeout=15)
                if resp.status_code == 200:
                    data = resp.json()
                    for f in data.get('response', []):
                        all_matches.append({
                            "match": f"{f['teams']['home']['name']} vs {f['teams']['away']['name']}",
                            "league": name,
                            "date": f['fixture']['date'][:10],
                            "home_team": f['teams']['home']['name']
                        })
            except:
                continue
        return all_matches[:60]

    def run(self):
        today = datetime.now().strftime("%Y-%m-%d")
        print(f"📅 Running on: {today}\n")
        
        fixtures = self.fetch_fixtures()
        print(f"Found {len(fixtures)} fixtures\n")
        
        recommendations = []
        for fx in fixtures:
            home = fx["home_team"].lower()
            confidence = 65
            if any(t in home for t in ["bayern", "psg", "man city", "real madrid", "barcelona", "al hilal"]):
                confidence += 25
            
            if confidence >= 72:
                bet_type = "Home -1.5 Asian Handicap" if confidence > 82 else "Home Win + Over 2.5"
                odds_range = "1.40 - 1.65" if confidence > 82 else "1.45 - 1.75"
                
                rec = {
                    "match": fx["match"],
                    "league": fx["league"],
                    "date": fx["date"],
                    "recommended_bet": bet_type,
                    "odds_range": odds_range,
                    "confidence": min(92, confidence)
                }
                recommendations.append(rec)
        
        acca_legs = sorted(recommendations, key=lambda x: x['confidence'], reverse=True)[:28]
        
        msg = f"""<b>🔔 GrokBet Robot - Daily Report</b>

📅 Date: {today}
High Confidence Matches: <b>{len(acca_legs)}</b>

<b>🎯 Recommended {len(acca_legs)}-leg Accumulator</b>
"""
        for i, bet in enumerate(acca_legs[:10], 1):
            msg += f"\n{i}. <b>{bet['match']}</b>\n   → {bet['recommended_bet']} ({bet['odds_range']}) | {bet['confidence']}%"

        msg += "\n\n✅ Full recommendations generated."
        send_telegram_message(msg)
        print("✅ Robot finished!")

if __name__ == "__main__":
    robot = GrokBetRobot()
    robot.run()
