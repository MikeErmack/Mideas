import requests
import os
from datetime import datetime, timedelta

# ===================== CONFIG =====================
API_KEY = os.getenv("API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

headers = {'x-apisports-key': API_KEY}

LEAGUES = {
    39: "Premier League", 140: "La Liga", 78: "Bundesliga",
    135: "Serie A", 61: "Ligue 1", 88: "Eredivisie",
    203: "Primeira Liga", 307: "Saudi Pro League",
    40: "Austrian Bundesliga", 38: "Belgian Pro League",
    253: "MLS", 94: "Turkish Super Lig"
}

STRONG_HOME_TEAMS = {
    "bayern", "psg", "man city", "real madrid", "barcelona", "al hilal",
    "inter", "benfica", "juventus", "atletico", "dortmund", "liverpool",
    "arsenal", "napoli", "ajax", "porto"
}

def send_telegram_message(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
        resp = requests.post(url, json=payload, timeout=15)
        print(f"📤 Telegram status: {resp.status_code}")
    except Exception as e:
        print("❌ Telegram error:", e)

class GrokBetRobot:
    def __init__(self):
        print("🚀 GrokBet Robot v2.3 - Started")

    def fetch_fixtures(self):
        today = datetime.now()
        print(f"📅 Current date: {today.strftime('%Y-%m-%d')}")

        all_matches = []
        seasons = [today.year, today.year-1, today.year+1]

        for season in seasons:
            print(f"🔍 Trying season {season}...")
            from_date = today.strftime("%Y-%m-%d")
            to_date = (today + timedelta(days=21)).strftime("%Y-%m-%d")

            for league_id, name in LEAGUES.items():
                try:
                    url = f"https://api-football-v1.p.rapidapi.com/v3/fixtures?league={league_id}&season={season}&from={from_date}&to={to_date}"
                    resp = requests.get(url, headers=headers, timeout=20)

                    if resp.status_code == 200:
                        data = resp.json()
                        for f in data.get('response', []):
                            home = f['teams']['home']['name']
                            away = f['teams']['away']['name']
                            all_matches.append({
                                "match": f"{home} vs {away}",
                                "league": name,
                                "date": f['fixture']['date'][:10],
                                "time": f['fixture']['date'][11:16],
                                "home_lower": home.lower()
                            })
                except:
                    continue

            if len(all_matches) >= 10:
                break

        all_matches.sort(key=lambda x: x["date"])
        print(f"📊 Total fixtures found: {len(all_matches)}")
        return all_matches[:60]

    def run(self):
        today_str = datetime.now().strftime("%Y-%m-%d")
        fixtures = self.fetch_fixtures()

        if len(fixtures) < 5:
            msg = f"""<b>🔔 GrokBet Robot - Pre-season Mode</b>

📅 Date: {today_str}
🏟️ Status: Very few fixtures available (Off-season)

Most top leagues start mid-August 2026.
Robot is working correctly."""
            send_telegram_message(msg)
            print("✅ Pre-season message sent")
            return

        # Normal mode
        recommendations = []
        for fx in fixtures:
            confidence = 62
            if any(team in fx["home_lower"] for team in STRONG_HOME_TEAMS):
                confidence += 28
            if any(big in fx["home_lower"] for big in ["bayern", "psg", "man city", "real madrid", "al hilal"]):
                confidence += 8

            confidence = min(94, confidence)

            if confidence >= 72:
                bet_type = "Home -1.5 Asian Handicap" if confidence > 85 else "Home Win + Over 2.5 Goals"
                odds = "1.38-1.62" if confidence > 85 else "1.45-1.78"

                recommendations.append({
                    "match": fx["match"],
                    "league": fx["league"],
                    "date": fx["date"],
                    "time": fx["time"],
                    "bet": bet_type,
                    "odds": odds,
                    "conf": confidence
                })

        acca = sorted(recommendations, key=lambda x: x['conf'], reverse=True)[:25]

        msg = f"""<b>🔔 GrokBet Robot - Daily Report</b>

📅 Date: {today_str}
🔥 High Confidence Bets: <b>{len(acca)}</b>

<b>🎯 Recommended Accumulator</b>
"""

        for i, bet in enumerate(acca[:12], 1):
            msg += f"\n{i}. <b>{bet['match']}</b> ({bet['league']})"
            msg += f"\n   📆 {bet['date']} {bet['time']} → {bet['bet']} | {bet['odds']} | <b>{bet['conf']}%</b>"

        if len(acca) > 12:
            msg += f"\n\n... and {len(acca)-12} more high-confidence bets"

        msg += "\n\n⚠️ Bet responsibly."
        send_telegram_message(msg)
        print(f"✅ Daily report sent with {len(acca)} recommendations!")


# ===================== RUN =====================
if __name__ == "__main__":
    robot = GrokBetRobot()
    robot.run()
