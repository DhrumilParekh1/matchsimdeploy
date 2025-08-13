"""
Enhanced UI Components for Match Simulator App
This module provides enhanced styling and visual components
"""

import streamlit as st
import base64
from PIL import Image
import os
import pandas as pd

def load_css():
    """Load custom CSS for enhanced UI"""
    st.markdown("""
    <style>
    /* Main app styling */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
    }
    
    .player-card {
        background: linear-gradient(145deg, #f0f2f6, #ffffff);
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        border-left: 4px solid #667eea;
        transition: transform 0.3s ease;
    }
    
    .player-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.15);
    }
    
    .stat-card {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        padding: 1.5rem;
        border-radius: 12px;
        text-align: center;
        margin: 0.5rem;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }
    
    .transfer-bid {
        background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        border-left: 4px solid #ff6b6b;
    }
    
    .success-card {
        background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
        border-radius: 12px;
        padding: 1rem;
        margin: 1rem 0;
        border-left: 4px solid #00d4aa;
    }
    
    .club-badge {
        width: 60px;
        height: 60px;
        border-radius: 50%;
        object-fit: cover;
        border: 3px solid #667eea;
        margin: 0 auto;
        display: block;
    }
    
    .player-image {
        width: 80px;
        height: 80px;
        border-radius: 50%;
        object-fit: cover;
        border: 3px solid #764ba2;
        margin: 0 auto 1rem auto;
        display: block;
    }
    
    .dashboard-metric {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        padding: 1.5rem;
        border-radius: 12px;
        text-align: center;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        margin: 0.5rem;
    }
    
    .sidebar-nav {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
        border-radius: 12px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    .transfer-status-pending {
        background: #fff3cd;
        color: #856404;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: bold;
        display: inline-block;
    }
    
    .transfer-status-approved {
        background: #d4edda;
        color: #155724;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: bold;
        display: inline-block;
    }
    
    .transfer-status-rejected {
        background: #f8d7da;
        color: #721c24;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: bold;
        display: inline-block;
    }
    
    .animated-button {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        border: none;
        padding: 0.75rem 1.5rem;
        border-radius: 25px;
        font-weight: bold;
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }
    
    .animated-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
    }
    
    .welcome-hero {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 3rem 2rem;
        border-radius: 20px;
        text-align: center;
        margin: 2rem 0;
        position: relative;
        overflow: hidden;
    }
    
    .welcome-hero::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="grain" width="100" height="100" patternUnits="userSpaceOnUse"><circle cx="50" cy="50" r="1" fill="white" opacity="0.1"/></pattern></defs><rect width="100" height="100" fill="url(%23grain)"/></svg>');
        animation: grain 20s linear infinite;
        pointer-events: none;
    }
    
    @keyframes grain {
        0%, 100% { transform: translate(0, 0) }
        10% { transform: translate(-5%, -5%) }
        20% { transform: translate(-10%, 5%) }
        30% { transform: translate(5%, -10%) }
        40% { transform: translate(-5%, 15%) }
        50% { transform: translate(-10%, 5%) }
        60% { transform: translate(15%, 0%) }
        70% { transform: translate(0%, 10%) }
        80% { transform: translate(-15%, 0%) }
        90% { transform: translate(10%, 5%) }
    }
    </style>
    """, unsafe_allow_html=True)

def get_image_base64(image_path):
    """Convert image to base64 for embedding"""
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except:
        return None

def display_player_card(player, show_image=True, show_bid_button=False, user_cash=0):
    """Display enhanced player card with styling"""
    
    # Try to get player image
    player_images = {
        'messi': 'messi.jpeg',
        'ronaldo': 'ronaldo.jpg',
        'neymar': 'ney.jpg',
        'dembele': 'demb.jpg'
    }
    
    player_img = None
    player_name_lower = player['player_name'].lower()
    for key, img_file in player_images.items():
        if key in player_name_lower:
            if os.path.exists(img_file):
                player_img = img_file
            break
    
    # Create player card HTML
    card_html = f"""
    <div class="player-card">
        <div style="display: flex; align-items: center;">
    """
    
    if show_image and player_img:
        img_base64 = get_image_base64(player_img)
        if img_base64:
            card_html += f"""
            <img src="data:image/jpeg;base64,{img_base64}" class="player-image" />
            """
    
    card_html += f"""
        <div style="flex: 1; margin-left: 1rem;">
            <h3 style="margin: 0; color: #667eea;">{player['player_name']}</h3>
            <p style="margin: 0.5rem 0; color: #666;"><strong>Club:</strong> {player['club_name']}</p>
            <p style="margin: 0.5rem 0; color: #666;"><strong>Position:</strong> {player['positions']}</p>
            <p style="margin: 0.5rem 0; color: #666;"><strong>Rating:</strong> {player['overall_rating']}</p>
            <p style="margin: 0.5rem 0; color: #666;"><strong>Value:</strong> €{player['value_eur']:,.0f}</p>
        </div>
        </div>
    </div>
    """
    
    st.markdown(card_html, unsafe_allow_html=True)

