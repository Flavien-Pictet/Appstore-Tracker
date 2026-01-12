# Apple App Store Tracker Bot

Bot Discord qui surveille le top 100 des applications les plus rentables de l'Apple App Store US et envoie des notifications pour les nouvelles entrées avec un revenu supérieur à 5 000$/mois.

## Fonctionnalités

- Scrape automatiquement le top 100 des apps par catégorie sur l'App Store US
- Récupère les estimations de revenus depuis AppStoreTracker.com (GRATUIT!)
- Détecte les nouvelles apps entrant dans le top 100
- Filtre les apps de plus de 6 mois (focus sur nouveautés)
- Filtre par seuil de revenu (par défaut: >5 000$/mois)
- Envoie des notifications Discord avec des embeds formatés et icônes d'apps
- Base de données SQLite pour tracking historique
- Optimisé pour cron jobs (1 scan puis exit)

## Stack Technique

- **Python 3.11+**
- **discord.py** - Bot Discord
- **aiohttp** - Requêtes HTTP asynchrones
- **Selenium** - Scraping AppStoreTracker.com
- **SQLite** - Base de données
- **asyncio** - Programmation asynchrone

## Installation

### 1. Prérequis

- Python 3.11 ou supérieur
- Chrome/Chromium (pour Selenium)

### 2. Installation des dépendances

```bash
pip install -r requirements.txt
```

### 3. Configuration

Créez un fichier `.env` basé sur `.env.example`:

```bash
cp .env.example .env
```

Éditez `.env` avec vos paramètres:

```env
# Discord Bot Configuration
DISCORD_BOT_TOKEN=votre_token_discord
DISCORD_CHANNEL_ID=id_du_channel

# Scraping Configuration
REVENUE_THRESHOLD_USD=5000

# Categories à surveiller (comma-separated)
APP_STORE_CATEGORIES=lifestyle,utilities,health-fitness,productivity,shopping
```

### 4. Créer un Bot Discord

