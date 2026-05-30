import json
import requests
from datetime import datetime, timedelta
import time
import os

# ===================== CONFIG (from GitHub Secrets or local) =====================
API_KEY = os.getenv("API_KEY", "YOUR_API_KEY_HERE")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "YOUR_CHAT_ID_HERE")

headers = {'x-apisports-key': API_KEY}

LEAGUES = {
    39: "Premier League",
    140: "La Liga",
    78: "Bundesliga",
    135: "Serie A",
    61: "Ligue 1",
    88: "Eredivisie",
    94: "Primeira Liga",
    307: "Saudi Pro League",
    218: "Austrian Bundesliga",
    144: "Belgian Pro League",
    1: "World Cup"
}

class APICounter:
    def __init__(self, max_calls=82):
        self.calls = 0
        self.max_calls = max_calls

    def increment(self):
        self.calls += 1
        if self.calls > self.max_calls:
            raise Exception("API call limit reached for safety")

api = APICounter()


def send_telegram_message(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
        requests.post(url, json=payload, timeout=20)
    except Exception as e:
        print(f"Telegram error: {e}")


def get_fixtures_next_3_days():
    today = datetime.now()
    from_date = today.strftime("%Y-%m-%d")
    to_date = (today + timedelta(days=3)).strftime("%Y-%m-%d")

    fixtures = []
    for league_id, league_name in LEAGUES.items():
        try:
            api.increment()
            url = "https://api-football-v1.p.rapidapi.com/v3/fixtures"
            params = {"league": league_id, "season": 2026, "from": from_date, "to": to_date, "status": "NS"}
            resp = requests.get(url, headers=headers, params=params, timeout=15)
            if resp.status_code == 200:
                for f in resp.json().get('response', []):
                    fixtures.append({
                        "fixture_id": f['fixture']['id'],
                        "date": f['fixture']['date'][:10],
                        "league": league_name,
                        "league_id": league_id,
                        "home_team": f['teams']['home']['name'],
                        "away_team": f['teams']['away']['name'],
                        "home_id": f['teams']['home']['id'],
                        "away_id": f['teams']['away']['id']
                    })
            time.sleep(0.5)
        except:
            continue
    return fixtures


def get_standings(league_id):
    try:
        api.increment()
        url = "https://api-football-v1.p.rapidapi.com/v3/standings"
        params = {"league": league_id, "season": 2026}
        resp = requests.get(url, headers=headers, params=params, timeout=10)
        if resp.status_code == 200:
            return resp.json().get('response', [{}])[0].get('league', {}).get('standings', [[]])[0]
    except:
        pass
    return []


def get_team_stats(team_id, league_id):
    try:
        api.increment()
        url = "https://api-football-v1.p.rapidapi.com/v3/teams/statistics"
        params = {"team": team_id, "league": league_id, "season": 2026}
        resp = requests.get(url, headers=headers, params=params, timeout=10)
        if resp.status_code == 200:
            return resp.json().get('response', {})
    except:
        pass
    return {}


def get_head_to_head(home_id, away_id):
    try:
        api.increment()
        url = "https://api-football-v1.p.rapidapi.com/v3/fixtures/headtohead"
        params = {"h2h": f"{home_id}-{away_id}", "last": 6}
        resp = requests.get(url, headers=headers, params=params, timeout=10)
        if resp.status_code == 200:
            return resp.json().get('response', [])
    except:
        pass
    return []


class PreMatchAnalyzer:
    def __init__(self):
        self.standings_cache = {}

    def get_standings(self, league_id):
        if league_id not in self.standings_cache:
            self.standings_cache[league_id] = get_standings(league_id)
        return self.standings_cache[league_id]

    def analyze_match(self, fixture):
        league_id = fixture['league_id']
        home_id = fixture['home_id']
        away_id = fixture['away_id']

        standings = self.get_standings(league_id)
        home_stats = get_team_stats(home_id, league_id)
        away_stats = get_team_stats(away_id, league_id)
        h2h = get_head_to_head(home_id, away_id)

        home_form = home_stats.get('form', '')[-5:] if home_stats.get('form') else "N/A"
        away_form = away_stats.get('form', '')[-5:] if away_stats.get('form') else "N/A"

        # Improved scoring system
        score = 50
        if "W" in home_form[-3:]:
            score += 14
        if "L" in away_form[-3:]:
            score += 12
        score += 8  # Home advantage

        home_wins_h2h = sum(1 for m in h2h if m['teams']['home']['id'] == home_id and m['teams']['home']['winner'])
        if home_wins_h2h >= 3:
            score += 7

        confidence = min(93, max(58, score))

        if confidence >= 84:
            suggestion = "Strong value on Home Win or Home -1.5"
        elif confidence >= 76:
            suggestion = "Home Win or BTTS looks interesting"
        else:
            suggestion = "Low confidence - consider Under 2.5 or skip"

        return {
            "fixture": fixture,
            "home_form": home_form,
            "away_form": away_form,
            "h2h_matches": len(h2h),
            "confidence": round(confidence, 1),
            "suggestion": suggestion
        }

    def run(self):
        print("Starting Pre-Match Analyzer v4 (Next 3 Days)...\n")
        fixtures = get_fixtures_next_3_days()

        if not fixtures:
            send_telegram_message("No matches found in the next 3 days.")
            return

        analyzed = []
        for fx in fixtures:
            try:
                analysis = self.analyze_match(fx)
                analyzed.append(analysis)
            except Exception as e:
                if "limit" in str(e).lower():
                    break
                continue

        analyzed.sort(key=lambda x: x['confidence'], reverse=True)
        top_matches = analyzed[:20]

        today = datetime.now().strftime("%Y-%m-%d")

        # Message 1: Summary (15 matches)
        msg1 = f"<b>📊 GrokBet Pre-Match Analyzer</b>\n📅 {today} | Next 3 Days\n\nTop 15 Matches:\n\n"
        for i, m in enumerate(top_matches[:15], 1):
            fx = m['fixture']
            msg1 += f"{i}. <b>{fx['home_team']} vs {fx['away_team']}</b> ({fx['league']})\n   Confidence: {m['confidence']}%\n\n"
        send_telegram_message(msg1)

        # Message 2: Deep Dive (Top 6)
        msg2 = "<b>🔍 Deep Dive - Best 6 Matches</b>\n\n"
        for i, m in enumerate(top_matches[:6], 1):
            fx = m['fixture']
            msg2 += f"<b>{i}. {fx['home_team']} vs {fx['away_team']}</b>\n"
            msg2 += f"Form: {m['home_form']} | {m['away_form']}\n"
            msg2 += f"H2H: {m['h2h_matches']} matches\n"
            msg2 += f"Confidence: <b>{m['confidence']}%</b>\n"
            msg2 += f"Suggestion: {m['suggestion']}\n\n"
        send_telegram_message(msg2)

        print(f"\n✅ Done. Used {api.calls} API calls.")


if __name__ == "__main__":
    PreMatchAnalyzer().run()