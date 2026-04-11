# Entry Guardian - a Telegram bot that prevents spam bots from joining a group
# Copyright: 2025 Entry Guardian Dev Team

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

from aiogram import Router, types, Bot
from aiogram.filters import CommandStart
from aiogram.types import FSInputFile, ChatPermissions
from dbmanager import DBManager
from captchagenerator import CaptchaGenerator
from translator import Translator
import chat_member_handler
import os
import config

router = Router()
db_man = DBManager()
translator = Translator(config.LOCALE)
captcha_generator = CaptchaGenerator()

# In-memory state; safe to lose on restart — user just sends /start again
_answer_by_uid: dict[int, str] = {}
_attempts_left_by_uid: dict[int, int] = {}
_did_request_captcha: dict[int, bool] = {}


def _get_captcha(user_id: int) -> tuple[FSInputFile, str]:
    result = captcha_generator.generate_picture()
    _answer_by_uid[user_id] = result.solution  # always a string
    return FSInputFile(result.filename), result.hint_key


async def _unrestrict_user(bot: Bot, user_id: int):
    for chat_id in db_man.get_pending_chats(user_id):
        try:
            await bot.restrict_chat_member(
                chat_id=chat_id,
                user_id=user_id,
                permissions=ChatPermissions(
                    can_send_messages=True,
                    can_send_audios=True,
                    can_send_documents=True,
                    can_send_photos=True,
                    can_send_videos=True,
                    can_send_polls=True,
                    can_send_other_messages=True
                )
            )
        except Exception:
            pass
    db_man.clear_pending_chats(user_id)


@router.message(CommandStart())
async def start_handler(message: types.Message):
    user_id = message.from_user.id

    if message.chat.id < 0:
        return

    if user_id in config.BLOCKLIST:
        await message.answer(translator.get_string('blocked_msg'))
        return

    if _did_request_captcha.get(user_id, False) and not db_man.is_user_allowed(user_id):
        await message.answer(translator.get_string('already_requested'))
        return

    if db_man.is_user_blocked(user_id):
        await message.answer(translator.get_string('temp_block'))
        return

    if db_man.is_user_allowed(user_id):
        await message.answer(translator.get_string('already_verified'))
        return

    await message.answer(translator.get_string('start_msg'))
    _attempts_left_by_uid[user_id] = config.MAX_ATTEMPTS
    input_file, hint_key = _get_captcha(user_id)
    hint_text = translator.get_string(hint_key)
    await message.answer_photo(input_file, caption=hint_text)
    os.remove(input_file.path)
    _did_request_captcha[user_id] = True


@router.message()
async def handle_captcha_attempt(message: types.Message, bot: Bot):
    if message.chat.type != 'private':
        return

    user_id = message.from_user.id

    if user_id not in _answer_by_uid:
        await message.answer(translator.get_string('no_captcha_requested'))
        return

    if _attempts_left_by_uid.get(user_id, 0) <= 0:
        if db_man.is_user_blocked(user_id):
            await message.answer(translator.get_string('temp_block'))
        return

    user_input = (message.text or '').strip().upper()
    correct = _answer_by_uid[user_id].strip().upper()

    if user_input == correct:
        await message.answer(translator.get_string('verified'))
        db_man.verify_user(user_id)
        _answer_by_uid.pop(user_id, None)
        _did_request_captcha.pop(user_id, None)
        await _unrestrict_user(bot, user_id)
        await chat_member_handler.delete_welcome_msg(bot, user_id)
    else:
        _attempts_left_by_uid[user_id] -= 1
        if _attempts_left_by_uid[user_id] > 0:
            await message.answer(translator.get_string('incorrect'))
            input_file, hint_key = _get_captcha(user_id)
            hint_text = translator.get_string(hint_key)
            await message.answer_photo(input_file, caption=hint_text)
            os.remove(input_file.path)
        else:
            db_man.temp_block(user_id)
            await message.answer(translator.get_string('temp_block'))
            _answer_by_uid.pop(user_id, None)
            _did_request_captcha.pop(user_id, None)
