# High Five Recognition System

A QR code-based recognition system.

## 🎯 Features

- 🎫 QR code scanning with unique token and category parameters
- ✅ Token validation (checks if token has been used before)
- 💬 Recognition message submission form
- 📊 CSV-based storage
- 🔐 Admin dashboard with password protection
- 📥 Download data as CSV or Excel
- 📈 Statistics and analytics
- 📱 Mobile-responsive design

## 🚀 Quick Start

### Run Locally

```bash
# Create a virtual environment
uv venv

# Install dependencies
uv sync

# Set admin password in .streamlit/secrets.toml
echo 'ADMIN_PASSWORD = "your-password"' > .streamlit/secrets.toml

# Run the app
streamlit run streamlit-app/app.py

# Test it
# User: http://localhost:8501?token=TEST001&category=collaboration_excellence
# Admin: http://localhost:8501?admin
```

## 📋 How It Works

### For Users (QR Code Recipients)

1. **Scan QR code** on token
2. **Read existing message** (if token already used) OR **Submit new message**
3. **Enter name and message**
4. **Submit** - Token is now marked as used

### For Admins

1. **Access admin dashboard** (via `?admin` in the URL or the Admin button/sidebar)
2. **Enter password**
3. **View all submissions**, download data, see statistics

## 🎨 QR Code Format

Generate QR codes with this URL format:

```
https://highfive.streamlit.app?token=UNIQUE_TOKEN&category=CATEGORY_NAME
```

**Examples:**

```
https://highfive.streamlit.app?token=ABC123&category=collaboration_excellence
https://highfive.streamlit.app?token=DEF456&category=knowledge_growth
https://highfive.streamlit.app?token=TEAM2025-001&category=supplier_management
```

**Admin Access:**

```
https://highfive.streamlit.app?admin
```

## 🎨 Supported Bosch Categories & Colors

| Category                 | Color Name         | Hex       |
| ------------------------ | ------------------ | --------- |
| collaboration_excellence | Bosch Purple 40    | "#9E2896" |
| knowledge_growth         | Bosch Blue 50      | #007BC0   |
| supplier_management      | Bosch Turquoise 50 | #18837E   |
| performance_delivery     | Bosch Green 50     | #00884A   |

A Bosch brand color bar appears at the top of the app for visual identity.

## 📄 License

MIT License - Feel free to use and modify for your organization!
