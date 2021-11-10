from io import BytesIO
from graia.ariadne.message.element import Image
from PIL import Image as IMG, ImageDraw, ImageFont
from graia.ariadne.message.chain import MessageChain


LEFT_PART_VERTICAL_BLANK_MULTIPLY_FONT_HEIGHT = 2
LEFT_PART_HORIZONTAL_BLANK_MULTIPLY_FONT_WIDTH = 1 / 4
RIGHT_PART_VERTICAL_BLANK_MULTIPLY_FONT_HEIGHT = 1
RIGHT_PART_HORIZONTAL_BLANK_MULTIPLY_FONT_WIDTH = 1 / 4
RIGHT_PART_RADII = 10
FONT_SIZE = 50


class YoutubeStyleUtils:
    BG_COLOR = "#FFFFFF"
    BOX_COLOR = "#FF0000"
    LEFT_TEXT_COLOR = "#000000"
    RIGHT_TEXT_COLOR = "#FFFFFF"

    @staticmethod
    async def create_left_part_img(text: str, font_size: int):
        font = ImageFont.truetype("font/ArialEnUnicodeBold.ttf", font_size)
        font_width, font_height = font.getsize(text)
        offset_y = font.font.getsize(text)[1][1]
        blank_height = font_height * LEFT_PART_VERTICAL_BLANK_MULTIPLY_FONT_HEIGHT
        right_blank = int(
            font_width / len(text) * LEFT_PART_HORIZONTAL_BLANK_MULTIPLY_FONT_WIDTH
        )
        img_height = font_height + offset_y + blank_height * 2
        image_width = font_width + right_blank
        image_size = image_width, img_height
        image = IMG.new("RGBA", image_size, YoutubeStyleUtils.BG_COLOR)
        draw = ImageDraw.Draw(image)
        draw.text(
            (0, blank_height), text, fill=YoutubeStyleUtils.LEFT_TEXT_COLOR, font=font
        )
        return image

    @staticmethod
    async def create_right_part_img(text: str, font_size: int):
        radii = RIGHT_PART_RADII
        font = ImageFont.truetype("font/ArialEnUnicodeBold.ttf", font_size)
        font_width, font_height = font.getsize(text)
        offset_y = font.font.getsize(text)[1][1]
        blank_height = font_height * RIGHT_PART_VERTICAL_BLANK_MULTIPLY_FONT_HEIGHT
        left_blank = int(
            font_width / len(text) * RIGHT_PART_HORIZONTAL_BLANK_MULTIPLY_FONT_WIDTH
        )
        image_width = font_width + 2 * left_blank
        image_height = font_height + offset_y + blank_height * 2
        image = IMG.new(
            "RGBA", (image_width, image_height), YoutubeStyleUtils.BOX_COLOR
        )
        draw = ImageDraw.Draw(image)
        draw.text(
            (left_blank, blank_height),
            text,
            fill=YoutubeStyleUtils.RIGHT_TEXT_COLOR,
            font=font,
        )

        # 圆
        magnify_time = 10
        magnified_radii = radii * magnify_time
        circle = IMG.new(
            "L", (magnified_radii * 2, magnified_radii * 2), 1
        )  # 创建一个黑色背景的画布
        draw = ImageDraw.Draw(circle)
        draw.ellipse(
            (0, 0, magnified_radii * 2, magnified_radii * 2), fill=255
        )  # 画白色圆形

        # 画4个角（将整圆分离为4个部分）
        magnified_alpha_width = image_width * magnify_time
        magnified_alpha_height = image_height * magnify_time
        alpha = IMG.new("L", (magnified_alpha_width, magnified_alpha_height), 255)
        alpha.paste(
            circle.crop((0, 0, magnified_radii, magnified_radii)), (0, 0)
        )  # 左上角
        alpha.paste(
            circle.crop((magnified_radii, 0, magnified_radii * 2, magnified_radii)),
            (magnified_alpha_width - magnified_radii, 0),
        )  # 右上角
        alpha.paste(
            circle.crop(
                (
                    magnified_radii,
                    magnified_radii,
                    magnified_radii * 2,
                    magnified_radii * 2,
                )
            ),
            (
                magnified_alpha_width - magnified_radii,
                magnified_alpha_height - magnified_radii,
            ),
        )  # 右下角
        alpha.paste(
            circle.crop((0, magnified_radii, magnified_radii, magnified_radii * 2)),
            (0, magnified_alpha_height - magnified_radii),
        )  # 左下角
        alpha = alpha.resize((image_width, image_height), IMG.ANTIALIAS)
        image.putalpha(alpha)
        return image

    @staticmethod
    async def combine_img(left_text: str, right_text, font_size: int) -> bytes:
        print(2)
        left_img = await YoutubeStyleUtils.create_left_part_img(left_text, font_size)
        right_img = await YoutubeStyleUtils.create_right_part_img(right_text, font_size)
        blank = 30
        print(3)
        bg_img_width = left_img.width + right_img.width + blank * 2
        bg_img_height = left_img.height
        bg_img = IMG.new(
            "RGBA", (bg_img_width, bg_img_height), YoutubeStyleUtils.BG_COLOR
        )
        print(4)
        bg_img.paste(left_img, (blank, 0))
        bg_img.paste(
            right_img,
            (blank + left_img.width, int((bg_img_height - right_img.height) / 2)),
            mask=right_img,
        )
        print(5)
        byte_io = BytesIO()
        print(6)
        bg_img.save(byte_io, format="PNG")
        print(2)
        return byte_io.getvalue()

    @staticmethod
    async def make_yt_style_logo(left_text: str, right_text: str) -> MessageChain:
        print(1)
        return MessageChain.create(
            [
                Image(
                    data_bytes=await YoutubeStyleUtils.combine_img(
                        left_text, right_text, FONT_SIZE
                    )
                )
            ]
        )
