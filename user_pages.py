import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import base64
from PIL import Image
import io
from ui_components import display_tab_background, display_enhanced_table, display_player_stats_card

def show_search_players():
    # Add background image for players tab
    display_tab_background('players', 'Player Search')
    
    conn = sqlite3.connect('match_simulator.db')
    
    # Search filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        search_name = st.text_input("Player Name")
    
    with col2:
        # Get unique clubs for filter
        clubs_df = pd.read_sql_query('''
            SELECT DISTINCT club_name 
            FROM players 
            WHERE club_name IS NOT NULL AND club_name != ''
            ORDER BY club_name
        ''', conn)
        club_filter = st.selectbox("Club", ["All"] + clubs_df['club_name'].tolist())
    
    with col3:
        position_filter = st.text_input("Position")
    
    # Build query
    query = "SELECT * FROM players WHERE 1=1"
    params = []
    
    if search_name:
        query += " AND player_name LIKE ?"
        params.append(f"%{search_name}%")
    
    if club_filter != "All":
        query += " AND club_name = ?"
        params.append(club_filter)
    
    if position_filter:
        query += " AND positions LIKE ?"
        params.append(f"%{position_filter}%")
    
    query += " ORDER BY overall_rating DESC LIMIT 100"
    
    # Execute search
    players_df = pd.read_sql_query(query, conn, params=params)
    
    if players_df.empty:
        st.info("No players found matching your criteria.")
    else:
        st.subheader(f"Search Results ({len(players_df)} players)")
        
        # Display enhanced table instead of basic dataframe
        display_enhanced_table(players_df, "Player Search Results")
    
    conn.close()

def show_check_squad():
    # Add background image for squad tab
    display_tab_background('squad', 'Squad Management')
    
    user = st.session_state.user
    
    if not user['club_name']:
        st.warning("You haven't been assigned a club yet. Please wait for admin approval.")
        return
    
    conn = sqlite3.connect('match_simulator.db')
    
    # Get players from user's club
    squad_df = pd.read_sql_query('''
        SELECT player_name, positions, age, nationality, overall_rating, 
               potential, value_eur, wage_eur
        FROM players
        WHERE club_name = ?
        ORDER BY overall_rating DESC
    ''', conn, params=(user['club_name'],))
    
    if squad_df.empty:
        st.info(f"No players found for {user['club_name']}. Contact admin if this seems incorrect.")
        conn.close()
        return
    
    st.subheader(f"{user['club_name']} Squad ({len(squad_df)} players)")
    
    # Squad statistics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        avg_rating = squad_df['overall_rating'].mean()
        st.metric("Average Rating", f"{avg_rating:.1f}")
    
    with col2:
        total_value = squad_df['value_eur'].sum()
        st.metric("Total Squad Value", f"€{total_value:,.0f}")
    
    with col3:
        top_player = squad_df.loc[squad_df['overall_rating'].idxmax()]
        st.metric("Best Player", f"{top_player['player_name']} ({top_player['overall_rating']})")
    
    with col4:
        st.metric("Squad Size", len(squad_df))
    
    # Display enhanced squad table
    display_enhanced_table(squad_df, f"{user['club_name']} Squad")
    
    conn.close()

