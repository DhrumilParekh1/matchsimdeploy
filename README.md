# Match Simulator App (2025 Server)

A comprehensive football management application built with Streamlit that allows users to manage teams, make transfers, and interact with a complete player database.

## Features

### For Users
- 🔍 **Search Players**: Browse and search through thousands of players
- 👥 **Check Squad**: View your assigned club's complete squad with statistics
- 📤 **Upload Squad**: Upload squad images with descriptions for admin approval
- 💸 **Make Transfer Bids**: Bid on players from other clubs
- 💰 **Balance & Inventory**: Track your cash and items

### For Admins
- 👥 **Manage Users**: Approve user registrations and assign clubs
- 💰 **Distribute Items & Cash**: Give cash and items to users
- 🔄 **Manage Transfers**: Approve or reject transfer bids
- 📊 **Transfer Logs**: View complete transfer history
- ➕ **Add Custom Players**: Add new players to the database
- 📋 **User Squads**: Approve squad uploads from users

## Installation

1. Install required dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
streamlit run app.py
```

## Usage

1. **Welcome Page**: Start at the welcome page to understand the app features
2. **Sign Up**: Create an account as either a User or Admin
3. **Login**: Access your dashboard based on your role
4. **User Workflow**:
   - Wait for admin approval and club assignment
   - Explore your squad and search for players
   - Make transfer bids and upload squad images
5. **Admin Workflow**:
   - Approve user registrations
   - Manage transfers and distribute resources
   - Monitor all user activities

## Database Structure

The app uses SQLite with the following main tables:
- `users`: User accounts and profiles
- `players`: Player database (from CSV + custom additions)
- `squad_uploads`: User squad image submissions
- `transfer_bids`: Transfer requests and approvals
- `user_inventory`: User items and resources

## Data Source

Player data is loaded from `player-data-full.csv` which should contain player information including:
- Player ID, name, positions
- Club names, age, nationality
- Ratings, potential, market value

## Key Features

- **Role-based Authentication**: Separate admin and user interfaces
- **Transfer System**: Complete bid and approval workflow
- **Squad Management**: Image uploads with admin approval
- **Real-time Updates**: Database changes reflect immediately
- **Comprehensive Logging**: Track all transfers and activities

## Security

- Password hashing for secure authentication
- Role-based access control
- Input validation and error handling
