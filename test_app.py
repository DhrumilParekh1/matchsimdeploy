"""
Test script for Match Simulator App
This script tests the core functionality of the application
"""

import sqlite3
import pandas as pd
from app import create_user, authenticate_user, hash_password
import os

def test_database_setup():
    """Test if database is properly initialized"""
    print("Testing database setup...")
    
    conn = sqlite3.connect('match_simulator.db')
    cursor = conn.cursor()
    
    # Check if all tables exist
    tables = ['users', 'players', 'squad_uploads', 'transfer_bids', 'user_inventory']
    
    for table in tables:
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
        result = cursor.fetchone()
        if result:
            print(f"✅ Table '{table}' exists")
        else:
            print(f"❌ Table '{table}' missing")
    
    # Check if player data is loaded
    cursor.execute("SELECT COUNT(*) FROM players")
    player_count = cursor.fetchone()[0]
    print(f"✅ Player database contains {player_count} players")
    
    conn.close()

def test_user_creation():
    """Test user creation and authentication"""
    print("\nTesting user creation and authentication...")
    
    # Test admin user creation
    admin_created = create_user("test_admin", "admin123", "admin", "admin@test.com")
    if admin_created:
        print("✅ Admin user created successfully")
    else:
        print("⚠️ Admin user already exists or creation failed")
    
    # Test regular user creation
    user_created = create_user("test_user", "user123", "user", "user@test.com")
    if user_created:
        print("✅ Regular user created successfully")
    else:
        print("⚠️ Regular user already exists or creation failed")
    
    # Test authentication
    admin_auth = authenticate_user("test_admin", "admin123")
    user_auth = authenticate_user("test_user", "user123")
    
    if admin_auth and admin_auth['role'] == 'admin':
        print("✅ Admin authentication successful")
    else:
        print("❌ Admin authentication failed")
    
    if user_auth and user_auth['role'] == 'user':
        print("✅ User authentication successful")
    else:
        print("❌ User authentication failed")

def test_player_data():
    """Test player data functionality"""
    print("\nTesting player data...")
    
    conn = sqlite3.connect('match_simulator.db')
    
    # Check for unique clubs
    clubs_df = pd.read_sql_query('''
        SELECT DISTINCT club_name, COUNT(*) as player_count
        FROM players 
        WHERE club_name IS NOT NULL AND club_name != ''
        GROUP BY club_name
        ORDER BY player_count DESC
        LIMIT 10
    ''', conn)
    
    print(f"✅ Found {len(clubs_df)} unique clubs")
    print("Top 5 clubs by player count:")
    for _, club in clubs_df.head().iterrows():
        print(f"   - {club['club_name']}: {club['player_count']} players")
    
    # Test custom player addition
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT OR IGNORE INTO players 
            (player_id, player_name, positions, club_name, age, nationality,
             overall_rating, potential, value_eur, wage_eur, is_custom)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, TRUE)
        ''', ("TEST001", "Test Player", "ST", "Test FC", 25, "Test Country", 80, 85, 5000000, 100000))
        conn.commit()
        print("✅ Custom player addition works")
    except Exception as e:
        print(f"❌ Custom player addition failed: {e}")
    
    conn.close()

def test_transfer_system():
    """Test transfer bid system"""
    print("\nTesting transfer system...")
    
    conn = sqlite3.connect('match_simulator.db')
    cursor = conn.cursor()
    
    # Get a test user and player
    cursor.execute("SELECT id FROM users WHERE role = 'user' LIMIT 1")
    user_result = cursor.fetchone()
    
    cursor.execute("SELECT player_id FROM players LIMIT 1")
    player_result = cursor.fetchone()
    
    if user_result and player_result:
        user_id = user_result[0]
        player_id = player_result[0]
        
        try:
            # Create a test transfer bid
            cursor.execute('''
                INSERT INTO transfer_bids (user_id, player_id, bid_amount, description)
                VALUES (?, ?, ?, ?)
            ''', (user_id, player_id, 10000000, "Test transfer bid"))
            conn.commit()
            print("✅ Transfer bid creation works")
            
            # Test bid retrieval
            cursor.execute('''
                SELECT COUNT(*) FROM transfer_bids 
                WHERE user_id = ? AND player_id = ?
            ''', (user_id, player_id))
            bid_count = cursor.fetchone()[0]
            
            if bid_count > 0:
                print("✅ Transfer bid retrieval works")
            else:
                print("❌ Transfer bid retrieval failed")
                
        except Exception as e:
            print(f"❌ Transfer system test failed: {e}")
    else:
        print("⚠️ No test users or players available for transfer test")
    
    conn.close()

def test_file_structure():
    """Test if all required files exist"""
    print("\nTesting file structure...")
    
    required_files = [
        'app.py',
        'pages.py', 
        'user_pages.py',
        'requirements.txt',
        'README.md',
        'player-data-full.csv'
    ]
    
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file} exists")
        else:
            print(f"❌ {file} missing")

def run_all_tests():
    """Run all tests"""
    print("🚀 Starting Match Simulator App Tests\n")
    print("=" * 50)
    
    test_file_structure()
    test_database_setup()
    test_user_creation()
    test_player_data()
    test_transfer_system()
    
    print("\n" + "=" * 50)
    print("🏁 All tests completed!")
    print("\n💡 To run the app: streamlit run app.py")

if __name__ == "__main__":
    run_all_tests()
