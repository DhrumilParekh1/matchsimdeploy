"""
Comprehensive CSV Data Loader for Match Simulator App
This script properly loads all player data from player-data-full.csv
"""

import pandas as pd
import sqlite3
import numpy as np
from datetime import datetime

def load_csv_data():
    """Load all player data from CSV into database"""
    print("🔄 Loading player data from CSV...")
    
    try:
        # Read CSV with proper settings
        df = pd.read_csv('player-data-full.csv', low_memory=False)
        print(f"✅ Successfully loaded CSV with {len(df)} rows and {len(df.columns)} columns")
        
        # Display column information
        print(f"📊 Available columns: {list(df.columns)}")
        
        # Connect to database
        conn = sqlite3.connect('match_simulator.db')
        cursor = conn.cursor()
        
        # Clear existing non-custom players
        print("🗑️ Clearing existing non-custom players...")
        cursor.execute("DELETE FROM players WHERE is_custom = FALSE")
        conn.commit()
        
        # Process data in batches
        batch_size = 1000
        successful_inserts = 0
        failed_inserts = 0
        
        print(f"📦 Processing data in batches of {batch_size}...")
        
        for i in range(0, len(df), batch_size):
            batch = df.iloc[i:i+batch_size]
            batch_success = 0
            
            for idx, row in batch.iterrows():
                try:
                    # Extract player data with multiple fallback options
                    player_data = extract_player_data(row, idx)
                    
                    # Skip if essential data is missing
                    if not player_data['player_name'] or player_data['player_name'] in ['Unknown', 'nan', '']:
                        continue
                    
                    # Insert into database
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
                    
                    batch_success += 1
                    successful_inserts += 1
                    
                except Exception as e:
                    failed_inserts += 1
                    if failed_inserts < 10:  # Show first 10 errors
                        print(f"⚠️ Error processing row {idx}: {str(e)[:100]}")
                    continue
            
            # Commit batch
            conn.commit()
            print(f"✅ Batch {i//batch_size + 1}: {batch_success}/{len(batch)} players inserted")
        
        print(f"\n📊 Final Results:")
        print(f"✅ Successfully inserted: {successful_inserts} players")
        print(f"❌ Failed insertions: {failed_inserts} players")
        
        # Verify data
        cursor.execute("SELECT COUNT(*) FROM players WHERE is_custom = FALSE")
        total_players = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(DISTINCT club_name) 
            FROM players 
            WHERE club_name IS NOT NULL AND club_name != '' AND club_name != 'Unknown'
        """)
        total_clubs = cursor.fetchone()[0]
        
        print(f"🏆 Database now contains {total_players} players from {total_clubs} clubs")
        
        # Show top clubs by player count
        clubs_df = pd.read_sql_query('''
            SELECT club_name, COUNT(*) as player_count
            FROM players 
            WHERE club_name IS NOT NULL AND club_name != '' AND club_name != 'Unknown'
            GROUP BY club_name
            ORDER BY player_count DESC
            LIMIT 10
        ''', conn)
        
        print(f"\n🏅 Top 10 clubs by player count:")
        for _, club in clubs_df.iterrows():
            print(f"   {club['club_name']}: {club['player_count']} players")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error loading CSV: {e}")
        return False

def extract_player_data(row, idx):
    """Extract player data from CSV row with multiple fallback options"""
    
    # Helper function to safely get value
    def safe_get(row, keys, default=None):
        for key in keys:
            if key in row and pd.notna(row[key]) and str(row[key]).strip() != '':
                return str(row[key]).strip()
        return default
    
    def safe_get_numeric(row, keys, default=None):
        for key in keys:
            if key in row and pd.notna(row[key]):
                try:
                    return float(row[key])
                except:
                    continue
        return default
    
    def safe_get_int(row, keys, default=None):
        for key in keys:
            if key in row and pd.notna(row[key]):
                try:
                    return int(float(row[key]))
                except:
                    continue
        return default
    
    # Extract player ID
    player_id = safe_get(row, ['player_id', 'sofifa_id', 'id'], f'player_{idx}')
    
    # Extract player name
    player_name = safe_get(row, ['short_name', 'long_name', 'player_name', 'name'], 'Unknown')
    
    # Extract positions
    positions = safe_get(row, ['player_positions', 'position', 'positions'], '')
    
    # Extract club name
    club_name = safe_get(row, ['club_name', 'team_name', 'club'], '')
    
    # Extract age
    age = safe_get_int(row, ['age'], None)
    
    # Extract nationality
    nationality = safe_get(row, ['nationality_name', 'nationality', 'nation'], '')
    
    # Extract overall rating
    overall_rating = safe_get_int(row, ['overall', 'overall_rating', 'rating'], None)
    
    # Extract potential
    potential = safe_get_int(row, ['potential', 'potential_rating'], None)
    
    # Extract value
    value_eur = safe_get_numeric(row, ['value_eur', 'market_value', 'value'], None)
    
    # Extract wage
    wage_eur = safe_get_numeric(row, ['wage_eur', 'wage', 'salary'], None)
    
    return {
        'player_id': player_id,
        'player_name': player_name,
        'positions': positions,
        'club_name': club_name,
        'age': age,
        'nationality': nationality,
        'overall_rating': overall_rating,
        'potential': potential,
        'value_eur': value_eur,
        'wage_eur': wage_eur
    }

def verify_data_loading():
    """Verify that data was loaded correctly"""
    print("\n🔍 Verifying data loading...")
    
    conn = sqlite3.connect('match_simulator.db')
    
    # Check total players
    total_players = pd.read_sql_query('SELECT COUNT(*) as count FROM players', conn).iloc[0]['count']
    print(f"📊 Total players in database: {total_players}")
    
    # Check players with ratings
    rated_players = pd.read_sql_query('SELECT COUNT(*) as count FROM players WHERE overall_rating IS NOT NULL', conn).iloc[0]['count']
    print(f"⭐ Players with ratings: {rated_players}")
    
    # Check clubs
    clubs_with_players = pd.read_sql_query('''
        SELECT COUNT(DISTINCT club_name) as count 
        FROM players 
        WHERE club_name IS NOT NULL AND club_name != '' AND club_name != 'Unknown'
    ''', conn).iloc[0]['count']
    print(f"🏟️ Clubs with players: {clubs_with_players}")
    
    # Sample some data
    sample_players = pd.read_sql_query('''
        SELECT player_name, club_name, overall_rating, positions
        FROM players 
        WHERE overall_rating IS NOT NULL 
        ORDER BY overall_rating DESC 
        LIMIT 5
    ''', conn)
    
    print(f"\n🌟 Top 5 rated players:")
    for _, player in sample_players.iterrows():
        print(f"   {player['player_name']} ({player['club_name']}) - {player['overall_rating']} - {player['positions']}")
    
    conn.close()

def main():
    """Main function to run the CSV loading process"""
    print("🚀 Starting CSV Data Loading Process")
    print("=" * 60)
    
    success = load_csv_data()
    
    if success:
        verify_data_loading()
        print("\n" + "=" * 60)
        print("🎉 CSV data loading completed successfully!")
        print("💡 Restart your Streamlit app to see all the loaded data")
    else:
        print("\n" + "=" * 60)
        print("❌ CSV data loading failed!")

if __name__ == "__main__":
    main()
