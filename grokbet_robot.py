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

# Champions League
CL_LEAGUE_ID = 2
CL_NAME = "Champions League"

STRONG_HOME_TEAMS = {
    "bayern", "psg", "man city", "real madrid", "barcelona", "al hilal",
    "inter", "benfica", "juventus", "atletico", "dortmund", "liverpool",
    "arsenal", "napoli", "ajax", "porto", "ac milan", "bayer leverkusen"
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
        print("🚀 GrokBet Robot v2.4 - CL Priority Mode")

    def fetch_fixtures(self):
        today = datetime.now()
        print(f"📅 Current date: {today.strftime('%Y-%m-%d')}")

        all_matches = []
        seasons = [today.year, today.year-1, today.year+1]

        # Fetch domestic leagues
        for season in seasons:
            print(f"🔍 Trying season {season}...")
            from_date = today.strftime("%Y-%m-%d")
            to_date = (today + timedelta(days=21)).strftime("%Y-%m-%d")

            for league_id, name in LEAGUES.items():
                try:
                    url = f"https://api-football-v1.p.rapidapi.com/v3/fixtures?league={league_id}&season={season}&from={from_date}&to={to_date}"
                    resp = requests.get(url, headers=headers, timeout=20)
                    if resp.status_code == 200:
                        for f in resp.json().get('response', []):
                            home = f['teams']['home']['name']
                            away = f['teams']['away']['name']
                            all_matches.append({
                                "match": f"{home} vs {away}",
                                "league": name,
                                "league_id": league_id,
                                "date": f['fixture']['date'][:10],
                                "time": f['fixture']['date'][11:16],
                                "home_lower": home.lower(),
                                "is_cl": False
                            })
                except:
                    continue

            if len(all_matches) >= 15:
                break

        # Fetch Champions League matches
        try:
            print(f"🔍 Fetching Champions League...")
            url = f"https://api-football-v1.p.rapidapi.com/v3/fixtures?league={CL_LEAGUE_ID}&season={today.year}&from={from_date}&to={to_date}"
            resp = requests.get(url, headers=headers, timeout=20)
            if resp.status_code == 200:
                for f in resp.json().get('response', []):
                    home = f['teams']['home']['name']
                    away = f['teams']['away']['name']
                    all_matches.append({
                        "match": f"{home} vs {away}",
                        "league": CL_NAME,
                        "league_id": CL_LEAGUE_ID,
                        "date": f['fixture']['date'][:10],
                        "time": f['fixture']['date'][11:16],
                        "home_lower": home.lower(),
                        "is_cl": True
                    })
        except:
            pass

        all_matches.sort(key=lambda x: x["date"])
        print(f"📊 Total fixtures found: {len(all_matches)}")
        return all_matches[:70]

    def run(self):
        today_str = datetime.now().strftime("%Y-%m-%d")
        fixtures = self.fetch_fixtures()

        if len(fixtures) < 5:
            msg = f"""<b>🔔 GrokBet Robot - Pre-season Mode</b>

📅 Date: {today_str}
No fixtures available yet."""
            send_telegram_message(msg)
            print("✅ Pre-season message sent")
            return

        # Generate recommendations with new CL logic
        recommendations = []
        cl_teams = set()

        for fx in fixtures:
            if fx["is_cl"]:
                cl_teams.add(fx["home_lower"])

        for fx in fixtures:
            home_lower = fx["home_lower"]

            # Completely skip domestic matches for teams still in CL
            if not fx["is_cl"] and home_lower in cl_teams:
                continue  # ← Completely skip

            # Confidence calculation
            confidence = 62
            if any(team in home_lower for team in STRONG_HOME_TEAMS):
                confidence += 28
            if any(big in home_lower for big in ["bayern", "psg", "man city", "real madrid", "al hilal"]):
                confidence += 10

            # Extra boost for Champions League matches
            if fx["is_cl"]:
                confidence += 15

            confidence = min(95, confidence)

            if confidence >= 72:
                bet_type = "Home -1.5 Asian Handicap" if confidence > 85 else "Home Win + Over 2.5 Goals"
                odds = "1.35-1.60" if confidence > 85 else "1.45-1.78"

                recommendations.append({
                    "match": fx["match"],
                    "league": fx["league"],
                    "date": fx["date"],
                    "time": fx["time"],
                    "bet": bet_type,
                    "odds": odds,
                    "conf": confidence,
                    "is_cl": fx["is_cl"]
                })

        # Sort: CL matches first, then by confidence
        acca = sorted(recommendations, key=lambda x: (not x['is_cl'], -x['conf']))[:25]

        # Build message
        msg = f"""<b>🔔 GrokBet Robot - Daily Report</b>

📅 Date: {today_str}
🔥 High Confidence Bets: <b>{len(acca)}</b> 
🎯 CL Priority Mode Active
"""

        for i, bet in enumerate(acca[:12], 1):
            cl_tag = " 🔥 CL" if bet["is_cl"] else ""
            msg += f"\n{i}. <b>{bet['match']}</b> ({bet['league']}{cl_tag})"
            msg += f"\n   📆 {bet['date']} {bet['time']} → {bet['bet']} | {bet['odds']} | <b>{bet['conf']}%</b>"

        if len(acca) > 12:
            msg += f"\n\n... and {len(acca)-12} more"

        msg += "\n\n⚠️ Bet responsibly."
        send_telegram_message(msg)
        print(f"✅ Daily report sent with {len(acca)} recommendations!")


if __name__ == "__main__":
    robot = GrokBetRobot()
    robot.run()
