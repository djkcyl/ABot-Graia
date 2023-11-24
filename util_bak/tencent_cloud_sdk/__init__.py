from core_bak.config import ABotConfig

from .requtst import TencentCloudClient  # noqa: F401
from .signer import TencentCloudSigner  # noqa: F401

tcs = TencentCloudSigner(
    ABotConfig.tencent_cloud_secret_id, ABotConfig.tencent_cloud_secret_key
)
tcc = TencentCloudClient(tcs)
