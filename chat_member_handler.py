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
from aiogram.filters.chat_member_updated import ChatMemberUpdatedFilter
from aiogram.types.chat_member_updated import ChatMemberUpdated
from aiogram.types.chat_permissions import ChatPermissions
from aiogram.filters import IS_MEMBER, IS_NOT_MEMBER
from aiogram.methods.restrict_chat_member import RestrictChatMember
from aiogram.types.chat_permissions import ChatPermissions
from dbmanager import DBManager
from datetime import datetime
import socket
import os
import asyncio
import threading

router = Router()
db_man = DBManager()
chats_by_user_id = dict()
loop = None

@router.chat_member(ChatMemberUpdatedFilter(IS_NOT_MEMBER >> IS_MEMBER))
async def handle_new_user(event: ChatMemberUpdated, bot: Bot):
	global loop
	loop = asyncio.get_running_loop()
	print(f'New chat member! uid={event.from_user.id}')
	user_id = event.from_user.id
	chat_id = event.chat.id
	if not db_man.is_user_allowed(user_id):
		await bot.restrict_chat_member(
			chat_id=chat_id,
			user_id=user_id,
			permissions=ChatPermissions(can_send_messages=False),
			until_date=int(datetime.now().timestamp()) + 5
		)
		
		if user_id not in chats_by_user_id:
			chats_by_user_id[user_id] = {chat_id}
		else:
			chats_by_user_id[user_id].add(chat_id)
		
		threading.Thread(
            target=socket_listener,
            args=(user_id, bot),
            daemon=True
        ).start()
		
		#asyncio.to_thread(socket_listener, user_id, bot)
		#asyncio.create_task(socket_listener(user_id, bot))
		#thread = threading.Thread(
		#	target=socket_listener,
		#	args=(user_id, bot),
		#	daemon=True
		#)
		#thread.start()
		#thread.join()
		#asyncio.run(socket_listener(user_id, bot))
		#await socket_listener(user_id, bot)
		
async def unrestrict_user(bot, user_id):
	for chat_id in chats_by_user_id[user_id]:
		await bot.restrict_chat_member(
			chat_id=chat_id,
            user_id=user_id,
            permissions=ChatPermissions(can_send_messages=True)
		)

def socket_listener(user_id, bot):		
	socket_path = f'/tmp/{user_id}'
	try:
		os.unlink(socket_path)
	except OSError:
		if os.path.exists(socket_path):
			os.remove(socket_path)
		
	server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
	server.bind(socket_path)
	server.listen(1)
	connection, client_address = server.accept()
	try:
		while True:
			data = connection.recv(1024)
			if not data:
				break
			s = data.decode()
			if s == 'verified':
				for chat_id in chats_by_user_id[user_id]:
					#await bot.restrict_chat_member(
					#	chat_id=chat_id,
					#	user_id=user_id,
					#	permissions=ChatPermissions(can_send_messages=True)
					#)
					asyncio.run_coroutine_threadsafe(
                       unrestrict_user(bot, user_id),
                       loop
                    )
	finally:
		connection.close()
		os.unlink(socket_path)
