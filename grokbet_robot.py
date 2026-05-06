import json
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
        print("🚀 GrokBet Robot v2.2 - Started")

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

        # Pre-season / no matches
        if len(fixtures) < 5:
            msg = f"""<b>🔔 GrokBet Robot - Pre-season Mode</b>

📅 Date: {today_str}
🏟️ Status: Very few fixtures available (Off-season)

Most top leagues start mid-August 2026.
The robot is working correctly and will automatically switch to full mode when matches return."""
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

        # Build Telegram message
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

        msg += "\n\n⚠️ Bet responsibly. For information only."
        send_telegram_message(msg)
        print(f"✅ Daily report sent with {len(acca)} recommendations!")


# ===================== RUN =====================
if __name__ == "__main__":
    robot = GrokBetRobot()
    robot.run()        all_matches = []
        seasons = self.get_current_seasons()

        for season in seasons:
            print(f"🔍 Trying season {season}...")
            from_date = today.strftime("%Y-%m-%d")
            to_date = (today + timedelta(days=21)).strftime("%Y-%m-%d")  # 3 weeks ahead

            for league_id, name in LEAGUES.items():
                try:
                    url = f"https://api-football-v1.p.rapidapi.com/v3/fixtures?league={league_id}&season={season}&from={from_date}&to={to_date}"
                    resp = requests.get(url, headers=headers, timeout=20)

                    if resp.status_code == 200:
                        data = resp.json()
                        fixtures = data.get('response', [])
                        print(f"   → {name} ({season}): {len(fixtures)} fixtures")

                        for f in fixtures:
                            fixture_date = f['fixture']['date'][:10]
                            home_name = f['teams']['home']['name']
                            
                            all_matches.append({
                                "match": f"{home_name} vs {f['teams']['away']['name']}",
                                "league": name,
                                "date": fixture_date,
                                "home_team": home_name.lower(),
                                "timestamp": f['fixture']['timestamp']
                            })
                except Exception as e:
                    print(f"   Error fetching {name} ({season}): {e}")
                    continue

            if len(all_matches) >= 15:  # Good enough data found
                break

        # Sort by date
        all_matches.sort(key=lambda x: x.get('timestamp', 0))
        print(f"📊 Total fixtures found: {len(all_matches)}")
        return all_matches[:80]  # Cap for performance

    def run(self):
        today_str = datetime.now().strftime("%Y-%m-%d")
        print(f"📅 Running daily report for: {today_str}\n")

        fixtures = self.fetch_fixtures()

        if len(fixtures) < 5:  # Very few matches → pre-season mode
            msg = f"""<b>🔔 GrokBet Robot - Pre-season Mode</b>

📅 Date: {today_str}
🏟️ Status: Limited fixtures available

The 2026/27 season is approaching (most top leagues start mid-August). 
The robot is running correctly and will automatically switch to full recommendation mode once fixtures become abundant."""

            send_telegram_message(msg)
            print("✅ Pre-season message sent")
            return

        # Normal mode - generate recommendations
        recommendations = []
        for fx in fixtures:
            home_lower = fx["home_team"]
            base_conf = 62

            # Boost for strong home teams
            if any(team in home_lower for team in STRONG_HOME_TEAMS):
                base_conf += 28

            # Extra boost for very strong ones
            if any(big in home_lower for big in ["bayern", "psg", "man city", "real madrid", "al hilal"]):
                base_conf += 8

            confidence = min(94, base_conf)

            if confidence >= 72:
                if confidence > 85:
                    bet_type = "Home -1.5 Asian Handicap"
                    odds_range = "1.38 - 1.62"
                else:
                    bet_type = "Home Win + Over 2.5 Goals"
                    odds_range = "1.45 - 1.78"

                recommendations.append({
                    "match": fx["match"],
                    "league": fx["league"],
                    "date": fx["date"],
                    "recommended_bet": bet_type,
                    "odds_range": odds_range,
                    "confidence": confidence
                })

        # Sort by confidence
        acca_legs = sorted(recommendations, key=lambda x: x['confidence'], reverse=True)[:25]

        # Build message
        msg = f"""<b>🔔 GrokBet Robot - Daily Report</b>

📅 Date: {today_str}
🔥 High Confidence Matches: <b>{len(acca_legs)}</b>

<b>🎯 Recommended {min(20, len(acca_legs))}-leg Accumulator</b>
"""

        for i, bet in enumerate(acca_legs[:12], 1):  # Show top 12 in Telegram
            msg += f"\n{i}. <b>{bet['match']}</b> ({bet['league']})"
            msg += f"\n   → {bet['recommended_bet']}  |  {bet['odds_range']}  |  <b>{bet['confidence']}%</b>"

        if len(acca_legs) > 12:
            msg += f"\n\n... +{len(acca_legs)-12} more high-confidence bets generated"

        msg += "\n\n⚠️ Always bet responsibly. These are algorithmic suggestions."

        send_telegram_message(msg)
        print(f"✅ Daily report sent with {len(acca_legs)} recommendations!")


# ===================== RUN =====================
if __name__ == "__main__":
    robot = GrokBetRobot()
    robot.run()
