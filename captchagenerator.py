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

RED_FACTOR = 0.299
GREEN_FACTOR = 0.587
BLUE_FACTOR = 0.114
THRESHOLD = 150

class CaptchaGenerator:
    def generate_problem(self):
        lhs = random.randint(1, 10)
        rhs = random.randint(1, 10)
        operator = random.choice(('+', '-', '*'))
        problem = f'{lhs} {operator} {rhs}'
        return Captcha(problem, eval(problem))
    
    def random_color(self):
        return tuple([random.randint(0, 255) for _ in range(3)])
	
    def luminance(self, color):
        return color[0] * RED_FACTOR + \
                color[1] * GREEN_FACTOR + \
                color[2] * BLUE_FACTOR

    def generate_picture(self):
        bg_color = self.random_color()
        noise_color = self.random_color()

        if self.luminance(bg_color) > THRESHOLD:
            fg_color = (255, 255, 255)
        else:
            fg_color = (0, 0, 0)
        
        image = Image.new(
            'RGB', 
            (config.PIC_WIDTH, config.PIC_HEIGHT),
            bg_color
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
                  fill=fg_color)
        
        for x in range(config.PIC_WIDTH):
            for y in range(config.PIC_HEIGHT):
                if random.random() < config.NOISE_LEVEL / 100:
                    draw.point((x, y), fill=noise_color)
        _, path = tempfile.mkstemp(suffix='.png')
        image.save(path)
        return Result(path, captcha.solution)
