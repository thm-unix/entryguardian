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

from aiogram import Router, Bot
from aiogram.filters.chat_member_updated import ChatMemberUpdatedFilter
from aiogram.types.chat_member_updated import ChatMemberUpdated
from aiogram.types.chat_permissions import ChatPermissions
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import IS_MEMBER, IS_NOT_MEMBER
from dbmanager import DBManager
from datetime import datetime
import config
from translator import Translator

router = Router()
db_man = DBManager()
translator = Translator(config.LOCALE)

# Set by run.py after bot.get_me() so we can build the deep-link URL
bot_username: str | None = None

# user_id → (chat_id, message_id) of that user's welcome message
_welcome_msg_by_user: dict[int, tuple[int, int]] = {}


async def delete_welcome_msg(bot: Bot, user_id: int) -> None:
    """Delete the welcome message for a user after they verify. Called from personal_msg_handler."""
    if user_id in _welcome_msg_by_user:
        chat_id, msg_id = _welcome_msg_by_user.pop(user_id)
        try:
            await bot.delete_message(chat_id, msg_id)
        except Exception:
            pass


@router.chat_member(ChatMemberUpdatedFilter(IS_NOT_MEMBER >> IS_MEMBER))
async def handle_new_user(event: ChatMemberUpdated, bot: Bot):
    user = event.new_chat_member.user
    user_id = user.id
    chat_id = event.chat.id

    if db_man.is_user_allowed(user_id):
        return

    user_display = f'@{user.username}' if user.username else user.first_name
    msg = translator.get_string('welcome_msg').format(user_display)

    keyboard = None
    if bot_username:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(
                text=translator.get_string('start_button'),
                url=f'https://t.me/{bot_username}?start=verify'
            )
        ]])

    # Delete any existing welcome message in this chat (for a previous pending user)
    for uid, (cid, mid) in list(_welcome_msg_by_user.items()):
        if cid == chat_id:
            try:
                await bot.delete_message(chat_id, mid)
            except Exception:
                pass
            del _welcome_msg_by_user[uid]

    sent = await bot.send_message(chat_id, msg, reply_markup=keyboard)
    _welcome_msg_by_user[user_id] = (chat_id, sent.message_id)

    await bot.restrict_chat_member(
        chat_id=chat_id,
        user_id=user_id,
        permissions=ChatPermissions(can_send_messages=False),
        until_date=int(datetime.now().timestamp()) + 5
    )

    db_man.add_pending_chat(user_id, chat_id)
