import asyncio
import numpy as np

from PIL import Image
from io import BytesIO
from cnocr import CnOcr
from pathlib import Path
from typing import Union
from loguru import logger

from .time_tools import TimeRecorder


# paddleocr_file = Path(pocr.__file__).read_text()
# if "# print(params)" not in paddleocr_file:
#     logger.warning("paddleocr.paddleocr.__file__ fixed")
#     Path(pocr.__file__).write_text(paddleocr_file.replace("print(params)", "# print(params)"))

ocr_core = CnOcr()


class OCR:
    def __init__(self, image_data: Union[bytes, Image.Image, np.ndarray, Path, str]):
        self.image_data = image_data

    async def ocr(self, detail=False):
        if isinstance(self.image_data, Image.Image):
            img: np.ndarray = np.array(self.image_data.convert("RGB"), np.float32)
        elif isinstance(self.image_data, np.ndarray):
            img = self.image_data
        elif isinstance(self.image_data, bytes):
            img = np.array(Image.open(BytesIO(self.image_data)).convert("RGB"), np.float32)
        else:
            raise TypeError("image_data must be bytes, Image.Image, np.ndarray")

        time = TimeRecorder()
        result = await asyncio.to_thread(ocr_core.ocr, img, cls=False)
        ocr_result = {
            "time": time.total(),
            "result": result if detail else [r[-1][0] for r in result],
        }
        logger.debug(f"OCR - {ocr_result}")

        return ocr_result
