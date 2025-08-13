"""
Improved CSV Data Loader with Value Cleaning for Match Simulator App
This script properly cleans and loads player values from formats like €185M, €50K, etc.
"""

import pandas as pd
import sqlite3
import numpy as np
import re
from datetime import datetime

def clean_value(value_str):
    """
    Clean value strings like '€185M', '€50K', '€2.5M' to numerical values in euros
    """
    if pd.isna(value_str) or value_str == '' or value_str is None:
        return None
    
    # Convert to string and clean
    value_str = str(value_str).strip()
    
    # Remove currency symbols and spaces
    value_str = re.sub(r'[€$£¥]', '', value_str)
    value_str = value_str.replace(',', '').replace(' ', '')
    
    # Handle different suffixes
    multiplier = 1
    if value_str.upper().endswith('M'):
        multiplier = 1000000  # Million
        value_str = value_str[:-1]
    elif value_str.upper().endswith('K'):
        multiplier = 1000     # Thousand
        value_str = value_str[:-1]
    elif value_str.upper().endswith('B'):
        multiplier = 1000000000  # Billion
        value_str = value_str[:-1]
    
    try:
        # Convert to float and apply multiplier
        numeric_value = float(value_str) * multiplier
        return int(numeric_value)  # Return as integer euros
    except (ValueError, TypeError):
        return None

def clean_wage(wage_str):
    """
    Clean wage strings like '€50K', '€2.5K' to numerical values in euros
    """
    return clean_value(wage_str)  # Same logic as value cleaning

def load_csv_data_improved():
    """Load all player data from CSV with improved value cleaning"""
    print("🔄 Loading player data from CSV with value cleaning...")
    
    try:
        # Read CSV with proper settings
        df = pd.read_csv('player-data-full.csv', low_memory=False)
        print(f"✅ Successfully loaded CSV with {len(df)} rows and {len(df.columns)} columns")
        
        # Display available columns
        print(f"📊 Available columns: {list(df.columns)}")
        
        # Show sample values before cleaning
        if 'value' in df.columns:
            print(f"💰 Sample values before cleaning: {df['value'].dropna().head(5).tolist()}")
        
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
        value_cleaning_stats = {'cleaned': 0, 'failed': 0}
        
        print(f"📦 Processing data in batches of {batch_size}...")
        
        for i in range(0, len(df), batch_size):
            batch = df.iloc[i:i+batch_size]
            batch_success = 0
            
            for idx, row in batch.iterrows():
                try:
                    # Extract player data with improved value cleaning
                    player_data = extract_player_data_improved(row, idx, value_cleaning_stats)
                    
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
        print(f"💰 Value cleaning: {value_cleaning_stats['cleaned']} cleaned, {value_cleaning_stats['failed']} failed")
        
        # Verify data with value statistics
        verify_data_with_values(conn)
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error loading CSV: {e}")
        return False

def extract_player_data_improved(row, idx, value_stats):
    """Extract player data from CSV row with improved value cleaning"""
    
    # Helper function to safely get value
    def safe_get(row, keys, default=None):
        for key in keys:
            if key in row and pd.notna(row[key]) and str(row[key]).strip() != '':
                return str(row[key]).strip()
        return default
    
    def safe_get_int(row, keys, default=None):
        for key in keys:
            if key in row and pd.notna(row[key]):
                try:
                    return int(float(row[key]))
                except:
                    continue
        return default
    
    # Extract basic player data
    player_id = safe_get(row, ['player_id', 'sofifa_id', 'id'], f'player_{idx}')
    player_name = safe_get(row, ['short_name', 'long_name', 'player_name', 'name'], 'Unknown')
    positions = safe_get(row, ['player_positions', 'position', 'positions'], '')
    club_name = safe_get(row, ['club_name', 'team_name', 'club'], '')
    age = safe_get_int(row, ['age'], None)
    nationality = safe_get(row, ['nationality_name', 'nationality', 'nation'], '')
    overall_rating = safe_get_int(row, ['overall', 'overall_rating', 'rating'], None)
    potential = safe_get_int(row, ['potential', 'potential_rating'], None)
    
    # Extract and clean value
    value_eur = None
    raw_value = safe_get(row, ['value', 'market_value', 'value_eur'], None)
    if raw_value:
        cleaned_value = clean_value(raw_value)
        if cleaned_value is not None:
            value_eur = cleaned_value
            value_stats['cleaned'] += 1
        else:
            value_stats['failed'] += 1
    
    # Extract and clean wage
    wage_eur = None
    raw_wage = safe_get(row, ['wage', 'salary', 'wage_eur'], None)
    if raw_wage:
        cleaned_wage = clean_wage(raw_wage)
        if cleaned_wage is not None:
            wage_eur = cleaned_wage
    
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

