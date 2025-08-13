import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import base64
from PIL import Image
import io
from ui_components import display_tab_background, display_enhanced_table, display_player_stats_card

def show_signup_page():
    st.title("📝 Sign Up")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.form("signup_form"):
            st.subheader("Create New Account")
            
            username = st.text_input("Username")
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            role = st.selectbox("Role", ["user", "admin"])
            
            # Show admin code input only if admin role is selected
            admin_code = ""
            if role == "admin":
                admin_code = st.text_input("Admin Code", type="password", help="Contact system administrator for the admin code")
            
            submitted = st.form_submit_button("Sign Up")
            
            if submitted:
                if not username or not password:
                    st.error("Username and password are required!")
                elif password != confirm_password:
                    st.error("Passwords don't match!")
                elif role == "admin" and admin_code != "1919":
                    st.error("Invalid admin code. Please enter the correct admin code.")
                else:
                    from app import create_user
                    if create_user(username, password, role, email):
                        st.success("Account created successfully! Please login.")
                        st.session_state.page = 'login'
                        st.rerun()
                    else:
                        st.error("Username already exists!")

def show_login_page():
    st.title("🔐 Login")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.form("login_form"):
            st.subheader("Login to Your Account")
            
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            
            submitted = st.form_submit_button("Login")
            
            if submitted:
                from app import authenticate_user
                user = authenticate_user(username, password)
                if user:
                    st.session_state.authenticated = True
                    st.session_state.user = user
                    st.success(f"Welcome back, {user['username']}!")
                    st.rerun()
                else:
                    st.error("Invalid username or password!")

