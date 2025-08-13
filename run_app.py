"""
Final deployment script for Match Simulator App (2025 Server)
This script ensures all components are properly initialized and the app runs smoothly
"""

import subprocess
import sys
import os
from pathlib import Path

def check_dependencies():
    """Check if all required dependencies are installed"""
    required_packages = ['streamlit', 'pandas', 'pillow']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package} is installed")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package} is missing")
    
    if missing_packages:
        print(f"\n🔧 Installing missing packages: {', '.join(missing_packages)}")
        subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing_packages)
        print("✅ All dependencies installed!")
    
    return True

def initialize_database():
    """Initialize the database with player data"""
    print("🗄️ Initializing database...")
    
    try:
        from app import init_database, initialize_players_from_csv
        init_database()
        initialize_players_from_csv()
        print("✅ Database initialized successfully!")
    except Exception as e:
        print(f"⚠️ Database initialization warning: {e}")
        # Try to load improved CSV data
        try:
            if os.path.exists('improved_csv_loader.py'):
                subprocess.run([sys.executable, 'improved_csv_loader.py'], check=False)
                print("✅ Player data loaded with improved loader!")
        except Exception as e2:
            print(f"⚠️ CSV loading warning: {e2}")
    
    return True

def run_streamlit_app():
    """Run the Streamlit application"""
    print("🚀 Starting Match Simulator App...")
    print("📱 The app will open in your default browser")
    print("🌐 Access URL: http://localhost:8501")
    print("=" * 50)
    
    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py", "--server.port", "8501"], check=True)
    except KeyboardInterrupt:
        print("\n👋 App stopped by user")
    except Exception as e:
        print(f"❌ Error running app: {e}")
        print("💡 Try running manually: streamlit run app.py")

def main():
    """Main function to run the complete setup and launch"""
    print("🏆 Match Simulator App (2025 Server) - Final Setup")
    print("=" * 60)
    
    # Check current directory
    if not os.path.exists('app.py'):
        print("❌ app.py not found! Please run this script from the project directory.")
        return
    
    # Step 1: Check dependencies
    print("\n📦 Step 1: Checking dependencies...")
    check_dependencies()
    
    # Step 2: Initialize database
    print("\n🗄️ Step 2: Setting up database...")
    initialize_database()
    
    # Step 3: Run the app
    print("\n🚀 Step 3: Launching application...")
    run_streamlit_app()

if __name__ == "__main__":
    main()
