"""
Database migration script to add missing columns for enhanced transfer workflow
"""

import sqlite3
import os

def migrate_database():
    """Add missing columns to transfer_bids table"""
    
    if not os.path.exists('match_simulator.db'):
        print("❌ Database not found! Please run the app first to create the database.")
        return
    
    conn = sqlite3.connect('match_simulator.db')
    cursor = conn.cursor()
    
    try:
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(transfer_bids)")
        columns = [column[1] for column in cursor.fetchall()]
        
        print(f"📊 Current transfer_bids columns: {columns}")
        
        # Add seller_response_date column if it doesn't exist
        if 'seller_response_date' not in columns:
            cursor.execute('''
                ALTER TABLE transfer_bids 
                ADD COLUMN seller_response_date TEXT
            ''')
            print("✅ Added seller_response_date column")
        else:
            print("✅ seller_response_date column already exists")
        
        # Add admin_response_date column if it doesn't exist
        if 'admin_response_date' not in columns:
            cursor.execute('''
                ALTER TABLE transfer_bids 
                ADD COLUMN admin_response_date TEXT
            ''')
            print("✅ Added admin_response_date column")
        else:
            print("✅ admin_response_date column already exists")
        
        # Update status column to handle new statuses if needed
        cursor.execute("SELECT DISTINCT status FROM transfer_bids")
        statuses = [row[0] for row in cursor.fetchall()]
        print(f"📊 Current transfer statuses: {statuses}")
        
        conn.commit()
        print("🎉 Database migration completed successfully!")
        
        # Show updated table structure
        cursor.execute("PRAGMA table_info(transfer_bids)")
        columns_info = cursor.fetchall()
        print("\n📋 Updated transfer_bids table structure:")
        for col in columns_info:
            print(f"  - {col[1]} ({col[2]})")
        
    except Exception as e:
        print(f"❌ Migration error: {e}")
        conn.rollback()
    
    finally:
        conn.close()

def verify_migration():
    """Verify that the migration was successful"""
    
    conn = sqlite3.connect('match_simulator.db')
    cursor = conn.cursor()
    
    try:
        # Test the new columns
        cursor.execute('''
            SELECT id, status, seller_response_date, admin_response_date 
            FROM transfer_bids 
            LIMIT 1
        ''')
        print("✅ Migration verification successful - new columns are accessible")
        
    except Exception as e:
        print(f"❌ Migration verification failed: {e}")
    
    finally:
        conn.close()

if __name__ == "__main__":
    print("🔧 Starting database migration...")
    migrate_database()
    verify_migration()
    print("✅ Migration complete!")
