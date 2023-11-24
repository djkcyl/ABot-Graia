from pathlib import Path
from loguru import logger


from .config import ABotConfig

base_path = Path(ABotConfig.data_path)
base_path.mkdir(exist_ok=True)
logger.info(f"[Core.datafile] 数据文件夹路径: {base_path}")


def get_data_path(*path: str) -> Path:
    data_path = base_path.joinpath(*path)
    if not data_path.exists():
        data_path.mkdir(exist_ok=True, parents=True)
        logger.info(f"[Core.datafile] 创建数据文件夹: {data_path}")
    return data_path
