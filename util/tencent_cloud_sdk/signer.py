import hashlib
import hmac
import json
import time
from datetime import datetime


class TencentCloudSigner:
    ALGORITHM = "TC3-HMAC-SHA256"
    CANONICAL_URI = "/"
    CANONICAL_QUERYSTRING = ""
    CONTENT_TYPE = "application/json; charset=utf-8"
    TC3_REQUEST = "tc3_request"
    REGION = "ap-guangzhou"
    VERSION = "2020-12-29"

    def __init__(self, secret_id, secret_key):
        self.secret_id = secret_id
        self.secret_key = secret_key

    @staticmethod
    def sign(key, msg):
        return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()

    @staticmethod
    def sha256_hash(data):
        return hashlib.sha256(data.encode("utf-8")).hexdigest()

    def get_headers(self, base_url, action, params, method):
        timestamp = int(time.time())
        date = datetime.utcfromtimestamp(timestamp).strftime("%Y-%m-%d")
        payload = json.dumps(params)
        canonical_headers = f"content-type:{self.CONTENT_TYPE}\n" f"host:{base_url}\n" f"x-tc-action:{action.lower()}\n"
        signed_headers = "content-type;host;x-tc-action"
        hashed_request_payload = self.sha256_hash(payload)
        canonical_request = (
            f"{method}\n"
            f"{self.CANONICAL_URI}\n"
            f"{self.CANONICAL_QUERYSTRING}\n"
            f"{canonical_headers}\n"
            f"{signed_headers}\n"
            f"{hashed_request_payload}"
        )
        credential_scope = f"{date}/{action}/{self.TC3_REQUEST}"
        hashed_canonical_request = self.sha256_hash(canonical_request)
        string_to_sign = f"{self.ALGORITHM}\n" f"{timestamp}\n" f"{credential_scope}\n" f"{hashed_canonical_request}"
        secret_date = self.sign(f"TC3{self.secret_key}".encode("utf-8"), date)
        secret_service = self.sign(secret_date, action)
        secret_signing = self.sign(secret_service, self.TC3_REQUEST)
        signature = hmac.new(secret_signing, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()
        authorization = (
            f"{self.ALGORITHM} "
            f"Credential={self.secret_id}/{credential_scope}, "
            f"SignedHeaders={signed_headers}, "
            f"Signature={signature}"
        )
        return {
            "Authorization": authorization,
            "Content-Type": self.CONTENT_TYPE,
            "Host": base_url,
            "X-TC-Action": action,
            "X-TC-Timestamp": str(timestamp),
            "X-TC-Version": self.VERSION,
            "X-TC-Region": self.REGION,
        }