1. Allez sur [Discord Developer Portal](https://discord.com/developers/applications)
2. Créez une nouvelle application
3. Allez dans "Bot" et créez un bot
4. Copiez le token et ajoutez-le dans `.env`
5. Activez les "Message Content Intent" dans les paramètres du bot
6. Invitez le bot sur votre serveur avec les permissions:
   - Send Messages
   - Embed Links
   - Read Message History

### 5. Obtenir l'ID du Channel Discord

1. Activez le mode développeur dans Discord (Paramètres > Avancés > Mode développeur)
2. Clic droit sur le channel où vous voulez les notifications
3. Cliquez sur "Copier l'identifiant"
4. Ajoutez l'ID dans `.env`

## Utilisation

### Exécution Manuelle (Test)

```bash
python main.py
```

Le bot va:
1. Se connecter à Discord
2. Initialiser la base de données
3. Scanner les 5 catégories (500 apps total)
4. Vérifier les revenus sur AppStoreTracker.com
5. Envoyer des notifications pour les nouvelles apps qualifiées
6. S'arrêter automatiquement

### Déploiement en Production (Cron Job)

**Le bot est conçu pour être exécuté via cron 1x par jour.**

#### Sur VPS Ubuntu/Debian:

1. **Configurer le cron job:**

```bash
crontab -e
```

2. **Ajouter cette ligne (exécution quotidienne à 9h du matin):**

```bash
0 9 * * * cd /chemin/vers/appstore-tracker && /usr/bin/python3 main.py >> logs.txt 2>&1
```

3. **Vérifier le cron:**

```bash
crontab -l
```

#### Exemples d'horaires cron:

```bash
# Tous les jours à 9h
0 9 * * * cd /path/to/appstore-tracker && python3 main.py

# Tous les jours à minuit
0 0 * * * cd /path/to/appstore-tracker && python3 main.py

# Deux fois par jour (9h et 21h)
0 9,21 * * * cd /path/to/appstore-tracker && python3 main.py
```

### Commandes Discord

Dans le channel Discord:
- `!status` - Vérifier si le bot fonctionne
- `!help` - Afficher l'aide

## Configuration des Catégories

Les catégories disponibles de l'App Store (configurables dans `.env`):

- `lifestyle` - Style de vie ⭐
- `utilities` - Utilitaires ⭐
- `health-fitness` - Santé & Fitness ⭐
- `productivity` - Productivité ⭐
- `shopping` - Shopping ⭐
- `games` - Jeux
- `social-networking` - Réseaux sociaux
- `photo-video` - Photo & Vidéo
- `entertainment` - Divertissement
- `music` - Musique

⭐ = Catégories configurées par défaut

Exemple:
```env
APP_STORE_CATEGORIES=lifestyle,utilities,health-fitness,productivity,shopping
```

## Critères de Notification

Une notification Discord est envoyée **uniquement si l'app remplit TOUS ces critères:**

1. ✅ **Nouvelle dans le top 100** (première fois détectée)
2. ✅ **App gratuite ou freemium** (apps payantes exclues)
3. ✅ **Revenue mensuel ≥ $5,000** (configurable)
4. ✅ **App sortie il y a moins de 6 mois** (focus sur nouveautés)
5. ✅ **Pas déjà notifiée** (évite les doublons)

## Structure du Projet

```
appstore-tracker/
├── main.py                          # Point d'entrée principal
├── config.py                        # Configuration
├── database.py                      # Gestion base de données
├── discord_bot.py                   # Bot Discord et notifications
├── scrapers/
│   ├── __init__.py
│   ├── appstore_scraper.py         # Scraper Apple App Store RSS
│   └── appstoretracker_scraper.py  # Scraper AppStoreTracker.com
├── requirements.txt                 # Dépendances Python
├── .env.example                     # Exemple de configuration
├── .gitignore
└── README.md
```

## Base de Données

Le bot utilise SQLite avec deux tables principales:

- **apps**: Informations sur les applications
- **rankings**: Historique des classements et revenus

La base de données permet de:
- Tracker quand une app entre dans le top 100
- Éviter les notifications en double
- Conserver l'historique des revenus

## Source des Données

### App Store (officiel via RSS)
- Top 100 grossing apps par catégorie
- Nom, ID, développeur, icône, lien App Store
- **Source:** `https://itunes.apple.com/us/rss/topgrossingapplications/`
- **Gratuit et public**

### AppStoreTracker.com
- Estimations de revenus mensuels
- **Alternative GRATUITE à SensorTower**
- Scraping via Selenium + JavaScript DOM traversal
- **URL format:** `https://www.appstoretracker.com/app/{slug}-{app_id}`

### iTunes API
- Release date des apps (pour filtrer par âge)
- **Source:** `https://itunes.apple.com/lookup?id={app_id}`
- **Gratuit et public**

## Personnalisation

### Modifier le seuil de revenu

Dans `.env`:
```env
REVENUE_THRESHOLD_USD=10000  # Pour 10 000$/mois minimum
```

### Modifier le filtre d'âge

Dans [main.py:68](main.py#L68), changer:
```python
if age_months > 6:  # Changer 6 en 12 pour apps < 1 an
```

### Inclure les apps payantes

Par défaut, seules les apps **gratuites/freemium** sont trackées. Pour inclure les apps payantes, commentez la vérification dans [main.py:52-59](main.py#L52-L59):

```python
# Check if app is free (skip paid apps)
# is_free = await appstore_scraper.is_app_free(app_id)
# if not is_free:
#     print(f"💰 App {app_info['app_name']} is paid, skipping")
#     return
```

### Personnaliser les notifications Discord

Éditez la méthode `send_notification()` dans [discord_bot.py:52-88](discord_bot.py#L52-L88) pour changer le format des embeds.

## Tests

Plusieurs scripts de test sont disponibles:

```bash
# Test notification Discord avec UMAX
python test_simple_notification.py

# Test scraping revenue
python test_umax_correct.py

# Test filtre d'âge
python test_age_filter.py

# Test avec apps populaires
python test_popular_apps.py
```

## Troubleshooting

### Le bot ne se connecte pas à Discord
- Vérifiez que `DISCORD_BOT_TOKEN` est correct
- Vérifiez que le bot a les bonnes permissions
- Vérifiez que "Message Content Intent" est activé

### Pas de données de revenu
- AppStoreTracker.com peut être temporairement indisponible
- Vérifiez manuellement l'URL dans les logs
- Le site peut changer sa structure (ajustez le JavaScript dans `appstoretracker_scraper.py`)

### Chrome driver errors
- Assurez-vous que Chrome/Chromium est installé
- `webdriver-manager` télécharge automatiquement le driver
- Essayez: `apt install chromium-browser chromium-chromedriver` (Linux)

### Icônes d'apps ne s'affichent pas
- Les icônes viennent du RSS App Store (généralement fiables)
- Fallback sur iTunes API si nécessaire
- Vérifiez les logs pour les erreurs de fetch

### Base de données corrompue
```bash
rm appstore_tracker.db
# Relancez le bot, il recréera la base de données
```

### Cron job ne s'exécute pas
```bash
# Vérifier les logs cron
grep CRON /var/log/syslog

# Vérifier les permissions
chmod +x main.py

# Tester manuellement
cd /chemin/vers/appstore-tracker && python3 main.py
```

## Performance

**Par scan complet:**
- 5 catégories × 100 apps = 500 apps
- ~3 secondes par app (politesse API)
- Total: ~25 minutes par scan
- Revenue scraping: uniquement pour nouvelles apps

**Recommandations:**
- 1 scan par jour suffit largement
- Évitez scans trop fréquents (rate limiting)
- Logs automatiques via cron redirection

## Améliorations Futures

- [ ] Multi-régions (UK, FR, DE, etc.)
- [ ] Dashboard web pour visualiser les données
- [ ] Export des données en CSV/JSON
- [ ] Graphiques de tendances de revenus
- [ ] Alertes Telegram en plus de Discord
- [ ] Dockerisation pour déploiement facile

## Licence

Ce projet est fourni à des fins éducatives. Respectez les conditions d'utilisation de l'App Store, AppStoreTracker.com et Discord.

## Avertissement

Le scraping de sites web peut violer leurs conditions d'utilisation. Utilisez ce bot de manière responsable et à vos propres risques. Considérez l'utilisation d'APIs officielles quand elles sont disponibles.

## Support

Pour toute question ou problème, créez une issue sur GitHub.
# Appstore-Tracker