def show_manage_users():
    # Add background image for admin tab
    display_tab_background('admin', 'User Management')
    
    conn = sqlite3.connect('match_simulator.db')
    
    # Get all users
    users_df = pd.read_sql_query('''
        SELECT id, username, role, email, club_name, cash, status, created_at
        FROM users
        ORDER BY created_at DESC
    ''', conn)
    
    if users_df.empty:
        st.info("No users found.")
        conn.close()
        return
    
    # Pending users section
    st.subheader("Pending User Approvals")
    pending_users = users_df[users_df['status'] == 'pending']
    
    if not pending_users.empty:
        for _, user in pending_users.iterrows():
            with st.expander(f"User: {user['username']} ({user['role']})"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Email:** {user['email']}")
                    st.write(f"**Role:** {user['role']}")
                    st.write(f"**Registered:** {user['created_at']}")
                
                with col2:
                    if user['role'] == 'user':
                        # Get available clubs
                        clubs_df = pd.read_sql_query('''
                            SELECT DISTINCT club_name 
                            FROM players 
                            WHERE club_name IS NOT NULL AND club_name != ''
                            ORDER BY club_name
                        ''', conn)
                        
                        club_name = st.selectbox(f"Assign Club to {user['username']}", 
                                               clubs_df['club_name'].tolist(), 
                                               key=f"club_{user['id']}")
                        starting_cash = st.number_input(f"Starting Cash for {user['username']}", 
                                                      value=100000000, step=1000000,
                                                      key=f"cash_{user['id']}")
                    
                    col_a, col_b = st.columns(2)
                    with col_a:
                        if st.button("✅ Approve", key=f"approve_{user['id']}"):
                            if user['role'] == 'user':
                                cursor = conn.cursor()
                                cursor.execute('''
                                    UPDATE users 
                                    SET status = 'approved', club_name = ?, cash = ?
                                    WHERE id = ?
                                ''', (club_name, starting_cash, user['id']))
                                conn.commit()
                            else:
                                cursor = conn.cursor()
                                cursor.execute('''
                                    UPDATE users 
                                    SET status = 'approved'
                                    WHERE id = ?
                                ''', (user['id'],))
                                conn.commit()
                            st.success(f"User {user['username']} approved!")
                            st.rerun()
                    
                    with col_b:
                        if st.button("❌ Reject", key=f"reject_{user['id']}"):
                            cursor = conn.cursor()
                            cursor.execute('DELETE FROM users WHERE id = ?', (user['id'],))
                            conn.commit()
                            st.success(f"User {user['username']} rejected!")
                            st.rerun()
    else:
        st.info("No pending users.")
    
    # All users section with enhanced table
    st.subheader("All Users")
    display_enhanced_table(users_df, "User Database")
    
    conn.close()

def show_distribute_items():
    st.title("💰 Distribute Items & Cash")
    
    conn = sqlite3.connect('match_simulator.db')
    
    # Get approved users
    users_df = pd.read_sql_query('''
        SELECT id, username, club_name, cash
        FROM users
        WHERE status = 'approved' AND role = 'user'
        ORDER BY username
    ''', conn)
    
    if users_df.empty:
        st.info("No approved users found.")
        conn.close()
        return
    
    tab1, tab2, tab3 = st.tabs(["💰 Distribute Cash", "🎁 Distribute Items", "👤 Manage Individual Users"])
    
    with tab1:
        st.subheader("Distribute Cash")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📤 To Selected Users")
            with st.form("distribute_cash_selected"):
                selected_users = st.multiselect("Select Users", 
                                              users_df['username'].tolist())
                cash_amount = st.number_input("Cash Amount (€)", value=1000000, step=100000, key="cash_selected")
                reason = st.text_input("Reason", key="reason_selected")
                
                if st.form_submit_button("Distribute to Selected"):
                    if selected_users and cash_amount > 0:
                        cursor = conn.cursor()
                        for username in selected_users:
                            cursor.execute('''
                                UPDATE users 
                                SET cash = cash + ?
                                WHERE username = ?
                            ''', (cash_amount, username))
                        conn.commit()
                        st.success(f"Distributed €{cash_amount:,} to {len(selected_users)} users!")
                        st.rerun()
                    else:
                        st.error("Please select users and enter a valid amount.")
        
        with col2:
            st.markdown("### 🌍 To All Users")
            with st.form("distribute_cash_all"):
                st.info(f"This will give cash to all {len(users_df)} approved users")
                cash_amount_all = st.number_input("Cash Amount (€)", value=1000000, step=100000, key="cash_all")
                reason_all = st.text_input("Reason", key="reason_all")
                confirm_all = st.checkbox("I confirm to give cash to ALL users")
                
                if st.form_submit_button("Distribute to ALL Users"):
                    if confirm_all and cash_amount_all > 0:
                        cursor = conn.cursor()
                        cursor.execute('''
                            UPDATE users 
                            SET cash = cash + ?
                            WHERE status = 'approved' AND role = 'user'
                        ''', (cash_amount_all,))
                        conn.commit()
                        st.success(f"Distributed €{cash_amount_all:,} to ALL {len(users_df)} users!")
                        st.rerun()
                    elif not confirm_all:
                        st.error("Please confirm to distribute to all users.")
                    else:
                        st.error("Please enter a valid amount.")
    
    with tab2:
        st.subheader("Distribute Items")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📤 To Selected Users")
            with st.form("distribute_items_selected"):
                selected_users_items = st.multiselect("Select Users", 
                                                    users_df['username'].tolist(),
                                                    key="item_users_selected")
                item_name = st.text_input("Item Name", key="item_name_selected")
                quantity = st.number_input("Quantity", value=1, min_value=1, key="quantity_selected")
                
                if st.form_submit_button("Distribute to Selected"):
                    if selected_users_items and item_name:
                        cursor = conn.cursor()
                        for username in selected_users_items:
                            user_id = users_df[users_df['username'] == username]['id'].iloc[0]
                            cursor.execute('''
                                INSERT INTO user_inventory (user_id, item_name, quantity)
                                VALUES (?, ?, ?)
                            ''', (user_id, item_name, quantity))
                        conn.commit()
                        st.success(f"Distributed {quantity} {item_name} to {len(selected_users_items)} users!")
                    else:
                        st.error("Please select users and enter item details.")
        
        with col2:
            st.markdown("### 🌍 To All Users")
            with st.form("distribute_items_all"):
                st.info(f"This will give items to all {len(users_df)} approved users")
                item_name_all = st.text_input("Item Name", key="item_name_all")
                quantity_all = st.number_input("Quantity", value=1, min_value=1, key="quantity_all")
                confirm_all_items = st.checkbox("I confirm to give items to ALL users")
                
                if st.form_submit_button("Distribute to ALL Users"):
                    if confirm_all_items and item_name_all:
                        cursor = conn.cursor()
                        for _, user in users_df.iterrows():
                            cursor.execute('''
                                INSERT INTO user_inventory (user_id, item_name, quantity)
                                VALUES (?, ?, ?)
                            ''', (user['id'], item_name_all, quantity_all))
                        conn.commit()
                        st.success(f"Distributed {quantity_all} {item_name_all} to ALL {len(users_df)} users!")
                    elif not confirm_all_items:
                        st.error("Please confirm to distribute to all users.")
                    else:
                        st.error("Please enter item details.")
    
    with tab3:
        st.subheader("Manage Individual Users")
        
        # Search/filter users
        search_user = st.text_input("🔍 Search User", placeholder="Type username to search...")
        
        # Filter users based on search
        if search_user:
            filtered_users = users_df[users_df['username'].str.contains(search_user, case=False)]
        else:
            filtered_users = users_df
        
        if filtered_users.empty:
            st.info("No users found matching your search.")
        else:
            st.markdown(f"### Found {len(filtered_users)} users")
            
            for _, user in filtered_users.iterrows():
                with st.expander(f"👤 {user['username']} - {user['club_name']} - €{user['cash']:,.2f}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("#### 💰 Cash Management")
                        
                        # Set specific cash amount
                        with st.form(f"set_cash_{user['id']}"):
                            new_cash = st.number_input(
                                "Set Cash Amount (€)", 
                                value=float(user['cash']), 
                                step=100000.0,
                                key=f"set_cash_input_{user['id']}"
                            )
                            
                            if st.form_submit_button("Set Cash Amount"):
                                cursor = conn.cursor()
                                cursor.execute('''
                                    UPDATE users 
                                    SET cash = ?
                                    WHERE id = ?
                                ''', (new_cash, user['id']))
                                conn.commit()
                                st.success(f"Set {user['username']}'s cash to €{new_cash:,.2f}!")
                                st.rerun()
                        
                        # Add/Remove cash
                        with st.form(f"adjust_cash_{user['id']}"):
                            cash_adjustment = st.number_input(
                                "Add/Remove Cash (€) - Use negative for removal", 
                                value=0, 
                                step=100000,
                                key=f"adjust_cash_input_{user['id']}"
                            )
                            
                            if st.form_submit_button("Adjust Cash"):
                                if cash_adjustment != 0:
                                    cursor = conn.cursor()
                                    cursor.execute('''
                                        UPDATE users 
                                        SET cash = cash + ?
                                        WHERE id = ?
                                    ''', (cash_adjustment, user['id']))
                                    conn.commit()
                                    action = "Added" if cash_adjustment > 0 else "Removed"
                                    st.success(f"{action} €{abs(cash_adjustment):,.2f} {('to' if cash_adjustment > 0 else 'from')} {user['username']}!")
                                    st.rerun()
                    
                    with col2:
                        st.markdown("#### 🎁 Give Items")
                        
                        with st.form(f"give_item_{user['id']}"):
                            item_name_individual = st.text_input(
                                "Item Name", 
                                key=f"item_name_{user['id']}"
                            )
                            quantity_individual = st.number_input(
                                "Quantity", 
                                value=1, 
                                min_value=1,
                                key=f"quantity_{user['id']}"
                            )
                            
                            if st.form_submit_button("Give Item"):
                                if item_name_individual:
                                    cursor = conn.cursor()
                                    cursor.execute('''
                                        INSERT INTO user_inventory (user_id, item_name, quantity)
                                        VALUES (?, ?, ?)
                                    ''', (user['id'], item_name_individual, quantity_individual))
                                    conn.commit()
                                    st.success(f"Gave {quantity_individual} {item_name_individual} to {user['username']}!")
                                else:
                                    st.error("Please enter an item name.")
                        
                        # Show user's current inventory
                        inventory_df = pd.read_sql_query('''
                            SELECT item_name, quantity, received_at
                            FROM user_inventory
                            WHERE user_id = ?
                            ORDER BY received_at DESC
                            LIMIT 5
                        ''', conn, params=(user['id'],))
                        
                        if not inventory_df.empty:
                            st.markdown("**Recent Items:**")
                            for _, item in inventory_df.iterrows():
                                st.write(f"• {item['item_name']} x{item['quantity']}")
                        else:
                            st.write("*No items in inventory*")
    
    # Current user balances summary
    st.markdown("---")
    st.subheader("📊 Current User Balances Summary")
    
    # Add summary statistics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_users = len(users_df)
        st.metric("Total Users", total_users)
    
    with col2:
        total_cash = users_df['cash'].sum()
        st.metric("Total Cash in System", f"€{total_cash:,.0f}")
    
    with col3:
        avg_cash = users_df['cash'].mean()
        st.metric("Average Cash per User", f"€{avg_cash:,.0f}")
    
    with col4:
        max_cash = users_df['cash'].max()
        st.metric("Highest Balance", f"€{max_cash:,.0f}")
    
    # Display user balances table
    display_df = users_df.copy()
    display_df['cash'] = display_df['cash'].apply(lambda x: f"€{x:,.2f}")
    st.dataframe(display_df, use_container_width=True)
    
    conn.close()

def show_manage_transfers():
    # Add background image for transfers tab
    display_tab_background('transfers', 'Transfer Management')
    
    st.markdown("**Transfer Workflow:** User bids → Seller accepts → Admin confirms → Transfer complete")
    
    conn = sqlite3.connect('match_simulator.db')
    
    # Create tabs for different transfer statuses
    tab1, tab2, tab3 = st.tabs(["⏳ Awaiting Admin Confirmation", "📋 All Transfer Activity", "📊 Transfer Statistics"])
    
    with tab1:
        st.subheader("Transfers Awaiting Admin Approval")
        st.info("These transfers have been accepted by sellers and need your final confirmation")
        
        # Get seller-accepted transfers awaiting admin approval
        pending_transfers_df = pd.read_sql_query('''
            SELECT tb.*, u.username as bidder, u.club_name as bidder_club, u.cash as bidder_cash,
                   p.player_name, p.club_name as current_club, p.overall_rating, p.value_eur
            FROM transfer_bids tb
            JOIN users u ON tb.user_id = u.id
            JOIN players p ON tb.player_id = p.player_id
            WHERE tb.status = 'seller_accepted'
            ORDER BY tb.seller_response_date DESC
        ''', conn)
        
        if not pending_transfers_df.empty:
            st.success(f"🎉 {len(pending_transfers_df)} transfer(s) awaiting your approval!")
            
            for _, transfer in pending_transfers_df.iterrows():
                # Enhanced transfer card for admin approval
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
                            <h3 style="margin: 0; color: #856404; font-size: 1.6rem;">⏳ {transfer['player_name']}</h3>
                            <p style="margin: 0.5rem 0; color: #6c757d; font-size: 1.1rem;">
                                Rating: {transfer['overall_rating']} • Value: €{transfer['value_eur']:,}
                            </p>
                            <p style="margin: 0.5rem 0; color: #495057; font-weight: bold;">
                                {transfer['current_club']} → {transfer['bidder_club']}
                            </p>
                        </div>
                        <div style="text-align: right;">
                            <div style="background: #f39c12; color: white; padding: 1rem 1.5rem; border-radius: 25px; font-weight: bold; font-size: 1.3rem;">
                                €{transfer['bid_amount']:,}
                            </div>
                            <small style="color: #6c757d;">AWAITING APPROVAL</small>
                        </div>
                    </div>
                    <div style="background: rgba(255,255,255,0.8); padding: 1rem; border-radius: 10px; margin: 1rem 0;">
                        <p style="margin: 0; color: #495057; font-style: italic;">
                            💬 "{transfer['description']}"
                        </p>
                        <p style="margin: 0.5rem 0 0 0; color: #6c757d; font-size: 0.9rem;">
                            — Bidder: {transfer['bidder']} ({transfer['bidder_club']}) - Balance: €{transfer['bidder_cash']:,}
                        </p>
                        <p style="margin: 0.5rem 0 0 0; color: #28a745; font-size: 0.9rem;">
                            ✅ Seller accepted: {transfer.get('seller_response_date', 'Recently')}
                        </p>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Admin confirmation buttons
                col_confirm, col_reject, col_info = st.columns([1, 1, 2])
                
                with col_confirm:
                    if st.button(f"✅ Approve Transfer", key=f"approve_{transfer['id']}", type="primary"):
                        if transfer['bidder_cash'] >= transfer['bid_amount']:
                            cursor = conn.cursor()
                            
                            # Transfer player to new club
                            cursor.execute('''
                                UPDATE players 
                                SET club_name = ?
                                WHERE player_id = ?
                            ''', (transfer['bidder_club'], transfer['player_id']))
                            
                            # Deduct money from bidder
                            cursor.execute('''
                                UPDATE users 
                                SET cash = cash - ?
                                WHERE id = ?
                            ''', (transfer['bid_amount'], transfer['user_id']))
                            
                            # Add money to seller
                            cursor.execute('''
                                SELECT id FROM users WHERE club_name = ?
                            ''', (transfer['current_club'],))
                            seller_result = cursor.fetchone()
                            if seller_result:
                                cursor.execute('''
                                    UPDATE users 
                                    SET cash = cash + ?
                                    WHERE id = ?
                                ''', (transfer['bid_amount'], seller_result[0]))
                            
                            # Update transfer status
                            cursor.execute('''
                                UPDATE transfer_bids 
                                SET status = 'approved', approved_at = CURRENT_TIMESTAMP
                                WHERE id = ?
                            ''', (transfer['id'],))
                            
                            conn.commit()
                            st.success(f"✅ Transfer approved! {transfer['player_name']} is now at {transfer['bidder_club']}")
                            st.rerun()
                        else:
                            st.error("❌ Bidder doesn't have enough cash!")
                
                with col_reject:
                    if st.button(f"❌ Reject Transfer", key=f"reject_{transfer['id']}"):
                        cursor = conn.cursor()
                        cursor.execute('''
                            UPDATE transfer_bids 
                            SET status = 'rejected', approved_at = CURRENT_TIMESTAMP
                            WHERE id = ?
                        ''', (transfer['id'],))
                        conn.commit()
                        st.success(f"❌ Transfer rejected!")
                        st.rerun()
                
                with col_info:
                    st.info(f"💡 Transfer ID: {transfer['id']} • Created: {transfer['created_at']}")
        
        else:
            st.info("🎉 No transfers awaiting approval!")
    
    with tab2:
        st.subheader("All Transfer Activity")
        
        # Get all transfer bids
        all_transfers_df = pd.read_sql_query('''
            SELECT tb.*, u.username as bidder, u.club_name as bidder_club,
                   p.player_name, p.club_name as current_club, p.overall_rating
            FROM transfer_bids tb
            JOIN users u ON tb.user_id = u.id
            JOIN players p ON tb.player_id = p.player_id
            ORDER BY tb.created_at DESC
        ''', conn)
        
        if not all_transfers_df.empty:
            # Display enhanced table
            display_enhanced_table(all_transfers_df, "Transfer History")
        else:
            st.info("No transfer activity found.")
    
    with tab3:
        st.subheader("Transfer Statistics")
        
        # Calculate statistics
        total_transfers = len(all_transfers_df) if 'all_transfers_df' in locals() else 0
        approved_transfers = len(all_transfers_df[all_transfers_df['status'] == 'approved']) if 'all_transfers_df' in locals() else 0
        pending_transfers = len(all_transfers_df[all_transfers_df['status'] == 'pending']) if 'all_transfers_df' in locals() else 0
        rejected_transfers = len(all_transfers_df[all_transfers_df['status'] == 'rejected']) if 'all_transfers_df' in locals() else 0
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Transfers", total_transfers)
        
        with col2:
            st.metric("Approved", approved_transfers)
        
        with col3:
            st.metric("Pending", pending_transfers)
        
        with col4:
            st.metric("Rejected", rejected_transfers)
    
    conn.close()

def show_transfer_logs():
    st.title("📊 Transfer Logs")
    
    conn = sqlite3.connect('match_simulator.db')
    
    # Get all transfer bids with status
    logs_df = pd.read_sql_query('''
        SELECT u.username, p.player_name, p.club_name, u.club_name as bidding_club,
               tb.bid_amount, tb.status, tb.created_at, tb.approved_at
        FROM transfer_bids tb
        JOIN users u ON tb.user_id = u.id
        JOIN players p ON tb.player_id = p.player_id
        ORDER BY tb.created_at DESC
    ''', conn)
    
    if logs_df.empty:
        st.info("No transfer logs found.")
        conn.close()
        return
    
    # Filter options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        status_filter = st.selectbox("Filter by Status", 
                                   ["All", "pending", "approved", "rejected"])
    
    with col2:
        user_filter = st.selectbox("Filter by User", 
                                 ["All"] + logs_df['username'].unique().tolist())
    
    # Apply filters
    filtered_df = logs_df.copy()
    
    if status_filter != "All":
        filtered_df = filtered_df[filtered_df['status'] == status_filter]
    
    if user_filter != "All":
        filtered_df = filtered_df[filtered_df['username'] == user_filter]
    
    # Display logs
    st.subheader(f"Transfer Logs ({len(filtered_df)} records)")
    
    # Format the dataframe for better display
    display_df = filtered_df.copy()
    display_df['bid_amount'] = display_df['bid_amount'].apply(lambda x: f"€{x:,.0f}")
    
    st.dataframe(display_df, use_container_width=True)
    
    # Statistics
    st.subheader("Transfer Statistics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Bids", len(logs_df))
    
    with col2:
        approved_bids = len(logs_df[logs_df['status'] == 'approved'])
        st.metric("Approved", approved_bids)
    
    with col3:
        pending_bids = len(logs_df[logs_df['status'] == 'pending'])
        st.metric("Pending", pending_bids)
    
    with col4:
        rejected_bids = len(logs_df[logs_df['status'] == 'rejected'])
        st.metric("Rejected", rejected_bids)
    
    conn.close()

def show_add_players():
    st.title("➕ Add Custom Players")
    
    conn = sqlite3.connect('match_simulator.db')
    
    # Load unique club names from CSV
    try:
        clubs_df = pd.read_csv('player-data-full.csv', usecols=['club_name'])
        unique_clubs = [''] + sorted(clubs_df['club_name'].dropna().unique().tolist())
    except Exception as e:
        st.error(f"Error loading club data: {e}")
        unique_clubs = []
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Add New Player")
        
        with st.form("add_player"):
            player_id = st.text_input("Player ID*")
            player_name = st.text_input("Player Name*")
            positions = st.text_input("Positions*")
            
            # Replace text input with dropdown for club selection
            if unique_clubs:
                club_name = st.selectbox("Club*", options=unique_clubs, format_func=lambda x: 'Select a club...' if x == '' else x)
            else:
                club_name = st.text_input("Club Name*")
                
            age = st.number_input("Age", min_value=15, max_value=50, value=25)
            nationality = st.text_input("Nationality")
            overall_rating = st.number_input("Overall Rating", min_value=1, max_value=99, value=75)
            potential = st.number_input("Potential", min_value=1, max_value=99, value=80)
            value_eur = st.number_input("Value (EUR)", min_value=0, value=1000000)
            wage_eur = st.number_input("Wage (EUR)", min_value=0, value=50000)
            
            if st.form_submit_button("Add Player"):
                if player_id and player_name and positions and club_name and club_name != 'Select a club...':
                    cursor = conn.cursor()
                    try:
                        cursor.execute('''
                            INSERT INTO players 
                            (player_id, player_name, positions, club_name, age, nationality,
                             overall_rating, potential, value_eur, wage_eur, is_custom)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, TRUE)
                        ''', (player_id, player_name, positions, club_name, age, nationality,
                              overall_rating, potential, value_eur, wage_eur))
                        conn.commit()
                        st.success(f"Player {player_name} added successfully to {club_name}!")
                    except sqlite3.IntegrityError:
                        st.error("Player ID already exists!")
                else:
                    st.error("Please fill in all required fields (marked with *)!")
    
    with col2:
        st.subheader("Recent Custom Players")
        
        custom_players_df = pd.read_sql_query('''
            SELECT player_name, positions, club_name, overall_rating, created_at
            FROM players
            WHERE is_custom = TRUE
            ORDER BY created_at DESC
            LIMIT 10
        ''', conn)
        
        if not custom_players_df.empty:
            st.dataframe(custom_players_df, use_container_width=True)
        else:
            st.info("No custom players added yet.")
    
    conn.close()

def show_user_squads():
    st.title("📋 User Squads")
    
    conn = sqlite3.connect('match_simulator.db')
    
    # Get all squad uploads
    uploads_df = pd.read_sql_query('''
        SELECT su.id, u.username, u.club_name, su.description, su.status, 
               su.uploaded_at, su.approved_at
        FROM squad_uploads su
        JOIN users u ON su.user_id = u.id
        ORDER BY su.uploaded_at DESC
    ''', conn)
    
    if uploads_df.empty:
        st.info("No squad uploads found.")
        conn.close()
        return
    
    # Filter by status
    status_filter = st.selectbox("Filter by Status", ["All", "pending", "approved", "rejected"])
    
    if status_filter != "All":
        filtered_uploads = uploads_df[uploads_df['status'] == status_filter]
    else:
        filtered_uploads = uploads_df
    
    st.subheader(f"Squad Uploads ({len(filtered_uploads)} records)")
    
    for _, upload in filtered_uploads.iterrows():
        with st.expander(f"{upload['username']} ({upload['club_name']}) - {upload['status'].upper()}"):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.write(f"**Club:** {upload['club_name']}")
                st.write(f"**Description:** {upload['description']}")
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
                        st.image(image, caption="Squad Image", width=400)
                    except:
                        st.error("Could not display image")
            
            with col2:
                if upload['status'] == 'pending':
                    col_a, col_b = st.columns(2)
                    
                    with col_a:
                        if st.button("✅ Approve", key=f"approve_squad_{upload['id']}"):
                            cursor = conn.cursor()
                            cursor.execute('''
                                UPDATE squad_uploads 
                                SET status = 'approved', approved_at = CURRENT_TIMESTAMP
                                WHERE id = ?
                            ''', (upload['id'],))
                            conn.commit()
                            st.success("Squad approved!")
                            st.rerun()
                    
                    with col_b:
                        if st.button("❌ Reject", key=f"reject_squad_{upload['id']}"):
                            cursor = conn.cursor()
                            cursor.execute('''
                                UPDATE squad_uploads 
                                SET status = 'rejected'
                                WHERE id = ?
                            ''', (upload['id'],))
                            conn.commit()
                            st.success("Squad rejected!")
                            st.rerun()
    
    conn.close()

def show_admin_home():
    from ui_components import display_dashboard_metrics, display_player_card
    
    # Enhanced title with styling
    st.markdown("""
    <div class="main-header">
        <h1>🏠 Admin Dashboard Home</h1>
        <p>Manage your football empire with complete control</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Load unique club names from CSV for dropdown
    try:
        clubs_df = pd.read_csv('player-data-full.csv', usecols=['club_name'])
        unique_clubs = sorted(clubs_df['club_name'].dropna().unique().tolist())
    except Exception as e:
        st.error(f"Error loading club data: {e}")
        unique_clubs = []
    
    conn = sqlite3.connect('match_simulator.db')
    
    # Dashboard statistics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_players = pd.read_sql_query('SELECT COUNT(*) as count FROM players', conn).iloc[0]['count']
        st.metric("Total Players", total_players)
    
    with col2:
        total_clubs = pd.read_sql_query('SELECT COUNT(DISTINCT club_name) as count FROM players WHERE club_name IS NOT NULL AND club_name != ""', conn).iloc[0]['count']
        st.metric("Total Clubs", total_clubs)
    
    with col3:
        pending_users = pd.read_sql_query('SELECT COUNT(*) as count FROM users WHERE status = "pending"', conn).iloc[0]['count']
        st.metric("Pending Users", pending_users)
    
    with col4:
        pending_transfers = pd.read_sql_query('SELECT COUNT(*) as count FROM transfer_bids WHERE status = "pending"', conn).iloc[0]['count']
        st.metric("Pending Transfers", pending_transfers)
    
    st.markdown("---")
    
    # Player search and management
    st.subheader("🔍 Player Database Management")
    
    # Search filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        search_name = st.text_input("Search by Player Name")
    
    with col2:
        clubs_df = pd.read_sql_query('''
            SELECT DISTINCT club_name 
            FROM players 
            WHERE club_name IS NOT NULL AND club_name != ''
            ORDER BY club_name
        ''', conn)
        club_filter = st.selectbox("Filter by Club", ["All"] + clubs_df['club_name'].tolist())
    
    with col3:
        position_filter = st.text_input("Filter by Position")
    
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
    
    query += " ORDER BY overall_rating DESC LIMIT 50"
    
    # Execute search
    players_df = pd.read_sql_query(query, conn, params=params)
    
    if players_df.empty:
        st.info("No players found matching your criteria.")
    else:
        st.subheader(f"Players ({len(players_df)} found)")
        
        # Display players with edit functionality
        for _, player in players_df.iterrows():
            with st.expander(f"{player['player_name']} ({player['club_name']}) - Rating: {player['overall_rating']}"):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.write(f"**Position:** {player['positions']}")
                    st.write(f"**Age:** {player['age']}")
                    st.write(f"**Nationality:** {player['nationality']}")
                    st.write(f"**Club:** {player['club_name']}")
                    if player['value_eur']:
                        st.write(f"**Value:** €{player['value_eur']:,.0f}")
                    if player['wage_eur']:
                        st.write(f"**Wage:** €{player['wage_eur']:,.0f}")
                
                with col2:
                    st.subheader("Edit Player Stats")
                    
                    with st.form(f"edit_player_{player['id']}"):
                        new_overall = st.number_input(
                            "Overall Rating", 
                            min_value=1, 
                            max_value=99, 
                            value=int(player['overall_rating']) if player['overall_rating'] else 75,
                            key=f"overall_{player['id']}"
                        )
                        
                        new_potential = st.number_input(
                            "Potential", 
                            min_value=1, 
                            max_value=99, 
                            value=int(player['potential']) if player['potential'] else 80,
                            key=f"potential_{player['id']}"
                        )
                        
                        if st.form_submit_button("Update Stats"):
                            cursor = conn.cursor()
                            cursor.execute('''
                                UPDATE players 
                                SET overall_rating = ?, potential = ?
                                WHERE id = ?
                            ''', (new_overall, new_potential, player['id']))
                            conn.commit()
                            st.success(f"Updated {player['player_name']}'s ratings!")
                            st.rerun()
    
    st.markdown("---")
    st.subheader("🔀 Change Player Club")
    
    with st.expander("Search and Update Player Club", expanded=True):
        search_query = st.text_input("Search player by name or ID")
        
        if search_query:
            # Search for players matching the query
            search_results = pd.read_sql_query('''
                SELECT id, player_id, player_name, club_name, overall_rating, positions
                FROM players
                WHERE player_name LIKE ? OR player_id = ?
                ORDER BY overall_rating DESC
                LIMIT 10
            ''', conn, params=(f'%{search_query}%', search_query))
            
            if not search_results.empty:
                st.write("Matching Players:")
                for _, player in search_results.iterrows():
                    with st.expander(f"{player['player_name']} ({player['club_name']} - {player['overall_rating']} OVR)"):
                        with st.form(key=f"update_club_{player['id']}"):
                            new_club = st.selectbox(
                                "New Club",
                                options=unique_clubs,
                                index=unique_clubs.index(player['club_name']) if player['club_name'] in unique_clubs else 0,
                                key=f"club_select_{player['id']}"
                            )
                            
                            if st.form_submit_button(f"Update {player['player_name']}'s Club"):
                                cursor = conn.cursor()
                                cursor.execute('''
                                    UPDATE players 
                                    SET club_name = ?
                                    WHERE id = ?
                                ''', (new_club, player['id']))
                                conn.commit()
                                st.success(f"Successfully moved {player['player_name']} to {new_club}!")
                                st.rerun()
            else:
                st.info("No players found matching your search.")
    
    conn.close()

def show_user_home():
    st.title("🏠 User Dashboard Home")
    
    user = st.session_state.user
    conn = sqlite3.connect('match_simulator.db')
    
    # User statistics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Your Cash", f"€{user['cash']:,.2f}")
    
    with col2:
        if user['club_name']:
            squad_count = pd.read_sql_query('SELECT COUNT(*) as count FROM players WHERE club_name = ?', conn, params=(user['club_name'],)).iloc[0]['count']
            st.metric("Squad Size", squad_count)
        else:
            st.metric("Squad Size", "N/A")
    
    with col3:
        pending_bids = pd.read_sql_query('SELECT COUNT(*) as count FROM transfer_bids WHERE user_id = ? AND status = "pending"', conn, params=(user['id'],)).iloc[0]['count']
        st.metric("Pending Bids", pending_bids)
    
    with col4:
        if user['club_name']:
            squad_value = pd.read_sql_query('SELECT SUM(value_eur) as total FROM players WHERE club_name = ?', conn, params=(user['club_name'],)).iloc[0]['total']
            st.metric("Squad Value", f"€{squad_value:,.0f}" if squad_value else "€0")
        else:
            st.metric("Squad Value", "N/A")
    
    st.markdown("---")
    
    # Player search
    st.subheader("🔍 Player Database")
    
    # Search filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        search_name = st.text_input("Search by Player Name")
    
    with col2:
        clubs_df = pd.read_sql_query('''
            SELECT DISTINCT club_name 
            FROM players 
            WHERE club_name IS NOT NULL AND club_name != ''
            ORDER BY club_name
        ''', conn)
        club_filter = st.selectbox("Filter by Club", ["All"] + clubs_df['club_name'].tolist())
    
    with col3:
        position_filter = st.text_input("Filter by Position")
    
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
    
    query += " ORDER BY overall_rating DESC LIMIT 50"
    
    # Execute search
    players_df = pd.read_sql_query(query, conn, params=params)
    
    if players_df.empty:
        st.info("No players found matching your criteria.")
    else:
        st.subheader(f"Players ({len(players_df)} found)")
        
        # Display players
        for _, player in players_df.iterrows():
            with st.expander(f"{player['player_name']} ({player['club_name']}) - Rating: {player['overall_rating']}"):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.write(f"**Position:** {player['positions']}")
                    st.write(f"**Age:** {player['age']}")
                    st.write(f"**Nationality:** {player['nationality']}")
                    st.write(f"**Club:** {player['club_name']}")
                    st.write(f"**Overall Rating:** {player['overall_rating']}")
                    st.write(f"**Potential:** {player['potential']}")
                    if player['value_eur']:
                        st.write(f"**Value:** €{player['value_eur']:,.0f}")
                    if player['wage_eur']:
                        st.write(f"**Wage:** €{player['wage_eur']:,.0f}")
                
                with col2:
                    if player['club_name'] != user['club_name']:
                        st.subheader("Make Transfer Bid")
                        
                        with st.form(f"bid_form_{player['id']}"):
                            bid_amount = st.number_input(
                                "Bid Amount (€)", 
                                value=int(player['value_eur']) if player['value_eur'] else 1000000, 
                                step=100000,
                                key=f"bid_{player['id']}"
                            )
                            description = st.text_area(
                                "Bid Description", 
                                key=f"desc_{player['id']}"
                            )
                            
                            if st.form_submit_button("Submit Bid"):
                                if bid_amount > 0 and bid_amount <= user['cash']:
                                    cursor = conn.cursor()
                                    cursor.execute('''
                                        INSERT INTO transfer_bids 
                                        (user_id, player_id, bid_amount, description)
                                        VALUES (?, ?, ?, ?)
                                    ''', (user['id'], player['player_id'], bid_amount, description))
                                    conn.commit()
                                    st.success(f"Bid submitted for {player['player_name']}!")
                                elif bid_amount > user['cash']:
                                    st.error("Insufficient funds!")
                                else:
                                    st.error("Please enter a valid bid amount!")
                    else:
                        st.info("This player is already in your squad!")
    
    conn.close()
