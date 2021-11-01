import os
import rsa
import base64


PRIVATE = "./saya/Lottery/server-private.pem"
PUBLIC = "./saya/Lottery/server-public.pem"


if not os.path.exists(PRIVATE) or not os.path.exists(PUBLIC):
    print("未找到私钥或公钥，正在重新生成")
    public, private = rsa.newkeys(1024)
    PUBLIC_PEM = public
    PRIVATE_PEM = private
    public = public.save_pkcs1()
    private = private.save_pkcs1()
    with open(PRIVATE, "wb") as x:  # 保存私钥
        x.write(private)
    with open(PUBLIC, "wb") as x:  # 保存公钥
        x.write(public)
else:
    with open(PRIVATE, "rb") as f:
        p = f.read()
        PRIVATE_PEM = rsa.PrivateKey.load_pkcs1(p)
    with open(PUBLIC, "rb") as f:
        p = f.read()
        PUBLIC_PEM = rsa.PublicKey.load_pkcs1(p)


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
