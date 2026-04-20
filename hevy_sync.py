import os
import requests
import pandas as pd
from datetime import datetime

# --- CONFIGURATION ---
# This pulls the secret key from your Linux system (~/.bashrc) 
# so it never shows up as plain text on GitHub.
API_KEY = os.getenv('HEVY_API_KEY')
BASE_URL = 'https://api.hevyapp.com/v1/workouts'

HEADERS = {
    'api-key': API_KEY,
    'Accept': 'application/json'
}

def fetch_workouts():
    if not API_KEY:
        print("Error: HEVY_API_KEY not found. Run 'source ~/.bashrc' or check your config.")
        return []
    
    print("Connecting to Hevy...")
    try:
        response = requests.get(BASE_URL, headers=HEADERS)
        if response.status_code == 200:
            return response.json()['workouts']
        else:
            print(f"Error {response.status_code}: {response.text}")
            return []
    except Exception as e:
        print(f"Connection failed: {e}")
        return []

def run_pipeline():
    workouts = fetch_workouts()
    if not workouts: return

    all_sets = []
    for w in workouts:
        # Convert ISO timestamp to a cleaner date format
        date_obj = datetime.fromisoformat(w['start_time'].replace('Z', ''))
        date_str = date_obj.strftime('%m/%d')
        for exercise in w['exercises']:
            for s in exercise['sets']:
                # Pull raw KG from Hevy, convert to LBS, and round
                raw_kg = s.get('weight_kg', 0) or 0
                lbs = round(raw_kg * 2.20462, 1)
                
                all_sets.append({
                    'Date': date_str,
                    'Date_Obj': date_obj,
                    'Exercise': exercise['title'],
                    'Weight': lbs,
                    'Reps': s.get('reps', 0) or 0
                })

    df = pd.DataFrame(all_sets)

    # Logic for "Best Set" (Highest Weight, then Reps) per exercise per day
    top_sets = df.sort_values(['Weight', 'Reps'], ascending=False).drop_duplicates(['Exercise', 'Date'])
    top_sets = top_sets.sort_values(['Exercise', 'Date_Obj'])

    # Shifting data to compare against your previous performance
    top_sets['Last Weight'] = top_sets.groupby('Exercise')['Weight'].shift(1)
    top_sets['Last Reps'] = top_sets.groupby('Exercise')['Reps'].shift(1)
    
    # --- TERMINAL DISPLAY ---
    print(f"\n{'='*70}")
    print(f" HEVY PERFORMANCE PIPELINE (LBS) - {datetime.now().strftime('%Y-%m-%d')} ")
    print(f"{'='*70}")
    
    display_cols = ['Date', 'Exercise', 'Weight', 'Last Weight', 'Reps', 'Last Reps']
    print(top_sets[display_cols].tail(15).to_string(index=False))

    # --- LATEST SESSION SUMMARY ---
    recent = workouts[0]
    # Calculate volume in lbs for the most recent session
    session_vol = sum((s.get('weight_kg', 0) or 0) * 2.20462 * (s.get('reps', 0) or 0) for e in recent['exercises'] for s in e['sets'])
    print(f"\n--- LATEST SESSION: {recent['title']} ---")
    print(f"• Session Volume: {round(session_vol):,} lbs")

if __name__ == "__main__":
    run_pipeline()