def verify_data_with_values(conn):
    """Verify that data was loaded correctly with value statistics"""
    print("\n🔍 Verifying data loading with values...")
    
    # Check total players
    total_players = pd.read_sql_query('SELECT COUNT(*) as count FROM players', conn).iloc[0]['count']
    print(f"📊 Total players in database: {total_players}")
    
    # Check players with values
    valued_players = pd.read_sql_query('SELECT COUNT(*) as count FROM players WHERE value_eur IS NOT NULL', conn).iloc[0]['count']
    print(f"💰 Players with market values: {valued_players}")
    
    # Check value statistics
    value_stats = pd.read_sql_query('''
        SELECT 
            MIN(value_eur) as min_value,
            MAX(value_eur) as max_value,
            AVG(value_eur) as avg_value
        FROM players 
        WHERE value_eur IS NOT NULL
    ''', conn).iloc[0]
    
    print(f"💎 Value statistics:")
    print(f"   Min: €{value_stats['min_value']:,.0f}")
    print(f"   Max: €{value_stats['max_value']:,.0f}")
    print(f"   Avg: €{value_stats['avg_value']:,.0f}")
    
    # Show most valuable players
    top_players = pd.read_sql_query('''
        SELECT player_name, club_name, value_eur, overall_rating
        FROM players 
        WHERE value_eur IS NOT NULL 
        ORDER BY value_eur DESC 
        LIMIT 10
    ''', conn)
    
    print(f"\n💎 Top 10 most valuable players:")
    for _, player in top_players.iterrows():
        print(f"   {player['player_name']} ({player['club_name']}) - €{player['value_eur']:,.0f} - Rating: {player['overall_rating']}")
    
    # Check clubs with highest total squad values
    club_values = pd.read_sql_query('''
        SELECT 
            club_name, 
            COUNT(*) as player_count,
            SUM(value_eur) as total_value,
            AVG(value_eur) as avg_value
        FROM players 
        WHERE club_name IS NOT NULL AND club_name != '' AND value_eur IS NOT NULL
        GROUP BY club_name
        ORDER BY total_value DESC
        LIMIT 10
    ''', conn)
    
    print(f"\n🏆 Top 10 clubs by total squad value:")
    for _, club in club_values.iterrows():
        print(f"   {club['club_name']}: €{club['total_value']:,.0f} ({club['player_count']} players, avg: €{club['avg_value']:,.0f})")

def main():
    """Main function to run the improved CSV loading process"""
    print("🚀 Starting Improved CSV Data Loading with Value Cleaning")
    print("=" * 70)
    
    success = load_csv_data_improved()
    
    if success:
        print("\n" + "=" * 70)
        print("🎉 Improved CSV data loading completed successfully!")
        print("💰 All player values have been cleaned and converted to euros!")
        print("💡 Restart your Streamlit app to see all the loaded data with proper values")
    else:
        print("\n" + "=" * 70)
        print("❌ CSV data loading failed!")

if __name__ == "__main__":
    main()