def display_welcome_hero():
    """Display welcome hero section with branding"""
    # Get background image
    bg_image = get_image_base64('wallpaper.png')
    
    st.markdown(f"""
    <div style="
        background: url('data:image/jpeg;base64,{bg_image}') center/cover;
        height: 400px;
        border-radius: 20px;
        margin: 2rem 0;
        box-shadow: 0 8px 25px rgba(0,0,0,0.1);
        position: relative;
        overflow: hidden;
    ">
    </div>
    """, unsafe_allow_html=True)
    
    # Add branding section outside hero
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        margin: 2rem 0;
        color: white;
        text-align: center;
    ">
        <div style="display: flex; justify-content: center; align-items: center; gap: 3rem; flex-wrap: wrap;">
            <div style="display: flex; align-items: center; gap: 0.5rem;">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515a.074.074 0 0 0-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 0 0-5.487 0a12.64 12.64 0 0 0-.617-1.25a.077.077 0 0 0-.079-.037A19.736 19.736 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 0 0 .031.057a19.9 19.9 0 0 0 5.993 3.03a.078.078 0 0 0 .084-.028a14.09 14.09 0 0 0 1.226-1.994a.076.076 0 0 0-.041-.106a13.107 13.107 0 0 1-1.872-.892a.077.077 0 0 1-.008-.128a10.2 10.2 0 0 0 .372-.292a.074.074 0 0 1 .077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 0 1 .078.01c.12.098.246.198.373.292a.077.077 0 0 1-.006.127a12.299 12.299 0 0 1-1.873.892a.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 .084.028a19.839 19.839 0 0 0 6.002-3.03a.077.077 0 0 0 .032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.03zM8.02 15.33c-1.183 0-2.157-1.085-2.157-2.419c0-1.333.956-2.419 2.157-2.419c1.21 0 2.176 1.096 2.157 2.42c0 1.333-.956 2.418-2.157 2.418zm7.975 0c-1.183 0-2.157-1.085-2.157-2.419c0-1.333.955-2.419 2.157-2.419c1.21 0 2.176 1.096 2.157 2.42c0 1.333-.946 2.418-2.157 2.418z"/>
                </svg>
                <div>
                    <div style="font-weight: bold; font-size: 1.1rem;">Join Our Community</div>
                    <div style="opacity: 0.9;">The beautiful game</div>
                </div>
            </div>
            <div style="display: flex; align-items: center; gap: 0.5rem;">
                <div>
                    <div style="font-weight: bold; font-size: 1.1rem;">Contact Me</div>
                    <div style="opacity: 0.9;">yurinova0509@gmail.com</div>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def display_dashboard_metrics(metrics):
    """Display enhanced dashboard metrics"""
    
    cols = st.columns(len(metrics))
    
    for i, (title, value, icon) in enumerate(metrics):
        with cols[i]:
            metric_html = f"""
            <div class="dashboard-metric">
                <div style="font-size: 2rem; margin-bottom: 0.5rem;">{icon}</div>
                <div style="font-size: 2rem; font-weight: bold; margin-bottom: 0.5rem;">{value}</div>
                <div style="font-size: 1rem; opacity: 0.9;">{title}</div>
            </div>
            """
            st.markdown(metric_html, unsafe_allow_html=True)

def display_transfer_bid_card(bid, status="pending"):
    """Display enhanced transfer bid card"""
    
    status_class = f"transfer-status-{status}"
    status_colors = {
        "pending": "#ffc107",
        "approved": "#28a745", 
        "rejected": "#dc3545"
    }
    
    bid_html = f"""
    <div class="transfer-bid">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <h4 style="margin: 0; color: #333;">{bid.get('player_name', 'Unknown Player')}</h4>
                <p style="margin: 0.5rem 0; color: #666;">
                    <strong>From:</strong> {bid.get('current_club', 'Unknown')} → 
                    <strong>To:</strong> {bid.get('bidding_club', 'Unknown')}
                </p>
                <p style="margin: 0.5rem 0; color: #666;">
                    <strong>Bid Amount:</strong> €{bid.get('bid_amount', 0):,.0f}
                </p>
            </div>
            <div>
                <span class="{status_class}" style="background-color: {status_colors.get(status, '#666')}; color: white;">
                    {status.upper()}
                </span>
            </div>
        </div>
    </div>
    """
    
    st.markdown(bid_html, unsafe_allow_html=True)

