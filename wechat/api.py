import base64
import json
import logging
import time
import traceback
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Optional

import requests
from constance import config
from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.serialization import load_pem_public_key
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from django.conf import settings
from django.urls import reverse

from system.log import Log, tb_for_log
from system.models import Log as LogModel

logger = logging.getLogger(__name__)


def truncate_string_if_needed(input_string: str, max_bytes: int) -> str:
    current_length = len(input_string.encode())
    if current_length <= max_bytes:
        return input_string
    for i in range(len(input_string) - 1, 0, -1):
        current_string = input_string[:i] + "..."
        current_length = len(current_string.encode())
        if current_length <= max_bytes - 3:
            return current_string
    return "..."


class WechatAPIException(Exception):
    def __init__(self, errcode, errmsg):
        self.errcode = errcode
        self.errmsg = errmsg
        super().__init__(self.__str__())

    def __str__(self):
        return f"微信接口错误 - 错误码: {self.errcode}, 错误信息: {self.errmsg}"


class WechatPayAPIV3Mixin:
    WECHAT_PAY_V3_BASE_URL = "https://api.mch.weixin.qq.com"
    WECHAT_PAY_V3_TRANSACTIONS_JSAPI_URL = "/v3/pay/transactions/jsapi"
    WECHAT_PAY_V3_TRANSACTIONS_NATIVE_URL = "/v3/pay/transactions/native"
    WECHAT_PAY_V3_TRANSACTIONS_OUT_TRADE_NO_URL = "/v3/pay/transactions/out-trade-no/{out_trade_no}"
    WECHAT_PAY_V3_TRANSACTIONS_CLOSE_URL = "/v3/pay/transactions/out-trade-no/{out_trade_no}/close"
    WECHAT_PAY_V3_REFUND_URL = "/v3/refund/domestic/refunds"

    @property
    def appid(self):
        return config.WECHAT_PAY_APP_ID or config.WECHAT_APP_ID

    @property
    def mch_id(self):
        return config.WECHAT_PAY_MCH_ID

    @property
    def serial_no(self):
        return config.WECHAT_PAY_SERIAL_NO

    @property
    def api_v3_key(self):
        return config.WECHAT_PAY_API_V3_KEY

    @property
    def private_key(self):
        return config.WECHAT_PAY_PRIVATE_KEY

    def _generate_v3_sign(self, method: str, url_path: str, body: str, nonce_str: str, timestamp: str) -> str:
        sign_str = f"{method.upper()}\n{url_path}\n{timestamp}\n{nonce_str}\n{body}\n"
        try:
            private_key = load_pem_private_key(self.private_key.encode("utf-8"), password=None)
            signature = private_key.sign(sign_str.encode("utf-8"), padding.PKCS1v15(), hashes.SHA256())
            return base64.b64encode(signature).decode("utf-8")
        except Exception as e:
            traceback.print_exc()
            logger.error("生成API v3签名失败: %s", str(e))
            Log.error(
                "微信支付API：生成V3签名失败",
                f"{e}\n{tb_for_log()}",
                LogModel.Module.WECHAT_PAY,
            )
            raise WechatAPIException(-1, "生成API v3签名失败")

    def _build_authorization(self, method: str, url_path: str, body: str) -> str:
        timestamp = str(int(time.time()))
        nonce_str = str(uuid.uuid4()).replace("-", "")
        signature = self._generate_v3_sign(method, url_path, body, nonce_str, timestamp)
        auth_parts = [
            f'mchid="{self.mch_id}"',
            f'nonce_str="{nonce_str}"',
            f'timestamp="{timestamp}"',
            f'serial_no="{self.serial_no}"',
            f'signature="{signature}"',
        ]
        return f'WECHATPAY2-SHA256-RSA2048 {",".join(auth_parts)}'

    def get_pay_prepay_id(
        self,
        order_id: str,
        openid: str,
        total_fee_minor: int,
        description: str,
        base_url: Optional[str] = None,
        time_expire: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        base = base_url.rstrip("/") if base_url else settings.BASE_URL.rstrip("/")
        notify_url = (config.WECHAT_PAY_NOTIFY_URL or "").strip() or (base + reverse("wechat:pay_notify"))
        data = {
            "appid": self.appid,
            "mchid": self.mch_id,
            "description": truncate_string_if_needed(description, 120),
            "out_trade_no": order_id,
            "notify_url": notify_url,
            "amount": {"total": int(total_fee_minor), "currency": "CNY"},
            "payer": {"openid": openid},
        }
        if time_expire is not None:
            if time_expire.tzinfo is None:
                raise ValueError("time_expire must be a timezone-aware datetime object")
            data["time_expire"] = time_expire.isoformat()
        return self._request_json("POST", self.WECHAT_PAY_V3_TRANSACTIONS_JSAPI_URL, data)

    def get_native_code_url(
        self,
        order_id: str,
        total_fee_minor: int,
        description: str,
        base_url: Optional[str] = None,
        time_expire: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        base = base_url.rstrip("/") if base_url else settings.BASE_URL.rstrip("/")
        notify_url = (config.WECHAT_PAY_NOTIFY_URL or "").strip() or (base + reverse("wechat:pay_notify"))
        data = {
            "appid": self.appid,
            "mchid": self.mch_id,
            "description": truncate_string_if_needed(description, 120),
            "out_trade_no": order_id,
            "notify_url": notify_url,
            "amount": {"total": int(total_fee_minor), "currency": "CNY"},
        }
        if time_expire is not None:
            if time_expire.tzinfo is None:
                raise ValueError("time_expire must be a timezone-aware datetime object")
            data["time_expire"] = time_expire.isoformat()
        return self._request_json("POST", self.WECHAT_PAY_V3_TRANSACTIONS_NATIVE_URL, data)

    def get_pay_sign(self, prepay_id: str) -> Dict[str, Any]:
        timestamp = str(int(time.time()))
        nonce_str = str(uuid.uuid4()).replace("-", "")
        package = f"prepay_id={prepay_id}"
        message = f"{self.appid}\n{timestamp}\n{nonce_str}\n{package}\n"
        try:
            private_key = load_pem_private_key(self.private_key.encode("utf-8"), password=None)
            signature = private_key.sign(message.encode("utf-8"), padding.PKCS1v15(), hashes.SHA256())
            sign = base64.b64encode(signature).decode("utf-8")
            return {
                "appId": self.appid,
                "timeStamp": timestamp,
                "nonceStr": nonce_str,
                "package": package,
                "signType": "RSA",
                "paySign": sign,
            }
        except Exception as e:
            traceback.print_exc()
            Log.error(
                "微信支付API：生成支付签名失败",
                f"{e}\n{tb_for_log()}",
                LogModel.Module.WECHAT_PAY,
            )
            raise WechatAPIException(-1, f"生成支付签名失败: {str(e)}")

    def get_pay_transaction(self, out_trade_no: str) -> Dict[str, Any]:
        api_path = self.WECHAT_PAY_V3_TRANSACTIONS_OUT_TRADE_NO_URL.format(out_trade_no=out_trade_no)
        api_path = f"{api_path}?mchid={self.mch_id}"
        return self._request_json("GET", api_path, None)

    def close_pay_transaction(self, out_trade_no: str) -> bool:
        api_path = self.WECHAT_PAY_V3_TRANSACTIONS_CLOSE_URL.format(out_trade_no=out_trade_no)
        self._request_json("POST", api_path, {"mchid": self.mch_id})
        return True

    def create_refund(
        self,
        out_trade_no: str,
        out_refund_no: str,
        reason: str,
        total_amount_minor: int,
        refund_amount_minor: int,
    ) -> Dict[str, Any]:
        base = settings.BASE_URL.rstrip("/")
        notify_url = (config.WECHAT_PAY_REFUND_NOTIFY_URL or "").strip() or (base + reverse("wechat:refund_notify"))
        data = {
            "out_trade_no": out_trade_no,
            "out_refund_no": out_refund_no,
            "reason": truncate_string_if_needed(reason, 70),
            "notify_url": notify_url,
            "amount": {
                "refund": int(refund_amount_minor),
                "total": int(total_amount_minor),
                "currency": "CNY",
            },
        }
        return self._request_json("POST", self.WECHAT_PAY_V3_REFUND_URL, data)

    def verify_notify_signature(self, headers: Dict[str, str], body: str) -> None:
        verify_public_key_pem = (config.WECHAT_PAY_VERIFY_PUBLIC_KEY_PEM or "").strip()
        verify_key_id = (config.WECHAT_PAY_VERIFY_KEY_ID or "").strip()
        if not verify_public_key_pem:
            raise WechatAPIException(-1, "未配置微信回调验签公钥")
        timestamp = headers.get("Wechatpay-Timestamp") or headers.get("wechatpay-timestamp")
        nonce = headers.get("Wechatpay-Nonce") or headers.get("wechatpay-nonce")
        signature_b64 = headers.get("Wechatpay-Signature") or headers.get("wechatpay-signature")
        serial = headers.get("Wechatpay-Serial") or headers.get("wechatpay-serial")
        if not (timestamp and nonce and signature_b64):
            raise WechatAPIException(-1, "缺少微信回调签名头")
        if verify_key_id and serial and verify_key_id != serial:
            raise WechatAPIException(-1, "回调公钥ID不匹配")
        message = f"{timestamp}\n{nonce}\n{body}\n".encode("utf-8")
        signature = base64.b64decode(signature_b64)
        try:
            public_key = load_pem_public_key(verify_public_key_pem.encode("utf-8"))
        except ValueError:
            cert = x509.load_pem_x509_certificate(verify_public_key_pem.encode("utf-8"))
            public_key = cert.public_key()
        public_key.verify(signature, message, padding.PKCS1v15(), hashes.SHA256())

    def decrypt_payment_notify(self, resource: dict) -> dict:
        try:
            nonce = resource.get("nonce", "").encode("utf-8")
            ciphertext = base64.b64decode(resource.get("ciphertext", ""))
            associated_data = resource.get("associated_data", "")
            ad_bytes = associated_data.encode("utf-8") if associated_data else None
            aesgcm = AESGCM(self.api_v3_key.encode("utf-8"))
            plain = aesgcm.decrypt(nonce, ciphertext, ad_bytes)
            return json.loads(plain.decode("utf-8"))
        except Exception as e:
            traceback.print_exc()
            Log.error(
                "微信支付API：解密通知数据失败",
                f"{e}\n{tb_for_log()}",
                LogModel.Module.WECHAT_PAY,
            )
            raise WechatAPIException(-1, f"解密通知数据失败: {str(e)}")

    def verify_and_decrypt_notify(self, headers: Dict[str, str], raw_body: str) -> dict:
        self.verify_notify_signature(headers, raw_body)
        notify_body = json.loads(raw_body)
        return self.decrypt_payment_notify(notify_body.get("resource", {}))

    def _request_json(self, method: str, api_path: str, data: Optional[dict]) -> Dict[str, Any]:
        json_data = "" if data is None else json.dumps(data, ensure_ascii=False)
        authorization = self._build_authorization(method, api_path, json_data)
        response = requests.request(
            method=method.upper(),
            url=f"{self.WECHAT_PAY_V3_BASE_URL}{api_path}",
            data=json_data.encode("utf-8") if json_data else None,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Authorization": authorization,
            },
            timeout=30,
        )
        if response.status_code in (200, 201, 204):
            if response.content:
                return response.json()
            return {}
        try:
            result = response.json()
            exc = WechatAPIException(result.get("code", response.status_code), result.get("message", "未知错误"))
            Log.error(
                "微信支付API：HTTP 非成功",
                f"path={api_path} status={response.status_code} body={result}\n\n{tb_for_log(exc)}",
                LogModel.Module.WECHAT_PAY,
            )
            raise exc
        except ValueError:
            exc = WechatAPIException(response.status_code, response.text[:200])
            Log.error(
                "微信支付API：HTTP 非成功（非 JSON）",
                f"path={api_path} status={response.status_code} text={response.text[:500]}\n\n{tb_for_log()}",
                LogModel.Module.WECHAT_PAY,
            )
            raise exc


class WechatAPI(WechatPayAPIV3Mixin):
    pass
