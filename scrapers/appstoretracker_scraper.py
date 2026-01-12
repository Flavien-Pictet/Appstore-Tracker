"""
Scraper pour appstoretracker.com - Alternative GRATUITE à SensorTower
"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import asyncio
import time
import re
import os
from typing import Optional

class AppStoreTrackerScraper:
    """Scraper pour appstoretracker.com"""

    def __init__(self):
        self.driver = None

    def _init_driver(self):
        """Initialize Chrome driver"""
        if self.driver:
            return

        chrome_options = Options()
        chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

        # Fix chromedriver path
        driver_path = ChromeDriverManager().install()
        driver_dir = os.path.dirname(driver_path)
        actual_driver = os.path.join(driver_dir, 'chromedriver')
        if os.path.exists(actual_driver):
            driver_path = actual_driver

        service = Service(driver_path)
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.set_page_load_timeout(30)

    def _slugify(self, text: str) -> str:
        """Convertir un nom d'app en slug"""
        text = text.lower()
        text = re.sub(r'[^\w\s-]', '', text)
        text = re.sub(r'[-\s]+', '-', text)
        return text.strip('-')

    def _build_url(self, app_name: str, app_id: str) -> str:
        """Construire l'URL pour appstoretracker.com"""
        slug = self._slugify(app_name)
        return f"https://www.appstoretracker.com/app/{slug}-{app_id}"

    def _parse_revenue(self, revenue_str: str) -> float:
        """Convertir une string de revenue ($100K, $1.5M) en nombre"""
        # Enlever le $ et espaces
        revenue_str = revenue_str.replace('$', '').replace(',', '').strip().upper()

        # Extraire le nombre et le multiplicateur
        match = re.match(r'([0-9.]+)\s*([KM])?', revenue_str)
        if not match:
            return 0.0

        number = float(match.group(1))
        multiplier = match.group(2)

        if multiplier == 'K':
            return number * 1000
        elif multiplier == 'M':
            return number * 1000000
        else:
            return number

    async def get_app_revenue(self, app_name: str, app_id: str) -> Optional[float]:
        """
        Récupère le revenue d'une app depuis appstoretracker.com
        Retourne le revenue mensuel estimé en USD
        """
        if not self.driver:
            self._init_driver()

        try:
            url = self._build_url(app_name, app_id)
            print(f"Fetching revenue from: {url}")

            self.driver.get(url)

            # Attendre que la page charge
            await asyncio.sleep(6)  # Attendre le chargement JS

            # Vérifier si la page existe
            if "Not Found" in self.driver.title:
                print(f"App not found on appstoretracker.com: {app_name}")
                return None

            # Stratégie: Utiliser JavaScript pour trouver le container "Est. Revenue" avec son montant exact
            try:
                script = """
                const elements = Array.from(document.querySelectorAll('*'));
                for (const el of elements) {
                    const text = el.innerText || el.textContent;
                    if (text && text.includes('Est. Revenue') && text.match(/\\$[0-9,.]+[KM]/)) {
                        // Extraire le montant ($XXK ou $XXM)
                        const match = text.match(/\\$([0-9,.]+[KM])/);
                        if (match) {
                            return match[1];
                        }
                    }
                }
                return null;
                """

                revenue_str = self.driver.execute_script(script)

                if revenue_str:
                    monthly_revenue = self._parse_revenue(revenue_str)

                    if monthly_revenue > 0:
                        print(f"✅ Found Est. Revenue for {app_name}: ${monthly_revenue:,.0f}/month")
                        return monthly_revenue

            except Exception as e:
                print(f"JavaScript extraction failed: {e}")

            print(f"⚠️  No revenue data found for {app_name}")
            return None

        except Exception as e:
            print(f"❌ Error getting revenue for {app_name}: {e}")
            return None

    async def get_app_revenue_by_id(self, app_id: str, app_name: str = None) -> Optional[float]:
        """Alias pour compatibilité avec l'ancien code"""
        if not app_name:
            app_name = f"app-{app_id}"
        return await self.get_app_revenue(app_name, app_id)

    async def close(self):
        """Fermer le navigateur"""
        if self.driver:
            self.driver.quit()
            self.driver = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
