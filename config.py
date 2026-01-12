import os
from dotenv import load_dotenv

load_dotenv()

# Discord Configuration
DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
DISCORD_CHANNEL_ID = int(os.getenv('DISCORD_CHANNEL_ID', 0))

# Scraping Configuration
REVENUE_THRESHOLD_USD = int(os.getenv('REVENUE_THRESHOLD_USD', 5000))  # Monthly revenue threshold

# App Store Categories
APP_STORE_CATEGORIES = os.getenv('APP_STORE_CATEGORIES', 'games').split(',')

# Database
DATABASE_PATH = 'appstore_tracker.db'

# Category mappings (genre_id for Apple App Store)
CATEGORY_MAP = {
    'games': '6014',
    'social-networking': '6005',
    'photo-video': '6008',
    'entertainment': '6016',
    'utilities': '6002',
    'shopping': '6024',
    'productivity': '6007',
    'lifestyle': '6012',
    'health-fitness': '6013',
    'music': '6011',
}
