import pandas as pd

def exponential_smoothing(series, alpha=0.3):
    result = [series[0]]  # First value is the same as series
    for n in range(1, len(series)):
        result.append(alpha * series[n] + (1 - alpha) * result[n-1])
    return result

def preprocess_data(data):
    """Clean, convert, and rename raw scraped data for database insertion."""
    
    # Clean 'deaths' column
    data['deaths'] = data['deaths'].str.extract(r'/\s*(\d+)\s*/').astype(float).fillna(1)
    
    # Convert to numeric
    data['kills'] = pd.to_numeric(data['kills'], errors='coerce').fillna(0).astype(int)
    data['assists'] = pd.to_numeric(data['assists'], errors='coerce').fillna(0).astype(int)
    data['kast'] = pd.to_numeric(data['kast'].str.rstrip('%'), errors='coerce').fillna(0) / 100
    data['acs'] = pd.to_numeric(data['acs'].apply(lambda x: ''.join(filter(str.isdigit, str(x)))), errors='coerce').fillna(0)
    data['adr'] = pd.to_numeric(data['adr'], errors='coerce').fillna(0)
    
    return data
