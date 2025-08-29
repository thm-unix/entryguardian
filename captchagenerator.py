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

import random
import config
from collections import namedtuple
from PIL import Image, ImageDraw, ImageFont
import tempfile

Captcha = namedtuple('Captcha', 'problem solution')
Result = namedtuple('Result', 'filename solution')

class CaptchaGenerator:
	def generate_problem(self):
		lhs = random.randint(1, 10)
		rhs = random.randint(1, 10)
		operator = random.choice(('+', '-', '*'))
		problem = f'{lhs} {operator} {rhs}'
		return Captcha(problem, eval(problem))

	def generate_picture(self):
		image = Image.new(
			'RGB', 
			(config.PIC_WIDTH, config.PIC_HEIGHT),
			config.BG_COLOR
		)
		draw = ImageDraw.Draw(image)
		captcha = self.generate_problem()
		font = ImageFont.truetype(config.FONT_PATH,
								  config.FONT_SIZE)
		
		text_width = draw.textlength(captcha.problem, font)
		x = (config.PIC_WIDTH - text_width) / 2
		y = (config.PIC_HEIGHT - config.FONT_SIZE) / 2
		draw.text((x, y),
				  captcha.problem,
				  font=font,
				  fill=config.FG_COLOR)
		
		for x in range(config.PIC_WIDTH):
			for y in range(config.PIC_HEIGHT):
				if random.random() < config.NOISE_LEVEL / 100:
					draw.point((x, y), fill=config.NOISE_COLOR)

		_, path = tempfile.mkstemp(suffix='.png')
		image.save(path)
		return Result(path, captcha.solution)
