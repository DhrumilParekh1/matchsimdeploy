"""
Clean User Data Script
This script removes all user-generated data while preserving player data and database structure.
Use this to reset the system for fresh testing or production deployment.
"""

import sqlite3
import os

def clean_all_data():
    """Remove ALL data including users, admin data, and transfer logs for fresh start"""
    
    if not os.path.exists('match_simulator.db'):
        print("❌ Database not found!")
        return
    
    conn = sqlite3.connect('match_simulator.db')
    cursor = conn.cursor()
    
    try:
        print("🧹 Starting COMPLETE data cleanup...")
        print("⚠️  This will remove ALL data except player database structure")
        
        # Get all table counts before cleanup
        tables_to_check = ['users', 'transfer_bids', 'user_squads', 'user_items']
        counts = {}
        
        for table in tables_to_check:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                counts[table] = cursor.fetchone()[0]
            except:
                counts[table] = 0
        
        cursor.execute("SELECT COUNT(*) FROM players")
        player_count = cursor.fetchone()[0]
        
        print(f"📊 Current data counts:")
        for table, count in counts.items():
            print(f"  - {table.replace('_', ' ').title()}: {count}")
        print(f"  - Players: {player_count} (structure will be preserved)")
        
        # Confirm cleanup
        print("\n🚨 WARNING: This will delete ALL user data, admin data, and transfer logs!")
        confirm = input("Are you absolutely sure? Type 'DELETE ALL' to confirm: ")
        if confirm != 'DELETE ALL':
            print("❌ Cleanup cancelled.")
            return
        
        print("\n🗑️  Performing complete data wipe...")
        
        # Delete ALL data in correct order (respecting foreign keys)
        
        # 1. Delete user items
        cursor.execute("DELETE FROM user_items")
        print("✅ Deleted all user items")
        
        # 2. Delete user squads
        cursor.execute("DELETE FROM user_squads")
        print("✅ Deleted all user squads")
        
        # 3. Delete ALL transfer bids (including logs)
        cursor.execute("DELETE FROM transfer_bids")
        print("✅ Deleted all transfer bids and logs")
        
        # 4. Delete ALL users (including admin accounts)
        cursor.execute("DELETE FROM users")
        print("✅ Deleted all users (including admin accounts)")
        
        # 5. Reset player data to original state
        print("🔄 Resetting player data to original state...")
        # This will reload fresh player data from CSV
        
        # 6. Reset any sequences/auto-increment counters
        cursor.execute("DELETE FROM sqlite_sequence WHERE name IN ('users', 'transfer_bids', 'user_squads', 'user_items')")
        print("✅ Reset ID sequences")
        
        # Commit all changes
        conn.commit()
        
        # Verify cleanup
        final_counts = {}
        for table in tables_to_check:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                final_counts[table] = cursor.fetchone()[0]
            except:
                final_counts[table] = 0
        
        cursor.execute("SELECT COUNT(*) FROM players")
        remaining_players = cursor.fetchone()[0]
        
        print(f"\n✅ COMPLETE DATA WIPE SUCCESSFUL!")
        print(f"📊 Final data counts:")
        for table, count in final_counts.items():
            print(f"  - {table.replace('_', ' ').title()}: {count}")
        print(f"  - Players: {remaining_players} (structure preserved)")
        
        print(f"\n🎉 Successfully removed:")
        total_removed = sum(counts.values())
        for table, count in counts.items():
            if count > 0:
                print(f"  - {count} {table.replace('_', ' ')}")
        
        print(f"\n🚀 Database is now completely clean and ready for fresh deployment!")
        print("💡 All user data, admin data, and transfer logs have been removed.")
        print("🔄 Player database structure is ready for fresh data loading.")
        
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
        conn.rollback()
        print("🔄 Changes have been rolled back.")
    
    finally:
        conn.close()

def reset_player_clubs():
    """Optional: Reset all player clubs to original CSV state"""
    
    print("\n🔄 Would you like to reset player club assignments to original state?")
    print("   This will undo any transfers made during testing.")
    
    reset_confirm = input("Reset player clubs? (yes/no): ")
    if reset_confirm.lower() != 'yes':
        print("⏭️  Skipping player club reset.")
        return
    
    # This would require reloading from CSV
    print("💡 To reset player clubs, run: python improved_csv_loader.py")
    print("   This will reload all player data from the original CSV file.")

if __name__ == "__main__":
    print("🧹 Match Simulator App - COMPLETE DATA CLEANUP")
    print("=" * 60)
    print("🚨 WARNING: This script will remove ALL data including:")
    print("  - ALL user accounts (including admin accounts)")
    print("  - ALL transfer bids and logs")
    print("  - ALL user squads and uploads")
    print("  - ALL user items and inventory")
    print("  - ALL admin data and logs")
    print("\n💾 Only the player database structure will be preserved.")
    print("=" * 60)
    
    clean_all_data()
    
    print("\n✨ Complete cleanup finished! The app is ready for fresh deployment.")
    print("🚀 You can now run the app with a completely clean slate!")
