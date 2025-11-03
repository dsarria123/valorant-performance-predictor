#Match scraper
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import time
from get_methods.getPlayerName import get_playername
from Scraping.TableScraperCopy import scrape_dataCopy
from Preprocessing.preprocessData import preprocess_data
from databaseFunctions import get_existing_match_ids


pd.set_option('display.max_rows', 100)

def scrape_player_dataCopy(player_id, opposing_team):

    #STEP 1 SET UP SELENIUM DRIVERS
    chrome_options = Options()
    #chrome_options.add_argument("--headless")  # Uncomment for headless mode
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    #SET UP WAIT TIMES AND JUST SOME STUFF 
    wait = WebDriverWait(driver, 1)
    match_map_data = [] 
    page_number = 1
    player_name = get_playername(player_id, driver)
    existing_match_ids = get_existing_match_ids(player_id)


    while True:
    #Grabs the url based off player id
        url = f'https://www.vlr.gg/player/matches/{player_id}/?page={page_number}'
        driver.get(url)
        
        try:
            # Collect all the match links on the current page
            match_links = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'a.wf-card.fc-flex.m-item')))
            match_urls = [link.get_attribute('href') for link in match_links]
        
    #STEP 2 GOES THROUGH EVERY MATCH LINK, IF ITS A BO1, MOVE TO NEXT LINK, IF NOT, SEND THE DRIVER URL AND PLAYER NAME TO "TableScraper.py"
            for match_url in match_urls:

                match_id = int(match_url.split('/')[3])  # e.g., 'https://www.vlr.gg/123456/...' → 123456


                if match_id in existing_match_ids:
                    print(f"🛑 Match ID {match_id} already in DB. Stopping scrape.")
                    driver.quit()
                    df = pd.DataFrame(match_map_data)
                    df.to_csv("output.csv", index=False)
                    return df


                matchData = scrape_dataCopy(driver, player_name, match_url, match_id, player_id)

        
            
                match_map_data.extend(matchData)

            
        except TimeoutException:
            print(f"Page {page_number} took too long to load or no matches found. Ending the search.")
            break

        page_number += 1  # Increment page number to proceed to the next page of matches

    driver.quit()
    df = pd.DataFrame(match_map_data)
    
    df.to_csv("output.csv", index=False)  # Saves the DataFrame to output.csv without the index
    return df





