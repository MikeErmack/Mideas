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

CL_LEAGUE_ID = 2
CL_NAME = "Champions League"

STRONG_HOME_TEAMS = {"bayern", "psg", "man city", "real madrid", "barcelona", "al hilal",
                     "inter", "benfica", "juventus", "atletico", "dortmund", "liverpool",
                     "arsenal", "napoli", "ajax", "porto", "ac milan", "bayer leverkusen"}

standings_cache = {}

def send_telegram_message(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
        requests.post(url, json=payload, timeout=15)
        print("✅ Telegram sent")
    except Exception as e:
        print("❌ Telegram error:", e)

# ================== HELPERS (Standings, H2H, Injuries) ==================
def get_standings(league_id, season):
    key = (league_id, season)
    if key in standings_cache:
        return standings_cache[key]
    try:
        url = f"https://api-football-v1.p.rapidapi.com/v3/standings?league={league_id}&season={season}"
        resp = requests.get(url, headers=headers, timeout=12)
        if resp.status_code == 200:
            data = resp.json().get('response', [])
            if data:
                standings = {}
                for entry in data[0]['league']['standings'][0]:
                    name = entry['team']['name'].lower()
                    standings[name] = {'position': entry['rank'], 'form': entry.get('form', '-----')}
                standings_cache[key] = standings
                return standings
    except:
        pass
    return {}

def get_h2h(home_id, away_id):
    try:
        url = f"https://api-football-v1.p.rapidapi.com/v3/fixtures/headtohead?h2h={home_id}-{away_id}&last=10"
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code == 200:
            fixtures = resp.json().get('response', [])
            if fixtures:
                home_wins = sum(1 for f in fixtures if f['teams']['home'].get('winner') is True)
                away_wins = sum(1 for f in fixtures if f['teams']['away'].get('winner') is True)
                recent_home = sum(1 for f in fixtures[:4] if f['teams']['home'].get('winner') is True)
                return (home_wins * 2 + recent_home * 2) - (away_wins * 1.5)
    except:
        pass
    return 0

def get_injury_penalty(fixture_id):
    try:
        url = f"https://api-football-v1.p.rapidapi.com/v3/injuries?fixture={fixture_id}"
        resp = requests.get(url, headers=headers, timeout=12)
        if resp.status_code == 200:
            injuries = resp.json().get('response', [])
            count = len(injuries)
            if count >= 3: return -22
            elif count >= 2: return -15
            elif count >= 1: return -8
    except:
        pass
    return 0

class GrokBetRobot:
    def __init__(self):
        print("🚀 GrokBet Robot v2.8 - Smart Splitting + Full 20 Bets")

    def fetch_fixtures(self):
        # (Same fetching logic as v2.7 - kept short for readability)
        today = datetime.now()
        all_matches = []
        seasons = [today.year, today.year-1, today.year+1]
        from_date = today.strftime("%Y-%m-%d")
        to_date = (today + timedelta(days=21)).strftime("%Y-%m-%d")

        # Domestic leagues + CL (same as previous versions)
        for season in seasons:
            for league_id, name in LEAGUES.items():
                try:
                    url = f"https://api-football-v1.p.rapidapi.com/v3/fixtures?league={league_id}&season={season}&from={from_date}&to={to_date}"
                    resp = requests.get(url, headers=headers, timeout=20)
                    if resp.status_code == 200:
                        for f in resp.json().get('response', []):
                            home = f['teams']['home']['name']
                            all_matches.append({
                                "match": f"{home} vs {f['teams']['away']['name']}",
                                "league": name,
                                "league_id": league_id,
                                "date": f['fixture']['date'][:10],
                                "time": f['fixture']['date'][11:16],
                                "home_lower": home.lower(),
                                "is_cl": False,
                                "home_id": f['teams']['home']['id'],
                                "away_id": f['teams']['away']['id'],
                                "fixture_id": f['fixture']['id']
                            })
                except:
                    continue

        # Champions League
        try:
            url = f"https://api-football-v1.p.rapidapi.com/v3/fixtures?league={CL_LEAGUE_ID}&season={today.year}&from={from_date}&to={to_date}"
            resp = requests.get(url, headers=headers, timeout=20)
            if resp.status_code == 200:
                for f in resp.json().get('response', []):
                    home = f['teams']['home']['name']
                    all_matches.append({
                        "match": f"{home} vs {f['teams']['away']['name']}",
                        "league": CL_NAME,
                        "league_id": CL_LEAGUE_ID,
                        "date": f['fixture']['date'][:10],
                        "time": f['fixture']['date'][11:16],
                        "home_lower": home.lower(),
                        "is_cl": True,
                        "home_id": f['teams']['home']['id'],
                        "away_id": f['teams']['away']['id'],
                        "fixture_id": f['fixture']['id']
                    })
        except:
            pass

        all_matches.sort(key=lambda x: x["date"])
        print(f"📊 Total fixtures found: {len(all_matches)}")
        return all_matches[:90]

    def calculate_confidence(self, fx):
        base = 60
        home_lower = fx["home_lower"]

        if any(team in home_lower for team in STRONG_HOME_TEAMS):
            base += 25
        if any(big in home_lower for big in ["bayern", "psg", "man city", "real madrid", "al hilal"]):
            base += 10

        standings = get_standings(fx["league_id"], datetime.now().year)
        if home_lower in standings:
            pos = standings[home_lower]['position']
            form = standings[home_lower]['form']
            if pos <= 4: base += 12
            elif pos <= 8: base += 6
            recent_wins = form.count('W')
            if recent_wins >= 4: base += 10
            elif recent_wins >= 3: base += 5

        h2h_score = get_h2h(fx["home_id"], fx["away_id"])
        base += h2h_score

        if fx["is_cl"]:
            base += 18

        injury_penalty = get_injury_penalty(fx["fixture_id"])
        base += injury_penalty

        return min(96, max(55, int(base)))

    def run(self):
        today_str = datetime.now().strftime("%Y-%m-%d")
        fixtures = self.fetch_fixtures()

        if len(fixtures) < 5:
            send_telegram_message(f"<b>🔔 GrokBet Robot - Pre-season Mode</b>\n\n📅 Date: {today_str}\nSmart Logic + H2H + Injuries Active")
            return

        recommendations = []
        cl_teams = {fx["home_lower"] for fx in fixtures if fx["is_cl"]}

        for fx in fixtures:
            if not fx["is_cl"] and fx["home_lower"] in cl_teams:
                continue
            conf = self.calculate_confidence(fx)
            if conf >= 70:
                bet_type = "Home -1.5 Asian Handicap" if conf > 85 else "Home Win + Over 2.5 Goals"
                odds = "1.35-1.60" if conf > 85 else "1.45-1.78"
                recommendations.append({
                    "match": fx["match"],
                    "league": fx["league"],
                    "date": fx["date"],
                    "time": fx["time"],
                    "bet": bet_type,
                    "odds": odds,
                    "conf": conf,
                    "is_cl": fx["is_cl"]
                })

        acca = sorted(recommendations, key=lambda x: -x['conf'])[:20]

        # ================== BUILD MESSAGE WITH SMART SPLITTING ==================
        msg = f"""<b>🔔 GrokBet Robot - Daily Smart Report v2.8</b>

📅 Date: {today_str}
🔥 Total High Confidence Bets: <b>{len(acca)}</b>
🎯 Smart Logic + H2H + Injury Checks Active

<b>🛡️ SAFE ACCA (Top 5)</b> - Highest win probability
"""

        for i, bet in enumerate(acca[:5], 1):
            cl_tag = " 🔥 CL" if bet["is_cl"] else ""
            msg += f"\n{i}. <b>{bet['match']}</b> ({bet['league']}{cl_tag})"
            msg += f"\n   📆 {bet['date']} {bet['time']} → {bet['bet']} | {bet['odds']} | <b>{bet['conf']}%</b>"

        msg += "\n\n<b>🎯 MEDIUM ACCA (Top 8)</b> - Good balance"
        for i, bet in enumerate(acca[:8], 1):
            if i > 5:
                cl_tag = " 🔥 CL" if bet["is_cl"] else ""
                msg += f"\n{i}. {bet['match']} ({bet['league']}{cl_tag})"
                msg += f"\n   📆 {bet['date']} {bet['time']} → {bet['bet']} | {bet['odds']} | <b>{bet['conf']}%</b>"

        msg += "\n\n<b>🚀 HIGH-RISK ACCA (Top 12)</b> - Bigger payout"
        for i, bet in enumerate(acca[:12], 1):
            if i > 8:
                cl_tag = " 🔥 CL" if bet["is_cl"] else ""
                msg += f"\n{i}. {bet['match']} ({bet['league']}{cl_tag})"
                msg += f"\n   📆 {bet['date']} {bet['time']} → {bet['bet']} | {bet['odds']} | <b>{bet['conf']}%</b>"

        msg += "\n\n<b>📋 FULL LIST (All 20 bets)</b> - Choose any combination you want"
        for i, bet in enumerate(acca[12:], 13):
            cl_tag = " 🔥 CL" if bet["is_cl"] else ""
            msg += f"\n{i}. {bet['match']} ({bet['league']}{cl_tag})"
            msg += f"\n   📆 {bet['date']} {bet['time']} → {bet['bet']} | {bet['odds']} | <b>{bet['conf']}%</b>"

        msg += "\n\n⚠️ You can mix any bets you like. Highest confidence first. Bet responsibly."
        send_telegram_message(msg)
        print(f"✅ Sent full 20 bets with smart splitting!")


if __name__ == "__main__":
    robot = GrokBetRobot()
    robot.run()
