import requests
import pandas as pd
from datetime import datetime

# --- CONFIGURATION ---
API_KEY = '2d885d6b-bea6-43c6-a40d-f7fb45348644'
BASE_URL = 'https://api.hevyapp.com/v1/workouts'

HEADERS = {
    'api-key': API_KEY,
    'Accept': 'application/json'
}

def fetch_workouts():
    print("Connecting to Hevy...")
    try:
        response = requests.get(BASE_URL, headers=HEADERS)
        if response.status_code == 200:
            return response.json()['workouts']
        else:
            print(f"Error {response.status_code}")
            return []
    except Exception as e:
        print(f"Connection failed: {e}")
        return []

def run_pipeline():
    workouts = fetch_workouts()
    if not workouts: return

    all_sets = []
    for w in workouts:
        date_obj = datetime.fromisoformat(w['start_time'].replace('Z', ''))
        date_str = date_obj.strftime('%m/%d')
        for exercise in w['exercises']:
            for s in exercise['sets']:
                # Convert KG to LBS and round to 1 decimal place
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

    # Logic for "Best Set" per exercise per day
    top_sets = df.sort_values(['Weight', 'Reps'], ascending=False).drop_duplicates(['Exercise', 'Date'])
    top_sets = top_sets.sort_values(['Exercise', 'Date_Obj'])

    # Shifting data to get "Last Workout" stats
    top_sets['Last Weight'] = top_sets.groupby('Exercise')['Weight'].shift(1)
    top_sets['Last Reps'] = top_sets.groupby('Exercise')['Reps'].shift(1)
    
    print(f"\n{'='*70}")
    print(f" HEVY PERFORMANCE PIPELINE (LBS) - {datetime.now().strftime('%Y-%m-%d')} ")
    print(f"{'='*70}")
    
    display_cols = ['Date', 'Exercise', 'Weight', 'Last Weight', 'Reps', 'Last Reps']
    print(top_sets[display_cols].tail(15).to_string(index=False))

    # Summary of most recent session
    recent = workouts[0]
    session_vol = sum((s.get('weight_kg', 0) or 0) * 2.20462 * (s.get('reps', 0) or 0) for e in recent['exercises'] for s in e['sets'])
    print(f"\n--- LATEST SESSION: {recent['title']} ---")
    print(f"• Session Volume: {round(session_vol):,} lbs")

if __name__ == "__main__":
    run_pipeline()
