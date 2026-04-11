# Entry Guardian

A Telegram bot that protects group chats from spam bots. When a new member joins, the bot restricts their permissions and asks them to solve a CAPTCHA in a private message. Once passed, restrictions are lifted automatically.

## Features

- Automatically restricts new members until they complete verification
- 4 randomly selected CAPTCHA types:
  - **Arithmetic** — solve a math expression (`7 * 3`)
  - **Text** — type the characters shown in the image (`A4FK2`)
  - **Sequence** — find the missing number (`3, 7, ?, 15`)
  - **Shape counting** — count the circles in the image
- Inline button in the welcome message with a direct deep link to the bot
- Welcome message is automatically deleted after the user verifies
- Temporary ban after exhausting all attempts (15 minutes by default)
- Verification state is persisted in a database — survives bot restarts
- Localization support (`ru_RU`, `en_US`)
- Blocklist — permanently ban specific users on join

## Requirements

- Python 3.11+
- [SimpleHandmade](https://www.dafont.com/simple-handmade-2.font) font (or any TTF; path is set in `.env`)
- Dependencies: `aiogram`, `pillow`, `python-dotenv`

## Font Installation

The bot uses the **SimpleHandmade** font to render CAPTCHA images.

1. Download the font archive from [dafont.com](https://www.dafont.com/simple-handmade-2.font)
2. Extract the archive and copy `SimpleHandmade.ttf` to `/usr/share/fonts/TTF/`:

```bash
sudo cp SimpleHandmade.ttf /usr/share/fonts/TTF/SimpleHandmade.ttf
```

The font must be in place before starting the bot.

## Installation & Running

### Directly

```bash
cp .env.example .env
# edit .env and set TOKEN
pip install -r requirements.txt
python run.py
```

### Docker Compose

```bash
cp .env.example .env
# edit .env and set TOKEN
docker compose up -d
```

The database is mounted from `./users.db` and the font from `/usr/share/fonts/TTF/SimpleHandmade.ttf` on the host.

## Configuration

All parameters are set in `.env` (copy from `.env.example`):

| Variable | Default | Description |
|---|---|---|
| `TOKEN` | — | Bot token from @BotFather |
| `LOCALE` | `ru_RU` | Message language (`ru_RU` or `en_US`) |
| `MAX_ATTEMPTS` | `3` | Number of CAPTCHA attempts allowed |
| `COOL_DOWN` | `900` | Temporary ban duration in seconds after failing |
| `FONT_PATH` | `/usr/share/fonts/TTF/SimpleHandmade.ttf` | Path to the TTF font for CAPTCHA images |
| `FONT_SIZE` | `144` | Font size (auto-scaled for longer text) |
| `PIC_WIDTH` | `300` | CAPTCHA image width in pixels |
| `PIC_HEIGHT` | `140` | CAPTCHA image height in pixels |
| `NOISE_LEVEL` | `30` | Noise level on the image (0–100) |
| `DB_PATH` | `users.db` | Path to the SQLite database file |
| `BLOCKLIST` | _(empty)_ | Comma-separated Telegram user IDs to permanently ban on join |

## Blocklist

To permanently ban specific users, add their Telegram IDs to `BLOCKLIST` in `.env`:

```
BLOCKLIST=123456789,987654321
```

Banned users are kicked the moment they join any chat where the bot is active. If they message the bot directly, they receive a "You have been blocked" reply. Restart the bot after editing the blocklist.

## Adding the Bot to a Chat

1. Create a bot via [@BotFather](https://t.me/BotFather) and get the token
2. Set the token in `.env` → `TOKEN`
3. Add the bot to your group and grant it **administrator** rights (required: restrict members, delete messages, ban members)
4. Start the bot

## Managing Users Manually

Delete a user from the database (e.g. for testing):

```bash
sqlite3 users.db "DELETE FROM user WHERE id=USER_ID; DELETE FROM pending_chats WHERE user_id=USER_ID;"
```

List all users:

```bash
sqlite3 users.db "SELECT * FROM user;"
```

## License

GNU General Public License v3.0 — see the `LICENSE` file for details.
