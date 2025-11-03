from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time
import pandas as pd
from sqlalchemy import create_engine

'''
ONLY RUN ONCE EVERY WEEK OR MONTH — THIS FULLY UPDATES THE TABLE IN SUPABASE
'''

#Supabase PostgreSQL connection (Transaction Pooler)
engine = create_engine(
    "",
    pool_pre_ping=True
)

def get_valorant_rankings_dataframe():
    start_page = 1
    end_page = 10
    delay = 4

    chrome_options = Options()
    # chrome_options.add_argument("--headless")  # optional headless
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    all_teams = []

    for page_num in range(start_page, end_page + 1):
        print(f"Scraping page {page_num}...")
        url = f"https://www.gosugamers.net/valorant/rankings?pageNo={page_num}"
        driver.get(url)
        time.sleep(delay)

        teams = driver.find_elements(By.CLASS_NAME, "MuiListItem-root")

        for team in teams:
            try:
                rank = team.find_element(By.TAG_NAME, "span").text
                ps = team.find_elements(By.TAG_NAME, "p")
                team_name = ps[0].text
                elo = ps[-1].text.replace(",", "")
                all_teams.append({
                    "global_rank": int(rank),
                    "team": team_name,
                    "elo": int(elo)
                })
            except Exception as e:
                print(f"Error on page {page_num}: {e}")

    driver.quit()
    return pd.DataFrame(all_teams)

# Upload to Supabase `elo_ratings` table
if __name__ == "__main__":
    df = get_valorant_rankings_dataframe()
    

    # Upload to Supabase
    try:
        df.to_sql("elo_ratings", engine, if_exists="replace", index=False)
        print("Data uploaded to Supabase successfully.")
    except Exception as e:
        print(f"Failed to upload to Supabase: {e}")
