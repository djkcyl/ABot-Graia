from pathlib import Path
from pydantic import BaseModel


class ABotConfigModel(BaseModel):
    mongodb_uri: str = "mongodb://localhost:27017"
    data_path: Path = Path("./data")
    master: int = 123456789
    tencent_cloud_secret_id: str = ""
    tencent_cloud_secret_key: str = ""


ABotConfig = ABotConfigModel()
