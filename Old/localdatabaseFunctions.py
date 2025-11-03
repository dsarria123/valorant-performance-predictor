from sqlalchemy import create_engine, text

engine = create_engine("postgresql://postgres:Ilikepie109!@localhost:5432/vlr.gg_scraped")

def local_get_latest_match_date(player_id):
    """
    Get the latest match_date for a given player_id.
    """
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT MAX(match_date)
            FROM player_matches
            WHERE player_id = :pid
        """), {'pid': player_id})
        return result.scalar()

def local_get_existing_match_ids(player_id):
    """
    Get a list of match_ids already in the database for a given player.
    """
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT DISTINCT match_id FROM player_matches
            WHERE player_id = :pid
        """), {'pid': player_id})
        return [row[0] for row in result.fetchall()]

def local_load_database(df, table_name):
    """
    Insert new rows from df into the PostgreSQL table, skipping duplicates.
    """
    if df.empty:
        print("Nothing in the df brev")
        return

    player_id = int(df['player_id'].iloc[0]) 
    match_ids = get_existing_match_ids(player_id)

    # Filter out already-inserted matches
    filtered_df = df[~df['match_id'].isin(match_ids)]

    if filtered_df.empty:
        print("All match_ids already in database — nothing new to insert.")
        return

    try:
        filtered_df.to_sql(table_name, engine, if_exists='append', index=False)
        print(f"Loaded {len(filtered_df)} new rows into '{table_name}'")
    except Exception as e:
        print(f"Error loading data into database: {e}")
