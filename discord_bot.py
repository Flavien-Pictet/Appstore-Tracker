import discord
from discord.ext import commands
import asyncio
from typing import Dict
import config

class DiscordNotifier:
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        self.bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)
        self.channel = None
        self.is_ready = False

        @self.bot.event
        async def on_ready():
            print(f'Discord bot logged in as {self.bot.user}')
            self.channel = self.bot.get_channel(config.DISCORD_CHANNEL_ID)
            if self.channel:
                print(f'Connected to channel: {self.channel.name}')
                self.is_ready = True
            else:
                print(f'ERROR: Could not find channel with ID {config.DISCORD_CHANNEL_ID}')

        @self.bot.command(name='status')
        async def status(ctx):
            """Check bot status"""
            await ctx.send('Bot is running and monitoring App Store! 🚀')

        @self.bot.command(name='help')
        async def help_command(ctx):
            """Show help message"""
            help_text = """
**App Store Tracker Bot Commands:**
`!status` - Check if bot is running
`!help` - Show this help message

**What I do:**
I monitor the US Apple App Store top 100 grossing apps and notify you when:
- An app enters the top 100 for the first time
- The app has a daily revenue > $5,000 (via SensorTower)
            """
            await ctx.send(help_text)

    async def start(self):
        """Start the Discord bot"""
        try:
            await self.bot.start(config.DISCORD_BOT_TOKEN)
        except Exception as e:
            print(f"Error starting Discord bot: {str(e)}")

    async def send_notification(self, app_info: Dict):
        """Send a notification about a new app in top 100"""
        if not self.is_ready or not self.channel:
            print("Discord channel not ready, skipping notification")
            return

        try:
            embed = discord.Embed(
                title=f"🎉 New App in Top 100!",
                description=f"**{app_info['app_name']}** just entered the top 100 grossing apps!",
                color=discord.Color.green()
            )

            embed.add_field(name="Rank", value=f"#{app_info['rank']}", inline=True)
            embed.add_field(name="Category", value=app_info['category'].title(), inline=True)

            # Add launch date if available
            if app_info.get('age_months') is not None:
                age_months = app_info['age_months']
                if age_months < 1:
                    age_display = "Less than 1 month ago"
                elif age_months < 2:
                    age_display = "1 month ago"
                else:
                    age_display = f"{age_months:.0f} months ago"
                embed.add_field(name="Launched", value=age_display, inline=True)

            if app_info.get('revenue'):
                revenue_formatted = f"${app_info['revenue']:,.0f}"
                embed.add_field(name="Monthly Revenue (est.)", value=revenue_formatted, inline=True)

            if app_info.get('artist'):
                embed.add_field(name="Developer", value=app_info['artist'], inline=False)

            # Add app icon as thumbnail if available
            if app_info.get('icon_url'):
                embed.set_thumbnail(url=app_info['icon_url'])

            embed.set_footer(text=f"App ID: {app_info['app_id']}")

            # Create button view with one button
            view = discord.ui.View(timeout=None)

            # Button: Visit App Store
            app_store_button = discord.ui.Button(
                label="Visit App Store",
                style=discord.ButtonStyle.link,
                url=app_info['app_url'],
                emoji="📱"
            )
            view.add_item(app_store_button)

            # Send embed with button
            await self.channel.send(embed=embed, view=view)

            print(f"Sent notification for {app_info['app_name']}")

        except Exception as e:
            print(f"Error sending notification: {str(e)}")

    async def send_message(self, message: str):
        """Send a simple text message"""
        if self.is_ready and self.channel:
            try:
                await self.channel.send(message)
            except Exception as e:
                print(f"Error sending message: {str(e)}")

    async def stop(self):
        """Stop the Discord bot"""
        if self.bot:
            await self.bot.close()
