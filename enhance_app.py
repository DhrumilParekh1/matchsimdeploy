"""
Enhancement script for Match Simulator App
This script improves CSV loading and adds final polish
"""

import pandas as pd
import sqlite3
import os

def improve_csv_loading():
    """Improve CSV loading with better error handling and data processing"""
    print("🔄 Improving CSV data loading...")
    
    try:
        # Load CSV with specific encoding and error handling
        df = pd.read_csv('player-data-full.csv', encoding='utf-8', low_memory=False)
        print(f"✅ Successfully loaded CSV with {len(df)} rows")
        
        # Display column information
        print(f"📊 CSV columns: {list(df.columns)}")
        
        # Connect to database
        conn = sqlite3.connect('match_simulator.db')
        cursor = conn.cursor()
        
        # Clear existing non-custom players
        cursor.execute("DELETE FROM players WHERE is_custom = FALSE")
        
        # Process and insert player data in batches
        batch_size = 1000
        successful_inserts = 0
        
        for i in range(0, len(df), batch_size):
            batch = df.iloc[i:i+batch_size]
            
            for _, row in batch.iterrows():
                try:
                    # Map CSV columns to database fields
                    player_data = {
                        'player_id': str(row.get('sofifa_id', row.get('id', f'player_{i}'))),
                        'player_name': str(row.get('short_name', row.get('long_name', row.get('player_name', 'Unknown')))),
                        'positions': str(row.get('player_positions', row.get('position', ''))),
                        'club_name': str(row.get('club_name', '')),
                        'age': int(row.get('age', 0)) if pd.notna(row.get('age')) else None,
                        'nationality': str(row.get('nationality_name', row.get('nationality', ''))),
                        'overall_rating': int(row.get('overall', 0)) if pd.notna(row.get('overall')) else None,
                        'potential': int(row.get('potential', 0)) if pd.notna(row.get('potential')) else None,
                        'value_eur': float(row.get('value_eur', 0)) if pd.notna(row.get('value_eur')) else None,
                        'wage_eur': float(row.get('wage_eur', 0)) if pd.notna(row.get('wage_eur')) else None
                    }
                    
                    # Skip if essential data is missing
                    if not player_data['player_name'] or player_data['player_name'] == 'Unknown':
                        continue
                    
                    cursor.execute('''
                        INSERT OR IGNORE INTO players 
                        (player_id, player_name, positions, club_name, age, nationality, 
                         overall_rating, potential, value_eur, wage_eur, is_custom)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, FALSE)
                    ''', (
                        player_data['player_id'],
                        player_data['player_name'],
                        player_data['positions'],
                        player_data['club_name'],
                        player_data['age'],
                        player_data['nationality'],
                        player_data['overall_rating'],
                        player_data['potential'],
                        player_data['value_eur'],
                        player_data['wage_eur']
                    ))
                    successful_inserts += 1
                    
                except Exception as e:
                    continue
            
            # Commit batch
            conn.commit()
            print(f"📦 Processed batch {i//batch_size + 1}, total inserted: {successful_inserts}")
        
        print(f"✅ Successfully inserted {successful_inserts} players into database")
        
        # Verify data
        cursor.execute("SELECT COUNT(*) FROM players WHERE is_custom = FALSE")
        total_players = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT club_name) FROM players WHERE club_name IS NOT NULL AND club_name != ''")
        total_clubs = cursor.fetchone()[0]
        
        print(f"📊 Database now contains {total_players} players from {total_clubs} clubs")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error loading CSV: {e}")

def add_sample_data():
    """Add some sample data for testing"""
    print("🎯 Adding sample data for testing...")
    
    conn = sqlite3.connect('match_simulator.db')
    cursor = conn.cursor()
    
    # Sample clubs and players
    sample_players = [
        ("MESSI001", "Lionel Messi", "RW,CF", "Inter Miami", 36, "Argentina", 93, 93, 50000000, 1000000),
        ("RONALDO001", "Cristiano Ronaldo", "ST,LW", "Al Nassr", 39, "Portugal", 91, 91, 15000000, 500000),
        ("MBAPPE001", "Kylian Mbappé", "ST,LW", "Paris Saint-Germain", 25, "France", 91, 95, 180000000, 800000),
        ("HAALAND001", "Erling Haaland", "ST", "Manchester City", 23, "Norway", 91, 94, 170000000, 750000),
        ("NEYMAR001", "Neymar Jr", "LW,CAM", "Al-Hilal", 32, "Brazil", 89, 89, 90000000, 600000),
        ("BENZEMA001", "Karim Benzema", "ST", "Al-Ittihad", 36, "France", 86, 86, 20000000, 400000),
        ("MODRIC001", "Luka Modrić", "CM", "Real Madrid", 38, "Croatia", 88, 88, 10000000, 300000),
        ("DEBRUYNE001", "Kevin De Bruyne", "CAM,CM", "Manchester City", 32, "Belgium", 91, 91, 100000000, 700000),
        ("SALAH001", "Mohamed Salah", "RW,ST", "Liverpool", 31, "Egypt", 89, 89, 65000000, 500000),
        ("LEWANDOWSKI001", "Robert Lewandowski", "ST", "Barcelona", 35, "Poland", 89, 89, 45000000, 450000)
    ]
    
    for player in sample_players:
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO players 
                (player_id, player_name, positions, club_name, age, nationality, 
                 overall_rating, potential, value_eur, wage_eur, is_custom)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, FALSE)
            ''', player)
        except:
            continue
    
    conn.commit()
    conn.close()
    
    print("✅ Sample data added successfully")

def create_deployment_config():
    """Create deployment configuration for easy deployment"""
    print("🚀 Creating deployment configuration...")
    
    # Create a simple deployment script
    deploy_script = """#!/bin/bash
# Deployment script for Match Simulator App

echo "🚀 Deploying Match Simulator App..."

# Install dependencies
pip install -r requirements.txt

# Initialize database
python -c "from app import init_database, initialize_players_from_csv; init_database(); initialize_players_from_csv()"

# Run enhancements
python enhance_app.py

# Start the application
streamlit run app.py --server.port 8501 --server.address 0.0.0.0

echo "✅ Deployment complete! App running on port 8501"
"""
    
    with open('deploy.sh', 'w') as f:
        f.write(deploy_script)
    
    # Create Windows batch file
    deploy_bat = """@echo off
echo 🚀 Deploying Match Simulator App...

REM Install dependencies
pip install -r requirements.txt

REM Initialize database
python -c "from app import init_database, initialize_players_from_csv; init_database(); initialize_players_from_csv()"

REM Run enhancements
python enhance_app.py

REM Start the application
streamlit run app.py --server.port 8501

echo ✅ Deployment complete! App running on port 8501
pause
"""
    
    with open('deploy.bat', 'w') as f:
        f.write(deploy_bat)
    
    print("✅ Deployment scripts created (deploy.sh and deploy.bat)")

def run_enhancements():
    """Run all enhancements"""
    print("🎨 Running Match Simulator App Enhancements")
    print("=" * 50)
    
    improve_csv_loading()
    add_sample_data()
    create_deployment_config()
    
    print("\n" + "=" * 50)
    print("🎉 All enhancements completed!")
    print("\n🚀 Your Match Simulator App is now fully enhanced and ready!")
    print("💡 Run 'streamlit run app.py' to start the application")

if __name__ == "__main__":
    run_enhancements()
