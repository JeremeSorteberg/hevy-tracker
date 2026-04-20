import os
import requests
import pandas as pd
from datetime import datetime
from rich.console import Console
from rich.table import Table

console = Console()

# --- CONFIGURATION ---
API_KEY = os.getenv('HEVY_API_KEY')
BASE_URL = 'https://api.hevyapp.com/v1/workouts'
EXCEL_FILE = "Gym_Progress.xlsx"

def fetch_workouts():
    if not API_KEY:
        console.print("[bold red]Error:[/bold red] API Key not found.")
        return []
    
    try:
        response = requests.get(BASE_URL, headers={'api-key': API_KEY, 'Accept': 'application/json'})
        return response.json().get('workouts', []) if response.status_code == 200 else []
    except:
        return []

def run_pipeline():
    workouts = fetch_workouts()
    if not workouts: return

    all_sets = []
    for w in workouts:
        date_obj = datetime.fromisoformat(w['start_time'].replace('Z', ''))
        for exercise in w['exercises']:
            for s in exercise['sets']:
                all_sets.append({
                    'Date': date_obj.strftime('%Y-%m-%d'),
                    'Exercise': exercise['title'],
                    'Weight (lbs)': round((s.get('weight_kg', 0) or 0) * 2.20462, 1),
                    'Reps': s.get('reps', 0) or 0,
                    'Workout Name': w['title']
                })

    df = pd.DataFrame(all_sets)
    
    # --- ORGANIZE DATA FOR EXCEL ---
    # Sort by Exercise and Date so progress is linear
    df = df.sort_values(['Exercise', 'Date'], ascending=[True, False])

    # Save to Excel with Professional Formatting
    try:
        with pd.ExcelWriter(EXCEL_FILE, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Lifting Logs')
            
            # Auto-adjust column widths
            worksheet = writer.sheets['Lifting Logs']
            for col in worksheet.columns:
                max_length = 0
                column = col[0].column_letter
                for cell in col:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except: pass
                worksheet.column_dimensions[column].width = max_length + 2
        
        console.print(f"[bold green]✔ Excel file updated:[/bold green] {EXCEL_FILE}")
    except Exception as e:
        console.print(f"[bold red]Excel Error:[/bold red] {e}")

    # --- SHOW TERMINAL DASHBOARD ---
    table = Table(title="Recent Activity", title_style="bold cyan", box=None)
    table.add_column("Exercise", style="white")
    table.add_column("Weight", justify="right", style="green")
    table.add_column("Reps", justify="right", style="bold yellow")

    # Show top sets from last session in terminal
    latest_date = df['Date'].iloc[0]
    last_session = df[df['Date'] == latest_date].drop_duplicates('Exercise')
    for _, row in last_session.iterrows():
        table.add_row(row['Exercise'], f"{row['Weight (lbs)']} lbs", str(row['Reps']))

    console.print(table)

if __name__ == "__main__":
    run_pipeline()
