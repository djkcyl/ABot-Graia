from loguru import logger
from miniopy_async import Minio
from launart import Service, Launart
from graia.ariadne.app import Ariadne
from miniopy_async.error import S3Error
from launart.service import ExportInterface


class WeedFS(ExportInterface["WeedFSService"], Minio):
    async def get_object(self, object_name):
        return await super().get_object(
            "abot", object_name, Ariadne.current().service.client_session
        )

    async def object_exists(self, object_name):
        try:
            await self.get_object(object_name)
            return True
        except S3Error as e:
            if e.code == "NoSuchKey":
                return False
            else:
                raise e


class WeedFSService(Service):
    id: str = "abot/weedfs"
    weed = WeedFS("127.0.0.1:8333", secure=False)
    supported_interface_types = {WeedFS}

    @property
    def required(self):
        return set()

    @property
    def stages(self):
        return {"preparing"}

    async def launch(self, _: Launart):
        async with self.stage("preparing"):
            if await self.weed.bucket_exists("abot"):
                logger.info("WeaweedFS Bucket 已存在")
            else:
                logger.info("正在创建 WeaweedFS Bucket")
                await self.weed.make_bucket("abot")
                logger.success("WeaweedFS Bucket 创建成功")

    def get_interface(self, _) -> Minio:
        return self.weed
