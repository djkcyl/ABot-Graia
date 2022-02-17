import rsa
import base64

from pathlib import Path
from loguru import logger

PRIVATE = Path(__file__).parent.joinpath("server-private.pem")
PUBLIC = Path(__file__).parent.joinpath("server-public.pem")


if not PRIVATE.exists() or not PUBLIC.exists():
    logger.warning("未找到私钥或公钥，正在重新生成")
    public, private = rsa.newkeys(1024)
    PUBLIC_PEM = public
    PRIVATE_PEM = private
    public = public.save_pkcs1()
    private = private.save_pkcs1()
    PUBLIC.write_bytes(public)
    PRIVATE.write_bytes(private)
else:
    PUBLIC_PEM = rsa.PublicKey.load_pkcs1(
        PUBLIC.read_bytes()
    )
    PRIVATE_PEM = rsa.PrivateKey.load_pkcs1(
        PRIVATE.read_bytes()
    )


def encrypt(text):
    text = base64.b64encode(text.encode())
    crypto = rsa.encrypt(text, PUBLIC_PEM)
    msg = base64.b64encode(crypto).decode()
    return msg


def decrypt(text):
    crypto = base64.b64decode(text)
    text = rsa.decrypt(crypto, PRIVATE_PEM).decode()
    password = base64.b64decode(text).decode()
    return password
