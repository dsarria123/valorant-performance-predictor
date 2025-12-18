# Valorant Kill Prediction Project

## Overview
This project predicts how many kills a Valorant player will get in an upcoming match using data scraped from [vlr.gg](https://www.vlr.gg/) and stored in a Supabase PostgreSQL database.  
The modeling process focuses strictly on **pre-match information** to avoid data leakage — meaning the model never uses details like agent, map, or round outcomes that are only known after the match begins.

---

## Data Source
The dataset is hosted in **Supabase PostgreSQL** under the table `player_matches`, containing over 37,000 rows of match-level data.  
The data is accessed in Python using SQLAlchemy and pandas through a direct connection to the Supabase instance.

---

## Data Flow
1. **Scraping** – The `scraping` folder contains scripts that collect player and match data from VLR.gg.  
   These scripts use Selenium to gather statistics for each match, including player performance, team results, and opponent information.

2. **Database Integration** – The `databaseFunctions.py` and `load_database.py` files manage all interaction between the scraper and the Supabase database.  
They handle creating tables, inserting new data, checking for duplicates, and syncing updates from new matches.

3. **Modeling** – The main notebook, `xgboost-model.ipynb`, handles all data preparation, model training, evaluation, and prediction.

---

## Modeling Approach
**Notebook:** `xgboost-model.ipynb`

The model is designed to predict a player's kill count **before** a match begins.  
It uses historical statistics and opponent context — all computed in a time-aware way so that no future information leaks into training.

### Target
- `kills` (number of kills by a player in a match)

### Features
All features are built using **only prior match history**:
- `player_recent_kills_5`: rolling mean of last 5 matches for each player  
- `player_cum_kills_avg`: cumulative mean of kills up to prior match  
- `opponent_allowed_kills_avg`: historical average kills conceded by the opposing team  
- `player_vs_opp_recent_kills_5`: rolling mean of player performance against this specific opponent  
- `player_trend_ewm`: exponentially weighted moving average to emphasize recent form  
- `player_team_offense_recent5`: rolling mean of kills by all players on the same team  
- `opponent_defense_allowed_recent5`: rolling mean of kills conceded by the opposing team

---

## Model Details
- **Algorithm:** `XGBRegressor` from XGBoost  
- **Objective:** `count:poisson` (suitable for predicting count values like kills)  
- **Pipeline:** combines one-hot encoding for categorical features with numeric passthroughs  
- **Split:** time-based (last 20% of matches as the test set)  
- **Cross-validation:** `TimeSeriesSplit(n_splits=3)`  
- **Hyperparameter tuning:** RandomizedSearchCV on `n_estimators`, `max_depth`, `learning_rate`, `subsample`, `colsample_bytree`, `reg_lambda`


## Prediction
Once the model is trained, predictions can be made directly from the notebook.


If a player or team has not appeared before, the model automatically falls back to global averages to generate a reasonable estimate.  
A version of the function also includes an optional 90% prediction interval based on historical residuals.


## Project Summary
- **Scraping:** automated collection of match data from VLR.gg  
- **Database:** Supabase PostgreSQL backend accessed with SQLAlchemy  
- **Modeling:** XGBoost Poisson regression predicting player kills using pre-match stats  
- **Evaluation:** time-based validation, no feature leakage  
- **Prediction:** clean function for real-time or batch prediction based on player and opponent names

This setup allows continuous data updates through the scraper, seamless database integration, and reproducible training and evaluation directly within `xgboost-model.ipynb`.

## Limitations & Future Work
- The model does not account for map, agent selection, or team composition,
  which are intentionally excluded to preserve pre-match validity.
- Player form is approximated through rolling and exponentially weighted
  averages rather than sequence models.
- Future work could explore hierarchical or Bayesian approaches to better
  handle uncertainty for low-sample players.

