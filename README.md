# Entry Guardian

Telegram anti-spam bot that gates group entry behind a interactive captcha. When a new user joins a group, the bot mutes them and sends them a link to play a short minigame. After completing the challenge the user receives an 8-character code, sends it to the bot, and gets unmuted.

The captcha type is chosen randomly from the enabled types: **DOOM** (shoot N enemies), **Tetris** (place N pieces), or **Mario** (reach the flagpole).

## How it works

1. A new user joins the group → bot mutes them and posts a welcome message with a button linking to the bot's DM.
2. The user sends `/start` to the bot in DM → bot replies with a button that opens the captcha page.
3. The user completes the minigame in the browser (one of DOOM / Tetris / Mario, chosen at random).
4. On completion the page shows an 8-character code.
5. The user sends the code to the bot → bot verifies it, unmutes the user in all pending chats, and deletes the welcome message.

Sessions expire after 10 minutes. Failed code attempts are limited; too many wrong attempts result in a temporary block.

## Captcha types

| Type | Task | Anti-bot measures |
|------|------|-------------------|
| **DOOM** | Kill N enemies | N kill events with per-kill cooldown + minimum play time |
| **Tetris** | Place N pieces on target slots | N placement events + minimum play time |
| **Mario** | Reach the flagpole (shortened 1-1 level) | Flagpole event + minimum time from page load to flagpole (≥ 5 s) |

All types share a common server-side defense: a per-session **challenge token** (generated at page load, required for every API call) and a **minimum play time** check before `/complete` is accepted.

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

# Which captcha types to use (chosen randomly per session)
CAPTCHA_TYPES=doom,tetris,mario

# Session lifetime
CAPTCHA_TIMEOUT=600       # seconds (default 10 min)

# General anti-bot timing
MIN_PLAY_TIME=3.0         # minimum seconds page must be open before /complete is accepted
KILL_COOLDOWN=0.5         # minimum seconds between registered kill events (doom)

# Per-type difficulty
CAPTCHA_ENEMIES=4         # DOOM: enemies the player must kill
CAPTCHA_MIN_PIECES=3      # Tetris: pieces the player must place
MARIO_MIN_PLAY_TIME=5.0   # Mario: minimum seconds from page load to flagpole event

# Bot behaviour
MAX_ATTEMPTS=3            # wrong code attempts before temp block
COOL_DOWN=900             # temp block duration in seconds
LOCALE=ru_RU
BLOCKLIST=                # comma-separated Telegram user IDs to permanently ban on join
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

location /tetris/ {
    proxy_pass http://127.0.0.1:8080/tetris/;
}

location /mario/ {
    proxy_pass http://127.0.0.1:8080/mario/;
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
├── captcha.html              # DOOM minigame page (served under /doom/)
├── tetris_captcha.html       # Tetris minigame page (served under /tetris/)
├── tetris_captcha.js         # Tetris game logic
├── mario_captcha.html        # Mario minigame page (served under /mario/)
├── FullScreenMario.min.js    # FullScreenMario engine (served under /mario/)
├── templates/
│   └── captcha_wrapper.html  # outer page that hosts the game iframe
├── l10n/
│   ├── ru_RU.json            # Russian locale strings
│   └── en_US.json            # English locale strings
├── static/                   # DOOM game assets (sprites, sounds)
├── Dockerfile
└── docker-compose.yml
```

## License

GNU General Public License v3.0 — see `LICENSE`.
