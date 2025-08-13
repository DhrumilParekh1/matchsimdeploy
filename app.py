import streamlit as st
import pandas as pd
import sqlite3
import hashlib
from datetime import datetime
import os
from PIL import Image
import io
import base64
from ui_components import (
    load_css, 
    display_welcome_hero, 
    display_dashboard_metrics, 
    display_tab_background,
    display_enhanced_table,
    display_player_stats_card
)

# Page configuration
st.set_page_config(
    page_title="Match Simulator App (2025 Server)",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Database initialization
def init_database():
    conn = sqlite3.connect('match_simulator.db')
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL,
            email TEXT,
            club_name TEXT,
            cash REAL DEFAULT 0,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Players table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS players (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id TEXT UNIQUE,
            player_name TEXT NOT NULL,
            positions TEXT,
            club_name TEXT,
            age INTEGER,
            nationality TEXT,
            overall_rating INTEGER,
            potential INTEGER,
            value_eur REAL,
            wage_eur REAL,
            is_custom BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Squad uploads table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS squad_uploads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            image_data BLOB,
            description TEXT,
            status TEXT DEFAULT 'pending',
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            approved_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Transfer bids table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transfer_bids (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            player_id TEXT,
            bid_amount REAL,
            description TEXT,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            approved_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Items/inventory table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            item_name TEXT,
            quantity INTEGER DEFAULT 1,
            received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()

# Load player data from CSV
@st.cache_data
def load_player_data():
    try:
        df = pd.read_csv('player-data-full.csv')
        return df
    except Exception as e:
        st.error(f"Error loading player data: {e}")
        return pd.DataFrame()

# Initialize players table with CSV data
def initialize_players_from_csv():
    conn = sqlite3.connect('match_simulator.db')
    cursor = conn.cursor()
    
    # Check if players table is empty
    cursor.execute("SELECT COUNT(*) FROM players WHERE is_custom = FALSE")
    count = cursor.fetchone()[0]
    
    if count == 0:
        df = load_player_data()
        if not df.empty:
            # Map CSV columns to our database schema
            for _, row in df.iterrows():
                try:
                    cursor.execute('''
                        INSERT OR IGNORE INTO players 
                        (player_id, player_name, positions, club_name, age, nationality, 
                         overall_rating, potential, value_eur, wage_eur, is_custom)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, FALSE)
                    ''', (
                        str(row.get('sofifa_id', '')),
                        str(row.get('short_name', '')),
                        str(row.get('player_positions', '')),
                        str(row.get('club_name', '')),
                        int(row.get('age', 0)) if pd.notna(row.get('age')) else None,
                        str(row.get('nationality_name', '')),
                        int(row.get('overall', 0)) if pd.notna(row.get('overall')) else None,
                        int(row.get('potential', 0)) if pd.notna(row.get('potential')) else None,
                        float(row.get('value_eur', 0)) if pd.notna(row.get('value_eur')) else None,
                        float(row.get('wage_eur', 0)) if pd.notna(row.get('wage_eur')) else None
                    ))
                except Exception as e:
                    continue
            conn.commit()
    
    conn.close()

# Authentication functions
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, password_hash):
    return hash_password(password) == password_hash

def create_user(username, password, role, email=None):
    conn = sqlite3.connect('match_simulator.db')
    cursor = conn.cursor()
    
    try:
        password_hash = hash_password(password)
        cursor.execute('''
            INSERT INTO users (username, password_hash, role, email)
            VALUES (?, ?, ?, ?)
        ''', (username, password_hash, role, email))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def authenticate_user(username, password):
    conn = sqlite3.connect('match_simulator.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, username, role, status, club_name, cash
        FROM users 
        WHERE username = ? AND password_hash = ?
    ''', (username, hash_password(password)))
    
    user = cursor.fetchone()
    conn.close()
    
    if user:
        return {
            'id': user[0],
            'username': user[1],
            'role': user[2],
            'status': user[3],
            'club_name': user[4],
            'cash': user[5]
        }
    return None

# Initialize session state
def init_session_state():
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'page' not in st.session_state:
        st.session_state.page = 'welcome'

# Main application
def main():
    init_session_state()
    init_database()
    initialize_players_from_csv()
    load_css()  # Load enhanced UI styling
    
    # Sidebar navigation
    with st.sidebar:
        st.title("Navigation")
        
        if not st.session_state.authenticated:
            if st.button("🏠 Welcome"):
                st.session_state.page = 'welcome'
            if st.button("📝 Sign Up"):
                st.session_state.page = 'signup'
            if st.button("🔐 Login"):
                st.session_state.page = 'login'
        else:
            user = st.session_state.user
            st.write(f"Welcome, **{user['username']}**")
            st.write(f"Role: **{user['role']}**")
            if user['club_name']:
                st.write(f"Club: **{user['club_name']}**")
            if user['cash'] is not None:
                st.write(f"Cash: **€{user['cash']:,.2f}**")
            
            if user['role'] == 'admin':
                st.subheader("Admin Dashboard")
                if st.button("🏠 Dashboard Home"):
                    st.session_state.page = 'admin_home'
                if st.button("👥 Manage Users"):
                    st.session_state.page = 'manage_users'
                if st.button("💰 Distribute Items & Cash"):
                    st.session_state.page = 'distribute_items'
                if st.button("🔄 Manage Transfers"):
                    st.session_state.page = 'manage_transfers'
                if st.button("📊 Transfer Logs"):
                    st.session_state.page = 'transfer_logs'
                if st.button("➕ Add Custom Players"):
                    st.session_state.page = 'add_players'
                if st.button("📋 User Squads"):
                    st.session_state.page = 'user_squads'
            else:
                if user['status'] == 'approved':
                    st.subheader("User Dashboard")
                    if st.button("🏠 Dashboard Home"):
                        st.session_state.page = 'user_home'
                    if st.button("🔍 Search Players"):
                        st.session_state.page = 'search_players'
                    if st.button("👥 Check Squad"):
                        st.session_state.page = 'check_squad'
                    if st.button("📤 Upload Squad"):
                        st.session_state.page = 'upload_squad'
                    if st.button("💸 Make Transfer Bid"):
                        st.session_state.page = 'transfer_bid'
                    if st.button("💰 Balance & Inventory"):
                        st.session_state.page = 'balance_inventory'
                else:
                    st.warning("Your account is pending admin approval.")
            
            if st.button("🚪 Logout"):
                st.session_state.authenticated = False
                st.session_state.user = None
                st.session_state.page = 'welcome'
                st.rerun()
    
    # Main content area
    if st.session_state.page == 'welcome':
        show_welcome_page()
    elif st.session_state.page == 'signup':
        show_signup_page()
    elif st.session_state.page == 'login':
        show_login_page()
    elif st.session_state.authenticated:
        if st.session_state.page == 'admin_home':
            show_admin_home()
        elif st.session_state.page == 'user_home':
            show_user_home()
        elif st.session_state.page == 'manage_users':
            show_manage_users()
        elif st.session_state.page == 'distribute_items':
            show_distribute_items()
        elif st.session_state.page == 'manage_transfers':
            show_manage_transfers()
        elif st.session_state.page == 'transfer_logs':
            show_transfer_logs()
        elif st.session_state.page == 'add_players':
            show_add_players()
        elif st.session_state.page == 'user_squads':
            show_user_squads()
        elif st.session_state.page == 'search_players':
            show_search_players()
        elif st.session_state.page == 'check_squad':
            show_check_squad()
        elif st.session_state.page == 'upload_squad':
            show_upload_squad()
        elif st.session_state.page == 'transfer_bid':
            show_transfer_bid()
        elif st.session_state.page == 'balance_inventory':
            show_balance_inventory()

def show_welcome_page():
    # Use enhanced welcome hero
    display_welcome_hero()
    
    # Add light background section with available images
    from ui_components import get_image_base64
    
    # Get some available images for background integration
    city_bg = get_image_base64('city.jpg')
    henderson_bg = get_image_base64('henderson-lifts-ucl-trophy.png')
    
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, rgba(255,255,255,0.85) 0%, rgba(248,249,250,0.85) 100%), 
                   url('data:image/jpeg;base64,{city_bg}') center/cover;
        background-blend-mode: lighten;
        padding: 3rem 2rem;
        border-radius: 20px;
        margin: 2rem 0;
        box-shadow: 0 8px 25px rgba(0,0,0,0.1);
    ">
        <div style="display: flex; justify-content: space-between; gap: 2rem; flex-wrap: wrap;">
            <div style="flex: 1; min-width: 300px;">
                <h3 style="color: #2c3e50; margin-bottom: 1.5rem; font-size: 1.8rem; display: flex; align-items: center;">
                    <img src="data:image/jpeg;base64,{get_image_base64('messi.jpeg')}" 
                         style="width: 80px; height: 80px; border-radius: 50%; margin-right: 0.5rem; border: 4px solid #667eea; box-shadow: 0 6px 20px rgba(0,0,0,0.3); object-fit: cover;" />
                    👤 For Users
                </h3>
                <ul style="color: #34495e; line-height: 1.8; font-size: 1.1rem;">
                    <li style="margin-bottom: 0.5rem;">🔍 <strong>Search & Scout</strong> thousands of players</li>
                    <li style="margin-bottom: 0.5rem;">👥 <strong>Build Your Squad</strong> with your assigned club</li>
                    <li style="margin-bottom: 0.5rem;">📤 <strong>Upload Squad Images</strong> for approval</li>
                    <li style="margin-bottom: 0.5rem;">💸 <strong>Make Transfer Bids</strong> for dream players</li>
                    <li style="margin-bottom: 0.5rem;">💰 <strong>Manage Your Budget</strong> and inventory</li>
                </ul>
            </div>
            <div style="flex: 1; min-width: 300px;">
                <h3 style="color: #2c3e50; margin-bottom: 1.5rem; font-size: 1.8rem; display: flex; align-items: center;">
                    <img src="data:image/jpeg;base64,{get_image_base64('ronaldo.jpg')}" 
                         style="width: 80px; height: 80px; border-radius: 50%; margin-right: 0.5rem; border: 4px solid #667eea; box-shadow: 0 6px 20px rgba(0,0,0,0.3); object-fit: cover;" />
                    👑 For Admins
                </h3>
                <ul style="color: #34495e; line-height: 1.8; font-size: 1.1rem;">
                    <li style="margin-bottom: 0.5rem;">👥 <strong>Manage Users</strong> and approve registrations</li>
                    <li style="margin-bottom: 0.5rem;">💰 <strong>Distribute Cash & Items</strong> to users</li>
                    <li style="margin-bottom: 0.5rem;">🔄 <strong>Approve Transfers</strong> and manage windows</li>
                    <li style="margin-bottom: 0.5rem;">📊 <strong>Track All Activities</strong> with detailed logs</li>
                    <li style="margin-bottom: 0.5rem;">➕ <strong>Add Custom Players</strong> to the database</li>
                </ul>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Add getting started section with another background
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, rgba(255,255,255,0.85) 0%, rgba(248,249,250,0.85) 100%), 
                   url('data:image/png;base64,{henderson_bg}') center/cover;
        background-blend-mode: lighten;
        padding: 3rem 2rem;
        border-radius: 20px;
        margin: 2rem 0;
        box-shadow: 0 8px 25px rgba(0,0,0,0.1);
        text-align: center;
    ">
        <h3 style="color: #2c3e50; margin-bottom: 2rem; font-size: 2rem; display: flex; align-items: center; justify-content: center;">
            <img src="data:image/png;base64,{get_image_base64('henderson-lifts-ucl-trophy.png')}" 
                 style="width: 100px; height: 100px; margin-right: 1rem; border-radius: 50%; border: 4px solid #667eea; box-shadow: 0 6px 20px rgba(0,0,0,0.3); object-fit: cover;" />
            🚀 Getting Started
        </h3>
        <div style="display: flex; justify-content: center; gap: 3rem; flex-wrap: wrap; margin-bottom: 2rem;">
            <div style="text-align: center; background: linear-gradient(135deg, #667eea, #764ba2); color: white; padding: 1.5rem; border-radius: 15px; min-width: 150px;">
                <div style="font-size: 2.5rem; margin-bottom: 1rem;">1️⃣</div>
                <div style="font-weight: 600; margin-bottom: 0.5rem;">Sign Up</div>
                <div style="font-size: 0.9rem; opacity: 0.9;">as either a User or Admin</div>
            </div>
            <div style="text-align: center; background: linear-gradient(135deg, #ff6b6b, #ee5a24); color: white; padding: 1.5rem; border-radius: 15px; min-width: 150px;">
                <div style="font-size: 2.5rem; margin-bottom: 1rem;">2️⃣</div>
                <div style="font-weight: 600; margin-bottom: 0.5rem;">Login</div>
                <div style="font-size: 0.9rem; opacity: 0.9;">with your credentials</div>
            </div>
            <div style="text-align: center; background: linear-gradient(135deg, #a8edea, #fed6e3); color: #2c3e50; padding: 1.5rem; border-radius: 15px; min-width: 150px;">
                <div style="font-size: 2.5rem; margin-bottom: 1rem;">3️⃣</div>
                <div style="font-weight: 600; margin-bottom: 0.5rem;">Explore</div>
                <div style="font-size: 0.9rem; opacity: 0.9;">the dashboard features</div>
            </div>
            <div style="text-align: center; background: linear-gradient(135deg, #ffecd2, #fcb69f); color: #2c3e50; padding: 1.5rem; border-radius: 15px; min-width: 150px;">
                <div style="font-size: 2.5rem; margin-bottom: 1rem;">4️⃣</div>
                <div style="font-weight: 600; margin-bottom: 0.5rem;">Start Building</div>
                <div style="font-size: 0.9rem; opacity: 0.9;">your ultimate team!</div>
            </div>
        </div>
        <div style="
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1rem 2rem;
            border-radius: 10px;
            display: inline-block;
            margin-top: 1rem;
        ">
            💡 <strong>New users</strong>: Your registration will need admin approval before you can access all features.
        </div>
    </div>
    """, unsafe_allow_html=True)

# Import all page functions
from pages import *
from user_pages import *

if __name__ == "__main__":
    main()
