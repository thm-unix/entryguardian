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

import sqlite3
import config
from datetime import datetime

class DBManager:
	def __init__(self):
		self.connection = sqlite3.connect(config.DB_PATH)
		self.cursor = self.connection.cursor()
		result = self.cursor.execute('SELECT name FROM sqlite_master')
		if not result.fetchone():
			self.cursor.execute('CREATE TABLE user(id, verified, blocked_until)')
			
	def unix_time(self):
		return int(datetime.now().timestamp())
	
	def is_user_known(self, user_id):
		query = f'SELECT id FROM user WHERE id={user_id}'
		result = self.cursor.execute(query).fetchone()
		return bool(result)
	
	def is_user_blocked(self, user_id):
		if not self.is_user_known(user_id):
			return False
		
		query = f'SELECT blocked_until FROM user WHERE id={user_id}'
		result = self.cursor.execute(query).fetchone()
		return result[0] > self.unix_time()
	
	def is_user_allowed(self, user_id):
		if self.is_user_known(user_id) and not self.is_user_blocked(user_id):
			query = f'SELECT verified FROM user WHERE id={user_id}'
			result = self.cursor.execute(query).fetchone()
			return bool(result[0])
		return False
	
	def verify_user(self, user_id):
		query = ''
		if not self.is_user_known(user_id):
			query = f'INSERT INTO user VALUES ({user_id}, 1, -1)'
		else:
			query = f'UPDATE user SET verified=1 WHERE id={user_id}'
		
		self.cursor.execute(query)
		self.connection.commit()
		
	def temp_block(self, user_id):
		timestamp = self.unix_time()
		blocked_until = timestamp + config.COOL_DOWN
		
		query = ''
		if not self.is_user_known(user_id):
			query = f'INSERT INTO user VALUES ({user_id}, 0, {blocked_until})'
		else:
			query = f'UPDATE user SET blocked_until={blocked_until} WHERE id={user_id}'
		
		self.cursor.execute(query)
		self.connection.commit()
