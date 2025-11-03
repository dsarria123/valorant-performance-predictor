"""
Load odds into available matches
"""

from bs4 import BeautifulSoup
import requests
from sqlalchemy import create_engine, text

# === DATABASE CONNECTION ===
engine = create_engine(
    "",
    pool_pre_ping=True
)

# === SCRAPER FUNCTION ===
def extract_betting_info(match_url):
    r = requests.get(match_url)
    soup = BeautifulSoup(r.text, 'html.parser')

    try:
        bet_section = soup.select_one('a.wf-card.mod-dark.match-bet-item')
        if not bet_section:
            return None

        odds_spans = bet_section.select('span.match-bet-item-odds')
        team_elem = bet_section.select_one('span.match-bet-item-team')

        bet_amount = int(odds_spans[0].text.strip().replace('$', ''))
        returned = int(odds_spans[1].text.strip().replace('$', ''))

        raw_odds_text = bet_section.text
        odds_match = [s for s in raw_odds_text.split() if s.startswith('1.')]

        odds = float(odds_match[0]) if odds_match else None
        implied_prob = round(1 / odds, 4) if odds else None
        opponent_implied_prob = round(1 - implied_prob, 4) if implied_prob else None
        opponent_odds = round(1 / opponent_implied_prob, 2) if opponent_implied_prob else None

        return {
            'team': team_elem.text.strip() if team_elem else None,
            'bet_amount': bet_amount,
            'returned': returned,
            'odds': odds,
            'implied_prob': implied_prob,
            'opponent_odds': opponent_odds,
            'opponent_implied_prob': opponent_implied_prob
        }

    except Exception as e:
        print(f"Parse error for {match_url}: {e}")
        return None

# === GET MATCHES TO UPDATE ===
def get_match_ids_to_update():
    """
    Return list of match_ids that don't have odds info yet
    AND are from matches dated after 2023.
    """
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT DISTINCT match_id
            FROM player_matches
            WHERE winning_team_pre_match_odds IS NULL
              AND match_date >= '2023-01-01'
        """))
        return [row[0] for row in result.fetchall()]

# === DB UPDATE FUNCTION ===
def update_match_odds_sqlalchemy(match_id, odds_data):
    if not odds_data:
        print(f"No odds data for match_id {match_id}")
        return

    team = odds_data['team']
    odds = odds_data['odds']
    prob = odds_data['implied_prob']
    opp_odds = odds_data['opponent_odds']
    opp_prob = odds_data['opponent_implied_prob']

    with engine.begin() as conn:
        # Update rows where team was the winning team
        conn.execute(text("""
            UPDATE player_matches
            SET winning_team_pre_match_odds = :team_odds,
                winning_team_pre_match_winprob = :team_prob,
                losing_team_pre_match_odds = :opp_odds,
                losing_team_pre_match_winprob = :opp_prob
            WHERE match_id = :match_id
              AND winning_team = :team
        """), {
            'team_odds': odds,
            'team_prob': prob,
            'opp_odds': opp_odds,
            'opp_prob': opp_prob,
            'match_id': match_id,
            'team': team
        })

        # Update rows where team was the losing team
        conn.execute(text("""
            UPDATE player_matches
            SET winning_team_pre_match_odds = :opp_odds,
                winning_team_pre_match_winprob = :opp_prob,
                losing_team_pre_match_odds = :team_odds,
                losing_team_pre_match_winprob = :team_prob
            WHERE match_id = :match_id
              AND losing_team = :team
        """), {
            'team_odds': odds,
            'team_prob': prob,
            'opp_odds': opp_odds,
            'opp_prob': opp_prob,
            'match_id': match_id,
            'team': team
        })

    print(f"✅ Match {match_id} updated with odds and win probabilities.")

# === MAIN LOOP ===
if __name__ == "__main__":
    match_ids = get_match_ids_to_update()

    print(f"Found {len(match_ids)} match_ids needing odds...")

    for mid in match_ids:
        print(f"Scraping and updating match {mid}...")
        odds = extract_betting_info(f"https://vlr.gg/{mid}")
        update_match_odds_sqlalchemy(mid, odds)
