# django_oss_storage 依赖的 Django API 在 4.0+ 有变更，在此做兼容
import django.utils.encoding as _encoding
if not hasattr(_encoding, "force_text"):
    _encoding.force_text = _encoding.force_str

import django.utils.timezone as _timezone
if not hasattr(_timezone, "utc"):
    from datetime import timezone as _dt_timezone
    _timezone.utc = _dt_timezone.utc

from django_oss_storage.backends import OssMediaStorage


class MyOssMediaStorage(OssMediaStorage):
    def path(self, name):
        key = self._get_key_name(name)
        return key