def show_upload_squad():
    st.title("📤 Upload Squad")
    
    user = st.session_state.user
    
    if not user['club_name']:
        st.warning("You haven't been assigned a club yet. Please wait for admin approval.")
        return
    
    conn = sqlite3.connect('match_simulator.db')
    
    # Upload form
    st.subheader("Upload Your Squad Image")
    
    with st.form("upload_squad"):
        uploaded_file = st.file_uploader("Choose squad image", type=['png', 'jpg', 'jpeg'])
        description = st.text_area("Description", placeholder="Describe your squad formation, tactics, etc.")
        
        if st.form_submit_button("Upload Squad"):
            if uploaded_file and description:
                # Convert image to bytes
                image_bytes = uploaded_file.read()
                
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO squad_uploads (user_id, image_data, description)
                    VALUES (?, ?, ?)
                ''', (user['id'], image_bytes, description))
                conn.commit()
                
                st.success("Squad uploaded successfully! Waiting for admin approval.")
            else:
                st.error("Please upload an image and provide a description.")
    
    # Show previous uploads
    st.subheader("Your Previous Uploads")
    
    uploads_df = pd.read_sql_query('''
        SELECT id, description, status, uploaded_at, approved_at
        FROM squad_uploads
        WHERE user_id = ?
        ORDER BY uploaded_at DESC
    ''', conn, params=(user['id'],))
    
    if uploads_df.empty:
        st.info("No previous uploads found.")
    else:
        for _, upload in uploads_df.iterrows():
            status_color = {"pending": "🟡", "approved": "🟢", "rejected": "🔴"}
            
            with st.expander(f"{status_color.get(upload['status'], '⚪')} {upload['status'].upper()} - {upload['uploaded_at']}"):
                st.write(f"**Description:** {upload['description']}")
                st.write(f"**Status:** {upload['status']}")
                st.write(f"**Uploaded:** {upload['uploaded_at']}")
                if upload['approved_at']:
                    st.write(f"**Approved:** {upload['approved_at']}")
                
                # Display image
                cursor = conn.cursor()
                cursor.execute('SELECT image_data FROM squad_uploads WHERE id = ?', (upload['id'],))
                image_data = cursor.fetchone()[0]
                
                if image_data:
                    try:
                        image = Image.open(io.BytesIO(image_data))
                        st.image(image, caption="Squad Image", width=300)
                    except:
                        st.error("Could not display image")
    
    conn.close()

def show_transfer_bid():
    st.markdown("""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 2rem; border-radius: 15px; color: white; text-align: center; margin-bottom: 2rem;">
        <h1>🔄 Transfer Market</h1>
        <p>Discover and bid on the world's best players</p>
    </div>
    """, unsafe_allow_html=True)
    
    user = st.session_state.user
    
    if not user['club_name']:
        st.warning("You haven't been assigned a club yet. Please wait for admin approval.")
        return
    
    conn = sqlite3.connect('match_simulator.db')
    
    # Enhanced layout with tabs
    tab1, tab2, tab3 = st.tabs(["🔍 Browse All Players", "📊 Your Transfer Activity", "📨 Incoming Bids"])
    
    with tab1:
        st.subheader("Available Players for Transfer")
        
        # Enhanced search filters
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            search_name = st.text_input("🔍 Search Player Name")
        
        with col2:
            # Get all clubs except user's club
            clubs_df = pd.read_sql_query('''
                SELECT DISTINCT club_name 
                FROM players 
                WHERE club_name IS NOT NULL AND club_name != '' AND club_name != ?
                ORDER BY club_name
            ''', conn, params=(user['club_name'],))
            club_filter = st.selectbox("🏟️ Filter by Club", ["All Clubs"] + clubs_df['club_name'].tolist())
        
        with col3:
            position_filter = st.selectbox("⚽ Position", ["All Positions", "GK", "CB", "LB", "RB", "CDM", "CM", "CAM", "LW", "RW", "ST"])
        
        with col4:
            rating_filter = st.selectbox("⭐ Min Rating", ["Any Rating", "80+", "85+", "90+", "95+"])
        
        # Build comprehensive query
        query = '''
            SELECT player_id, player_name, positions, club_name, age, nationality,
                   overall_rating, potential, value_eur, wage_eur
            FROM players
            WHERE club_name != ? AND club_name IS NOT NULL AND club_name != ''
        '''
        params = [user['club_name']]
        
        if search_name:
            query += " AND player_name LIKE ?"
            params.append(f"%{search_name}%")
        
        if club_filter != "All Clubs":
            query += " AND club_name = ?"
            params.append(club_filter)
        
        if position_filter != "All Positions":
            query += " AND positions LIKE ?"
            params.append(f"%{position_filter}%")
        
        if rating_filter != "Any Rating":
            min_rating = int(rating_filter.replace("+", ""))
            query += " AND overall_rating >= ?"
            params.append(min_rating)
        
        query += " ORDER BY overall_rating DESC LIMIT 50"
        
        # Execute search
        players_df = pd.read_sql_query(query, conn, params=params)
        
        if not players_df.empty:
            st.subheader(f"Available Players ({len(players_df)} found)")
            
            # Display summary stats
            col1, col2, col3 = st.columns(3)
            with col1:
                avg_rating = players_df['overall_rating'].mean()
                st.metric("Average Rating", f"{avg_rating:.1f}")
            with col2:
                total_value = players_df['value_eur'].sum()
                st.metric("Total Market Value", f"€{total_value:,.0f}")
            with col3:
                unique_clubs = players_df['club_name'].nunique()
                st.metric("Clubs Represented", unique_clubs)
            
            st.markdown("---")
            
            # Enhanced player cards with professional styling
            for _, player in players_df.iterrows():
                # Create professional player card
                st.markdown(f"""
                <div style="
                    background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                    border-radius: 15px;
                    padding: 1.5rem;
                    margin: 1rem 0;
                    border-left: 5px solid #4CAF50;
                    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                ">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <h3 style="margin: 0; color: #2c3e50; font-size: 1.4rem;">{player['player_name']}</h3>
                            <p style="margin: 0.5rem 0; color: #7f8c8d; font-size: 1rem;">
                                {player['positions']} • {player['club_name']} • Age {player['age']}
                            </p>
                        </div>
                        <div style="text-align: right;">
                            <div style="background: #3498db; color: white; padding: 0.5rem 1rem; border-radius: 25px; font-weight: bold;">
                                {player['overall_rating']} OVR
                            </div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Bidding form
                with st.expander(f"💰 Make Bid for {player['player_name']}", expanded=False):
                    col_a, col_b = st.columns([2, 1])
                    
                    with col_a:
                        st.markdown(f"""
                        **Player Details:**
                        - **Position:** {player['positions']}
                        - **Age:** {player['age']} years old
                        - **Nationality:** {player.get('nationality', 'Unknown')}
                        - **Current Club:** {player['club_name']}
                        - **Market Value:** €{player['value_eur']:,.0f}
                        - **Potential:** {player.get('potential', 'N/A')}
                        - **Weekly Wage:** €{player.get('wage_eur', 0):,.0f}
                        """)
                    
                    with col_b:
                        with st.form(f"bid_form_{player['player_id']}"):
                            st.markdown("**Submit Your Bid**")
                            bid_amount = st.number_input(
                                "Bid Amount (€)", 
                                value=max(int(player['value_eur']), 10000), 
                                step=10000,
                                min_value=10000,
                                help="Minimum bid: €10,000",
                                key=f"bid_{player['player_id']}"
                            )
                            description = st.text_area(
                                "Bid Description", 
                                placeholder="Why do you want this player? What's your strategy?",
                                key=f"desc_{player['player_id']}"
                            )
                            
                            if st.form_submit_button("Submit Bid", type="primary"):
                                if not description.strip():
                                    st.error("Please provide a bid description!")
                                elif bid_amount <= 0:
                                    st.error("Bid amount must be greater than 0!")
                                else:
                                    cursor = conn.cursor()
                                    cursor.execute('''
                                        INSERT INTO transfer_bids 
                                        (user_id, player_id, bid_amount, description, status)
                                        VALUES (?, ?, ?, ?, 'pending')
                                    ''', (user['id'], player['player_id'], bid_amount, description))
                                    conn.commit()
                                    
                                    st.success(f"✅ Bid submitted for {player['player_name']}!")
                                    st.info(f"💰 Bid Amount: €{bid_amount:,}")
                                    st.info("💡 Money will only be deducted when approved by admin.")
                                    st.balloons()
    
    with tab2:
        st.subheader("📊 Your Transfer Activity")
        
        # Get user's transfer bids
        bids_df = pd.read_sql_query('''
            SELECT tb.*, p.player_name, p.club_name, p.overall_rating, p.positions
            FROM transfer_bids tb
            JOIN players p ON tb.player_id = p.player_id
            WHERE tb.user_id = ?
            ORDER BY tb.created_at DESC
        ''', conn, params=(user['id'],))
        
        if bids_df.empty:
            st.info("No transfer bids yet.")
        if not bids_df.empty:
            # Display summary metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                total_bids = len(bids_df)
                st.metric("Total Bids", total_bids)
            with col2:
                pending_bids = len(bids_df[bids_df['status'] == 'pending'])
                st.metric("Pending Bids", pending_bids)
            with col3:
                total_value = bids_df['bid_amount'].sum()
                st.metric("Total Bid Value", f"€{total_value:,.0f}")
            
            st.markdown("---")
            
            # Display each bid with enhanced styling
            for _, bid in bids_df.iterrows():
                status_color = "#2ecc71" if bid['status'] == 'approved' else "#f39c12" if bid['status'] == 'pending' else "#e74c3c"
                status_icon = "✅" if bid['status'] == 'approved' else "⏳" if bid['status'] == 'pending' else "❌"
                
                st.markdown(f"""
                <div style="
                    background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
                    border-left: 5px solid {status_color};
                    border-radius: 10px;
                    padding: 1.5rem;
                    margin: 1rem 0;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                ">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <h4 style="margin: 0; color: #2c3e50;">{status_icon} {bid['player_name']}</h4>
                            <p style="margin: 0.5rem 0; color: #7f8c8d;">
                                {bid['positions']} • {bid['club_name']} • Rating: {bid['overall_rating']}
                            </p>
                            <p style="margin: 0.5rem 0; color: #34495e; font-style: italic;">
                                "{bid['description'][:100]}{'...' if len(bid['description']) > 100 else ''}"
                            </p>
                        </div>
                        <div style="text-align: right;">
                            <div style="background: {status_color}; color: white; padding: 0.5rem 1rem; border-radius: 20px; font-weight: bold; margin-bottom: 0.5rem;">
                                €{bid['bid_amount']:,}
                            </div>
                            <small style="color: #7f8c8d;">{bid['status'].title()}</small>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="
                text-align: center;
                padding: 3rem;
                background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
                border-radius: 15px;
                margin: 2rem 0;
            ">
                <h3 style="color: #6c757d; margin-bottom: 1rem;">🎯 No Transfer Bids Yet</h3>
                <p style="color: #6c757d; font-size: 1.1rem;">Start building your dream team by bidding on players!</p>
            </div>
            """, unsafe_allow_html=True)
    
    with tab3:
        st.subheader("📨 Incoming Transfer Bids")
        st.markdown("Players from your club that others want to buy")
        
        # Get incoming bids for user's club players
        incoming_bids_df = pd.read_sql_query('''
            SELECT tb.*, p.player_name, p.club_name, p.overall_rating, p.positions, p.value_eur,
                   u.username as bidder_name, u.club_name as bidder_club
            FROM transfer_bids tb
            JOIN players p ON tb.player_id = p.player_id
            JOIN users u ON tb.user_id = u.id
            WHERE p.club_name = ? AND tb.status = 'pending'
            ORDER BY tb.created_at DESC
        ''', conn, params=(user['club_name'],))
        
        if not incoming_bids_df.empty:
            st.success(f"🎉 You have {len(incoming_bids_df)} incoming bid(s) for your players!")
            
            # Display summary metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                total_incoming = len(incoming_bids_df)
                st.metric("Incoming Bids", total_incoming)
            with col2:
                total_potential = incoming_bids_df['bid_amount'].sum()
                st.metric("Total Potential Income", f"€{total_potential:,.0f}")
            with col3:
                avg_bid = incoming_bids_df['bid_amount'].mean()
                st.metric("Average Bid", f"€{avg_bid:,.0f}")
            
            st.markdown("---")
            
            # Display each incoming bid with accept/reject options
            for _, bid in incoming_bids_df.iterrows():
                st.markdown(f"""
                <div style="
                    background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%);
                    border-left: 5px solid #f39c12;
                    border-radius: 15px;
                    padding: 2rem;
                    margin: 1.5rem 0;
                    box-shadow: 0 4px 20px rgba(0,0,0,0.1);
                ">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                        <div>
                            <h3 style="margin: 0; color: #2c3e50; font-size: 1.5rem;">🔥 {bid['player_name']}</h3>
                            <p style="margin: 0.5rem 0; color: #7f8c8d; font-size: 1.1rem;">
                                {bid['positions']} • Rating: {bid['overall_rating']} • Value: €{bid['value_eur']:,}
                            </p>
                        </div>
                        <div style="text-align: right;">
                            <div style="background: #e74c3c; color: white; padding: 0.8rem 1.5rem; border-radius: 25px; font-weight: bold; font-size: 1.2rem;">
                                €{bid['bid_amount']:,}
                            </div>
                        </div>
                    </div>
                    <div style="background: rgba(255,255,255,0.7); padding: 1rem; border-radius: 10px; margin: 1rem 0;">
                        <h4 style="margin: 0 0 0.5rem 0; color: #2c3e50;">💬 Bidder's Message:</h4>
                        <p style="margin: 0; color: #34495e; font-style: italic; font-size: 1.1rem;">
                            "{bid['description']}"
                        </p>
                        <p style="margin: 0.5rem 0 0 0; color: #7f8c8d; font-size: 0.9rem;">
                            — {bid['bidder_name']} ({bid['bidder_club']})
                        </p>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Accept/Reject buttons
                col_accept, col_reject, col_info = st.columns([1, 1, 2])
                
                with col_accept:
                    if st.button(f"✅ Accept Bid", key=f"accept_{bid['id']}", type="primary"):
                        cursor = conn.cursor()
                        
                        # Get bidder information for the transfer
                        cursor.execute('''
                            SELECT u.club_name, u.cash 
                            FROM users u 
                            WHERE u.id = ?
                        ''', (bid['user_id'],))
                        bidder_info = cursor.fetchone()
                        
                        if bidder_info and bidder_info[1] >= bid['bid_amount']:
                            # Update transfer status to seller_accepted (waiting for admin)
                            cursor.execute('''
                                UPDATE transfer_bids 
                                SET status = 'seller_accepted', seller_response_date = datetime('now')
                                WHERE id = ?
                            ''', (bid['id'],))
                            
                            conn.commit()
                            st.success(f"✅ You accepted the bid for {bid['player_name']}!")
                            st.info(f"⏳ Status: Accepted and waiting for admin approval")
                            st.info(f"💰 You will receive €{bid['bid_amount']:,} once admin confirms the transfer")
                            st.balloons()
                            st.rerun()
                        else:
                            st.error(f"❌ Transfer failed! Bidder has insufficient funds.")
                            # Update bid status to failed
                            cursor.execute('''
                                UPDATE transfer_bids 
                                SET status = 'failed_insufficient_funds', seller_response_date = datetime('now')
                                WHERE id = ?
                            ''', (bid['id'],))
                            conn.commit()
                            st.rerun()
                
                with col_reject:
                    if st.button(f"❌ Reject Bid", key=f"reject_{bid['id']}"):
                        cursor = conn.cursor()
                        cursor.execute('''
                            UPDATE transfer_bids 
                            SET status = 'seller_rejected', seller_response_date = datetime('now')
                            WHERE id = ?
                        ''', (bid['id'],))
                        conn.commit()
                        st.error(f"❌ You rejected the bid for {bid['player_name']}.")
                        st.rerun()
                
                with col_info:
                    profit_loss = bid['bid_amount'] - bid['value_eur']
                    if profit_loss > 0:
                        st.success(f"💰 Profit: €{profit_loss:,} above market value")
                    elif profit_loss < 0:
                        st.warning(f"📉 Loss: €{abs(profit_loss):,} below market value")
                    else:
                        st.info("🎯 Exact market value bid")
                
                st.markdown("---")
        else:
            st.markdown("""
            <div style="
                text-align: center;
                padding: 3rem;
                background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
                border-radius: 15px;
                margin: 2rem 0;
            ">
                <h3 style="color: #6c757d; margin-bottom: 1rem;">📨 No Incoming Bids</h3>
                <p style="color: #6c757d; font-size: 1.1rem;">No one has made bids for your players yet.</p>
                <p style="color: #6c757d;">Your players must be performing well to attract interest!</p>
            </div>
            """, unsafe_allow_html=True)
    
    conn.close()

def show_balance_inventory():
    st.title("💰 Balance & Inventory")
    
    user = st.session_state.user
    conn = sqlite3.connect('match_simulator.db')
    
    # Current balance
    st.subheader("Current Balance")
    st.metric("Cash", f"€{user['cash']:,.2f}")
    
    # Recent transactions (simplified - could be expanded)
    st.subheader("Recent Activity")
    
    # Transfer bids
    bids_df = pd.read_sql_query('''
        SELECT p.player_name, tb.bid_amount, tb.status, tb.created_at
        FROM transfer_bids tb
        JOIN players p ON tb.player_id = p.player_id
        WHERE tb.user_id = ?
        ORDER BY tb.created_at DESC
        LIMIT 10
    ''', conn, params=(user['id'],))
    
    if not bids_df.empty:
        st.write("**Transfer Bids:**")
        for _, bid in bids_df.iterrows():
            status_icon = {"pending": "⏳", "approved": "✅", "rejected": "❌"}
            st.write(f"{status_icon.get(bid['status'], '❓')} {bid['player_name']} - €{bid['bid_amount']:,} ({bid['status']})")
    
    # Inventory
    st.subheader("Inventory")
    
    inventory_df = pd.read_sql_query('''
        SELECT item_name, quantity, received_at
        FROM user_inventory
        WHERE user_id = ?
        ORDER BY received_at DESC
    ''', conn, params=(user['id'],))
    
    if inventory_df.empty:
        st.info("No items in inventory.")
    else:
        st.dataframe(inventory_df, use_container_width=True)
    
    # Squad value
    if user['club_name']:
        st.subheader("Squad Value")
        
        squad_value_df = pd.read_sql_query('''
            SELECT COUNT(*) as player_count, 
                   AVG(overall_rating) as avg_rating,
                   SUM(value_eur) as total_value,
                   SUM(wage_eur) as total_wages
            FROM players
            WHERE club_name = ?
        ''', conn, params=(user['club_name'],))
        
        if not squad_value_df.empty and squad_value_df.iloc[0]['player_count'] > 0:
            squad_data = squad_value_df.iloc[0]
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Players", int(squad_data['player_count']))
            
            with col2:
                st.metric("Avg Rating", f"{squad_data['avg_rating']:.1f}")
            
            with col3:
                st.metric("Squad Value", f"€{squad_data['total_value']:,.0f}")
            
            with col4:
                st.metric("Annual Wages", f"€{squad_data['total_wages']:,.0f}")
    
    conn.close()
