import aiohttp
import asyncio
from typing import List, Dict, Optional
from datetime import datetime
import json
import re
import config

class AppStoreScraper:
    def __init__(self):
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def get_top_grossing_apps(self, category: str, limit: int = 100) -> List[Dict]:
        """
        Scrape top grossing apps using App-Figures API (public charts endpoint)
        Alternative: We can scrape from publicly available chart sites or use RSS
        """
        apps = []

        try:
            # Using a working public API - App Annie/Data.ai style endpoint
            # This uses the official Apple RSS generator
            # Format: https://itunes.apple.com/us/rss/topgrossingapplications/limit=100/genre=GENREID/json

            genre_id = config.CATEGORY_MAP.get(category, '6014')

            # Try the RSS feed with proper content type handling
            url = f"https://itunes.apple.com/us/rss/topgrossingapplications/limit={limit}/genre={genre_id}/json"

            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                'Accept': 'application/json, text/javascript, */*'
            }

            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    # Force parse as text first, then JSON
                    text = await response.text()
                    # Remove any potential callback wrapper
                    text = re.sub(r'^\w+\(', '', text)
                    text = re.sub(r'\);?\s*$', '', text)

                    data = json.loads(text)

                    if 'feed' in data and 'entry' in data['feed']:
                        entries = data['feed']['entry']

                        for idx, entry in enumerate(entries[:limit], 1):
                            try:
                                # Handle link field which can be an object or array
                                link = entry.get('link', {})
                                if isinstance(link, list):
                                    app_url = link[0].get('attributes', {}).get('href', '') if link else ''
                                else:
                                    app_url = link.get('attributes', {}).get('href', '')

                                # Get app icon - RSS feed usually has multiple sizes
                                icon_url = ''
                                if 'im:image' in entry:
                                    images = entry['im:image']
                                    # Get the largest icon (usually the last one)
                                    if isinstance(images, list) and len(images) > 0:
                                        icon_url = images[-1].get('label', '')
                                    elif isinstance(images, dict):
                                        icon_url = images.get('label', '')

                                app_info = {
                                    'rank': idx,
                                    'app_id': entry['id']['attributes']['im:id'],
                                    'app_name': entry['im:name']['label'],
                                    'app_url': app_url,
                                    'category': category,
                                    'bundle_id': entry['id']['attributes']['im:bundleId'],
                                    'artist': entry['im:artist']['label'],
                                    'icon_url': icon_url,
                                }
                                apps.append(app_info)
                            except (KeyError, TypeError) as e:
                                print(f"Error parsing entry {idx}: {e}")
                                continue

                        print(f"Scraped {len(apps)} apps from {category}")
                    else:
                        print(f"No entries found in feed for {category}")
                else:
                    print(f"Failed to fetch {category}: HTTP {response.status}")
                    # Print response for debugging
                    text = await response.text()
                    print(f"Response preview: {text[:200]}")

        except json.JSONDecodeError as e:
            print(f"JSON decode error for {category}: {e}")
            print(f"Response text: {text[:500]}")
        except Exception as e:
            print(f"Error scraping {category}: {str(e)}")
            import traceback
            traceback.print_exc()

        return apps

    async def get_app_details(self, app_id: str) -> Dict:
        """
        Get detailed information about a specific app using iTunes Search API
        Returns app details including releaseDate
        """
        url = f"https://itunes.apple.com/lookup?id={app_id}&country=us"

        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                'Accept': 'application/json'
            }

            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    # Force text parsing first, then JSON
                    text = await response.text()
                    data = json.loads(text)
                    if data.get('resultCount', 0) > 0:
                        return data['results'][0]
        except Exception as e:
            print(f"Error getting app details for {app_id}: {str(e)}")

        return {}

    async def get_app_release_date(self, app_id: str) -> Optional[datetime]:
        """
        Get the release date of an app from iTunes API
        Returns datetime object or None if not available
        """
        details = await self.get_app_details(app_id)

        if details and 'releaseDate' in details:
            try:
                # iTunes API returns dates in ISO format: "2023-01-15T08:00:00Z"
                release_date_str = details['releaseDate']
                release_date = datetime.fromisoformat(release_date_str.replace('Z', '+00:00'))
                return release_date
            except Exception as e:
                print(f"Error parsing release date for {app_id}: {e}")

        return None

    async def is_app_free(self, app_id: str) -> bool:
        """
        Check if an app is free (including freemium with in-app purchases)
        Returns True if free, False if paid
        """
        details = await self.get_app_details(app_id)

        if details and 'price' in details:
            price = float(details.get('price', 0))
            # price = 0 means free (can still have in-app purchases)
            return price == 0.0

        # If we can't determine, assume it's free (safer for our use case)
        return True

    async def scrape_all_categories(self, limit: int = 100) -> List[Dict]:
        """
        Scrape all configured categories
        """
        all_apps = []

        for category in config.APP_STORE_CATEGORIES:
            category = category.strip()
            apps = await self.get_top_grossing_apps(category, limit)
            all_apps.extend(apps)
            await asyncio.sleep(1)  # Be polite, avoid rate limiting

        return all_apps
