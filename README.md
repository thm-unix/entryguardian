# Entry Guardian

Telegram anti-spam bot that gates group entry behind a DOOM captcha. When a new user joins a group, the bot mutes them and sends them a link to play a short DOOM minigame. After killing the required number of enemies the user receives an 8-character code, sends it to the bot, and gets unmuted.

## How it works

1. A new user joins the group → bot mutes them and posts a welcome message with a button linking to the bot's DM.
2. The user sends `/start` to the bot in DM → bot replies with a button that opens the captcha page.
3. The user plays the DOOM minigame in the browser (kills N enemies).
4. On completion the page shows an 8-character code.
5. The user sends the code to the bot → bot verifies it, unmutes the user in all pending chats, and deletes the welcome message.

Sessions expire after 5 minutes. Failed code attempts are limited; too many wrong attempts result in a temporary block.

## Requirements

- Python 3.11+
- Docker + Docker Compose (recommended)
- A domain with HTTPS (nginx reverse proxy) so the captcha page is accessible from the internet
- A Telegram bot token from [@BotFather](https://t.me/BotFather) with **Group privacy mode disabled** and **Group member events** enabled

## Configuration

Copy `.env.example` to `.env` and fill in the values (`.env.example` lists all available options):

```env
TOKEN=<bot token>
DB_PATH=users.db

# Captcha web server
WEB_HOST=0.0.0.0
WEB_PORT=8080
CAPTCHA_BASE_URL=https://yourdomain.com/captcha

# Captcha difficulty
CAPTCHA_ENEMIES=4        # enemies the player must kill
CAPTCHA_TIMEOUT=300      # session lifetime in seconds
MIN_PLAY_TIME=3.0        # minimum seconds the page must be open before completion is accepted
KILL_COOLDOWN=0.5        # minimum seconds between registered kills (prevents scripted rapid kills)

# Bot behaviour
MAX_ATTEMPTS=3           # wrong code attempts before temp block
COOL_DOWN=900            # temp block duration in seconds
LOCALE=ru_RU
BLOCKLIST=               # comma-separated Telegram user IDs to permanently ban on join
```

## Running with Docker

```bash
# Create an empty database file so Docker mounts it as a file, not a directory
touch users.db

docker compose up -d
docker compose logs -f
```

The web server listens on `127.0.0.1:8080` on the host. Proxy it with nginx:

```nginx
location /captcha/ {
    proxy_pass http://127.0.0.1:8080/captcha/;
}

location /api/captcha/ {
    proxy_pass http://127.0.0.1:8080/api/captcha/;
}

location /doom/ {
    proxy_pass http://127.0.0.1:8080/doom/;
}
```

> **Note:** set `WEB_HOST=0.0.0.0` in `.env` — inside Docker the container's loopback is not reachable from the host.

## Running without Docker

```bash
pip install -r requirements.txt
cp .env.example .env  # edit .env
python run.py
```

## Adding the bot to a group

1. Create a bot via [@BotFather](https://t.me/BotFather), get the token, set it as `TOKEN` in `.env`.
2. Add the bot to your group and grant it **administrator** rights (restrict members, delete messages, ban members).
3. Start the bot.

## Project structure

```
entryguardian/
├── run.py                    # entry point — starts bot, web server, expiry task
├── config.py                 # settings loaded from .env
├── webserver.py              # aiohttp: captcha page, kill API, complete API, static files
├── session_manager.py        # in-memory session store
├── personal_msg_handler.py   # /start and code verification in bot DM
├── chat_member_handler.py    # new member detection, mute, welcome message
├── reaction_handler.py       # reaction events
├── dbmanager.py              # SQLite: verified users, pending chats
├── translator.py             # locale string loader
├── captcha.html              # DOOM minigame (served under /doom/)
├── templates/
│   └── captcha_wrapper.html  # outer page that hosts the game iframe
├── l10n/
│   ├── ru_RU.json            # Russian locale strings
│   └── en_US.json            # English locale strings
├── static/                   # game assets (sprites, sounds)
├── Dockerfile
└── docker-compose.yml
```

## License

GNU General Public License v3.0 — see `LICENSE`.