def display_success_message(message, icon="✅"):
    """Display enhanced success message"""
    
    success_html = f"""
    <div style="
        background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
        border-left: 5px solid #28a745;
        border-radius: 10px;
        padding: 1rem 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 2px 10px rgba(40, 167, 69, 0.2);
    ">
        <div style="display: flex; align-items: center; gap: 0.5rem;">
            <span style="font-size: 1.2rem;">{icon}</span>
            <span style="color: #155724; font-weight: 500;">{message}</span>
        </div>
    </div>
    """
    
    st.markdown(success_html, unsafe_allow_html=True)

def display_tab_background(tab_name, title=None):
    """Display themed background images for different tabs"""
    # Get background image based on tab
    if tab_name == 'transfers':
        bg_image = get_image_base64('demb.jpg')  # Transfer-related image
    elif tab_name == 'squad':
        bg_image = get_image_base64('intermilan.webp')  # Squad/team image - Inter Milan
    elif tab_name == 'admin':
        bg_image = get_image_base64('chamd.png')  # Admin/management image
    elif tab_name == 'dashboard':
        bg_image = get_image_base64('lamine.jpg')  # Dashboard/overview image - Lamine
    elif tab_name == 'players':
        bg_image = get_image_base64('ronaldo.jpg')  # Player search image
    else:
        bg_image = get_image_base64('wallpaper.png')  # Default background
    
    # Create background with title - using lighter overlay for more visible backgrounds
    if title:
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, rgba(255,255,255,0.7) 0%, rgba(248,249,250,0.7) 100%), 
                       url('data:image/jpeg;base64,{bg_image}') center/cover;
            background-blend-mode: lighten;
            padding: 2rem;
            border-radius: 15px;
            margin-bottom: 2rem;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        ">
            <h2 style="color: #2c3e50; margin: 0; font-size: 2.2rem; text-align: center;">
                {title}
            </h2>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, rgba(255,255,255,0.7) 0%, rgba(248,249,250,0.7) 100%), 
                       url('data:image/jpeg;base64,{bg_image}') center/cover;
            background-blend-mode: lighten;
            padding: 1rem;
            border-radius: 15px;
            margin-bottom: 2rem;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        ">
        </div>
        """, unsafe_allow_html=True)

def display_enhanced_table(df, title=None, max_height=400):
    """Display attractive styled table instead of basic dataframe"""
    
    if df.empty:
        st.info(f"No {title.lower() if title else 'data'} available")
        return
    
    if title:
        st.markdown(f"<h3 style='color: #2c3e50; margin-bottom: 1rem;'>{title}</h3>", unsafe_allow_html=True)
    
    # Use Streamlit's native dataframe with custom styling
    st.markdown("""
    <style>
    .enhanced-table {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        border-radius: 15px;
        padding: 1.5rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        margin: 1rem 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Format the dataframe for better display
    display_df = df.copy()
    
    # Format currency columns
    for col in display_df.columns:
        if 'amount' in col.lower() or 'value' in col.lower() or 'cash' in col.lower():
            display_df[col] = display_df[col].apply(lambda x: f"€{x:,.0f}" if pd.notna(x) and str(x).replace(',', '').replace('.', '').isdigit() else x)
    
    # Display with enhanced styling
    st.markdown('<div class="enhanced-table">', unsafe_allow_html=True)
    st.dataframe(display_df, use_container_width=True, height=max_height)
    st.markdown('</div>', unsafe_allow_html=True)

def display_player_stats_card(player_data):
    """Display enhanced player statistics card with background"""
    
    # Use a light background from available images
    bg_base64 = get_image_base64('city.jpg')
    
    card_html = f"""
    <div style="
        background: linear-gradient(rgba(255,255,255,0.9), rgba(255,255,255,0.9)), 
                   url('data:image/jpeg;base64,{bg_base64}') center/cover;
        border-radius: 15px;
        padding: 2rem;
        margin: 1rem 0;
        box-shadow: 0 8px 25px rgba(0,0,0,0.15);
        border: 1px solid rgba(0,0,0,0.1);
    ">
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1.5rem;">
            <div style="text-align: center;">
                <h3 style="color: #2c3e50; margin-bottom: 0.5rem;">{player_data.get('player_name', 'Unknown Player')}</h3>
                <p style="color: #6c757d; margin: 0;">{player_data.get('club_name', 'Unknown Club')}</p>
            </div>
            <div style="text-align: center;">
                <div style="background: #28a745; color: white; padding: 0.5rem 1rem; border-radius: 20px; display: inline-block; font-weight: bold;">
                    Rating: {player_data.get('overall_rating', 'N/A')}
                </div>
            </div>
            <div style="text-align: center;">
                <div style="color: #2c3e50; font-size: 1.2rem; font-weight: bold;">
                    €{player_data.get('value_eur', 0):,}
                </div>
                <p style="color: #6c757d; margin: 0; font-size: 0.9rem;">Market Value</p>
            </div>
        </div>
    </div>
    """
    
    st.markdown(card_html, unsafe_allow_html=True)
