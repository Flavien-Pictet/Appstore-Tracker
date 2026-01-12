import asyncio
from datetime import datetime, timedelta, timezone
from scrapers import AppStoreScraper
from scrapers.appstoretracker_scraper import AppStoreTrackerScraper
from discord_bot import DiscordNotifier
from database import Database
import config

class AppStoreTracker:
    def __init__(self):
        self.db = Database()
        self.discord = DiscordNotifier()
        self.is_running = False

    async def initialize(self):
        """Initialize the tracker"""
        print("Initializing App Store Tracker...")
        await self.db.initialize()
        print("Database initialized")

    async def process_app(self, app_info: dict, revenue_scraper: AppStoreTrackerScraper, appstore_scraper: AppStoreScraper):
        """Process a single app: check revenue and send notification if needed"""
        app_id = app_info['app_id']
        rank = app_info['rank']

        # Add/update app in database
        await self.db.add_app(
            app_id=app_id,
            app_name=app_info['app_name'],
            app_url=app_info['app_url'],
            category=app_info['category']
        )

        # Get revenue from AppStoreTracker.com (if available)
        revenue = None
        if revenue_scraper:
            try:
                revenue = await revenue_scraper.get_app_revenue(app_info['app_name'], app_id)
            except Exception as e:
                print(f"Error getting revenue for {app_id}: {e}")

        # Add ranking entry
        await self.db.add_ranking(app_id=app_id, rank=rank, revenue=revenue)

        # Check if this app should trigger a notification
        if rank <= 100:
            # Check if it's new in top 100 and has sufficient revenue
            is_new = await self.db.is_new_in_top_100(app_id)
            was_notified = await self.db.was_notified(app_id)

            if is_new and not was_notified:
                # Check if app is social/dating/marketplace (skip these types)
                app_name_lower = app_info['app_name'].lower()

                # Keywords that indicate dating apps (very conservative filter)
                # Only blocking obvious dating/relationship apps to avoid false positives
                social_keywords = [
                    'dating', 'match', 'single', 'hookup', 'relationship',
                    'tinder', 'bumble', 'hinge', 'badoo', 'muzz', 'raya'
                ]

                if any(keyword in app_name_lower for keyword in social_keywords):
                    print(f"🚫 App {app_info['app_name']} appears to be social/dating/marketplace, skipping")
                    return

                print(f"✅ App is utility-focused (not social/dating)")

                # Check if app is free (skip paid apps)
                is_free = await appstore_scraper.is_app_free(app_id)

                if not is_free:
                    print(f"💰 App {app_info['app_name']} is paid, skipping (only tracking free/freemium apps)")
                    return

                print(f"✅ App is free/freemium")

                # Check app age (skip apps older than 6 months)
                release_date = await appstore_scraper.get_app_release_date(app_id)
                age_months = None

                if release_date:
                    now = datetime.now(timezone.utc)
                    age_months = (now - release_date).days / 30.44  # Average days per month

                    if age_months > 6:
                        print(f"⏳ App {app_info['app_name']} is {age_months:.1f} months old, skipping (older than 6 months)")
                        return

                    print(f"✅ App age: {age_months:.1f} months (within 6 month threshold)")
                else:
                    print(f"⚠️  Could not determine release date for {app_info['app_name']}, proceeding anyway")

                # Check revenue threshold (monthly revenue)
                if revenue is not None and revenue >= config.REVENUE_THRESHOLD_USD:
                    print(f"🎯 Found qualifying app: {app_info['app_name']} (${revenue:,.0f}/month)")

                    # Prepare notification data
                    notification_data = {
                        **app_info,
                        'revenue': revenue,
                        'age_months': age_months
                    }

                    # Send Discord notification
                    await self.discord.send_notification(notification_data)

                    # Mark as notified
                    await self.db.mark_as_notified(app_id)

                elif revenue is not None:
                    print(f"App {app_info['app_name']} is new in top 100 but revenue (${revenue:,.0f}/month) is below threshold")
                else:
                    print(f"App {app_info['app_name']} is new in top 100 but no revenue data available")

    async def scan_cycle(self):
        """Perform one scan cycle"""
        print(f"\n{'='*60}")
        print(f"Starting scan cycle at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}\n")

        try:
            # Initialize scrapers
            async with AppStoreScraper() as appstore:
                # Scrape all categories
                print(f"Scraping categories: {', '.join(config.APP_STORE_CATEGORIES)}")
                all_apps = await appstore.scrape_all_categories(limit=100)

                print(f"Found {len(all_apps)} apps across all categories")

                # Initialize AppStoreTracker.com scraper for revenue data
                revenue_scraper = AppStoreTrackerScraper()
                print("✅ Using AppStoreTracker.com for FREE revenue data!")

                # Process each app
                for idx, app_info in enumerate(all_apps, 1):
                    print(f"Processing {idx}/{len(all_apps)}: {app_info['app_name']} (Rank #{app_info['rank']})")
                    await self.process_app(app_info, revenue_scraper, appstore)

                    # Be polite - add delay between requests
                    await asyncio.sleep(3)  # 3 seconds pour être respectueux

                # Close revenue scraper
                await revenue_scraper.close()

            print(f"\nScan cycle completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        except Exception as e:
            print(f"Error during scan cycle: {str(e)}")
            import traceback
            traceback.print_exc()

    async def start(self):
        """Start the tracker - runs ONE scan then exits (for cron jobs)"""
        await self.initialize()

        # Start Discord bot in background
        discord_task = asyncio.create_task(self.discord.start())

        # Wait for Discord to be ready
        print("Waiting for Discord bot to be ready...")
        for _ in range(30):
            if self.discord.is_ready:
                break
            await asyncio.sleep(1)

        if not self.discord.is_ready:
            print("WARNING: Discord bot not ready, but continuing anyway...")

        # Run ONE scan cycle
        await self.scan_cycle()

        # Stop Discord bot
        await self.discord.stop()

        print("\n✅ Scan complete! Exiting...")

    async def stop(self):
        """Stop the tracker"""
        await self.discord.stop()

async def main():
    tracker = AppStoreTracker()

    try:
        await tracker.start()
    except KeyboardInterrupt:
        print("\nShutting down...")
        await tracker.stop()
    except Exception as e:
        print(f"Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║         Apple App Store Tracker Bot                      ║
    ║         Monitoring Top 100 Grossing Apps                 ║
    ╚═══════════════════════════════════════════════════════════╝
    """)

    # Check configuration
    if not config.DISCORD_BOT_TOKEN:
        print("ERROR: DISCORD_BOT_TOKEN not set in .env file")
        exit(1)

    if not config.DISCORD_CHANNEL_ID:
        print("ERROR: DISCORD_CHANNEL_ID not set in .env file")
        exit(1)

    print(f"Configuration:")
    print(f"  - Categories: {', '.join(config.APP_STORE_CATEGORIES)}")
    print(f"  - Revenue threshold: ${config.REVENUE_THRESHOLD_USD:,}/month")
    print(f"  - Revenue source: AppStoreTracker.com (FREE!)")
    print(f"  - Mode: Single scan (for cron job)")
    print()

    asyncio.run(main())
