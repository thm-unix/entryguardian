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

from aiogram import Router, types
from aiogram.filters import CommandStart, Command
from aiogram.types import FSInputFile
from dbmanager import DBManager
from captchagenerator import CaptchaGenerator
from translator import Translator
import os
import config
import socket

router = Router()
db_man = DBManager()
translator = Translator(config.LOCALE)
captcha_generator = CaptchaGenerator()
answer_by_uid = dict()
attempts_left_by_uid = dict()
did_user_request_captcha = dict()

def get_captcha(user_id):
	pic_path, answer = captcha_generator.generate_picture()
	answer_by_uid[user_id] = answer
	return FSInputFile(pic_path)

@router.message(CommandStart())
async def start_handler(message: types.Message):
	user_id = message.from_user.id
	chat_id = message.chat.id

	if chat_id < 0:
		return

	if did_user_request_captcha.get(user_id, False) and not db_man.is_user_allowed(user_id):
		await message.answer(translator.get_string('already_requested'))
		return

	if not db_man.is_user_allowed(user_id) and not db_man.is_user_blocked(user_id):
		await message.answer(translator.get_string('start_msg'))
		attempts_left_by_uid[user_id] = config.MAX_ATTEMPTS
		input_file = get_captcha(user_id)
		await message.answer_photo(input_file)
		os.remove(input_file.path)
		did_user_request_captcha[user_id] = True
	elif db_man.is_user_blocked(user_id):
		await message.answer(translator.get_string('temp_block'))
	else:
		await message.answer(translator.get_string('already_verified'))

@router.message()
async def handle_captcha_attempt(message: types.Message):
	if message.chat.type == 'private':
		user_input = None
		try:
			user_input = int(message.text)
		except ValueError:
			pass
		
		user_id = message.from_user.id
		if user_id in answer_by_uid:
			if attempts_left_by_uid[user_id] > 0:
				if user_input == answer_by_uid[user_id]:
					await message.answer(translator.get_string('verified'))
					db_man.verify_user(user_id)
					answer_by_uid.pop(user_id)
					socket_path = f'/tmp/{user_id}'
					client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
					client.connect(socket_path)
					client.sendall('verified'.encode())
					client.close()
				else:
					attempts_left_by_uid[user_id] -= 1
					if attempts_left_by_uid[user_id] > 0:
						await message.answer(translator.get_string('incorrect'))
						input_file = get_captcha(user_id)
						await message.answer_photo(input_file)
						os.remove(input_file.path)
					else:
						db_man.temp_block(user_id)
						await message.answer(translator.get_string('temp_block'))
						answer_by_uid.pop(user_id)
			elif db_man.is_user_blocked(user_id):
				await message.answer(translator.get_string('temp_block'))
		else:
			await message.answer(translator.get_string('no_captcha_requested'))
